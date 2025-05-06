from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import CustomUser, Vehicle, VehicleDamage, VehicleInspection, DamageReport
import datetime

# Custom validator for 4-digit years
def validate_four_digit_year(value):
    if value is not None and (value < 1000 or value > 9999):
        raise forms.ValidationError("Please enter a valid 4-digit year")
    return value

class VehicleInspectionForm(forms.ModelForm):
    # Add custom validation for date fields
    inspection_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        error_messages={'invalid': 'Enter a valid date in YYYY-MM-DD format.'}
    )
    
    class Meta:
        model = VehicleInspection
        fields = [
            'vehicle', 'inspection_date',
            'pre_battery', 'pre_lights', 'pre_oil', 'pre_water', 'pre_brakes', 'pre_air', 'pre_gas',
            'pre_comments', 'pre_damages',
            'post_battery', 'post_lights', 'post_oil', 'post_water', 'post_brakes', 'post_air', 'post_gas',
            'post_comments', 'post_damages'
        ]
        widgets = {
            'pre_comments': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter comment here...'}),
            'pre_damages': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter damages incurred here...'}),
            'post_comments': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter comment here...'}),
            'post_damages': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter damages incurred here...'})
        }

    def clean_inspection_date(self):
        date = self.cleaned_data.get('inspection_date')
        if date:
            # Ensure the year is 4 digits
            if date.year < 1000 or date.year > 9999:
                raise forms.ValidationError("Please enter a valid 4-digit year")
        return date

class VehicleForm(forms.ModelForm):
    # Add explicit validators for the year field
    year = forms.IntegerField(
        validators=[
            MinValueValidator(1000, message="Year must be a 4-digit number"),
            MaxValueValidator(9999, message="Year must be a 4-digit number")
        ],
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter Year (4 digits)',
            'min': '1000',
            'max': '9999'
        })
    )
    
    # Add custom validation for the last_maintenance date
    last_maintenance = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        error_messages={'invalid': 'Enter a valid date in YYYY-MM-DD format.'}
    )

    class Meta:
        model = Vehicle
        fields = ['plate_number', 'vehicle_make', 'vehicle_model', 'year', 'photo', 'status', 'last_maintenance']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Plate Number'}),
            'vehicle_make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle Make'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle Model'}),
            'status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'})
        }
        
    def clean_last_maintenance(self):
        date = self.cleaned_data.get('last_maintenance')
        if date:
            # Ensure the year is 4 digits
            if date.year < 1000 or date.year > 9999:
                raise forms.ValidationError("Please enter a valid 4-digit year")
        return date


class VehicleDamageForm(forms.ModelForm):
    class Meta:
        model = VehicleDamage
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter damage description'})
        }
        
class VehicleFilterForm(forms.Form):
    STATUS_CHOICES = (
        ('', 'All Statuses'),
        ('Operational', 'Operational'),
        ('In Repair', 'In Repair'),
        ('Unavailable', 'Unavailable'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by plate number'
        })
    )


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["employee_id", "name", "email", "role"]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'})
        }

    def save(self, commit=True):
        # Just handle the basic form save - the view will take care of password
        return super().save(commit=commit)
    
class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match")
            
            if new_password == "00000000":
                raise forms.ValidationError("New password cannot be the same as the temporary password")
            
            if len(new_password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long")
                
        return cleaned_data

class DamageReportForm(forms.ModelForm):
    # Add custom validation for the inspection_date field
    inspection_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        error_messages={'invalid': 'Enter a valid date in YYYY-MM-DD format.'}
    )
    
    class Meta:
        model = DamageReport
        fields = [
            'vehicle', 'inspection_date',
            'battery_damage', 'lights_damage', 'oil_damage', 'water_damage', 
            'brakes_damage', 'air_damage', 'gas_damage',
            'maintenance_diagnosis', 'estimate_repair_time', 'concerns'
        ]
        widgets = {
            'battery_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'lights_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'oil_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'water_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'brakes_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'air_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'gas_damage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'maintenance_diagnosis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter diagnosis'}),
            'estimate_repair_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter estimated repair time'}),
            'concerns': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter concerns here'})
        }
        
    def clean_inspection_date(self):
        date = self.cleaned_data.get('inspection_date')
        if date:
            # Ensure the year is 4 digits
            if date.year < 1000 or date.year > 9999:
                raise forms.ValidationError("Please enter a valid 4-digit year")
        return date