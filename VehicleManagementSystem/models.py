from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import datetime
from cloudinary.models import CloudinaryField

class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('Operational', 'Operational'),
        ('In Repair', 'In Repair'),
        ('Unavailable', 'Unavailable'),
    )
    
    vehicle_id = models.AutoField(primary_key=True)
    report_id = models.CharField(max_length=20, blank=True, null=True)
    plate_number = models.CharField(
        max_length=20, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]+$',
                message=_('Plate number must contain only uppercase letters and numbers'),
            ),
        ]
    )
    vehicle_make = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)
    year = models.PositiveIntegerField(null=True, blank=True)
    photo = CloudinaryField('vehicle_photos', folder='vehicle_photos', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Operational')
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    last_maintenance = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehicle_make} - {self.vehicle_model} ({self.plate_number})"
    
    class Meta:
        ordering = ['plate_number']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

class VehicleDamage(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='damages')
    description = models.TextField()
    date_reported = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Damage to {self.vehicle.plate_number} - {self.date_reported.strftime('%Y-%m-%d')}"

class CustomUserManager(BaseUserManager):
    def create_user(self, employee_id, name, password=None, role=None, first_login=True):
        if not employee_id:
            raise ValueError("Employees must have an Employee ID")
        if not name:
            raise ValueError("Employees must have a name")
        if not role:
            raise ValueError("Employees must have a role")

        user = self.model(
            employee_id=employee_id, 
            name=name, 
            role=role,
            first_login=first_login
        )
        
        # Set the provided password or default temporary password
        if password is None:
            password = "00000000"  # Default temporary password
            
        user.set_password(password)  # Hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, name, password):
        user = self.create_user(
            employee_id, 
            name, 
            password, 
            role="Vehicle Management Team",
            first_login=False
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("Warehouse Personnel", "Warehouse Personnel"),
        ("Operations Team", "Operations Team"),
        ("Vehicle Management Team", "Vehicle Management Team"),
    )

    employee_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=25, choices=ROLE_CHOICES)
    first_login = models.BooleanField(default=True)  # Tracks if user needs to change password

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name} ({self.employee_id})"
    
class VehicleInspection(models.Model):
    COMPONENT_STATUS = (
        ('OK', 'OK'),
        ('Needs Repair', 'Needs Repair'),
    )
    
    COMPLETION_STATUS = (
        ('Draft', 'Draft'),
        ('Pre-Delivery Only', 'Pre-Delivery Only'),
        ('Complete', 'Complete'),
    )
    
    # Basic Information
    report_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conducted_inspections')
    inspection_date = models.DateField()
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status field to track completion
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS, default='Draft')
    
    # Pre-Delivery Inspection
    pre_battery = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_lights = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_oil = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_water = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_brakes = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_air = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_gas = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    pre_comments = models.TextField(blank=True)
    pre_damages = models.TextField(blank=True)
    
    # Post-Delivery Inspection
    post_battery = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_lights = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_oil = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_water = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_brakes = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_air = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_gas = models.CharField(max_length=20, choices=COMPONENT_STATUS, null=True, blank=True)
    post_comments = models.TextField(blank=True)
    post_damages = models.TextField(blank=True)
    
    # Flag to track if the report is submitted/finalized
    is_submitted = models.BooleanField(default=False)
    
    def __str__(self):
        status = f" ({self.completion_status})" if not self.is_submitted else ""
        return f"Inspection {self.report_id} for {self.vehicle} on {self.inspection_date}{status}"
        
    def update_completion_status(self):
        """Update the completion status based on filled fields, but don't mark as Complete unless submitted"""
        # Check if pre-delivery fields are filled
        pre_fields = [
            self.pre_battery, self.pre_lights, self.pre_oil, 
            self.pre_water, self.pre_brakes, self.pre_air, self.pre_gas
        ]
        
        # Check if post-delivery fields are filled
        post_fields = [
            self.post_battery, self.post_lights, self.post_oil, 
            self.post_water, self.post_brakes, self.post_air, self.post_gas
        ]
        
        pre_complete = all(field is not None for field in pre_fields)
        post_complete = all(field is not None for field in post_fields)
        
        # Only set to Complete if explicitly submitted
        if self.is_submitted and pre_complete and post_complete:
            self.completion_status = 'Complete'
        elif pre_complete:
            self.completion_status = 'Pre-Delivery Only'
        else:
            self.completion_status = 'Draft'

# Add to models.py

class DamageReport(models.Model):
    damage_id = models.AutoField(primary_key=True)
    report_id = models.CharField(max_length=20, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='damage_reports')
    inspector = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='damage_inspections')
    inspection_date = models.DateField()
    
    # Component damage descriptions
    battery_damage = models.TextField(null=True, blank=True)
    lights_damage = models.TextField(null=True, blank=True)
    oil_damage = models.TextField(null=True, blank=True)
    water_damage = models.TextField(null=True, blank=True)
    brakes_damage = models.TextField(null=True, blank=True)
    air_damage = models.TextField(null=True, blank=True)
    gas_damage = models.TextField(null=True, blank=True)
    
    # Maintenance information
    maintenance_diagnosis = models.TextField(null=True, blank=True)
    estimate_repair_time = models.CharField(max_length=50, default="0")
    concerns = models.TextField(null=True, blank=True)
    
    # Status tracking
    is_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Damage Report #{self.damage_id} - {self.vehicle}"
    
    def save(self, *args, **kwargs):
        # Generate a report ID if not already assigned
        if not self.report_id:
            # Format: DR-YYYYMMDD-XXXX where XXXX is a sequential number
            today = datetime.date.today().strftime('%Y%m%d')
            last_report = DamageReport.objects.filter(report_id__startswith=f'DR-{today}').order_by('report_id').last()
            
            if last_report:
                # Extract the last sequence number and increment
                last_seq = int(last_report.report_id.split('-')[-1])
                self.report_id = f'DR-{today}-{last_seq + 1:04d}'
            else:
                # First report of the day
                self.report_id = f'DR-{today}-0001'
        
        # First save this damage report
        super().save(*args, **kwargs)
        
        # After saving, update the vehicle's last_maintenance date
        # Only update if this report is submitted (not a draft)
        if self.is_submitted:
            # Update the vehicle's last_maintenance field with the inspection date
            self.vehicle.last_maintenance = self.inspection_date
            self.vehicle.save(update_fields=['last_maintenance'])