import datetime
import os
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, VehicleForm, VehicleDamageForm, VehicleFilterForm, PasswordChangeForm, DamageReportForm
from django.db.models import Q
from django.http import JsonResponse
from .models import Vehicle, VehicleDamage, VehicleInspection, CustomUser, DamageReport

from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

import cloudinary
import cloudinary.uploader
import cloudinary.api

def debug_cloudinary(request):
    """Detailed debugging for Cloudinary configuration."""
    try:
        # Check environment variables
        env_vars = {
            'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
            'CLOUDINARY_API_KEY': os.environ.get('CLOUDINARY_API_KEY', '[HIDDEN]'),
            'CLOUDINARY_API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', '[HIDDEN]')
        }
        
        # Check Cloudinary config
        cloudinary_config = {
            'cloud_name': cloudinary.config().cloud_name,
            'api_key': '[HIDDEN]' if cloudinary.config().api_key else None,
            'api_secret': '[HIDDEN]' if cloudinary.config().api_secret else None
        }
        
        # Try a test upload
        try:
            # Create a simple 1x1 pixel image for testing
            import base64
            test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"
            test_image = base64.b64decode(test_image_data)
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                test_image,
                public_id="debug_test",
                folder="media/test",
                overwrite=True
            )
            
            # Get URL of the uploaded image
            image_url = upload_result.get('secure_url')
        except Exception as upload_error:
            upload_result = str(upload_error)
            image_url = None
        
        return JsonResponse({
            'status': 'debug_info', 
            'env_vars': env_vars,
            'cloudinary_config': cloudinary_config,
            'upload_test': {
                'success': image_url is not None,
                'url': image_url,
                'result': upload_result if image_url else str(upload_result)
            },
            'media_settings': {
                'MEDIA_URL': settings.MEDIA_URL,
                'DEFAULT_FILE_STORAGE': settings.DEFAULT_FILE_STORAGE
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def test_cloudinary(request):
    """Test if Cloudinary is configured correctly."""
    try:
        # Try to access Cloudinary account info
        result = cloudinary.api.ping()
        
        # If you want to test upload, uncomment this:
        # test_upload = cloudinary.uploader.upload(
        #     "https://res.cloudinary.com/demo/image/upload/sample.jpg",
        #     public_id="test_connection",
        #     overwrite=True
        # )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Cloudinary connection successful',
            'cloudinary_url': cloudinary.config().cloud_name
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

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
            
            # Generate PDF with automatic redirect to dashboard
            pdf_url = reverse('generate_report_pdf', kwargs={'report_id': inspection.report_id})
            dashboard_url = reverse('WH_dashboard')
            
            # Return a page that initiates the PDF download and then redirects
            return render(request, 'VehicleManagementSystem/pdf_download_redirect.html', {
                'pdf_url': pdf_url,
                'redirect_url': dashboard_url
            })
    
    # Check if we're editing an existing report
    report_id = request.GET.get('report_id')
    preselected_vehicle_id = request.GET.get('vehicle_id')
    preselected_vehicle = None
    
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
        # Check if a vehicle ID was provided (from dashboard)
        if preselected_vehicle_id:
            try:
                preselected_vehicle = Vehicle.objects.get(vehicle_id=preselected_vehicle_id)
                # Check if the vehicle is operational
                if preselected_vehicle.status != 'Operational':
                    messages.warning(request, f"Vehicle {preselected_vehicle} is {preselected_vehicle.status} and may not be suitable for a new inspection.")
            except Vehicle.DoesNotExist:
                messages.error(request, "Selected vehicle not found.")
        
        context = {
            'vehicles': vehicles,
            'preselected_vehicle': preselected_vehicle,
            'today': datetime.date.today().strftime('%Y-%m-%d')  # Add today's date as default
        }
    
    return render(request, "VehicleManagementSystem/create_report.html", context)
    
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
    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1  # Center alignment
    normal_style = styles['Normal']
    
    # Create company heading
    logo_text = Paragraph("PETROZONE MARKETING CORPORATION", title_style)
    elements.append(logo_text)
    subtitle = Paragraph("Vehicle Management System", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.25*inch))
    
    # Create the inspection report title with a blue background
    report_title_data = [["VEHICLE INSPECTION REPORT"]]
    report_title_table = Table(report_title_data, colWidths=[6.5*inch])
    report_title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.2, 0.3, 0.7)),  # Dark blue
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('PADDING', (0, 0), (0, 0), 6),
    ]))
    elements.append(report_title_table)
    
    # Basic information table
    basic_info_data = [
        ["Date of Inspection", f"{inspection.inspection_date.strftime('%Y-%m-%d')}", "", ""],
        ["General Information", "", "", ""],
        ["Assigned Inspector", f"{inspection.inspector.name}", "", ""],
        ["ID Number", f"{inspection.inspector.employee_id}", "Driver", f"{inspection.driver_name or ''}"],
        ["Vehicle Model", f"{inspection.vehicle.vehicle_make} - {inspection.vehicle.vehicle_model}", 
         "Vehicle Plate Number", f"{inspection.vehicle.plate_number}"],
    ]
    
    # Create a table with the layout seen in the image
    col_widths = [1.625*inch, 1.625*inch, 1.625*inch, 1.625*inch]
    basic_info_table = Table(basic_info_data, colWidths=col_widths)
    
    # Apply styles to match the image
    basic_info_table.setStyle(TableStyle([
        # Borders around all cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Merge cells for Date row
        ('SPAN', (1, 0), (3, 0)),
        
        # Merge cells for General Information row - span ALL columns
        ('SPAN', (0, 1), (3, 1)),
        
        # Merge cells for Assigned Inspector row
        ('SPAN', (1, 2), (3, 2)),
        
        # Background color for General Information
        ('BACKGROUND', (0, 1), (3, 1), colors.white),
        ('ALIGN', (0, 1), (3, 1), 'CENTER'),
        ('FONTNAME', (0, 1), (3, 1), 'Helvetica-Bold'),
    ]))
    elements.append(basic_info_table)
    
    # Pre-Delivery Checklist title
    pre_delivery_title_data = [["Pre-Delivery Checklist"]]
    pre_delivery_title_table = Table(pre_delivery_title_data, colWidths=[6.5*inch])
    pre_delivery_title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (0, 0), 1, colors.black),
    ]))
    elements.append(pre_delivery_title_table)
    
    # Pre-Delivery Component Table
    pre_header = [["Vehicle Components", "Status", "Comments"]]
    pre_components = [
        ["Battery", inspection.pre_battery or "", inspection.pre_comments or ""],
        ["Lights", inspection.pre_lights or "", ""],
        ["Oil", inspection.pre_oil or "", ""],
        ["Water", inspection.pre_water or "", ""],
        ["Brakes", inspection.pre_brakes or "", ""],
        ["Air", inspection.pre_air or "", ""],
        ["Gas", inspection.pre_gas or "", ""]
    ]
    
    pre_component_data = pre_header + pre_components
    pre_col_widths = [1.65*inch, 1.65*inch, 3.2*inch]
    pre_component_table = Table(pre_component_data, colWidths=pre_col_widths)
    
    # Apply styles to match the image
    pre_component_table.setStyle(TableStyle([
        # Borders around all cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Center alignment for header row
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
        # Merge cells for Comments
        ('SPAN', (2, 1), (2, 7)),
    ]))
    elements.append(pre_component_table)
    
    # Post-Delivery Checklist title
    post_delivery_title_data = [["Post-Delivery Checklist"]]
    post_delivery_title_table = Table(post_delivery_title_data, colWidths=[6.5*inch])
    post_delivery_title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (0, 0), 1, colors.black),
    ]))
    elements.append(post_delivery_title_table)
    
    # Post-Delivery Component Table
    post_header = [["Vehicle Components", "Status", "Comments"]]
    post_components = [
        ["Battery", inspection.post_battery or "", inspection.post_comments or ""],
        ["Lights", inspection.post_lights or "", ""],
        ["Oil", inspection.post_oil or "", ""],
        ["Water", inspection.post_water or "", ""],
        ["Brakes", inspection.post_brakes or "", ""],
        ["Air", inspection.post_air or "", ""],
        ["Gas", inspection.post_gas or "", ""]
    ]
    
    post_component_data = post_header + post_components
    post_col_widths = [1.65*inch, 1.65*inch, 3.2*inch]
    post_component_table = Table(post_component_data, colWidths=post_col_widths)
    
    # Apply styles to match the image
    post_component_table.setStyle(TableStyle([
        # Borders around all cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Center alignment for header row
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
        # Merge cells for Comments
        ('SPAN', (2, 1), (2, 7)),
    ]))
    elements.append(post_component_table)
    
    # Damages Incurred section - using post_damages only
    damages_title_data = [["Damages Incurred"]]
    damages_title_table = Table(damages_title_data, colWidths=[6.5*inch])
    damages_title_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
    ]))
    elements.append(damages_title_table)
    
    # Damages content from post_damages
    damages_content = [
        [inspection.post_damages or "No damages incurred"]
    ]
    damages_content_table = Table(damages_content, colWidths=[6.5*inch], rowHeights=[1.5*inch])
    damages_content_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
    ]))
    elements.append(damages_content_table)
    
    # Removed signature section as requested
    
    # Build PDF document
    doc.build(elements)
    
    # Set a session flag to indicate PDF download and redirect to dashboard
    request.session['pdf_downloaded'] = True
    
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
    
    # Get damage reports associated with this vehicle
    damage_reports = DamageReport.objects.filter(vehicle=vehicle).order_by('-created_at')
    
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
        "damage_form": damage_form,
        "damage_reports": damage_reports  # Add damage reports to the context
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
            # Create the user without saving yet
            user = form.save(commit=False)
            
            # Explicitly set the password and first_login flag
            user.set_password("00000000")
            user.first_login = True
            user.save()
            
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
    
    # Create filter form
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
    
    return render(request, "VehicleManagementSystem/VMT_dashboard.html", context)

@login_required
def dashboard(request):
    # Create filter form
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
    
    return render(request, "VehicleManagementSystem/WH_dashboard.html", context)

@login_required
def driver_dashboard(request):
    # Check if user has the correct role
    if request.user.role != "Operations Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    # Create filter form
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
        'filter_form': filter_form,  # This comma was missing
        'operational_count': operational_count,
        'repair_count': repair_count,
        'unavailable_count': unavailable_count
    }
    
    return render(request, "VehicleManagementSystem/OPS_dashboard.html", context)

@login_required
def view_accounts(request):
    """View to display all user accounts for VMT team members"""
    # Check if user has the correct role (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    # Get all user accounts
    accounts = CustomUser.objects.all().order_by('employee_id')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        accounts = accounts.filter(
            Q(employee_id__icontains=search_query) | 
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    # Set up pagination
    paginator = Paginator(accounts, 10)  # Show 10 accounts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'accounts': page_obj.object_list,
        'search_query': search_query
    }
    
    return render(request, "VehicleManagementSystem/view_accounts.html", context)

@login_required
def edit_account(request, employee_id):
    """View to edit a user account"""
    # Check if user has the correct role (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    # Get the user account
    account = get_object_or_404(CustomUser, employee_id=employee_id)
    
    if request.method == "POST":
        # Create a form instance with the submitted data
        form = UserRegistrationForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account for {account.name} updated successfully!")
            return redirect("view_accounts")
    else:
        # Create a form instance with the account data
        form = UserRegistrationForm(instance=account)
    
    context = {
        'form': form,
        'account': account,
        'editing': True
    }
    
    return render(request, "VehicleManagementSystem/edit_account.html", context)

@login_required
def delete_account(request, employee_id):
    """View to handle account deletion"""
    # Check if user has the correct role (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    # Don't allow users to delete their own account
    if request.user.employee_id == employee_id:
        messages.error(request, "You cannot delete your own account.")
        return redirect("view_accounts")
        
    # Get the user account
    account = get_object_or_404(CustomUser, employee_id=employee_id)
    
    # Ensure POST method for deletion (security)
    if request.method == "POST":
        account_name = account.name
        account.delete()
        messages.success(request, f"Account for {account_name} has been deleted.")
        return redirect("view_accounts")
    
    context = {
        'account': account
    }
    
    return render(request, "VehicleManagementSystem/delete_account_confirm.html", context)

@login_required
def reset_password(request, employee_id):
    """View to reset a user's password to default"""
    # Check if user has the correct role (Vehicle Management Team)
    if request.user.role != "Vehicle Management Team":
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
        
    # Get the user account
    account = get_object_or_404(CustomUser, employee_id=employee_id)
    
    # Ensure POST method for password reset (security)
    if request.method == "POST":
        # Reset password to default
        account.set_password("00000000")
        account.first_login = True
        account.save()
        messages.success(request, f"Password for {account.name} has been reset. They will be prompted to change it on next login.")
        return redirect("view_accounts")
    
    return redirect("view_accounts")

# Add to views.py

@login_required
def create_damage_report(request):
    """View to create a damage report for a vehicle"""
    # Check if user has the correct role (Vehicle Management Team or Warehouse Personnel)
    if request.user.role not in ["Vehicle Management Team", "Warehouse Personnel"]:
        messages.error(request, "You don't have permission to access this page.")
        return redirect("WH_dashboard")
    
    vehicles = Vehicle.objects.all()
    
    if request.method == "POST":
        vehicle_id = request.POST.get('vehicle')
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        action = request.POST.get('action', 'submit')
        report_id = request.POST.get('report_id')
        redirect_to_dashboard = request.POST.get('redirect_to_dashboard') == 'true'
        
        # Determine if we're updating or creating
        if report_id:
            # Updating existing report
            damage_report = get_object_or_404(DamageReport, report_id=report_id)
            if damage_report.inspector != request.user:
                messages.error(request, "You don't have permission to edit this report.")
                return redirect("view_damage_reports")
                
            # If report is already submitted, don't allow edits
            if damage_report.is_submitted:
                messages.error(request, "This report has already been submitted and cannot be edited.")
                return redirect("view_damage_reports")
        else:
            # Create new damage report
            damage_report = DamageReport(
                vehicle=vehicle,
                inspector=request.user,
                inspection_date=request.POST.get('inspection_date')
            )
        
        # Update component damage fields
        damage_report.battery_damage = request.POST.get('battery_damage', '')
        damage_report.lights_damage = request.POST.get('lights_damage', '')
        damage_report.oil_damage = request.POST.get('oil_damage', '')
        damage_report.water_damage = request.POST.get('water_damage', '')
        damage_report.brakes_damage = request.POST.get('brakes_damage', '')
        damage_report.air_damage = request.POST.get('air_damage', '')
        damage_report.gas_damage = request.POST.get('gas_damage', '')
        
        # Update maintenance information
        damage_report.maintenance_diagnosis = request.POST.get('maintenance_diagnosis', '')
        damage_report.estimate_repair_time = request.POST.get('estimate_repair_time', '0')
        damage_report.concerns = request.POST.get('concerns', '')
        
        # Mark as submitted if the action is 'submit'
        if action == 'submit':
            damage_report.is_submitted = True
        
        damage_report.save()
        
        if action == 'save_exit':
            messages.success(request, "Damage report saved successfully. You can complete it later.")
            return redirect('view_damage_reports')
        else:  # submit action
            messages.success(request, "Damage report completed successfully!")
            
            # Generate PDF with automatic redirect to dashboard
            pdf_url = reverse('generate_damage_report_pdf', kwargs={'report_id': damage_report.report_id})
            
            # Determine the appropriate dashboard based on user role
            if request.user.role == "Vehicle Management Team":
                dashboard_url = reverse('VMT_dashboard')
            elif request.user.role == "Operations Team":
                dashboard_url = reverse('OPS_dashboard')
            else:
                dashboard_url = reverse('WH_dashboard')
            
            # Return a page that initiates the PDF download and then redirects
            return render(request, 'VehicleManagementSystem/pdf_download_redirect.html', {
                'pdf_url': pdf_url,
                'redirect_url': dashboard_url
            })
    
    # Check if we're editing an existing report
    report_id = request.GET.get('report_id')
    if report_id:
        try:
            damage_report = DamageReport.objects.get(report_id=report_id)
            
            # Don't allow editing submitted reports
            if damage_report.is_submitted:
                messages.error(request, "This report has already been submitted and cannot be edited.")
                return redirect("view_damage_reports")
                
            if damage_report.inspector != request.user:
                messages.error(request, "You don't have permission to edit this report.")
                return redirect("view_damage_reports")
            
            context = {
                'vehicles': vehicles,
                'damage_report': damage_report,
                'editing': True
            }
        except DamageReport.DoesNotExist:
            messages.error(request, "Report not found.")
            return redirect("view_damage_reports")
    else:
        context = {
            'vehicles': vehicles
        }
    
    return render(request, "VehicleManagementSystem/create_damage_report.html", context)

@login_required
def view_damage_reports(request):
    """View to display all damage reports"""
    # Get all damage reports
    reports = DamageReport.objects.all().order_by('-created_at')
    
    # If user is not from Vehicle Management Team, only show reports they created
    if request.user.role != "Vehicle Management Team":
        # Warehouse Personnel can see reports they created
        if request.user.role == "Warehouse Personnel":
            reports = reports.filter(inspector=request.user)
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        reports = reports.filter(
            Q(report_id__icontains=search_query) | 
            Q(vehicle__plate_number__icontains=search_query) | 
            Q(vehicle__vehicle_make__icontains=search_query) |
            Q(vehicle__vehicle_model__icontains=search_query)
        )
    
    # Set up pagination
    paginator = Paginator(reports, 10)  # Show 10 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reports': page_obj.object_list,
        'search_query': search_query
    }
    
    return render(request, "VehicleManagementSystem/view_damage_reports.html", context)

@login_required
def delete_damage_report(request, report_id):
    """View to handle damage report deletion"""
    # Get the report
    report = get_object_or_404(DamageReport, report_id=report_id)
    
    # Security checks
    if request.user.role not in ["Vehicle Management Team", "Warehouse Personnel"] or report.inspector != request.user:
        messages.error(request, "You don't have permission to delete this report.")
        return redirect("view_damage_reports")
    
    # Only allow deletion of non-submitted reports
    if report.is_submitted:
        messages.error(request, "Completed reports cannot be deleted.")
        return redirect("view_damage_reports")
    
    # Ensure POST method for deletion (security)
    if request.method == "POST":
        report.delete()
        messages.success(request, f"Damage Report {report_id} has been deleted.")
    
        return redirect("view_damage_reports")
    
    # If not POST, show confirmation page
    context = {
        'report': report
    }
    
    return render(request, "VehicleManagementSystem/delete_damage_report_confirm.html", context)

@login_required
def generate_damage_report_pdf(request, report_id):
    """View to generate a PDF of the damage report matching the template"""
    # Get the damage report
    damage_report = get_object_or_404(DamageReport, report_id=report_id)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="damage_report_{damage_report.report_id}.pdf"'
    
    # Create the PDF document
    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1  # Center alignment
    normal_style = styles['Normal']
    
    # Create company heading
    logo_text = Paragraph("PETROZONE MARKETING CORPORATION", title_style)
    elements.append(logo_text)
    subtitle = Paragraph("Vehicle Management System", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.25*inch))
    
    # Create the damage report title with a blue background
    report_title_data = [["VEHICLE DAMAGE REPORT"]]
    report_title_table = Table(report_title_data, colWidths=[6.5*inch])
    report_title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.2, 0.3, 0.7)),  # Dark blue
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('PADDING', (0, 0), (0, 0), 6),
        ('GRID', (0, 0), (0, 0), 1, colors.black),
    ]))
    elements.append(report_title_table)
    
    # Date information table
    date_info_data = [
        ["Date of Report", "Date of Last Inspection"],
        [damage_report.created_at.strftime("%Y-%m-%d"), damage_report.inspection_date.strftime("%Y-%m-%d")]
    ]
    date_info_table = Table(date_info_data, colWidths=[3.25*inch, 3.25*inch])
    date_info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),  # Light gray
    ]))
    elements.append(date_info_table)
    
    # General Information header
    general_info_header = [["General Information"]]
    general_header_table = Table(general_info_header, colWidths=[6.5*inch])
    general_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.9, 0.9, 0.9)),  # Light gray
    ]))
    elements.append(general_header_table)
    
    # General information data
    general_info_data = [
        ["Name", "ID Number"],
        [damage_report.inspector.name, damage_report.inspector.employee_id],
        ["Vehicle Plate Number", "Vehicle Model (Make)"],
        [damage_report.vehicle.plate_number, f"{damage_report.vehicle.vehicle_make} - {damage_report.vehicle.vehicle_model}"]
    ]
    general_info_table = Table(general_info_data, colWidths=[3.25*inch, 3.25*inch])
    general_info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
        ('BACKGROUND', (0, 2), (-1, 2), colors.Color(0.9, 0.9, 0.9)),
    ]))
    elements.append(general_info_table)
    
    # Maintenance Information header
    maintenance_header = [["MAINTENANCE INFORMATION"]]
    maintenance_header_table = Table(maintenance_header, colWidths=[6.5*inch])
    maintenance_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
    ]))
    elements.append(maintenance_header_table)
    
    # Accumulated Damages header
    accumulated_damages_header = [["Accumulated Damages"]]
    accumulated_header_table = Table(accumulated_damages_header, colWidths=[6.5*inch])
    accumulated_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.9, 0.9, 0.9)),
    ]))
    elements.append(accumulated_header_table)
    
    # Component damage table headers
    component_header = [["Vehicle Component/Section", "Description"]]
    component_header_table = Table(component_header, colWidths=[3.25*inch, 3.25*inch])
    component_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, 0), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(component_header_table)
    
    # Component damages data - include all components
    component_data = [
        ['Battery', damage_report.battery_damage or "No damage reported"],
        ['Lights', damage_report.lights_damage or "No damage reported"],
        ['Oil', damage_report.oil_damage or "No damage reported"],
        ['Water', damage_report.water_damage or "No damage reported"],
        ['Brakes', damage_report.brakes_damage or "No damage reported"],
        ['Air', damage_report.air_damage or "No damage reported"],
        ['Gas', damage_report.gas_damage or "No damage reported"]
    ]
    
    # Add minimum height to make the damages section taller
    component_table = Table(component_data, colWidths=[3.25*inch, 3.25*inch], rowHeights=[0.4*inch] * len(component_data))
    component_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(component_table)
    
    # Maintenance Diagnosis header
    diagnosis_header = [["Maintenance Diagnosis"]]
    diagnosis_header_table = Table(diagnosis_header, colWidths=[6.5*inch])
    diagnosis_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
    ]))
    elements.append(diagnosis_header_table)
    
    # Maintenance Diagnosis content
    diagnosis_content = [[damage_report.maintenance_diagnosis or "No diagnosis provided"]]
    diagnosis_content_table = Table(diagnosis_content, colWidths=[6.5*inch], rowHeights=[1.5*inch])
    diagnosis_content_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
    ]))
    elements.append(diagnosis_content_table)
    
    # Modified: Estimated Time of Repair with two columns
    time_repair_data = [["Estimated Time of Repair", damage_report.estimate_repair_time or "0"]]
    time_repair_table = Table(time_repair_data, colWidths=[3.25*inch, 3.25*inch])
    time_repair_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
    ]))
    elements.append(time_repair_table)
    
    # Concerns
    concerns_header = [["Concerns"]]
    concerns_header_table = Table(concerns_header, colWidths=[6.5*inch])
    concerns_header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
    ]))
    elements.append(concerns_header_table)
    
    # Concerns content
    concerns_content = [[damage_report.concerns or "No concerns noted"]]
    concerns_content_table = Table(concerns_content, colWidths=[6.5*inch], rowHeights=[1.5*inch])
    concerns_content_table.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 1, colors.black),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
    ]))
    elements.append(concerns_content_table)
    
    # Build PDF document
    doc.build(elements)
    
    return response

def forgot_password(request):
    """View to handle forgotten password requests"""
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        
        if not employee_id:
            messages.error(request, "Please enter your Employee ID.")
            return render(request, "VehicleManagementSystem/forgot_password.html")
        
        try:
            # Check if user exists
            user = CustomUser.objects.get(employee_id=employee_id)
            
            # Reset password to default temporary password
            user.set_password("00000000")
            user.first_login = True
            user.save()
            
            messages.success(request, "Password has been reset. You can now login with the temporary password: 00000000. You'll be asked to change it on login.")
            return redirect("login")
            
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this Employee ID.")
    
    return render(request, "VehicleManagementSystem/forgot_password.html")