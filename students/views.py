from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import *
from dean.models import *
from committee.models import *

from .forms import *
from dean.forms import *
from committee.forms import *

from django.db.models import Prefetch
import json


def register_student(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        
        if user_form.is_valid():
            try:
                with transaction.atomic():
                    # حفظ بيانات المستخدم
                    user = user_form.save(commit=False)
                    user.is_student = True
                    user.save()
                    
                    # إنشاء سجل الطالب المرتبط
                    Student.objects.create(user=user)
                    
                    # تسجيل الدخول تلقائياً
                    login(request, user)
                    
                    messages.success(request, 'تم إنشاء حسابك بنجاح!')
                    return redirect('student_dashboard')
                    
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
        else:
            error_messages = []
            for field, errors in user_form.errors.items():
                for error in errors:
                    error_messages.append(f"{user_form[field].label}: {error}")
            messages.error(request, 'يوجد أخطاء في البيانات المدخلة: ' + '، '.join(error_messages))
    else:
        user_form = UserForm()
    
    return render(request, 'register_student.html', {
        'user_form': user_form
    })


# @login_required
# def student_dashboard(request):
#     if not request.user.is_student:
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')
    
#     try:
#         student = request.user.student
#     except Student.DoesNotExist:
#         student = Student.objects.create(user=request.user)
#         messages.info(request, 'تم إنشاء ملفك الشخصي كطالب بنجاح')
    
#     applications = Application.objects.filter(student=student)

#     # جلب الإعلانات بنفس منطق صفحة الإعلانات
#     announcements = Announcement.objects.filter(
#         models.Q(is_public=True) |
#         models.Q(group__statuses__application__in=applications)
#     ).distinct().order_by('-created_at')

#     unread_announcements = announcements.filter(is_read=False)

#     # إذا كان لديك أكثر من application وتريد عرض واحد فقط في الداشبورد:
#     application = applications.first() if applications.exists() else None

#     committee_done = False
#     if application:
#         try:
#             current_status = application.applicationstatus_set.latest('created_at')
#             members_count = Employee.objects.filter(role='committee_member').count()
#             opinions_count = CommitteeOpinion.objects.filter(application_status=current_status).count()
#             committee_done = (opinions_count == members_count)
#         except:
#             committee_done = False

#     return render(request, 'student/dashboard.html', {
#         'student': student,
#         'application': application,
#         'announcements': unread_announcements,
#         'committee_done': committee_done,
#     })

@login_required
def submit_application(request):
    if not request.user.is_student:
        return redirect('home')

    departments = Department.objects.all()
    academicyear = AcademicYear.objects.all()

    # التحقق مما إذا كان الطالب قد قدم طلبًا بالفعل لهذا العام الدراسي
    if request.method == 'GET':
        academic_year_id = request.GET.get('academic_year')
        if academic_year_id:
            existing_application = Application.objects.filter(
                student=request.user.student,
                academic_year_id=academic_year_id
            ).first()
            if existing_application:
                messages.error(request, 'لقد قمت بتقديم طلب بالفعل لهذا العام الدراسي.')
                return redirect('application_status', application_id=existing_application.id)

    if request.method == 'POST':
        academic_year_id = request.POST.get('academic_year')
        # التحقق مرة أخرى قبل معالجة الطلب
        existing_application = Application.objects.filter(
            student=request.user.student,
            academic_year_id=academic_year_id
        ).first()
        if existing_application:
            messages.error(request, 'لقد قمت بتقديم طلب بالفعل لهذا العام الدراسي.')
            return redirect('application_status', application_id=existing_application.id)

        try:
            with transaction.atomic():
                student_data = {
                    'full_name': request.POST.get('full_name'),
                    'nickname': request.POST.get('nickname'),
                    'phone': request.POST.get('phone'),
                    'email': request.POST.get('email'),
                    'gender': request.POST.get('gender')
                }
                
                # تحديث بيانات الطالب إذا كانت موجودة
                if hasattr(request.user, 'student'):
                    for field, value in student_data.items():
                        if value:
                            setattr(request.user.student, field, value)
                    request.user.student.save()
                else:
                    # إنشاء سجل طالب جديد إذا لم يكن موجوداً
                    student = Student.objects.create(user=request.user, **student_data)

                # حفظ بيانات الميلاد
                birth_info = BirthInfo.objects.create(
                    birth_date=request.POST.get('birth_date'),
                    birth_place=request.POST.get('birth_place'),
                    governorate=request.POST.get('governorate'),
                    district=request.POST.get('district'),
                    directorate=request.POST.get('directorate')
                )

                # حفظ بيانات الأب
                father_info = FatherInfo.objects.create(
                    father_name=request.POST.get('father_name'),
                    father_phone=request.POST.get('father_phone'),
                    father_job=request.POST.get('father_job'),
                    father_job_type=request.POST.get('father_job_type'),
                    father_work_place=request.POST.get('father_work_place'),
                    father_address=request.POST.get('father_address')
                )

                # حفظ البيانات الشخصية
                personal_info = PersonalInfo.objects.create(
                    marital_status=request.POST.get('marital_status'),
                    current_address=request.POST.get('current_address'),
                    permanent_address=request.POST.get('permanent_address'),
                    id_number=request.POST.get('id_number'),
                    id_type=request.POST.get('id_type'),
                    id_issue_date=request.POST.get('id_issue_date'),
                    id_issue_place=request.POST.get('id_issue_place'),
                    current_job=request.POST.get('current_job'),
                    work_place=request.POST.get('work_place'),
                    employment_date=request.POST.get('employment_date'),
                    secondary_phone=request.POST.get('secondary_phone')
                )

                # حفظ المستندات
                documents = StudentDocuments.objects.create(
                    id_image=request.FILES.get('id_image'),
                    high_school_certificate=request.FILES.get('high_school_certificate'),
                    grade_data=request.FILES.get('grade_data'),
                    criminal_record=request.FILES.get('criminal_record'),
                    birth_certificate=request.FILES.get('birth_certificate')
                )

                # إنشاء الطلب مع تعيين الحالة مباشرة إلى 'submitted'
                application = Application.objects.create(
                    student=request.user.student,
                    department_id=request.POST.get('department'),
                    academic_year_id=academic_year_id,
                    birth_info=birth_info,
                    father_info=father_info,
                    personal_info=personal_info,
                    documents=documents,
                    status='submitted'  # هنا تم تعيين الحالة مباشرة عند الإنشاء
                )

                # حفظ المؤهلات (حتى 3 مؤهلات)
                qualification_count = 0
                for i in range(3):
                    qual_type = request.POST.get(f'qualification_type_{i}')
                    if qual_type:
                        qualification = Qualification.objects.create(
                            qualification_type=qual_type,
                            university=request.POST.get(f'university_{i}'),
                            gpa=request.POST.get(f'gpa_{i}'),
                            certificate_image=request.FILES.get(f'certificate_image_{i}'),
                            qualification_date=request.POST.get(f'qualification_date_{i}'),
                            grade=request.POST.get(f'grade_{i}')
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
                    notes='تم تقديم الطلب بنجاح'  # إضافة وصف للحالة
                )

                # إرسال إشعار للجنة المراجعة (إن أردت)
                # send_notification_to_committee(application)

                messages.success(request, 'تم تقديم الطلب بنجاح!')
                return redirect('application_status', application_id=application.id)

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')

    return render(request, 'student/submit_application.html', {
        'departments': departments,
        'academicyear': academicyear,
        'marital_status_choices': PersonalInfo.MARITAL_STATUS_CHOICES,
        'id_type_choices': PersonalInfo.ID_TYPE_CHOICES,
        'qualification_type_choices': Qualification.QUALIFICATION_TYPE_CHOICES
    })


# # حالة الطلب
# @login_required
# def application_status(request, application_id):
#     if not request.user.is_student:
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')
    
#     application = get_object_or_404(Application, id=application_id, student=request.user.student)
#     current_status = application.applicationstatus_set.order_by('-created_at').first()
    
#     return render(request, 'student/application_status.html', {
#         'application': application,
#         'current_status': current_status
#     })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Application, ApplicationStatus



from django.shortcuts import get_object_or_404
from dean.models import  Stage

@login_required
def application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id, student=request.user.student)

    # جميع المراحل مرتبة حسب الترتيب
    stages = Stage.objects.all().order_by('order')

    # جلب المرحلة الحالية من حالة الطلب الأحدث
    try:
        current_status = application.applicationstatus_set.latest('created_at')
        current_stage_order = current_status.stage.order
    except:
        current_stage_order = 0

    # تجهيز مراحل القبول بحالة مرئية
    completed_count = 0
    for stage in stages:
        stage.completed = stage.order < current_stage_order
        stage.current = stage.order == current_stage_order
        stage.pending = stage.order > current_stage_order

        if stage.completed:
            completed_count += 1

    total_stages = stages.count()
    progress_percentage = int((completed_count / total_stages) * 100) if total_stages > 0 else 0

    return render(request, 'student/dashboard.html', {
        'application': application,
        'stages': stages,
        'progress_percentage': progress_percentage,
    })







# @login_required
# def application_status(request, application_id):
#     if not request.user.is_student:
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')

#     application = get_object_or_404(Application, id=application_id, student=request.user.student)

#     # مراحل القبول الخمسة
#     stages = [
#         {'name': 'قبول الطلب', 'status': 'accepted'},
#         {'name': 'الفحص الطبي', 'status': 'medical'},
#         {'name': 'الامتحانات التحريرية', 'status': 'written_exam'},
#         {'name': 'الامتحانات الشفوية', 'status': 'oral_exam'},
#         {'name': 'المقابلات الشخصية', 'status': 'interview'},
#     ]

#     # حدد المرحلة الحالية بناءً على application.status
#     current_index = 0
#     status_order = ['accepted', 'medical', 'written_exam', 'oral_exam', 'interview']
#     if application.status in status_order:
#         current_index = status_order.index(application.status)
#     elif application.status == 'draft':
#         current_index = 0

#     for idx, stage in enumerate(stages):
#         if idx < current_index:
#             stage['completed'] = True
#         elif idx == current_index:
#             stage['current'] = True
#         else:
#             stage['pending'] = True

#     return render(request, 'student/dashboard.html', {
#         'application': application,
#         'stages': stages,
#     })

# تفاصيل الطلب
@login_required
def application_details(request, application_id):
    if request.user.is_student:
        application = get_object_or_404(Application, id=application_id, student=request.user.student)
    elif request.user.is_employee:
        application = get_object_or_404(Application, id=application_id)
    else:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    current_status = application.applicationstatus_set.order_by('-created_at').first()
    qualifications = application.qualifications.all()
    
    return render(request, 'application_details.html', {
        'application': application,
        'current_status': current_status,
        'qualifications': qualifications
    })


# @login_required
# def student_announcements(request):
#     if not request.user.is_student:
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')
    
#     student = request.user.student
#     applications = Application.objects.filter(student=student)
    
#     # الإعلانات العامة + الإعلانات الخاصة بمجموعات الطالب
#     announcements = Announcement.objects.filter(
#         models.Q(is_public=True) |
#         models.Q(group__statuses__application__in=applications)
#     ).distinct().order_by('-created_at')
    
#     unread_count = announcements.filter(is_read=False).count()
    
#     return render(request, 'student/announcements.html', {
#         'announcements': announcements,
#         'unread_count': unread_count
#     })

# @login_required
# def view_announcement(request, announcement_id):
#     if not request.user.is_student:
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')
    
#     announcement = get_object_or_404(Announcement, id=announcement_id)
    
#     # التحقق من صلاحية الطالب لرؤية الإعلان
#     if not announcement.is_public:
#         student_applications = Application.objects.filter(student=request.user.student)
#         if not announcement.group or not announcement.group.statuses.filter(application__in=student_applications).exists():
#             messages.error(request, 'ليس لديك صلاحية لعرض هذا الإعلان')
#             return redirect('student_announcements')
    
#     # تحديد الإعلان كمقروء
#     if not announcement.is_read:
#         announcement.is_read = True
#         announcement.read_at = timezone.now()
#         announcement.save()
    
#     return render(request, 'student/view_announcement.html', {
#         'announcement': announcement
#     })




@login_required
def student_dashboard(request):
    if not request.user.is_student:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)
        messages.info(request, 'تم إنشاء ملفك الشخصي كطالب بنجاح')
    
    applications = Application.objects.filter(student=student)
    active_application = applications.exclude(status='draft').first()

    stages = []
    progress_percentage = 0
    rejected = False  # متغير لتحديد إذا كان الطلب مرفوضاً
    rejection_stage = None  # المرحلة التي تم فيها الرفض

    if active_application:
        stages = Stage.objects.all().order_by('order')
        
        # التحقق من وجود رفض في أي مرحلة
        rejected_status = active_application.applicationstatus_set.filter(
            is_rejected=True
        ).first()
        
        if rejected_status:
            rejected = True
            rejection_stage = rejected_status.stage
        
        try:
            current_status = active_application.applicationstatus_set.latest('created_at')
            current_stage_order = current_status.stage.order
        except:
            current_stage_order = 0

        completed_count = 0
        is_final_approved = (active_application.status == 'approved')
        last_stage_order = stages.last().order if stages.exists() else 0

        for stage in stages:
            if rejected and stage.order == rejection_stage.order:
                stage.rejected = True
                stage.completed = False
                stage.current = False
                stage.pending = False
            else:
                # المرحلة مكتملة إذا ترتيبها أقل من الحالي
                # أو إذا الطلب معتمد نهائيًا والمرحلة هي الأخيرة
                if is_final_approved and stage.order == last_stage_order:
                    stage.completed = True
                    stage.current = False
                    stage.pending = False
                else:
                    stage.completed = stage.order < current_stage_order
                    stage.current = stage.order == current_stage_order and not rejected
                    stage.pending = stage.order > current_stage_order and not rejected

            if stage.completed:
                completed_count += 1

        total_stages = stages.count()
        progress_percentage = int((completed_count / total_stages) * 100) if total_stages > 0 else 0
    
    unread_announcements_count = Announcement.objects.filter(
        group__statuses__application__in=applications,
        is_read=False
    ).count()
        
    # جلب آخر 5 إعلانات للطالب
    notifications = Announcement.objects.filter(
        # models.Q(is_public=True) |
        models.Q(student=student) |
        models.Q(group__statuses__application__student=student)
    ).order_by('-created_at')[:5]

    unread_count = Announcement.objects.filter(
        models.Q(is_public=True) |
        models.Q(student=student) |
        models.Q(group__statuses__application__student=student),
        is_read=False
    ).count()

    announcements = Announcement.objects.filter(
    is_public=True
    ).order_by('-created_at')[:5]

    # جلب جميع الإعلانات العامة أولاً
    all_public_announcements = Announcement.objects.filter(is_public=True).order_by('-created_at')

    # بعد ذلك نأخذ أول 5 فقط للعرض في التمبلت
    announcements = all_public_announcements[:3]

    # ثم نعد غير المقروء منها على الاستعلام الكامل (بدون slice)
    unread_announcements_count = all_public_announcements.filter(is_read=False).count()



    return render(request, 'student/dashboard.html', {
    'student': student,
    'applications': applications,
    'active_application': active_application,
    'stages': stages,
    'progress_percentage': progress_percentage,
    'rejected': rejected,
    'rejection_stage': rejection_stage,
    'announcements': announcements,  # <--- هنا التغيير
    'unread_announcements_count': unread_announcements_count,  # <--- وهنا أيضاً
    'notifications': notifications,  # يمكن استخدامه لزر الجرس في التمبلت
    'unread_count': unread_count
})



    # return render(request, 'student/dashboard.html', {
    #     'student': student,
    #     'applications': applications,
    #     'active_application': active_application,
    #     'stages': stages,
    #     'progress_percentage': progress_percentage,
    #     'rejected': rejected,
    #     'rejection_stage': rejection_stage,
    #     'notifications': notifications,
    #     'unread_count': unread_count
    # })





@login_required
def student_announcements(request):
    if not request.user.is_student:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    student = request.user.student
    
    announcements = Announcement.objects.filter(
        models.Q(is_public=True) |
        models.Q(student=student) |
        models.Q(group__statuses__application__student=student)
    ).distinct().order_by('-created_at')

    unread_count = announcements.filter(is_read=False).count()

    return render(request, 'student/announcements.html', {
        'announcements': announcements,
        'unread_count': unread_count
    })

@login_required
def view_announcement(request, announcement_id):
    if not request.user.is_student:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    announcement = get_object_or_404(Announcement, id=announcement_id)
    student = request.user.student

    if not (announcement.is_public or 
            announcement.student == student or
            announcement.group and announcement.group.statuses.filter(
                application__student=student).exists()):
        messages.error(request, 'ليس لديك صلاحية لعرض هذا الإعلان')
        return redirect('student_announcements')

    if not announcement.is_read:
        announcement.is_read = True
        announcement.read_at = timezone.now()
        announcement.save()

    return render(request, 'student/view_announcement.html', {
        'announcement': announcement
    })

import json
from django.http import JsonResponse


@login_required
def mark_all_notifications_read(request):
    if not request.user.is_student:
        return JsonResponse({'status': 'error'}, status=403)
    
    student = request.user.student
    Announcement.objects.filter(
        models.Q(is_public=True) |
        models.Q(student=student) |
        models.Q(group__statuses__application__student=student),
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'status': 'success'})
