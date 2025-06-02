from django.contrib import admin

# Register your models here.
from .models import *
from students.models import *
from committee.models import *




admin.site.register(User)
admin.site.register(Department)
admin.site.register(AcademicYear)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(Stage)
admin.site.register(Employee)
admin.site.register(Application)
admin.site.register(Qualification)
admin.site.register(StudentDocuments)
admin.site.register(PersonalInfo)
admin.site.register(FatherInfo)
admin.site.register(BirthInfo)
admin.site.register(ApplicationStatus)
admin.site.register(StageResult)
# admin.site.register(Announcement)
