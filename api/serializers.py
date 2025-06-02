from rest_framework import serializers
from django.contrib.auth.models import User
from committee.models import *
from students.models import *
from dean.models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['full_name', 'nickname', 'phone', 'email', 'gender']

class BirthInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthInfo
        fields = ['birth_date', 'birth_place', 'governorate', 'district', 'directorate']

class FatherInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FatherInfo
        fields = ['father_name', 'father_phone', 'father_job', 'father_job_type', 
                 'father_work_place', 'father_address']

class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = ['marital_status', 'current_address', 'permanent_address', 
                 'id_number', 'id_type', 'id_issue_date', 'id_issue_place',
                 'current_job', 'work_place', 'employment_date', 'secondary_phone']

class StudentDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocuments
        fields = ['id_image', 'high_school_certificate', 'grade_data', 
                 'criminal_record', 'birth_certificate']

class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = ['qualification_type', 'university', 'gpa', 'certificate_image',
                'qualification_date', 'grade']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'department', 'year']

class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ['id', 'name', 'order']

class ApplicationStatusSerializer(serializers.ModelSerializer):
    stage = StageSerializer()
    
    class Meta:
        model = ApplicationStatus
        fields = ['id', 'stage', 'created_at', 'is_rejected', 'notes']

class ApplicationSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    birth_info = BirthInfoSerializer()
    father_info = FatherInfoSerializer()
    personal_info = PersonalInfoSerializer()
    documents = StudentDocumentsSerializer()
    qualifications = QualificationSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_stage = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    def get_current_stage(self, obj):
        return obj.get_current_stage()
    
    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()
    
    class Meta:
        model = Application
        fields = ['id', 'student', 'academic_year', 'birth_info', 'father_info',
                 'personal_info', 'documents', 'qualifications', 'application_date',
                 'department', 'status', 'status_display', 'current_stage',
                 'progress_percentage', 'last_updated']

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'announcement_type', 'created_at',
                 'is_public', 'attachment', 'is_read', 'read_at']
        



# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from rest_framework.authtoken.models import Token
# from django.contrib.auth import authenticate
# from django.contrib.auth.models import User
# from django.db import transaction
# from django.db.models import Q
# from students.models import Student
# from .models import Application, ApplicationStatus, Announcement, BirthInfo, FatherInfo, PersonalInfo, StudentDocuments, Qualification
# from dean.models import Stage, Department, AcademicYear


# @api_view(['POST'])
# @permission_classes([AllowAny])
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
#         with transaction.atomic():
#             user = User.objects.create_user(username=username, password=password)
#             user.is_student = True
#             user.save()
#             Student.objects.create(user=user)
#         return Response({'message': 'تم إنشاء الحساب بنجاح'})
#     except Exception as e:
#         return Response({'error': f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'}, status=500)


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


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def student_announcements_api(request):
#     if not request.user.is_student:
#         return Response({'error': 'غير مصرح'}, status=403)

#     student = request.user.student
#     announcements = Announcement.objects.filter(
#         Q(is_public=True) |
#         Q(student=student) |
#         Q(group__statuses__application__student=student)
#     ).distinct().order_by('-created_at')

#     return Response({
#         'announcements': list(announcements.values('id', 'title', 'content', 'created_at', 'is_read'))
#     })


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def mark_all_announcements_read_api(request):
#     if not request.user.is_student:
#         return Response({'error': 'غير مصرح'}, status=403)

#     student = request.user.student
#     Announcement.objects.filter(
#         Q(is_public=True) |
#         Q(student=student) |
#         Q(group__statuses__application__student=student),
#         is_read=False
#     ).update(is_read=True)

#     return Response({'message': 'تم تعليم جميع الإعلانات كمقروءة'})


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def submit_application_api(request):
#     student = request.user.student
#     academic_year_id = request.data.get('academic_year')

#     if Application.objects.filter(student=student, academic_year_id=academic_year_id).exists():
#         return Response({'error': 'لقد قمت بتقديم طلب بالفعل لهذا العام الدراسي.'}, status=400)

#     try:
#         with transaction.atomic():
#             birth_info = BirthInfo.objects.create(
#                 birth_date=request.data.get('birth_date'),
#                 birth_place=request.data.get('birth_place'),
#                 governorate=request.data.get('governorate'),
#                 district=request.data.get('district'),
#                 directorate=request.data.get('directorate')
#             )

#             father_info = FatherInfo.objects.create(
#                 father_name=request.data.get('father_name'),
#                 father_phone=request.data.get('father_phone'),
#                 father_job=request.data.get('father_job'),
#                 father_job_type=request.data.get('father_job_type'),
#                 father_work_place=request.data.get('father_work_place'),
#                 father_address=request.data.get('father_address')
#             )

#             personal_info = PersonalInfo.objects.create(
#                 marital_status=request.data.get('marital_status'),
#                 current_address=request.data.get('current_address'),
#                 permanent_address=request.data.get('permanent_address'),
#                 id_number=request.data.get('id_number'),
#                 id_type=request.data.get('id_type'),
#                 id_issue_date=request.data.get('id_issue_date'),
#                 id_issue_place=request.data.get('id_issue_place'),
#                 current_job=request.data.get('current_job'),
#                 work_place=request.data.get('work_place'),
#                 employment_date=request.data.get('employment_date'),
#                 secondary_phone=request.data.get('secondary_phone')
#             )

#             documents = StudentDocuments.objects.create(
#                 # استخدم File upload حقيقي في التطبيق الحقيقي
#             )

#             application = Application.objects.create(
#                 student=student,
#                 department_id=request.data.get('department'),
#                 academic_year_id=academic_year_id,
#                 birth_info=birth_info,
#                 father_info=father_info,
#                 personal_info=personal_info,
#                 documents=documents,
#                 status='submitted'
#             )

#             first_stage = Stage.objects.get(order=1)
#             ApplicationStatus.objects.create(
#                 application=application,
#                 stage=first_stage,
#                 notes='تم تقديم الطلب بنجاح'
#             )

#         return Response({'message': 'تم تقديم الطلب بنجاح'})

#     except Exception as e:
#         return Response({'error': f'حدث خطأ أثناء تقديم الطلب: {str(e)}'}, status=500)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def application_status_api(request, application_id):
#     try:
#         application = Application.objects.get(id=application_id, student=request.user.student)
#     except Application.DoesNotExist:
#         return Response({'error': 'الطلب غير موجود'}, status=404)

#     stages = Stage.objects.all().order_by('order')
#     try:
#         current_status = application.applicationstatus_set.latest('created_at')
#         current_stage_order = current_status.stage.order
#     except:
#         current_stage_order = 0

#     stage_list = []
#     for stage in stages:
#         status = 'pending'
#         if stage.order < current_stage_order:
#             status = 'completed'
#         elif stage.order == current_stage_order:
#             status = 'current'
#         stage_list.append({
#             'name': stage.name,
#             'order': stage.order,
#             'status': status
#         })

#     return Response({
#         'application_id': application.id,
#         'status': application.status,
#         'stages': stage_list
#     })


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def application_details_api(request, application_id):
#     try:
#         application = Application.objects.get(id=application_id, student=request.user.student)
#     except Application.DoesNotExist:
#         return Response({'error': 'الطلب غير موجود'}, status=404)

#     current_status = application.applicationstatus_set.order_by('-created_at').first()
#     qualifications = application.qualifications.all().values(
#         'qualification_type', 'university', 'gpa', 'qualification_date', 'grade'
#     )

#     return Response({
#         'application': {
#             'id': application.id,
#             'department': application.department.name,
#             'status': application.status,
#             'application_date': application.application_date
#         },
#         'current_status': current_status.stage.name if current_status else None,
#         'qualifications': list(qualifications)
#     })
