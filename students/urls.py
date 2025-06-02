from django.urls import path
from . import views

urlpatterns = [
    # الصفحات العامة
    # path('', views.home, name='home'),
    path('register/student/', views.register_student, name='register_student'),
   
    # مسارات الطالب
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/application/new/', views.submit_application, name='submit_application'),
    path('student/application/<int:application_id>/', views.application_status, name='application_status'),
    path('student/application/<int:application_id>/details/', views.application_details, name='application_details'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/announcements/<int:announcement_id>/', views.view_announcement, name='view_announcement'),
    path('application/<int:application_id>/status/', views.application_status, name='application_status'),

    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # path('public-announcements/', views.public_announcements_view, name='public_announcements'),
    # ... الروابط الأخرى ...


#   path('student/application/<int:application_id>/details/', 
#          views.application_details, 
#          name='application_details'),

    ]
