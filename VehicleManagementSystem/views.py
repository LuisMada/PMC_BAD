from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, VehicleForm, VehicleDamageForm, VehicleFilterForm, PasswordChangeForm
from django.db.models import Q
from django.http import JsonResponse
from .models import Vehicle, VehicleDamage, VehicleInspection, CustomUser

from django.core.paginator import Paginator
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

@login_required
def view_reports(request):
    """View to display all inspection reports"""
    # Get all vehicle inspection reports
    reports = VehicleInspection.objects.all().order_by('-inspection_date')
    
    # If user is not from Vehicle Management Team, only show reports they have access to
    if request.user.role != "Vehicle Management Team":
        # Warehouse Personnel can see reports they created
        if request.user.role == "Warehouse Personnel":
            reports = reports.filter(inspector=request.user)
        # Operations Team can see all reports (for now, can be restricted if needed)
    
    # Set up pagination
    paginator = Paginator(reports, 10)  # Show 10 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reports': page_obj.object_list,
    }
    
    return render(request, "VehicleManagementSystem/view_reports.html", context)

@login_required
def create_report(request):
    # Check if user has the correct role
    if request.user.role != "Warehouse Personnel":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    vehicles = Vehicle.objects.filter(status='Operational')
    
    if request.method == "POST":
        vehicle_id = request.POST.get('vehicle')
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        action = request.POST.get('action', 'submit')
        report_id = request.POST.get('report_id')
        
        # Determine if we're updating or creating
        if report_id:
            # Updating existing report
            inspection = get_object_or_404(VehicleInspection, report_id=report_id)
            if inspection.inspector != request.user:
                messages.error(request, "You don't have permission to edit this report.")
                return redirect("view_reports")
                
            # If report is already submitted/completed, don't allow edits
            if inspection.is_submitted:
                messages.error(request, "This report has already been submitted and cannot be edited.")
                return redirect("view_reports")
        else:
            # Create new inspection
            inspection = VehicleInspection(
                vehicle=vehicle,
                inspector=request.user,
                inspection_date=request.POST.get('inspection_date'),
                driver_name=request.POST.get('driver_name', '')
            )
        
        # Update pre-delivery fields if they exist in POST
        if 'pre_battery' in request.POST:
            inspection.pre_battery = request.POST.get('pre_battery')
            inspection.pre_lights = request.POST.get('pre_lights')
            inspection.pre_oil = request.POST.get('pre_oil')
            inspection.pre_water = request.POST.get('pre_water')
            inspection.pre_brakes = request.POST.get('pre_brakes')
            inspection.pre_air = request.POST.get('pre_air')
            inspection.pre_gas = request.POST.get('pre_gas')
            inspection.pre_comments = request.POST.get('pre_comments', '')
            inspection.pre_damages = request.POST.get('pre_damages', '')
        
        # Update post-delivery fields if they exist in POST
        if 'post_battery' in request.POST:
            inspection.post_battery = request.POST.get('post_battery')
            inspection.post_lights = request.POST.get('post_lights')
            inspection.post_oil = request.POST.get('post_oil')
            inspection.post_water = request.POST.get('post_water')
            inspection.post_brakes = request.POST.get('post_brakes')
            inspection.post_air = request.POST.get('post_air')
            inspection.post_gas = request.POST.get('post_gas')
            inspection.post_comments = request.POST.get('post_comments', '')
            inspection.post_damages = request.POST.get('post_damages', '')
        
        # Only mark as submitted if the action is 'submit'
        if action == 'submit':
            inspection.is_submitted = True
        
        # Update completion status based on filled fields
        inspection.update_completion_status()
        inspection.save()
        
        if action == 'save_exit':
            messages.success(request, "Report saved successfully. You can complete it later.")
            return redirect('view_reports')
        else:  # submit action
            messages.success(request, "Vehicle inspection report completed successfully!")
            return redirect('generate_report_pdf', report_id=inspection.report_id)
    
    # Check if we're editing an existing report
    report_id = request.GET.get('report_id')
    if report_id:
        try:
            inspection = VehicleInspection.objects.get(report_id=report_id)
            
            # Don't allow editing submitted reports
            if inspection.is_submitted:
                messages.error(request, "This report has already been submitted and cannot be edited.")
                return redirect("view_reports")
                
            if inspection.inspector != request.user:
                messages.error(request, "You don't have permission to edit this report.")
                return redirect("view_reports")
            
            context = {
                'vehicles': vehicles,
                'inspection': inspection,
                'editing': True
            }
        except VehicleInspection.DoesNotExist:
            messages.error(request, "Report not found.")
            return redirect("view_reports")
    else:
        context = {
            'vehicles': vehicles
        }
    
    return render(request, "VehicleManagementSystem/create_report.html", context)

# Add to views.py
@login_required
def delete_report(request, report_id):
    """View to handle report deletion"""
    # Get the report
    report = get_object_or_404(VehicleInspection, report_id=report_id)
    
    # Security checks
    if request.user.role != "Warehouse Personnel" or report.inspector != request.user:
        messages.error(request, "You don't have permission to delete this report.")
        return redirect("view_reports")
    
    # Only allow deletion of non-submitted reports
    if report.is_submitted:
        messages.error(request, "Completed reports cannot be deleted.")
        return redirect("view_reports")
    
    # Ensure POST method for deletion (security)
    if request.method == "POST":
        report.delete()
        messages.success(request, f"Report #{report_id} has been deleted.")
        return redirect("view_reports")
    
    # If not POST, redirect to reports view
    return redirect("view_reports")


@login_required
def generate_report_pdf(request, report_id):
    # Get the inspection report
    inspection = get_object_or_404(VehicleInspection, report_id=report_id)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vehicle_inspection_{inspection.report_id}.pdf"'
    
    # Create the PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add title
    elements.append(Paragraph("Vehicle Inspection Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add basic information
    elements.append(Paragraph("Basic Information", subtitle_style))
    
    # Vehicle and Inspector Information
    vehicle_info = [
        ["Report ID:", str(inspection.report_id)],
        ["Vehicle:", f"{inspection.vehicle.vehicle_make} - {inspection.vehicle.vehicle_model} ({inspection.vehicle.plate_number})"],
        ["Inspector:", inspection.inspector.name],
        ["Date:", inspection.inspection_date.strftime("%Y-%m-%d")],
    ]
    
    # Create vehicle info table
    info_table = Table(vehicle_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Pre-Delivery Inspection
    elements.append(Paragraph("Pre-Delivery Inspection", subtitle_style))
    
    pre_inspection_data = [
        ["Component", "Status"],
        ["Battery", inspection.pre_battery],
        ["Lights", inspection.pre_lights],
        ["Oil", inspection.pre_oil],
        ["Water", inspection.pre_water],
        ["Brakes", inspection.pre_brakes],
        ["Air", inspection.pre_air],
        ["Gas", inspection.pre_gas],
    ]
    
    pre_table = Table(pre_inspection_data, colWidths=[3*inch, 3*inch])
    pre_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(pre_table)
    
    # Add pre-delivery comments
    elements.append(Paragraph("Comments:", normal_style))
    elements.append(Paragraph(inspection.pre_comments or "No comments", normal_style))
    
    # Add pre-delivery damages
    elements.append(Paragraph("Damages:", normal_style))
    elements.append(Paragraph(inspection.pre_damages or "No damages reported", normal_style))
    
    elements.append(Spacer(1, 0.25*inch))
    
    # Post-Delivery Inspection
    elements.append(Paragraph("Post-Delivery Inspection", subtitle_style))
    
    post_inspection_data = [
        ["Component", "Status"],
        ["Battery", inspection.post_battery],
        ["Lights", inspection.post_lights],
        ["Oil", inspection.post_oil],
        ["Water", inspection.post_water],
        ["Brakes", inspection.post_brakes],
        ["Air", inspection.post_air],
        ["Gas", inspection.post_gas],
    ]
    
    post_table = Table(post_inspection_data, colWidths=[3*inch, 3*inch])
    post_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(post_table)
    
    # Add post-delivery comments
    elements.append(Paragraph("Comments:", normal_style))
    elements.append(Paragraph(inspection.post_comments or "No comments", normal_style))
    
    # Add post-delivery damages
    elements.append(Paragraph("Damages:", normal_style))
    elements.append(Paragraph(inspection.post_damages or "No damages reported", normal_style))
    
    # Add signature lines
    elements.append(Spacer(1, inch))
    
    signature_data = [
        ["Inspector Signature", "Driver Signature"],
        ["____________________", "____________________"],
        [f"Name: {inspection.inspector.name}", "Name: ________________"],
    ]
    
    sig_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(sig_table)
    
    # Build PDF document
    doc.build(elements)
    
    return response


@login_required
def manage_vehicles(request):
    # Check if user has permissions (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    filter_form = VehicleFilterForm(request.GET)
    vehicles = Vehicle.objects.all()
    
    # Apply filters if provided
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        search = filter_form.cleaned_data.get('search')
        
        if status:
            vehicles = vehicles.filter(status=status)
            
        if search:
            vehicles = vehicles.filter(
                Q(plate_number__icontains=search) | 
                Q(vehicle_make__icontains=search) | 
                Q(vehicle_model__icontains=search)
            )
    
    # Count vehicles by status
    operational_count = vehicles.filter(status='Operational').count()
    repair_count = vehicles.filter(status='In Repair').count()
    unavailable_count = vehicles.filter(status='Unavailable').count()
    
    context = {
        'vehicles': vehicles,
        'filter_form': filter_form,
        'operational_count': operational_count,
        'repair_count': repair_count,
        'unavailable_count': unavailable_count
    }
    
    return render(request, "VehicleManagementSystem/manage_vehicles.html", context)

@login_required
def add_vehicle(request):
    print("Add vehicle view called")
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    if request.method == "POST":
        print("POST request received")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            vehicle = form.save()
            print(f"Vehicle saved with ID: {vehicle.vehicle_id}")
            messages.success(request, "Vehicle added successfully!")
            return redirect("manage_vehicles")
        else:
            print("Form errors:", form.errors)
    else:
        form = VehicleForm()
    
    return render(request, "VehicleManagementSystem/add_vehicle.html", {"form": form})

@login_required
def edit_vehicle(request, plate_number):
    # Check if user has permissions (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)
    damages = vehicle.damages.all().order_by('-date_reported')
    
    if request.method == "POST":
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated successfully!")
            return redirect("manage_vehicles")
    else:
        form = VehicleForm(instance=vehicle)
    
    damage_form = VehicleDamageForm()
    
    context = {
        "form": form,
        "vehicle": vehicle,
        "damages": damages,
        "damage_form": damage_form
    }
    
    return render(request, "VehicleManagementSystem/edit_vehicle.html", context)

@login_required
def delete_vehicle(request, plate_number):
    # Check if user has permissions (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)
    
    if request.method == "POST":
        vehicle.delete()
        messages.success(request, f"Vehicle {plate_number} has been deleted.")
        return redirect("manage_vehicles")
    
    return render(request, "VehicleManagementSystem/delete_vehicle_confirm.html", {"vehicle": vehicle})

@login_required
def add_vehicle_damage(request, plate_number):
    # Check if user has permissions (Vehicle Management Team or Warehouse Personnel)
    if request.user.role not in ["Vehicle Management Team", "Warehouse Personnel"]:
        messages.error(request, "You don't have permission to add damage reports.")
        return redirect("WH_dashboard")
        
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)
    
    if request.method == "POST":
        form = VehicleDamageForm(request.POST)
        if form.is_valid():
            damage = form.save(commit=False)
            damage.vehicle = vehicle
            damage.save()
            messages.success(request, "Damage report added successfully!")
            return redirect("edit_vehicle", plate_number=plate_number)
    
    # If not POST or form invalid, redirect back to edit page
    return redirect("edit_vehicle", plate_number=plate_number)

def login_view(request):
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        password = request.POST.get("password")

        if not employee_id or not password:
            messages.error(request, "Employee ID or password missing.")
            return render(request, "VehicleManagementSystem/login.html")

        user = authenticate(request, employee_id=employee_id, password=password)
        if user is not None:
            login(request, user)

            # Check if user needs to change password on first login
            if user.first_login:
                return redirect("change_password")

            # Redirect based on role
            if user.role == "Operations Team":
                return redirect("OPS_dashboard")
            elif user.role == "Vehicle Management Team":
                return redirect("VMT_dashboard")
            else:
                return redirect("WH_dashboard")
        else:
            messages.error(request, "Invalid Employee ID or password.")

    return render(request, "VehicleManagementSystem/login.html")

@login_required
def change_password(request):
    """View for changing password on first login or when requested"""
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get("current_password")
            new_password = form.cleaned_data.get("new_password")
            
            # Verify current password
            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                return render(request, "VehicleManagementSystem/change_password.html", {"form": form})
            
            # Set new password and mark as not first login
            request.user.set_password(new_password)
            request.user.first_login = False
            request.user.save()
            
            # Re-authenticate with new password
            user = authenticate(request, employee_id=request.user.employee_id, password=new_password)
            if user is not None:
                login(request, user)
                messages.success(request, "Password changed successfully!")
                
                # Redirect based on role
                if user.role == "Operations Team":
                    return redirect("OPS_dashboard")
                elif user.role == "Vehicle Management Team":
                    return redirect("VMT_dashboard")
                else:
                    return redirect("WH_dashboard")
    else:
        form = PasswordChangeForm()
    
    return render(request, "VehicleManagementSystem/change_password.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

def register_view(request):
    # Only Vehicle Management Team can register users
    if request.user.is_authenticated and request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to register users.")
        return redirect("WH_dashboard")
  
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.name}! Temporary password: 00000000")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, "VehicleManagementSystem/register.html", {"form": form})

@login_required
def management_dashboard(request):
    # Check if user has the correct role
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    # Fetch all vehicles from the database
    vehicles = Vehicle.objects.all()
    
    # Count vehicles by status
    operational_count = Vehicle.objects.filter(status='Operational').count()
    repair_count = Vehicle.objects.filter(status='In Repair').count()
    unavailable_count = Vehicle.objects.filter(status='Unavailable').count()
    
    context = {
        'vehicles': vehicles,
        'operational_count': operational_count,
        'repair_count': repair_count,
        'unavailable_count': unavailable_count
    }
    
    return render(request, "VehicleManagementSystem/VMT_dashboard.html", context)

@login_required
def dashboard(request):
    # Fetch real vehicles from the database instead of using sample data
    vehicles = Vehicle.objects.all()
    
    return render(request, "VehicleManagementSystem/WH_dashboard.html", {"vehicles": vehicles})

@login_required
def driver_dashboard(request):
    # Check if user has the correct role
    if request.user.role != "Operations Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    # Fetch real vehicles from the database instead of using sample data
    vehicles = Vehicle.objects.all()
    
    return render(request, "VehicleManagementSystem/OPS_dashboard.html", {"vehicles": vehicles})

