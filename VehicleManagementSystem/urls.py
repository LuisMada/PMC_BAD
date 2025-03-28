from django.urls import path
from .views import (
    login_view, logout_view, register_view, dashboard, driver_dashboard, management_dashboard, 
    create_report, manage_vehicles, add_vehicle, edit_vehicle, delete_vehicle, add_vehicle_damage,
    change_password, generate_report_pdf, view_reports, delete_report, 
    view_accounts, edit_account, delete_account, reset_password  # Add new view functions
)

urlpatterns = [
    # Authentication URLs
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("change_password/", change_password, name="change_password"),
    
    # Dashboard URLs based on user role
    path("dashboard/", dashboard, name="WH_dashboard"),  # Warehouse Personnel
    path("ops/dashboard/", driver_dashboard, name="OPS_dashboard"),  # Operations Team
    path("vmt/dashboard/", management_dashboard, name="VMT_dashboard"),  # Vehicle Management Team
    
    # Report URLs
    path("create/report/", create_report, name="create_report"),
    path("report/<int:report_id>/pdf/", generate_report_pdf, name="generate_report_pdf"),
    path("report/<int:report_id>/delete/", delete_report, name="delete_report"),
    
    # Vehicle management URLs
    path("vehicles/", manage_vehicles, name="manage_vehicles"),
    path("vehicles/add/", add_vehicle, name="add_vehicle"),
    path("vehicles/edit/<str:plate_number>/", edit_vehicle, name="edit_vehicle"),
    path("vehicles/delete/<str:plate_number>/", delete_vehicle, name="delete_vehicle"),
    path("vehicles/<str:plate_number>/add-damage/", add_vehicle_damage, name="add_vehicle_damage"),
    path("reports/", view_reports, name="view_reports"),
    
    # Account management URLs
    path("accounts/", view_accounts, name="view_accounts"),
    path("accounts/edit/<str:employee_id>/", edit_account, name="edit_account"),
    path("accounts/delete/<str:employee_id>/", delete_account, name="delete_account"),
    path("accounts/reset-password/<str:employee_id>/", reset_password, name="reset_password"),
]