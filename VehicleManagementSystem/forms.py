from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Vehicle, VehicleDamage, VehicleInspection

class VehicleInspectionForm(forms.ModelForm):
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
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pre_comments': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter comment here...'}),
            'pre_damages': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter damages incurred here...'}),
            'post_comments': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter comment here...'}),
            'post_damages': forms.Textarea(attrs={'class': 'form-control comment-field', 'placeholder': 'Enter damages incurred here...'})
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate_number', 'vehicle_make', 'vehicle_model', 'year', 'photo', 'status', 'last_maintenance']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Plate Number'}),
            'vehicle_make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle Make'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle Model'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Year'}),
            'last_maintenance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.RadioSelect(attrs={'class': 'status-radio'})
        }

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
            'placeholder': 'Search plate number, make or model'
        })
    )

class UserRegistrationForm(forms.ModelForm):
    name = forms.CharField(max_length=50, required=True, 
                         widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True,
                          widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True,
                           widget=forms.Select(attrs={'class': 'form-select'}))
    employee_id = forms.CharField(max_length=20, required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ["employee_id", "name", "email", "role"]

    def save(self, commit=True):
        if self.instance.pk:  # If we're editing an existing instance
            user = self.instance
            user.employee_id = self.cleaned_data["employee_id"]
            user.name = self.cleaned_data["name"]
            user.email = self.cleaned_data["email"]
            user.role = self.cleaned_data["role"]
        else:  # Creating a new user
            user = CustomUser.objects.create_user(
                employee_id=self.cleaned_data["employee_id"],
                name=self.cleaned_data["name"],
                role=self.cleaned_data["role"],
                password="00000000"
            )
            user.email = self.cleaned_data["email"]
            
        if commit:
            user.save()
        return user
    
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
        

        