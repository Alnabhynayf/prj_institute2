from django.urls import path
from . import views

urlpatterns = [
    # الصفحات العامة
    path('', views.home, name='home'),
    path('register/employee/', views.register_employee, name='register_employee'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    

    path('dean/', views.dean_dashboard, name='dean_dashboard'),
    path('dean/dean_review/', views.dean_review, name='dean_review'),

  
    path('dean/stage-info/<int:application_id>/', views.stage_info, name='stage_info'),
    path('dean/rejected-applications/', views.rejected_applications, name='rejected_applications'),
    path('dean/rejected-applications/<int:application_id>/', views.rejected_application_details, name='rejected_application_details'),
    path('dean/announcements/', views.dean_announcements_list, name='dean_announcements_list'),
    path('dean/additions/', views.dean_additions, name='dean_additions'),
    
    # Academic Year URLs
    path('dean/academic-year/add/', views.manage_academic_year, name='add_academic_year'),
    path('dean/academic-year/edit/<int:year_id>/', views.manage_academic_year, name='edit_academic_year'),
    path('dean/academic-year/delete/<int:year_id>/', views.delete_academic_year, name='delete_academic_year'),
    
    # Subject URLs
    path('dean/subject/add/', views.manage_subject, name='add_subject'),
    path('dean/subject/edit/<int:subject_id>/', views.manage_subject, name='edit_subject'),
    path('dean/subject/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    
    # Department URLs
    path('dean/department/add/', views.manage_department, name='add_department'),
    path('dean/department/edit/<int:department_id>/', views.manage_department, name='edit_department'),
    path('dean/department/delete/<int:department_id>/', views.delete_department, name='delete_department'),
    
    # Stage URLs
    path('dean/stage/add/', views.manage_stage, name='add_stage'),
    path('dean/stage/edit/<int:stage_id>/', views.manage_stage, name='edit_stage'),
    path('dean/stage/delete/<int:stage_id>/', views.delete_stage, name='delete_stage'),

    path('dean/decision/<int:application_id>/', views.dean_decision, name='dean_decision'),
    # path('rejected-applications/', views.rejected_applications, name='rejected_applications'),
    
     # إدارة حسابات الموظفين
    path('manage_accounts/', views.manage_accounts, name='manage_accounts'),
    path('edit_employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete_employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),


    path('groups/', views.manage_groups, name='manage_groups'),
    path('groups/list/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('announcements/public/new/', views.create_public_announcement, name='create_public_announcement'),

    path('dean/export/excel/', views.dean_export_excel, name='dean_export_excel'),
    path('dean/export/pdf/', views.dean_export_pdf, name='dean_export_pdf'),


    ]
