from django.urls import path
from .views import *
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()

urlpatterns = [
    path('student/login/', student_login_api, name='student_login_api'),
    path('student/dashboard/', student_dashboard_api, name='student_dashboard_api'),
    path('student/register/', register_student_api, name='register_student_api'),
    path('student/submit-application/', submit_application_api, name='submit_application_api'),
    path('student/application/<int:application_id>/status/', application_status_api, name='application_status_api'),
    path('student/application/<int:application_id>/details/', application_details_api, name='application_details_api'),
    path('student/announcements/', student_announcements_api, name='student_announcements_api'),
    path('student/announcements/mark-all-read/', mark_all_announcements_read_api, name='mark_all_announcements_read_api'),
    # path('api/student/submit-application/', views.submit_application_api, name='submit_application_api'),
    path('student/departments/', departments_list_api, name='departments_list_api'),
    path('student/academic-years/<int:department_id>/', academic_years_by_department_api, name='academic_years_by_department_api'),

    # path('login/', LoginAPI.as_view(), name='api_login'),
    # path('logout/', LogoutAPI.as_view(), name='api_logout'),
    # path('register/student/', RegisterStudentAPI.as_view(), name='api_register_student'),
    # path('application/submit/', SubmitApplicationAPI.as_view(), name='api_submit_application'),
    # path('application/status/<int:application_id>/', ApplicationStatusAPI.as_view(), name='api_application_status'),
    # path('student/dashboard/', StudentDashboardAPI.as_view(), name='api_student_dashboard'),
    # path('student/announcements/', StudentAnnouncementsAPI.as_view(), name='api_student_announcements'),
    # path('announcement/<int:announcement_id>/', ViewAnnouncementAPI.as_view(), name='api_view_announcement'),
    # path('notifications/mark-all-read/', MarkAllNotificationsReadAPI.as_view(), name='api_mark_all_read'),
]

# urls.py
# from django.urls import path
# from . import views

# urlpatterns = [
#     path('api/student/submit-application/', views.submit_application_api, name='submit_application_api'),
#     path('api/student/departments/', views.departments_list_api, name='departments_list_api'),
#     path('api/student/academic-years/<int:department_id>/', views.academic_years_by_department_api, name='academic_years_by_department_api'),
# ]

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('api/student/login/', views.student_login_api, name='student_login_api'),
#     path('api/student/register/', views.register_student_api, name='register_student_api'),
#     path('api/student/dashboard/', views.student_dashboard_api, name='student_dashboard_api'),
#     path('api/student/submit-application/', views.submit_application_api, name='submit_application_api'),
#     path('api/student/application/<int:application_id>/status/', views.application_status_api, name='application_status_api'),
#     path('api/student/application/<int:application_id>/details/', views.application_details_api, name='application_details_api'),
#     path('api/student/announcements/', views.student_announcements_api, name='student_announcements_api'),
#     path('api/student/announcements/mark-all-read/', views.mark_all_announcements_read_api, name='mark_all_announcements_read_api'),
# ]




    # path('student/login/', student_login_api, name='student_login_api'),
    # path('student/dashboard/', student_dashboard_api, name='student_dashboard_api'),
    # path('api/student/register/', register_student_api, name='register_student_api'),

# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authtoken.models import Token
# from django.contrib.auth import authenticate
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from django.contrib.auth.models import User
# from students.models import Student

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register_student_api(request):
#     username = request.data.get('username')
#     password = request.data.get('password')

#     if not username or not password:
#         return Response({'error': 'اسم المستخدم وكلمة المرور مطلوبة'}, status=400)

#     if User.objects.filter(username=username).exists():
#         return Response({'error': 'اسم المستخدم مستخدم مسبقاً'}, status=400)

#     try:
#         user = User.objects.create_user(username=username, password=password)
#         user.is_student = True
#         user.save()
#         Student.objects.create(user=user)

#         return Response({'message': 'تم إنشاء الحساب بنجاح'})
#     except Exception as e:
#         return Response({'error': f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'}, status=500)


# @api_view(['POST'])
# def student_login_api(request):
#     username = request.data.get('username')
#     password = request.data.get('password')

#     user = authenticate(username=username, password=password)

#     if user is not None:
#         if user.is_student:
#             token, _ = Token.objects.get_or_create(user=user)
#             return Response({
#                 'token': token.key,
#                 'message': 'تم تسجيل الدخول بنجاح',
#                 'username': user.username,
#             })
#         else:
#             return Response({'error': 'هذا الحساب ليس حساب طالب'}, status=403)
#     else:
#         return Response({'error': 'بيانات الدخول غير صحيحة'}, status=400)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def student_dashboard_api(request):
#     if not request.user.is_student:
#         return Response({'error': 'غير مصرح'}, status=403)

#     student = request.user.student
#     applications = Application.objects.filter(student=student).values(
#         'id', 'status', 'department__name', 'application_date'
#     )
    
#     return Response({
#         'student': {
#             'full_name': student.full_name,
#             'email': student.email,
#         },
#         'applications': list(applications),
#     })

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def student_dashboard_api(request):
#     if not request.user.is_student:
#         return Response({'error': 'غير مصرح'}, status=403)

#     student = request.user.student
#     applications = Application.objects.filter(student=student)
#     active_app = applications.exclude(status='draft').first()

#     announcements = Announcement.objects.filter(
#         Q(is_public=True) |
#         Q(student=student) |
#         Q(group__statuses__application__student=student)
#     ).order_by('-created_at')[:5]

#     # إعداد مراحل التقدم
#     stages = Stage.objects.all().order_by('order')
#     current_stage_order = 0
#     rejection_stage = None
#     rejected = False
#     progress = 0

#     if active_app:
#         try:
#             current_status = active_app.applicationstatus_set.latest('created_at')
#             current_stage_order = current_status.stage.order
#         except:
#             current_stage_order = 0

#         rejected_status = active_app.applicationstatus_set.filter(is_rejected=True).first()
#         if rejected_status:
#             rejected = True
#             rejection_stage = rejected_status.stage.name

#         total_stages = stages.count()
#         completed = sum(1 for stage in stages if stage.order < current_stage_order)
#         progress = int((completed / total_stages) * 100) if total_stages else 0

#     return Response({
#         'student': {
#             'full_name': student.full_name,
#             'email': student.email,
#         },
#         'applications': list(applications.values(
#             'id', 'status', 'department__name', 'application_date'
#         )),
#         'active_application_id': active_app.id if active_app else None,
#         'progress_percentage': progress,
#         'rejected': rejected,
#         'rejection_stage': rejection_stage,
#         'announcements': list(announcements.values('title', 'content', 'created_at'))
#     })
