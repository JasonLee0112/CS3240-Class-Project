from django.contrib import admin

# Register your models here.
from schedule.models import Student, Advisor, Cart, Course, Schedule, AdvisorRequest

admin.site.register(Student)
admin.site.register(Advisor)
admin.site.register(AdvisorRequest)

# Admin finding list of associated classes done with:
# https://stackoverflow.com/questions/30471700/storing-list-of-objects-in-django-model

class ClassesInLine(admin.TabularInline):
    model = Course
    extra = 10

admin.site.register(Schedule)
admin.site.register(Course)
