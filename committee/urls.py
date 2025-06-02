from django.urls import path
from . import views

urlpatterns = [
   
    path('committee/', views.committee_dashboard, name='committee_dashboard'),
    # path('committee/opinion/<int:application_id>/', views.add_committee_opinion, name='add_committee_opinion'),
   
    path('data-entry/', views.data_entry_dashboard, name='data_entry_dashboard'),
    # path('rejected-applications/', views.rejected_applications, name='rejected_applications'),
    path('data_entry/process_stage/<int:application_id>/', views.process_stage, name='process_stage'),
    
    # رابط صفحة مراجعة اللجنة
    path('committee/review/<int:application_id>/', views.committee_review, name='committee_review'),
    path('stage/', views.stage_applications, name='stage_applications'),
    path('reviewed/', views.reviewed_applications, name='reviewed_applications'),
    # path('advanced-stages/', views.advanced_stages_applications, name='advanced_stages_applications'),
    path('advanced-stages/', views.all_advanced_stages, name='all_advanced_stages'),
    path('returned-applications/', views.returned_applications, name='returned_applications'),





    ]
