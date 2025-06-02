from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from students.models import Student
from .serializers import *
from committee.models import *
from students.models import *
from dean.models import *
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.authtoken.models import Token
# from django.contrib.auth import authenticate, login, logout
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from rest_framework.decorators import api_view, permission_classes
# from .serializers import *
# from committee.models import *
# from students.models import *
# from dean.models import *
from django.db.models import Q


@api_view(['POST'])
@permission_classes([AllowAny])
def register_student_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'اسم المستخدم وكلمة المرور مطلوبة'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'اسم المستخدم مستخدم مسبقاً'}, status=400)

    try:
        user = User.objects.create_user(username=username, password=password)
        user.is_student = True
        user.save()
        Student.objects.create(user=user)

        return Response({'message': 'تم إنشاء الحساب بنجاح'})
    except Exception as e:
        return Response({'error': f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'}, status=500)


@api_view(['POST'])
def student_login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_student:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'message': 'تم تسجيل الدخول بنجاح',
                'username': user.username,
            })
        else:
            return Response({'error': 'هذا الحساب ليس حساب طالب'}, status=403)
    else:
        return Response({'error': 'بيانات الدخول غير صحيحة'}, status=400)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard_api(request):
    if not request.user.is_student:
        return Response({'error': 'غير مصرح'}, status=403)

    student = request.user.student
    applications = Application.objects.filter(student=student)
    active_app = applications.exclude(status='draft').first()

    announcements = Announcement.objects.filter(
        Q(is_public=True) |
        Q(student=student) |
        Q(group__statuses__application__student=student)
    ).order_by('-created_at')[:5]

    # إعداد مراحل التقدم
    stages = Stage.objects.all().order_by('order')
    current_stage_order = 0
    rejection_stage = None
    rejected = False
    progress = 0

    if active_app:
        try:
            current_status = active_app.applicationstatus_set.latest('created_at')
            current_stage_order = current_status.stage.order
        except:
            current_stage_order = 0

        rejected_status = active_app.applicationstatus_set.filter(is_rejected=True).first()
        if rejected_status:
            rejected = True
            rejection_stage = rejected_status.stage.name

        total_stages = stages.count()
        completed = sum(1 for stage in stages if stage.order < current_stage_order)
        progress = int((completed / total_stages) * 100) if total_stages else 0

    return Response({
        'student': {
            'full_name': student.full_name,
            'email': student.email,
        },
        'applications': list(applications.values(
            'id', 'status', 'department__name', 'application_date'
        )),
        'active_application_id': active_app.id if active_app else None,
        'progress_percentage': progress,
        'rejected': rejected,
        'rejection_stage': rejection_stage,
        'announcements': list(announcements.values('title', 'content', 'created_at'))
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_announcements_api(request):
    if not request.user.is_student:
        return Response({'error': 'غير مصرح'}, status=403)

    student = request.user.student
    announcements = Announcement.objects.filter(
        Q(is_public=True) |
        Q(student=student) |
        Q(group__statuses__application__student=student)
    ).distinct().order_by('-created_at')

    return Response({
        'announcements': list(announcements.values('id', 'title', 'content', 'created_at', 'is_read'))
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_announcements_read_api(request):
    if not request.user.is_student:
        return Response({'error': 'غير مصرح'}, status=403)

    student = request.user.student
    Announcement.objects.filter(
        Q(is_public=True) |
        Q(student=student) |
        Q(group__statuses__application__student=student),
        is_read=False
    ).update(is_read=True)

    return Response({'message': 'تم تعليم جميع الإعلانات كمقروءة'})


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

# views.py (Django) — API تقديم الطلب وجلب البيانات
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
# from students.models import (
#     BirthInfo, FatherInfo, PersonalInfo, StudentDocuments,
#     Application, ApplicationStatus, Department, AcademicYear, Qualification
# )
# from dean.models import Stage


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def submit_application_api(request):
#     student = request.user.student

#     if Application.objects.filter(student=student, academic_year_id=request.data.get('academic_year')).exists():
#         return Response({'error': 'تم تقديم طلب لهذا العام مسبقاً'}, status=400)

#     try:
#         with transaction.atomic():
#             birth_info = BirthInfo.objects.create(
#                 birth_date=request.data.get('birth_date'),
#                 birth_place=request.data.get('birth_place'),
#                 governorate=request.data.get('governorate'),
#                 district=request.data.get('district'),
#                 directorate=request.data.get('directorate'),
#             )

#             father_info = FatherInfo.objects.create(
#                 father_name=request.data.get('father_name'),
#                 father_phone=request.data.get('father_phone'),
#                 father_job=request.data.get('father_job'),
#                 father_job_type=request.data.get('father_job_type'),
#                 father_work_place=request.data.get('father_work_place'),
#                 father_address=request.data.get('father_address'),
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
#                 student=student,
#                 photo=request.FILES.get('photo'),
#                 certificate=request.FILES.get('certificate'),
#                 id_copy=request.FILES.get('id_copy'),
#                 work_statement=request.FILES.get('work_statement'),
#             )

#             application = Application.objects.create(
#                 student=student,
#                 department_id=request.data.get('department'),
#                 academic_year_id=request.data.get('academic_year'),
#                 birth_info=birth_info,
#                 father_info=father_info,
#                 personal_info=personal_info,
#                 documents=documents,
#                 status='submitted'
#             )

#             qualification_count = 0
#             for i in range(3):
#                 if request.data.get(f'qualification_type_{i}'):
#                     qualification = Qualification.objects.create(
#                         qualification_type=request.data.get(f'qualification_type_{i}'),
#                         university=request.data.get(f'university_{i}'),
#                         gpa=request.data.get(f'gpa_{i}'),
#                         qualification_date=request.data.get(f'qualification_date_{i}'),
#                         grade=request.data.get(f'grade_{i}'),
#                         certificate_image=request.FILES.get(f'certificate_image_{i}')
#                     )
#                     application.qualifications.add(qualification)
#                     qualification_count += 1

#             if qualification_count == 0:
#                 raise ValueError("يجب إدخال مؤهل واحد على الأقل")

#             first_stage = Stage.objects.get(order=1)
#             ApplicationStatus.objects.create(
#                 application=application,
#                 stage=first_stage,
#                 notes='تم تقديم الطلب بنجاح'
#             )

#         return Response({'message': 'تم تقديم الطلب بنجاح'})
#     except Exception as e:
#         return Response({'error': str(e)}, status=500)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_application_api(request):
    # التحقق من أن المستخدم طالب
    if not hasattr(request.user, 'student'):
        raise PermissionDenied("المستخدم ليس طالباً")
    
    student = request.user.student
    academic_year_id = request.data.get('academic_year')

    # التحقق مما إذا كان الطالب قد قدم طلبًا بالفعل لهذا العام الدراسي
    if academic_year_id:
        existing_application = Application.objects.filter(
            student=student,
            academic_year_id=academic_year_id
        ).first()
        if existing_application:
            return Response(
                {'error': 'لقد قمت بتقديم طلب بالفعل لهذا العام الدراسي.'},
                status=400
            )

    try:
        with transaction.atomic():
            # تحديث بيانات الطالب
            student_data = {
                'full_name': request.data.get('full_name'),
                'nickname': request.data.get('nickname'),
                'phone': request.data.get('phone'),
                'email': request.data.get('email'),
                'gender': request.data.get('gender')
            }
            
            for field, value in student_data.items():
                if value is not None:
                    setattr(student, field, value)
            student.save()

            # حفظ بيانات الميلاد
            birth_info = BirthInfo.objects.create(
                birth_date=request.data.get('birth_date'),
                birth_place=request.data.get('birth_place'),
                governorate=request.data.get('governorate'),
                district=request.data.get('district'),
                directorate=request.data.get('directorate')
            )

            # حفظ بيانات الأب
            father_info = FatherInfo.objects.create(
                father_name=request.data.get('father_name'),
                father_phone=request.data.get('father_phone'),
                father_job=request.data.get('father_job'),
                father_job_type=request.data.get('father_job_type'),
                father_work_place=request.data.get('father_work_place'),
                father_address=request.data.get('father_address')
            )

            # حفظ البيانات الشخصية
            personal_info = PersonalInfo.objects.create(
                marital_status=request.data.get('marital_status', 'single'),
                current_address=request.data.get('current_address'),
                permanent_address=request.data.get('permanent_address'),
                id_number=request.data.get('id_number'),
                id_type=request.data.get('id_type', 'personal'),
                id_issue_date=request.data.get('id_issue_date'),
                id_issue_place=request.data.get('id_issue_place'),
                current_job=request.data.get('current_job'),
                work_place=request.data.get('work_place'),
                employment_date=request.data.get('employment_date'),
                secondary_phone=request.data.get('secondary_phone')
            )

            # حفظ المستندات
            documents = StudentDocuments.objects.create(
                id_image=request.FILES.get('id_image'),
                high_school_certificate=request.FILES.get('high_school_certificate'),
                grade_data=request.FILES.get('grade_data'),
                criminal_record=request.FILES.get('criminal_record'),
                birth_certificate=request.FILES.get('birth_certificate')
            )

            # إنشاء الطلب
            application = Application.objects.create(
                student=student,
                department_id=request.data.get('department'),
                academic_year_id=academic_year_id,
                birth_info=birth_info,
                father_info=father_info,
                personal_info=personal_info,
                documents=documents,
                status='submitted'
            )

            # حفظ المؤهلات (حتى 3 مؤهلات)
            qualification_count = 0
            for i in range(3):
                qual_type = request.data.get(f'qualification_type_{i}')
                if qual_type:
                    qualification = Qualification.objects.create(
                        qualification_type=qual_type,
                        university=request.data.get(f'university_{i}'),
                        gpa=request.data.get(f'gpa_{i}'),
                        certificate_image=request.FILES.get(f'certificate_image_{i}'),
                        qualification_date=request.data.get(f'qualification_date_{i}'),
                        grade=request.data.get(f'grade_{i}')
                    )
                    application.qualifications.add(qualification)
                    qualification_count += 1

            # التأكد من وجود مؤهل واحد على الأقل
            if qualification_count == 0:
                raise ValueError("يجب إضافة مؤهل واحد على الأقل")

            # تعيين الطلب للمرحلة الأولى
            first_stage = Stage.objects.get(order=1)
            ApplicationStatus.objects.create(
                application=application,
                stage=first_stage,
                notes='تم تقديم الطلب بنجاح'
            )

            return Response({'message': 'تم تقديم الطلب بنجاح!'})

    except Exception as e:
        return Response(
            {'error': f'حدث خطأ أثناء حفظ البيانات: {str(e)}'},
            status=500
        )
    
    
@api_view(['GET'])
@permission_classes([AllowAny])
def departments_list_api(request):
    departments = Department.objects.all().values('id', 'name')
    return Response({'departments': list(departments)})


@api_view(['GET'])
@permission_classes([AllowAny])
def academic_years_by_department_api(request, department_id):
    years = AcademicYear.objects.filter(department_id=department_id).values('id', 'year')
    return Response({'academic_years': list(years)})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_status_api(request, application_id):
    try:
        application = Application.objects.get(id=application_id, student=request.user.student)
    except Application.DoesNotExist:
        return Response({'error': 'الطلب غير موجود'}, status=404)

    stages = Stage.objects.all().order_by('order')
    try:
        current_status = application.applicationstatus_set.latest('created_at')
        current_stage_order = current_status.stage.order
    except:
        current_stage_order = 0

    stage_list = []
    for stage in stages:
        status = 'pending'
        if stage.order < current_stage_order:
            status = 'completed'
        elif stage.order == current_stage_order:
            status = 'current'
        stage_list.append({
            'name': stage.name,
            'order': stage.order,
            'status': status
        })

    return Response({
        'application_id': application.id,
        'status': application.status,
        'stages': stage_list
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_details_api(request, application_id):
    try:
        application = Application.objects.get(id=application_id, student=request.user.student)
    except Application.DoesNotExist:
        return Response({'error': 'الطلب غير موجود'}, status=404)

    current_status = application.applicationstatus_set.order_by('-created_at').first()
    qualifications = application.qualifications.all().values(
        'qualification_type', 'university', 'gpa', 'qualification_date', 'grade'
    )

    return Response({
        'application': {
            'id': application.id,
            'department': application.department.name,
            'status': application.status,
            'application_date': application.application_date
        },
        'current_status': current_status.stage.name if current_status else None,
        'qualifications': list(qualifications)
    })


# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.authtoken.models import Token
# from django.contrib.auth import authenticate, login, logout
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from rest_framework.decorators import api_view, permission_classes
# from .serializers import *
# from committee.models import *
# from students.models import *
# from dean.models import *
# from django.db.models import Q

# class LoginAPI(APIView):
#     def post(self, request):
#         username = request.data.get('username')
#         password = request.data.get('password')
#         user = authenticate(username=username, password=password)
        
#         if user is not None:
#             login(request, user)
#             token, created = Token.objects.get_or_create(user=user)
            
#             response_data = {
#                 'success': True,
#                 'token': token.key,
#                 'user_type': None
#             }
            
#             if user.is_student:
#                 response_data['user_type'] = 'student'
#                 response_data['redirect'] = 'student_dashboard'
#             elif user.is_employee:
#                 employee = user.employee
#                 response_data['user_type'] = employee.role
#                 if employee.role == 'dean':
#                     response_data['redirect'] = 'dean_dashboard'
#                 elif employee.role == 'data_entry':
#                     response_data['redirect'] = 'data_entry_dashboard'
#                 elif employee.role == 'committee_member':
#                     response_data['redirect'] = 'committee_dashboard'
#             elif user.is_superuser:
#                 response_data['user_type'] = 'admin'
#                 response_data['redirect'] = 'register_employee'
            
#             return Response(response_data)
#         else:
#             return Response(
#                 {'success': False, 'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )

# class LogoutAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         logout(request)
#         return Response({'success': True})

# class RegisterStudentAPI(APIView):
#     def post(self, request):
#         user_serializer = UserSerializer(data=request.data)
        
#         if user_serializer.is_valid():
#             try:
#                 with transaction.atomic():
#                     user = user_serializer.save()
#                     user.is_student = True
#                     user.save()
                    
#                     Student.objects.create(user=user)
                    
#                     token = Token.objects.create(user=user)
#                     login(request, user)
                    
#                     return Response({
#                         'success': True,
#                         'token': token.key,
#                         'redirect': 'student_dashboard'
#                     })
                    
#             except Exception as e:
#                 return Response(
#                     {'success': False, 'error': f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         else:
#             errors = []
#             for field, error_list in user_serializer.errors.items():
#                 for error in error_list:
#                     errors.append(f"{field}: {error}")
#             return Response(
#                 {'success': False, 'errors': errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

# class SubmitApplicationAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         if not request.user.is_student:
#             return Response(
#                 {'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         departments = Department.objects.all()
#         academicyear = AcademicYear.objects.all()
        
#         academic_year_id = request.query_params.get('academic_year')
#         if academic_year_id:
#             existing_application = Application.objects.filter(
#                 student=request.user.student,
#                 academic_year_id=academic_year_id
#             ).first()
            
#             if existing_application:
#                 return Response({
#                     'has_application': True,
#                     'application_id': existing_application.id
#                 })
        
#         return Response({
#             'departments': DepartmentSerializer(departments, many=True).data,
#             'academicyear': AcademicYearSerializer(academicyear, many=True).data,
#             'marital_status_choices': PersonalInfo.MARITAL_STATUS_CHOICES,
#             'id_type_choices': PersonalInfo.ID_TYPE_CHOICES,
#             'qualification_type_choices': Qualification.QUALIFICATION_TYPE_CHOICES
#         })
    
#     def post(self, request):
#         if not request.user.is_student:
#             return Response(
#                 {'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         academic_year_id = request.data.get('academic_year')
#         existing_application = Application.objects.filter(
#             student=request.user.student,
#             academic_year_id=academic_year_id
#         ).first()
        
#         if existing_application:
#             return Response({
#                 'has_application': True,
#                 'application_id': existing_application.id
#             })
        
#         try:
#             with transaction.atomic():
#                 student_data = request.data.get('student', {})
#                 if hasattr(request.user, 'student'):
#                     student = request.user.student
#                     for field, value in student_data.items():
#                         if value:
#                             setattr(student, field, value)
#                     student.save()
#                 else:
#                     student = Student.objects.create(user=request.user, **student_data)
                
#                 birth_info = BirthInfo.objects.create(**request.data.get('birth_info', {}))
#                 father_info = FatherInfo.objects.create(**request.data.get('father_info', {}))
#                 personal_info = PersonalInfo.objects.create(**request.data.get('personal_info', {}))
                
#                 documents_data = request.data.get('documents', {})
#                 documents = StudentDocuments.objects.create(
#                     id_image=request.FILES.get('id_image'),
#                     high_school_certificate=request.FILES.get('high_school_certificate'),
#                     grade_data=request.FILES.get('grade_data'),
#                     criminal_record=request.FILES.get('criminal_record'),
#                     birth_certificate=request.FILES.get('birth_certificate')
#                 )
                
#                 application = Application.objects.create(
#                     student=student,
#                     department_id=request.data.get('department'),
#                     academic_year_id=academic_year_id,
#                     birth_info=birth_info,
#                     father_info=father_info,
#                     personal_info=personal_info,
#                     documents=documents,
#                     status='submitted'
#                 )
                
#                 qualifications = request.data.get('qualifications', [])
#                 if not qualifications:
#                     raise ValueError("يجب إضافة مؤهل واحد على الأقل")
                
#                 for qual_data in qualifications:
#                     qualification = Qualification.objects.create(
#                         qualification_type=qual_data.get('qualification_type'),
#                         university=qual_data.get('university'),
#                         gpa=qual_data.get('gpa'),
#                         certificate_image=request.FILES.get(qual_data.get('certificate_image_key')),
#                         qualification_date=qual_data.get('qualification_date'),
#                         grade=qual_data.get('grade')
#                     )
#                     application.qualifications.add(qualification)
                
#                 first_stage = Stage.objects.get(order=1)
#                 ApplicationStatus.objects.create(
#                     application=application,
#                     stage=first_stage,
#                     notes='تم تقديم الطلب بنجاح'
#                 )
                
#                 return Response({
#                     'success': True,
#                     'application_id': application.id
#                 })
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': f'حدث خطأ أثناء حفظ البيانات: {str(e)}'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

# class ApplicationStatusAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request, application_id):
#         application = get_object_or_404(Application, id=application_id, student=request.user.student)
        
#         stages = Stage.objects.all().order_by('order')
#         current_status = application.applicationstatus_set.order_by('-created_at').first()
        
#         current_stage_order = current_status.stage.order if current_status else 0
#         completed_count = 0
        
#         stage_data = []
#         for stage in stages:
#             stage_info = {
#                 'id': stage.id,
#                 'name': stage.name,
#                 'order': stage.order,
#                 'completed': stage.order < current_stage_order,
#                 'current': stage.order == current_stage_order,
#                 'pending': stage.order > current_stage_order
#             }
            
#             if stage_info['completed']:
#                 completed_count += 1
                
#             stage_data.append(stage_info)
        
#         total_stages = len(stages)
#         progress_percentage = int((completed_count / total_stages) * 100) if total_stages > 0 else 0
        
#         return Response({
#             'application': ApplicationSerializer(application).data,
#             'stages': stage_data,
#             'progress_percentage': progress_percentage
#         })

# class StudentDashboardAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         if not request.user.is_student:
#             return Response(
#                 {'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         try:
#             student = request.user.student
#         except Student.DoesNotExist:
#             student = Student.objects.create(user=request.user)
        
#         applications = Application.objects.filter(student=student)
#         active_application = applications.exclude(status='draft').first()
        
#         stages = []
#         progress_percentage = 0
#         rejected = False
#         rejection_stage = None
        
#         if active_application:
#             stages = Stage.objects.all().order_by('order')
#             rejected_status = active_application.applicationstatus_set.filter(
#                 is_rejected=True
#             ).first()
            
#             if rejected_status:
#                 rejected = True
#                 rejection_stage = rejected_status.stage
            
#             try:
#                 current_status = active_application.applicationstatus_set.latest('created_at')
#                 current_stage_order = current_status.stage.order
#             except:
#                 current_stage_order = 0
            
#             completed_count = 0
#             is_final_approved = (active_application.status == 'approved')
#             last_stage_order = stages.last().order if stages.exists() else 0
            
#             for stage in stages:
#                 if rejected and stage.order == rejection_stage.order:
#                     stage.rejected = True
#                     stage.completed = False
#                     stage.current = False
#                     stage.pending = False
#                 else:
#                     if is_final_approved and stage.order == last_stage_order:
#                         stage.completed = True
#                         stage.current = False
#                         stage.pending = False
#                     else:
#                         stage.completed = stage.order < current_stage_order
#                         stage.current = stage.order == current_stage_order and not rejected
#                         stage.pending = stage.order > current_stage_order and not rejected
                
#                 if stage.completed:
#                     completed_count += 1
            
#             total_stages = stages.count()
#             progress_percentage = int((completed_count / total_stages) * 100) if total_stages > 0 else 0
        
#         unread_announcements_count = Announcement.objects.filter(
#             group__statuses__application__in=applications,
#             is_read=False
#         ).count()
        
#         notifications = Announcement.objects.filter(
#             Q(is_public=True) |
#             Q(student=student) |
#             Q(group__statuses__application__student=student)
#         ).order_by('-created_at')[:5]
        
#         unread_count = Announcement.objects.filter(
#             Q(is_public=True) |
#             Q(student=student) |
#             Q(group__statuses__application__student=student),
#             is_read=False
#         ).count()
        
#         return Response({
#             'student': StudentSerializer(student).data,
#             'applications': ApplicationSerializer(applications, many=True).data,
#             'active_application': ApplicationSerializer(active_application).data if active_application else None,
#             'stages': StageSerializer(stages, many=True).data if stages else [],
#             'progress_percentage': progress_percentage,
#             'rejected': rejected,
#             'rejection_stage': StageSerializer(rejection_stage).data if rejection_stage else None,
#             'notifications': AnnouncementSerializer(notifications, many=True).data,
#             'unread_count': unread_count
#         })

# class StudentAnnouncementsAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         if not request.user.is_student:
#             return Response(
#                 {'error': 'ليس لديك صلاحية الوصول إلى هذه الصفحة'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         student = request.user.student
        
#         announcements = Announcement.objects.filter(
#             Q(is_public=True) |
#             Q(student=student) |
#             Q(group__statuses__application__student=student)
#         ).distinct().order_by('-created_at')
        
#         unread_count = announcements.filter(is_read=False).count()
        
#         return Response({
#             'announcements': AnnouncementSerializer(announcements, many=True).data,
#             'unread_count': unread_count
#         })

# class ViewAnnouncementAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request, announcement_id):
#         if not request.user.is_student:
#             return Response(
#                 {'error': 'ليس لديك صلاحية الوصول إلى هذه الصفحة'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         announcement = get_object_or_404(Announcement, id=announcement_id)
#         student = request.user.student
        
#         if not (announcement.is_public or 
#                 announcement.student == student or
#                 announcement.group and announcement.group.statuses.filter(
#                     application__student=student).exists()):
#             return Response(
#                 {'error': 'ليس لديك صلاحية لعرض هذا الإعلان'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         if not announcement.is_read:
#             announcement.is_read = True
#             announcement.read_at = timezone.now()
#             announcement.save()
        
#         return Response(AnnouncementSerializer(announcement).data)

# class MarkAllNotificationsReadAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         if not request.user.is_student:
#             return Response(
#                 {'status': 'error'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         student = request.user.student
#         Announcement.objects.filter(
#             Q(is_public=True) |
#             Q(student=student) |
#             Q(group__statuses__application__student=student),
#             is_read=False
#         ).update(is_read=True, read_at=timezone.now())
        
#         return Response({'status': 'success'})