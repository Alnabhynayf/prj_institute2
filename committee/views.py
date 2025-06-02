from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from .models import *
from .forms import *
from students.forms import *
from dean.forms import *

from django.utils import timezone
from django.db.models import Q

from django.db.models import Max, F, Exists
from django.db.models import Prefetch
from students.models import *   
from dean.models import *   



# لوحة تحكم مدخل البيانات - معدلة لجميع المراحل
@login_required
def data_entry_dashboard(request):
    if not request.user.employee.role == 'data_entry':
        return redirect('home')
    
    # الحصول على الطلبات في المراحل من 2 إلى 5 والتي لم يتم إدخال نتائجها بعد
    applications = Application.objects.filter(
        applicationstatus__stage__order__in=[2, 3, 4, 5],
        applicationstatus__is_rejected=False,
        applicationstatus__stageresult__isnull=True
    ).distinct()
    
    return render(request, 'data_entry/dashboard.html', {
        'applications': applications
    })

# معالجة المراحل المختلفة - وظيفة واحدة لجميع المراحل
@login_required
@transaction.atomic
def process_stage(request, application_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'data_entry':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    application = get_object_or_404(Application, id=application_id)
    current_status = application.applicationstatus_set.latest('created_at')
    
    if request.method == 'POST':
        form = StageResultForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                stage_result = form.save(commit=False)
                stage_result.employee = request.user.employee
                stage_result.application_status = current_status
                
                # معالجة كل مرحلة حسب نوعها
                if current_status.stage.order == 2:  # الفحص الطبي
                    medical_info = {
                        'result': request.POST.get('medical_result', ''),
                        'notes': request.POST.get('medical_notes', ''),
                        'is_fit': request.POST.get('is_fit') == 'on',
                        'file': request.FILES.get('medical_file').name if request.FILES.get('medical_file') else None
                    }
                    stage_result.score = medical_info
                elif current_status.stage.order == 3:  # الاختبارات التحريرية
                    written_scores = {}
                    subjects = Subject.objects.filter(department=application.department, material_type='written')
                    for subject in subjects:
                        score_key = f'subject_{subject.id}'
                        if score_key in request.POST and request.POST[score_key]:
                            score = float(request.POST[score_key])
                            written_scores[subject.name] = score
                    written_scores['total'] = sum(written_scores.values())
                    written_scores['file'] = request.FILES.get('written_file').name if request.FILES.get('written_file') else None
                    stage_result.score = written_scores
                elif current_status.stage.order == 4:  # الاختبارات الشفوية
                    oral_scores = {}
                    subjects = Subject.objects.filter(department=application.department, material_type='oral')
                    for subject in subjects:
                        score_key = f'subject_{subject.id}'
                        if score_key in request.POST and request.POST[score_key]:
                            score = float(request.POST[score_key])
                            oral_scores[subject.name] = score
                    oral_scores['total'] = sum(oral_scores.values())
                    oral_scores['file'] = request.FILES.get('oral_file').name if request.FILES.get('oral_file') else None
                    stage_result.score = oral_scores
                elif current_status.stage.order == 5:  # المقابلة الشخصية
                    interview_result = {
                        'score': float(request.POST.get('interview_score', 0)),
                        'notes': request.POST.get('interview_notes', ''),
                        'file': request.FILES.get('interview_file').name if request.FILES.get('interview_file') else None
                    }
                    stage_result.score = interview_result
                
                stage_result.save()
                
                # تحديث حالة الطلب
                current_status.notes = 'تم إدخال النتائج وجاهز لمراجعة اللجنة'
                current_status.save()
                
                messages.success(request, 'تم حفظ النتائج وإرسال الطلب إلى اللجنة')
                return redirect('data_entry_dashboard')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')
                return redirect('data_entry_dashboard')
    else:
        form = StageResultForm()
    
    # تحديد البيانات المعروضة حسب المرحلة
    context = {
        'application': application,
        'current_status': current_status,
        'form': form
    }
    
    if current_status.stage.order == 2:
        context['is_medical'] = True
    elif current_status.stage.order == 3:
        context['subjects'] = Subject.objects.filter(department=application.department, material_type='written')
        context['is_written'] = True
    elif current_status.stage.order == 4:
        context['subjects'] = Subject.objects.filter(department=application.department, material_type='oral')
        context['is_oral'] = True
    elif current_status.stage.order == 5:
        context['is_interview'] = True
    
    return render(request, 'data_entry/process_stage.html', context)


















from django.db.models import Count, Q, Max
from django.utils import timezone
from datetime import timedelta

@login_required
def committee_dashboard(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    employee = request.user.employee

    # الطلبات التي قيّمها العضو
    reviewed_opinions = CommitteeOpinion.objects.filter(employee=employee)
    total_reviewed = reviewed_opinions.count()

    # الطلبات التي قيّمها العضو (distinct)
    reviewed_app_ids = reviewed_opinions.values_list('application_status__application_id', flat=True).distinct()
    total_applications = reviewed_app_ids.count()

    # الطلبات المنتظرة من العضو (لم يقيّمها بعد)
    all_app_ids = Application.objects.values_list('id', flat=True)
    pending_app_ids = set(all_app_ids) - set(reviewed_app_ids)
    pending_applications = len(pending_app_ids)
    pending_apps = Application.objects.filter(id__in=pending_app_ids)[:10]

    # الطلبات المعادة من العميد والتي لم يقيّمها العضو بعد
    returned_apps = Application.objects.filter(
        applicationstatus__is_rejected=False,
        applicationstatus__notes__icontains='تم إعادة الطلب للجنة للمراجعة'
    ).exclude(id__in=reviewed_app_ids).distinct()
    returned_count = returned_apps.count()

    # الطلبات المتأخرة (مثال: مضى عليها أكثر من 5 أيام ولم يقيّمها العضو)
    from datetime import timedelta
    from django.utils import timezone
    overdue_apps = Application.objects.filter(
        id__in=pending_app_ids,
        applicationstatus__created_at__lte=timezone.now() - timedelta(days=5)
    ).distinct()

    # توزيع الطلبات حسب المرحلة (فقط ما قيّمه العضو)
    stage_stats = (
        ApplicationStatus.objects.filter(
            committeeopinion__employee=employee
        ).values('stage__name')
        .annotate(total=Count('id'))
        .order_by('stage__order')
    )
    stage_labels = [s['stage__name'] for s in stage_stats]
    stage_values = [s['total'] for s in stage_stats]

    # توزيع الطلبات حسب الحالة (فقط ما قيّمه العضو)
    status_stats = (
        Application.objects.filter(id__in=reviewed_app_ids)
        .values('status')
        .annotate(total=Count('id'))
    )
    status_labels = [s['status'] for s in status_stats]
    status_values = [s['total'] for s in status_stats]

    # أحدث الطلبات التي قيّمها العضو
    latest_reviewed = reviewed_opinions.select_related('application_status__application').order_by('-created_at')[:10]

    context = {
        'total_applications': total_applications,
        'total_reviewed': total_reviewed,
        'pending_applications': pending_applications,
        'returned_count': returned_count,
        'overdue_apps': overdue_apps,
        'stage_labels': stage_labels,
        'stage_values': stage_values,
        'status_labels': status_labels,
        'status_values': status_values,
        'latest_reviewed': latest_reviewed,
        'pending_apps': pending_apps,
    }
    return render(request, 'committee/committee_dashboard.html', context)



@login_required
def reviewed_applications(request):
    """
    عرض الطلبات التي تم تقييمها من قبل العضو
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # الطلبات التي قام العضو بتقييمها
    reviewed_apps = Application.objects.filter(
        applicationstatus__committeeopinion__employee=request.user.employee
    ).distinct()

    # تجهيز بيانات الطلبات
    apps_data = []
    for app in reviewed_apps:
        current_status = app.applicationstatus_set.latest('created_at')
        opinion = CommitteeOpinion.objects.filter(
            application_status=current_status,
            employee=request.user.employee
        ).first()

        stage_result = StageResult.objects.filter(application_status=current_status).first()

        apps_data.append({
            'app': app,
            'current_status': current_status,
            'opinion': opinion,
            'stage_result': stage_result,
            'stage_data': stage_result.score if stage_result else {},
            'review_date': opinion.created_at if opinion else None,
            'has_opinion': True
        })

    context = {
        'apps_data': apps_data,
        'stage_title': 'الطلبات المقيّمة',
        'stage_description': 'الطلبات التي قمت بتقييمها مسبقاً'
    }
    return render(request, 'committee/stage_applications.html', context)











@login_required
def stage_applications(request):
    """
    عرض الطلبات في المرحلة الأولى (مع استبعاد الطلبات المعادة من العميد)
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # الطلبات في المرحلة الأولى (المراجعة الأولية)
    stage_one_apps = Application.objects.filter(
        applicationstatus__stage__order=1,
        applicationstatus__is_rejected=False
    ).exclude(
        # استبعاد الطلبات التي تمت الموافقة عليها في مراحل أعلى
        applicationstatus__stage__order__gt=1
    ).exclude(
        # استبعاد الطلبات التي تحتوي على ملاحظات إعادة من العميد
        applicationstatus__notes__icontains='تم إعادة الطلب للجنة للمراجعة'
    ).annotate(
        latest_status_date=Max('applicationstatus__created_at')
    ).order_by('latest_status_date')

    # تجهيز بيانات الطلبات
    apps_data = []
    for app in stage_one_apps:
        current_status = app.applicationstatus_set.latest('created_at')

        # تجاهل الطلبات التي قدّم العضو رأيه فيها
        if current_status.committeeopinion_set.filter(employee=request.user.employee).exists():
            continue

        apps_data.append({
            'app': app,
            'current_status': current_status,
            'has_opinion': False
        })

    context = {
        'apps_data': apps_data,
        'stage_title': 'المرحلة الأولى',
        'stage_description': 'الطلبات الجديدة التي تحتاج إلى مراجعة أولية (غير المعادة من العميد)'
    }
    return render(request, 'committee/stage_applications.html', context)

 
# @login_required
# def advanced_stages_applications(request):
#     """
#     عرض الطلبات في المراحل المتقدمة (2-5)
#     """
#     if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
#         messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
#         return redirect('home')

#     # الطلبات في المراحل الأخرى (2-5) بعد إدخال النتائج
#     other_stages_apps = Application.objects.filter(
#         applicationstatus__stage__order__in=[2, 3, 4, 5],
#         applicationstatus__is_rejected=False,
#         applicationstatus__stageresult__isnull=False
#     ).annotate(
#         latest_status_date=Max('applicationstatus__created_at')
#     ).order_by('latest_status_date').distinct()

#     # تجهيز بيانات الطلبات
#     apps_data = []
#     for app in other_stages_apps:
#         current_status = app.applicationstatus_set.latest('created_at')
#         stage_result = StageResult.objects.filter(application_status=current_status).first()

#         if not stage_result:
#             continue

#         if current_status.committeeopinion_set.filter(employee=request.user.employee).exists():
#             continue

#         apps_data.append({
#             'app': app,
#             'current_status': current_status,
#             'stage_result': stage_result,
#             'stage_data': stage_result.score or {},
#             'has_opinion': False
#         })

#     context = {
#         'apps_data': apps_data,
#         'stage_title': 'المراحل المتقدمة',
#         'stage_description': 'الطلبات التي وصلت إلى المراحل المتقدمة وتحتاج إلى تقييم'
#     }
#     return render(request, 'committee/stage_applications.html', context)


@login_required
def all_advanced_stages(request):
    """
    عرض جميع المراحل المتقدمة (2-5) في صفحة واحدة مع تقسيم لكل مرحلة
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # تجميع بيانات جميع المراحل
    stages_data = {
        'stage2': {
            'title': 'المرحلة الثانية',
            'description': 'الطلبات التي اجتازت الفحص الأولي',
            'order': 2,
            'apps': []
        },
        'stage3': {
            'title': 'المرحلة الثالثة',
            'description': 'الطلبات التي تحتاج لتقييم الاختبارات الكتابية',
            'order': 3,
            'apps': []
        },
        'stage4': {
            'title': 'المرحلة الرابعة',
            'description': 'الطلبات التي تحتاج لتقييم المقابلات الشخصية',
            'order': 4,
            'apps': []
        },
        'stage5': {
            'title': 'المرحلة الخامسة',
            'description': 'الطلبات التي تحتاج لتقييم نهائي',
            'order': 5,
            'apps': []
        }
    }

    # استرجاع جميع الطلبات في المراحل 2-5 مع معلومات القسم
    from django.db.models import Q

    advanced_apps = Application.objects.filter(
        applicationstatus__stage__order__in=[2, 3, 4, 5],
        applicationstatus__is_rejected=False,
        applicationstatus__stageresult__isnull=False
    ).exclude(
        applicationstatus__notes__icontains='تم إعادة الطلب للجنة للمراجعة'
    
        
    ).select_related('department').annotate(
        latest_status_date=Max('applicationstatus__created_at')
    ).order_by('latest_status_date').distinct()

    # تجهيز بيانات كل مرحلة
    for app in advanced_apps:
        current_status = app.applicationstatus_set.latest('created_at')
        stage_result = StageResult.objects.filter(application_status=current_status).first()
        stage_order = current_status.stage.order

        # تجاهل الطلبات التي قدّم العضو رأيه فيها
        if current_status.committeeopinion_set.filter(employee=request.user.employee).exists():
            continue

        app_data = {
            'app': app,
            'current_status': current_status,
            'stage_result': stage_result,
            'stage_data': stage_result.score if stage_result else {},
            'has_opinion': False
        }
       
        if not stage_result:
            continue

        # إضافة الطلب للمرحلة المناسبة
        if stage_order == 2:
            stages_data['stage2']['apps'].append(app_data)
        elif stage_order == 3:
            stages_data['stage3']['apps'].append(app_data)
        elif stage_order == 4:
            stages_data['stage4']['apps'].append(app_data)
        elif stage_order == 5:
            stages_data['stage5']['apps'].append(app_data)

    context = {
        'stages_data': stages_data,
        'page_title': 'المراحل المتقدمة'
    }
    return render(request, 'committee/all_advanced_stages.html', context)


@login_required
def returned_applications(request):
    """
    عرض الطلبات التي أعادها العميد للجنة للمراجعة
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # فلترة الطلبات المعادة من العميد
    returned_apps = Application.objects.filter(
        applicationstatus__is_rejected=False,
        applicationstatus__notes__icontains='تم إعادة الطلب للجنة للمراجعة'
    ).annotate(
        latest_status_date=Max('applicationstatus__created_at')
    ).order_by('latest_status_date').distinct()

    # تجهيز بيانات الطلبات
    apps_data = []
    for app in returned_apps:
        current_status = app.applicationstatus_set.latest('created_at')
        
        # تجاهل الطلبات التي قدّم العضو رأيه فيها مسبقاً
        if current_status.committeeopinion_set.filter(employee=request.user.employee).exists():
            continue

        # الحصول على ملاحظات العميد
        dean_notes = ""
        if 'تم إعادة الطلب للجنة للمراجعة' in current_status.notes:
            dean_notes = current_status.notes.split(':', 1)[-1].strip()

        apps_data.append({
            'app': app,
            'current_status': current_status,
            'dean_notes': dean_notes,
            'has_opinion': False
        })

    context = {
        'apps_data': apps_data,
        'stage_title': 'الطلبات المعادة',
        'stage_description': 'الطلبات التي أعادها العميد للجنة للمراجعة مرة أخرى'
    }
    return render(request, 'committee/returned_applications.html', context)



# رأي اللجنة - يعمل مع جميع المراحل
@login_required
def committee_review(request, application_id):
    """
    عرض نموذج مراجعة الطلب من قبل عضو اللجنة
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'employee') or request.user.employee.role != 'committee_member':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    application = get_object_or_404(Application, id=application_id)
    current_status = application.applicationstatus_set.latest('created_at')
    
    # التحقق من أن العضو لم يقدم رأيه بالفعل
    if CommitteeOpinion.objects.filter(application_status=current_status, employee=request.user.employee).exists():
        messages.warning(request, 'لقد قدمت رأيك بالفعل في هذا الطلب')
        return redirect('committee_dashboard')
    
    # جلب نتائج المرحلة إن وجدت
    stage_result = StageResult.objects.filter(application_status=current_status).first()
    stage_data = stage_result.score if stage_result else {}
    
    if request.method == 'POST':
        opinion_value = request.POST.get('opinion')
        notes = request.POST.get('notes', '')
        
        if not opinion_value or opinion_value not in ['accept', 'reject']:
            messages.error(request, 'يجب اختيار رأي صحيح (قبول/رفض)')
            return redirect('committee_review', application_id=application_id)
        
        if not notes.strip():
            messages.error(request, 'يجب إدخال تعليقاتك')
            return redirect('committee_review', application_id=application_id)
        
        try:
            # حفظ رأي العضو
            CommitteeOpinion.objects.create(
                employee=request.user.employee,
                application_status=current_status,
                opinion=opinion_value,
                notes=notes
            )
            
            # التحقق إذا كان جميع الأعضاء قد قدموا آرائهم
            total_members = Employee.objects.filter(role='committee_member').count()
            total_opinions = CommitteeOpinion.objects.filter(application_status=current_status).count()
            
            if total_opinions == total_members:
                # تحديث حالة الطلب لإعلام العميد
                current_status.notes = 'تمت مراجعة الطلب من قبل اللجنة وجاهز لمراجعة العميد'
                current_status.save()
                
                # إرسال إشعار للعميد (يمكن تنفيذه لاحقاً)
                # send_notification_to_dean(application)
            
            messages.success(request, 'تم تسجيل رأيك بنجاح')
            return redirect('committee_dashboard')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')
            return redirect('committee_review', application_id=application_id)
    
    # تحضير البيانات للعرض حسب المرحلة
    context = {
        'application': application,
        'current_status': current_status,
        'stage_data': stage_data,
    }
    # الفصل حسب المرحلة
    if current_status.stage.order == 1:
        template_name = 'committee/review.html'
    else:
        template_name = 'committee/review_stage.html'
    return render(request, template_name, context)

