from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from .models import *
from students.models import *
from committee.models import *

from .forms import *
from students.forms import *
from committee.forms import *

from django.utils import timezone
from django.db.models import Q

from django.db.models import Max, F, Exists
from django.db.models import Prefetch
import csv
from django.http import HttpResponse


# from .signals import *

def home(request):
    public_announcements = Announcement.objects.filter(
        is_public=True
    ).order_by('-created_at')[:5]
    
    return render(request, 'home.html', {
        'public_announcements': public_announcements
    })



@login_required
def register_employee(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'employee') and request.user.employee.role == 'dean')):
        messages.error(request, 'ليس لديك صلاحية لإنشاء حساب موظف')
        return redirect('home')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        employee_form = EmployeeForm(request.POST)
        
        if user_form.is_valid() and employee_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.is_employee = True
                user.save()
                
                employee = employee_form.save(commit=False)
                employee.user = user
                employee.save()
            
            messages.success(request, 'تم إنشاء حساب الموظف بنجاح')
            return redirect('home')
    else:
        user_form = UserForm()
        employee_form = EmployeeForm()
    
    return render(request, 'register_employee.html', {
        'user_form': user_form,
        'employee_form': employee_form
    })

# تسجيل الدخول
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.is_student:
                return redirect('student_dashboard')
            elif user.is_employee:
                employee = user.employee
                if employee.role == 'dean':
                    return redirect('dean_dashboard')
                elif employee.role == 'data_entry':
                    return redirect('data_entry_dashboard')
                elif employee.role == 'committee_member':
                    return redirect('committee_dashboard')
            elif user.is_superuser:
                return redirect('register_employee')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render(request, 'login.html')

# تسجيل الخروج
@login_required
def user_logout(request):
    logout(request)
    return redirect('login')




@login_required
def dean_dashboard(request):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # إجمالي الطلبات
    total_applications = Application.objects.count()
    # الطلبات حسب الحالة
    approved_count = Application.objects.filter(status='approved').count()
    rejected_count = Application.objects.filter(status='rejected').count()
    pending_count = Application.objects.exclude(status__in=['approved', 'rejected']).count()

    # الطلبات حسب القسم
    dept_stats = (
        Application.objects.values('department__name')
        .annotate(total=models.Count('id'))
        .order_by('-total')
    )

    # الطلبات حسب المراحل
    stage_stats = (
        ApplicationStatus.objects.values('stage__name')
        .annotate(total=models.Count('id'))
        .order_by('stage__order')
    )

    # أعضاء اللجنة وعدد الطلبات التي راجعوها
    committee_stats = (
        Employee.objects.filter(role='committee_member')
        .annotate(
            reviewed=models.Count('committeeopinion')
        )
        .values('user__first_name', 'user__last_name', 'reviewed')
    )

    # إحصائيات الإعلانات
    announcements_total = Announcement.objects.count()
    public_announcements = Announcement.objects.filter(is_public=True).count()
    private_announcements = announcements_total - public_announcements

    # أحدث الطلبات
    latest_apps = Application.objects.select_related('student', 'department').order_by('-application_date')[:10]

    return render(request, 'dean/dean_dashboard.html', {
        'total_applications': total_applications,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'dept_stats': dept_stats,
        'stage_stats': stage_stats,
        'committee_stats': committee_stats,
        'announcements_total': announcements_total,
        'public_announcements': public_announcements,
        'private_announcements': private_announcements,
        'latest_apps': latest_apps,
    })



@login_required
def dean_review(request):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # الحصول على الطلبات التي أكملت مرحلة اللجنة في أي مرحلة
    applications = Application.objects.filter(
        applicationstatus__committeeopinion__isnull=False
    ).distinct()

    accepted_applications = []
    rejected_applications = []
    disputed_applications = []

    # تحديد ترتيب المرحلة الأخيرة
    last_stage_order = Stage.objects.all().order_by('-order').first().order if Stage.objects.exists() else None

    for app in applications:
        current_status = app.applicationstatus_set.latest('created_at')
        opinions = CommitteeOpinion.objects.filter(application_status=current_status)
        members_count = Employee.objects.filter(role='committee_member').count()

        # تجاهل الطلبات التي تم قبولها في المرحلة النهائية
        if app.status == 'approved':
            continue

        # أيضاً، إذا الطلب في المرحلة الأخيرة وتم قبول الطلب فيها (أي أعضاء اللجنة وافقوا)
        if last_stage_order and current_status.stage.order == last_stage_order:
            accept_count = opinions.filter(opinion='accept').count()
            if opinions.count() == members_count and accept_count == members_count:
                # تم قبول الطلب في المرحلة النهائية -> تجاهله
                continue

        accept_count = opinions.filter(opinion='accept').count()
        reject_count = opinions.filter(opinion='reject').count()

        if opinions.count() == members_count:
            if accept_count == members_count:
                accepted_applications.append((app, current_status))
            elif reject_count == members_count:
                rejected_applications.append((app, current_status))
            else:
                disputed_applications.append((app, current_status))

    return render(request, 'dean/dean_review.html', {
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'disputed_applications': disputed_applications,
    })




@login_required
def stage_info(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    status = application.applicationstatus_set.latest('created_at')
    stage_order = status.stage.order
    stage_results = status.stageresult_set.all()

    return render(request, 'dean/stage_info.html', {
        'application': application,
        'stage_order': stage_order,
        'stage_results': stage_results,
    })



from django.utils import timezone

@login_required
def dean_decision(request, application_id):
    if not request.user.employee.role == 'dean':
        messages.error(request, 'ليس لديك صلاحية لاتخاذ القرار')
        return redirect('home')

    application = get_object_or_404(Application, id=application_id)
    current_status = application.applicationstatus_set.latest('created_at')
    opinions = CommitteeOpinion.objects.filter(application_status=current_status)
    next_stage = Stage.objects.filter(order=current_status.stage.order + 1).first()
    # جلب بيانات نتائج المرحلة إن وجدت
    stage_result = current_status.stageresult_set.first()
    stage_data = stage_result.score if stage_result else None

    if request.method == 'POST':
        decision = request.POST.get('decision')
        notes = request.POST.get('notes', '')

        if not decision:
            messages.error(request, 'يجب اختيار قرار')
            return redirect('dean_review', application_id=application_id)

        student = application.student
        stage_name = current_status.stage.name

        if decision == 'accept':
            # إنشاء إشعار قبول مرتبط بالطالب
            Announcement.objects.create(
                    title='تم قبول طلبك',
                    content=f'تم قبول طلبك في مرحلة "{stage_name}".',
                    announcement_type='private',
                    created_by=request.user.employee,
                    is_public=False,
                    group=None,
                    student=student  # الربط المباشر بالطالب
                    )

            if next_stage:
                ApplicationStatus.objects.create(
                    application=application,
                    stage=next_stage,
                    notes=f'تم قبول الطلب من قبل العميد: {notes}'
                )
                messages.success(request, 'تم قبول الطلب ونقله إلى المرحلة التالية')
            else:
                application.status = 'approved'
                application.save()
                messages.success(request, 'تم قبول الطلب بنجاح (المرحلة النهائية)')

        elif decision == 'reject':
            current_status.is_rejected = True
            current_status.notes = f'تم رفض الطلب من قبل العميد: {notes}'
            current_status.save()

            application.status = 'rejected'
            application.save()

            # إنشاء إشعار رفض مرتبط بالطالب
            Announcement.objects.create(
            title='تم رفض طلبك',
            content=f'نأسف، لقد تم رفض طلبك في مرحلة "{stage_name}".',
            announcement_type='private',
            created_by=request.user.employee,
            is_public=False,
            group=None,
            student=student  # الربط المباشر بالطالب
        )
            messages.success(request, 'تم رفض الطلب بنجاح')

        elif decision == 'resend':  # <-- تأكد أن القيمة هنا مطابقة للقالب
            with transaction.atomic():
                CommitteeOpinion.objects.filter(application_status=current_status).delete()
                current_status.notes = f'تم إعادة الطلب للجنة للمراجعة: {notes}'
                current_status.is_returned = True
                current_status.save()
                messages.success(request, 'تم إعادة الطلب إلى اللجنة بنجاح للمراجعة مرة أخرى')

        return redirect('dean_dashboard')

    return render(request, 'dean/dean_decision.html', {
        'application': application,
        'current_status': current_status,
        'committee_opinions': opinions,
        'next_stage': next_stage,
        'stage_data': stage_data,
    })






# # قرار العميد - يعمل مع جميع المراحل
# @login_required
# def dean_decision(request, application_id):
#     if not request.user.employee.role == 'dean':
#         messages.error(request, 'ليس لديك صلاحية لاتخاذ القرار')
#         return redirect('home')

#     application = get_object_or_404(Application, id=application_id)
#     current_status = application.applicationstatus_set.latest('created_at')
#     opinions = CommitteeOpinion.objects.filter(application_status=current_status)

#     if request.method == 'POST':
#         decision = request.POST.get('decision')
#         notes = request.POST.get('notes', '')

#         if not decision:
#             messages.error(request, 'يجب اختيار قرار')
#             return redirect('dean_review', application_id=application_id)

#         if decision == 'accept':
#             # قبول ونقل للمرحلة التالية
#             next_stage = Stage.objects.filter(order=current_status.stage.order + 1).first()
#             if next_stage:
#                 ApplicationStatus.objects.create(
#                     application=application,
#                     stage=next_stage,
#                     notes=f'تم قبول الطلب من قبل العميد: {notes}'
#                 )
#                 messages.success(request, 'تم قبول الطلب ونقله إلى المرحلة التالية')
#             else:
#                 messages.success(request, 'تم قبول الطلب بنجاح (المرحلة النهائية)')

#         elif decision == 'reject':
#             # رفض الطلب
#             current_status.is_rejected = True
#             current_status.notes = f'تم رفض الطلب من قبل العميد: {notes}'
#             current_status.save()
#             messages.success(request, 'تم رفض الطلب بنجاح')

#         elif decision == 'return':
#             # إعادة الطلب للجنة في نفس المرحلة
#             with transaction.atomic():
#                 # حذف جميع آراء اللجنة السابقة
#                 CommitteeOpinion.objects.filter(application_status=current_status).delete()
                
#                 # تحديث حالة الطلب الحالية
#                 current_status.notes = f'تم إعادة الطلب للجنة للمراجعة: {notes}'
#                 current_status.save()
                
#                 messages.success(request, 'تم إعادة الطلب إلى اللجنة بنجاح للمراجعة مرة أخرى')

#         return redirect('dean_dashboard')

#     return render(request, 'dean/review.html', {
#         'application': application,
#         'current_status': current_status,
#         'committee_opinions': opinions
#     })



@login_required
def rejected_applications(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    rejected_apps = ApplicationStatus.objects.filter(
        is_rejected=True
    ).select_related('application')
    
    return render(request, 'rejected_applications.html', {
        'rejected_apps': rejected_apps
    })


@login_required
def rejected_application_details(request, application_id):
    """عرض تفاصيل كاملة لطلب مرفوض (للعميد فقط)"""
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    application = get_object_or_404(Application, id=application_id)
    current_status = application.applicationstatus_set.order_by('-created_at').first()
    
    # التحقق أن الطلب مرفوض من قبل هذا العميد
    rejection_opinion = get_object_or_404(
        CommitteeOpinion,
        application_status=current_status,
        opinion='reject',
        employee__user=request.user
    )


@login_required
def manage_accounts(request):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    employees = Employee.objects.all().order_by('-user_id')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        employee_form = EmployeeForm(request.POST)
        
        if user_form.is_valid() and employee_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.is_employee = True
                    user.save()
                    
                    employee = employee_form.save(commit=False)
                    employee.user = user
                    employee.save()
                
                messages.success(request, 'تم إنشاء حساب الموظف بنجاح')
                return redirect('manage_accounts')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
    else:
        user_form = UserForm()
        employee_form = EmployeeForm()
    
    return render(request, 'dean/manage_accounts.html', {
        'user_form': user_form,
        'employee_form': employee_form,
        'employees': employees,
        'role_choices': Employee.ROLE_CHOICES
    })



@login_required
def edit_employee(request, employee_id):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    employee = get_object_or_404(Employee, user_id=employee_id)
    user = employee.user
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        employee_form = EmployeeForm(request.POST, instance=employee)
        
        if user_form.is_valid() and employee_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    employee_form.save()
                
                messages.success(request, 'تم تحديث بيانات الموظف بنجاح')
                return redirect('manage_accounts')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث البيانات: {str(e)}')
        else:
            print("User Form Errors:", user_form.errors)
            print("Employee Form Errors:", employee_form.errors)
    else:
        user_form = UserForm(instance=user)
        employee_form = EmployeeForm(instance=employee)
    
    return render(request, 'dean/edit_employee.html', {
        'user_form': user_form,
        'employee_form': employee_form,
        'employee': employee,
        'role_choices': Employee.ROLE_CHOICES
    })



@login_required
def delete_employee(request, employee_id):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    employee = get_object_or_404(Employee, user_id=employee_id)
    user = employee.user
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user.delete()
            messages.success(request, 'تم حذف الموظف بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الموظف: {str(e)}')
        
        return redirect('manage_accounts')
    
    return render(request, 'dean/confirm_delete.html', {
        'employee': employee
    })





@login_required
def dean_additions(request):
    """صفحة الإضافات الخاصة بالعميد"""
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    # جلب جميع السجلات لعرضها في الصفحة الرئيسية
    academic_years = AcademicYear.objects.all()
    subjects = Subject.objects.all()
    departments = Department.objects.all()
    stages = Stage.objects.all().order_by('order')
    
    return render(request, 'dean/add/additions.html', {
        'academic_years': academic_years,
        'subjects': subjects,
        'departments': departments,
        'stages': stages,
    })

# إدارة العام الدراسي (إضافة/تعديل/حذف)
@login_required
def manage_academic_year(request, year_id=None):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    if year_id:
        year = get_object_or_404(AcademicYear, id=year_id)
        form = AcademicYearForm(request.POST or None, instance=year)
        action = "تعديل"
    else:
        year = None
        form = AcademicYearForm(request.POST or None)
        action = "إضافة"
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            message = f'تم {action} العام الدراسي بنجاح'
            messages.success(request, message)
            return redirect('dean_additions')
    
    return render(request, 'dean/add/manage_academic_year.html', {
        'form': form,
        'action': action,
        'year': year,
    })

@login_required
def delete_academic_year(request, year_id):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    year = get_object_or_404(AcademicYear, id=year_id)
    
    if request.method == 'POST':
        year.delete()
        messages.success(request, 'تم حذف العام الدراسي بنجاح')
        return redirect('dean_additions')
    
    return render(request, 'dean/add/confirm_delete.html', {
        'object': year,
        'object_type': 'العام الدراسي',
    })

# إدارة المادة الدراسية (إضافة/تعديل/حذف)
@login_required
def manage_subject(request, subject_id=None):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        form = SubjectForm(request.POST or None, instance=subject)
        action = "تعديل"
    else:
        subject = None
        form = SubjectForm(request.POST or None)
        action = "إضافة"
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            message = f'تم {action} المادة الدراسية بنجاح'
            messages.success(request, message)
            return redirect('dean_additions')
    
    return render(request, 'dean/add/manage_subject.html', {
        'form': form,
        'action': action,
        'subject': subject,
    })

@login_required
def delete_subject(request, subject_id):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'تم حذف المادة الدراسية بنجاح')
        return redirect('dean_additions')
    
    return render(request, 'dean/add/confirm_delete.html', {
        'object': subject,
        'object_type': 'المادة الدراسية',
    })

# إدارة القسم (إضافة/تعديل/حذف)
@login_required
def manage_department(request, department_id=None):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    if department_id:
        department = get_object_or_404(Department, id=department_id)
        form = DepartmentForm(request.POST or None, instance=department)
        action = "تعديل"
    else:
        department = None
        form = DepartmentForm(request.POST or None)
        action = "إضافة"
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            message = f'تم {action} القسم بنجاح'
            messages.success(request, message)
            return redirect('dean_additions')
    
    return render(request, 'dean/add/manage_department.html', {
        'form': form,
        'action': action,
        'department': department,
    })

@login_required
def delete_department(request, department_id):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'تم حذف القسم بنجاح')
        return redirect('dean_additions')
    
    return render(request, 'dean/add/confirm_delete.html', {
        'object': department,
        'object_type': 'القسم',
    })

# إدارة المرحلة (إضافة/تعديل/حذف)
@login_required
def manage_stage(request, stage_id=None):
    if not (request.user.is_authenticated and hasattr(request.user, 'employee') and request.user.employee.role == 'dean'):
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    if stage_id:
        stage = get_object_or_404(Stage, id=stage_id)
        form = StageForm(request.POST or None, instance=stage)
        action = "تعديل"
    else:
        stage = None
        form = StageForm(request.POST or None)
        action = "إضافة"
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            message = f'تم {action} المرحلة بنجاح'
            messages.success(request, message)
            return redirect('dean_additions')
    
    return render(request, 'dean/add/manage_stage.html', {
        'form': form,
        'action': action,
        'stage': stage,
    })

@login_required
def delete_stage(request, stage_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'dean':
        messages.error(request, 'ليس لديك صلاحية لهذا الإجراء')
        return redirect('home')
    
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.method == 'POST':
        stage.delete()
        messages.success(request, 'تم حذف المرحلة بنجاح')
        return redirect('dean_additions')
    
    return render(request, 'dean/add/confirm_delete.html', {
        'object': stage,
        'object_type': 'المرحلة',
    })


@login_required
@user_passes_test(lambda u: u.is_employee and u.employee.role == 'dean')
def manage_groups(request):
    # الحصول على جميع المراحل مع عدد الطلبات في كل مرحلة
    stages = Stage.objects.annotate(
        applications_count=models.Count(
            'applicationstatus',
            filter=models.Q(
                applicationstatus__is_rejected=False
            ) & ~models.Q(
                models.Exists(
                    ApplicationStatus.objects.filter(
                        application=models.OuterRef('applicationstatus__application'),
                        stage__order__gt=models.OuterRef('order'),
                        is_rejected=False
                    )
                )
            )
        )
    ).order_by('order')

    selected_stage_id = request.GET.get('stage')
    selected_stage = None
    statuses = ApplicationStatus.objects.none()
    group_count = 0  # القيمة الافتراضية

    if selected_stage_id:
        selected_stage = get_object_or_404(Stage, id=selected_stage_id)
        statuses = ApplicationStatus.objects.filter(
            stage=selected_stage,
            is_rejected=False
        ).exclude(
            application__in=ApplicationStatus.objects.filter(
                stage__order__gt=selected_stage.order,
                is_rejected=False
            ).values('application')
        ).select_related('application__student')

        capacity = None
        if request.method != 'POST':
            form = GroupForm()
            try:
                capacity = int(request.GET.get('capacity', 1))
            except ValueError:
                capacity = 1
        else:
            form = GroupForm(request.POST)

        if statuses.exists():
            if request.method != 'POST' and capacity:
                group_count = (statuses.count() + capacity - 1) // capacity

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid() and selected_stage:
            capacity = form.cleaned_data['capacity']
            total_statuses = statuses.count()

            if total_statuses == 0:
                messages.error(request, 'لا توجد طلبات في هذه المرحلة')
                return redirect('manage_groups')

            group_count = (total_statuses + capacity - 1) // capacity

            with transaction.atomic():
                Group.objects.filter(statuses__stage=selected_stage).delete()
                for i in range(group_count):
                    group = Group.objects.create(
                        capacity=capacity,
                        group_number=i + 1
                    )
                    start = i * capacity
                    end = start + capacity
                    selected_statuses = statuses[start:end]
                    group.statuses.set(selected_statuses)

            messages.success(request, f'تم إنشاء {group_count} مجموعات بنجاح للمرحلة {selected_stage.name}')
            return redirect('group_list')

    elif request.method != 'POST':
        form = GroupForm()

    return render(request, 'dean/groups/manage.html', {
        'stages': stages,
        'selected_stage': selected_stage,
        'statuses': statuses,
        'form': form,
        'group_count': group_count,
    })


@login_required
def group_list(request):
    stage_id = request.GET.get('stage', '')
    groups = Group.objects.all().prefetch_related('statuses')
    
    if stage_id and stage_id != 'all':
        groups = groups.filter(statuses__stage_id=stage_id).distinct()
    
    stages = Stage.objects.all().order_by('order')
    
    return render(request, 'dean/groups/list.html', {
        'groups': groups,
        'stages': stages,
        'selected_stage_id': int(stage_id) if stage_id.isdigit() else None
    })

    
@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    statuses = group.statuses.select_related('application__student')
    
    if request.method == 'POST':
        form = GroupAnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user.employee
            announcement.group = group
            announcement.announcement_type = 'private'  # جعل الإعلان خاصاً تلقائياً
            announcement.is_public = False  # التأكد من أنه ليس عاماً
            announcement.save()
            
            messages.success(request, 'تم نشر الإعلان للمجموعة بنجاح')
            return redirect('group_detail', group_id=group_id)
    else:
        form = GroupAnnouncementForm()

    return render(request, 'dean/groups/detail.html', {
        'group': group,
        'statuses': statuses,
        'form': form
    })


@login_required
@user_passes_test(lambda u: u.is_employee and u.employee.role == 'dean')
def create_public_announcement(request):
    if request.method == 'POST':
        form = PublicAnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user.employee
            announcement.announcement_type = 'general'
            announcement.is_public = True
            announcement.save()
            messages.success(request, 'تم نشر الإعلان بنجاح')
            return redirect('home')
    else:
        form = PublicAnnouncementForm()
    
    return render(request, 'announcements/create_public.html', {'form': form})



@login_required
@user_passes_test(lambda u: u.is_employee and u.employee.role == 'dean')
def dean_announcements_list(request):
    # الحصول على جميع الإعلانات مرتبة من الأحدث
    announcements = Announcement.objects.all().order_by('-created_at')
    
    # تجهيز بيانات الإعلانات للعرض
    announcements_data = []
    for announcement in announcements:
        # جمع بيانات المجموعة إذا كان الإعلان خاصاً
        group_info = None
        if announcement.group:
            students = []
            for status in announcement.group.statuses.all():
                students.append({
                    'name': status.application.student.full_name,
                    'id': status.application.id
                })
            
            group_info = {
                'number': announcement.group.group_number,
                'students': students,
                'capacity': announcement.group.capacity
            }
        
        announcements_data.append({
            'announcement': announcement,
            'group_info': group_info,
            'is_public': announcement.is_public
        })
    
    return render(request, 'dean/announcements/list.html', {
        'announcements': announcements_data
    })




@login_required
def dean_export_excel(request):
    if not (request.user.is_employee and request.user.employee.role == 'dean'):
        return redirect('home')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="applications.csv"'
    writer = csv.writer(response)
    writer.writerow(['اسم الطالب', 'القسم', 'تاريخ التقديم', 'الحالة'])
    for app in Application.objects.select_related('student', 'department').all():
        writer.writerow([
            app.student.full_name,
            app.department.name,
            app.application_date,
            app.status
        ])
    return response

@login_required
def dean_export_pdf(request):
    # يمكنك لاحقاً توليد PDF فعلي هنا باستخدام مكتبة مثل reportlab أو weasyprint
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="applications.pdf"'
    response.write("تصدير PDF غير مفعل بعد.")
    return response
