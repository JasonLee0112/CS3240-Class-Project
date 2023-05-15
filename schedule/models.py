import json
from django.db import models
from django.contrib.auth.models import User
#Below are imports for advisee assignment
import uuid 
from django.contrib.auth.models import AbstractUser
import requests
from django.core.mail import *

'''
Title: Multiple user type sign up with django-allauth
Date: 2/23/2023
Author: mrnfrancesco
URL: https://stackoverflow.com/questions/44505242/multiple-user-type-sign-up-with-django-allauth
'''
class Advisor(models.Model):
    advisor_account = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length = 100)
    def get_students(self): #Getting a list of students for the advisor to view
        students = Student.objects.filter(advisor=self)
        return students
    
    def __str__(self):
        return '{} {}'.format(self.first_name.capitalize(), self.last_name.capitalize())

    @property
    def is_student(self):
        return False

# Create your models here.    
class Student(models.Model):
    student_account = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length = 100)
    advisor = models.ForeignKey(Advisor, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def get_advisor(self):
        return self.advisor

    @property
    def is_student(self):
        return True

class Course(models.Model):
    subject = models.CharField(max_length=6)
    catalog_num = models.IntegerField()
    class_nbr = models.IntegerField()
    strm = models.CharField(max_length=4)
    title = models.CharField(max_length=100)
    section = models.CharField(max_length=50)
    start_time = models.CharField(max_length=8)
    end_time = models.CharField(max_length=10)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    meet_days = models.CharField(max_length=20)
    instructor = models.CharField(max_length=100)
    component = models.CharField(max_length=10)
    units = models.CharField(max_length = 6)

    def printTerm(self):
        if(self.strm[3] == "2"):
            return 'Spring 20' + str(self.strm[1:3])
        elif(self.strm[3] == "6"):
            return 'Summer 20' + str(self.strm[1:3])
        elif(self.strm[3] == "1"):
            return 'Winter 20' + str(self.strm[1:3])
        else:
            return 'Fall 20' + str(self.strm[1:3])
        
    def getSemester(self):
        if(self.strm[3] == "2"):
            return 'SPRING'
        elif(self.strm[3] == "6"):
            return 'SUMMER'
        elif(self.strm[3] == "1"):
            return 'WINTER'
        else:
            return 'FALL'

'''
Title: Many-to-many relationships
Date: 3/27/2023
URL: https://docs.djangoproject.com/en/3.2/topics/db/examples/many_to_many/
'''
class ClassSearch(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    search_results = models.ManyToManyField(Course)

class Cart(models.Model):
    credits = models.IntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    courses = models.ManyToManyField(Course)

class Schedule(models.Model):
    courses = models.ManyToManyField(Course)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.CharField(max_length=4)
    editable = models.BooleanField(default=True)

    def get_schedule(self):
        days_of_week = ['Mo', 'Tu', 'We', 'Th', 'Fr','Sa','Su']
        scheduleList = [[],[],[],[],[],[],[]]

        for course in self.courses.all():
            for i in range(len(days_of_week)):
                if(course.meet_days.__contains__(days_of_week[i])):
                    scheduleList[i].append(course)
        return scheduleList
    
    def getTerm(self):
        if(int(self.term[2:]) == 2):
            return "Spring 20" + str(self.term[0:2])
        elif(int(self.term[2:]) == 1):
            return "Winter 20" + str(self.term[0:2])
        elif(int(self.term[2:]) == 6):
            return "Summer 20" + str(self.term[0:2])
        elif(int(self.term[2:]) == 8):
            return "Fall 20" + str(self.term[0:2])
    
    def __str__(self):
        return '{}\'s {} Schedule'.format(self.student.first_name, Schedule.getTerm(self))

class AdvisorRequest(models.Model):
    advisor = models.ForeignKey(Advisor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    status = models.IntegerField() # 0: sent | 1: seen | 2: approved | 3: rejected
    comment = models.TextField()
    seen = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if(self.status != 3):
            self.schedule.editable = False
        else:
            self.schedule.editable = True
        self.schedule.save()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return '{} : {}'.format(self.advisor, self.student)
