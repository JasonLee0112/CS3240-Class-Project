from http import HTTPStatus
import types
from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from . import views
from schedule.models import Advisor, AdvisorRequest, Cart, Course, Schedule, Student, User
from schedule.forms import SignupForm
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from schedule.scheduler import *
from django.core import mail

class AdvisorModelTestCase(TestCase):
    # Create your tests here.
    def test_advisor_get_1_students(self):
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        student1 = Student.objects.create(first_name="Student",last_name="Test", email="teststudent@test.test", advisor = advisor1)
        
        student_list = advisor1.get_students() #call get_students() to get list of advisor's students (students with Advisor Test as their advisor)
        #print(student_list)
        assert student1 in student_list #Check that student1 is in list
        assert len(student_list) == 1 #check that only student1 is in list
    def test_advisor_get_many_students(self):
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        for i in range(100):
            student2 = Student.objects.create(first_name="Student",last_name="Test", email="teststudent@test.test", advisor = advisor1)
             
        student_list = advisor1.get_students() #call get_students() to get list of advisor's students (students with Advisor Test as their advisor)
        
        assert student2 in student_list #Check that students created is in list
        assert len(student_list) == 100 #check that 100 students are in list    


class GoogleLoginTests(TestCase):
    '''
    Title: Django AllAuth KeyError at /accounts/signup/ 'sociallogin'
    Date: 3/20/23
    Author: gaurav
    URL: https://stackoverflow.com/questions/62500189/django-allauth-keyerror-at-accounts-signup-sociallogin
    '''
    def test_signup_form_student_no_advisor(self):
        student = types.SimpleNamespace()
        student.user = types.SimpleNamespace()
        student.user.email = "JohnSmith@gmail.com"
        student.user.username = "JohnSmith"
        student.user.first_name = "John"
        student.user.last_name = "Smith"
        form = SignupForm(sociallogin = student, data={"first_name": "John", "last_name": "Smith", "email": "JohnSmith@gmail.com", "user_type": 'student', "advisor_select": ""})

        self.assertTrue(form.is_valid())

    def test_signup_form_advisor(self):
        advisor = types.SimpleNamespace()
        advisor.user = types.SimpleNamespace()
        advisor.user.email = "TestAdvisor@ggmail.com"
        advisor.user.username = "TestAdvisor"
        advisor.user.first_name = "Test"
        advisor.user.last_name = "Advisor"
        form = SignupForm(sociallogin = advisor, data={"first_name": "Test", "last_name": "Advisor", "email": "TestAdvisor@gmail.com", "user_type": 'advisor'})

        self.assertTrue(form.is_valid())

    def test_signup_form_student_with_advisor(self):
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        student = types.SimpleNamespace()
        student.user = types.SimpleNamespace()
        student.user.email = "JohnSmith@ggmail.com"
        student.user.username = "JohnSmith"
        student.user.first_name = "John"
        student.user.last_name = "Smith"
        form = SignupForm(sociallogin = student, data={"first_name": "John", "last_name": "Smith", "email": "JohnSmith@gmail.com", "user_type": 'student', "advisor_select": advisor1.pk})
        
        self.assertTrue(form.is_valid())

class searchCoursesTests(TestCase):
    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        student = Student.objects.create(student_account = user, first_name = "test", last_name = "account", email = "testAccount@gmail.com", advisor = advisor1)
    
    def test_do_search_normal(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST['subject'] = 'CS'
        request.POST['term'] = 'spring'
        request.POST['year'] = '2023'
        request.POST['catalog_num'] = '3240'
        request.POST['name'] = ''
        request.user = User.objects.get(username = "testuser")

        response = views.do_search(request)
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response.url)
        self.assertContains(response, "<TD>15581</TD>")
        self.assertContains(response, "<TD>CS 3240 - 001 (LEC)</TD> ")
        self.assertContains(response, "<TD>Advanced Software Development Techniques </TD>")
        self.assertEqual(str(response.content).count('<TD>Advanced Software Development Techniques </TD>'), 3)

    def test_do_search_empty_class_fields(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST['subject'] = 'null'
        request.POST['term'] = 'spring'
        request.POST['year'] = '2023'
        request.POST['catalog_num'] = ''
        request.POST['name'] = ''
        request.user = User.objects.get(username = "testuser")
        '''
        Title: You cannot add messages without installing django.contrib.messages.middleware.MessageMiddleware
        Date: 3/27/2023
        URL: https://stackoverflow.com/questions/15852317/you-cannot-add-messages-without-installing-django-contrib-messages-middleware-me
        '''
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = views.do_search(request)
        self.assertEqual(response.url, '/student/class_search/')
        storage = get_messages(request)
        for message in storage:
            self.assertEqual(message.message, 'Please answer at least one of the class filters')

class BuildScheduleTests(TestCase):   
    student = Student()
    course = Course() 
    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        self.student = Student.objects.create(student_account = user, first_name = "test", last_name = "account", email = "testAccount@gmail.com", advisor = advisor1)
        self.course = Course.objects.create(subject = "CS", catalog_num = 1110 , class_nbr = 15865, strm = "1238", \
                                       title = "Introduction to Programming", section = "001", start_time = "02:00 PM", \
                                        end_time = "2:50 PM", meet_days = "MoWeFr", instructor = "Raymond Pettit", component = "LEC", units = "3")

    def test_empty_schedule(self):
        response = self.client.get("/student/build_schedule/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('schedule', response.context)
    
    def test_schedule_one_class(self):
        schedule = Schedule.objects.create(student = self.student)
        schedule.term = '238'
        schedule.save()
        schedule.courses.add(self.course)

        response = self.client.get("/student/build_schedule/" + str(schedule.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIn('schedule', response.context) 

    def test_add_class(self):
        schedule = Schedule.objects.create(student = self.student)
        schedule.term = '238'
        schedule.save()
        request = HttpRequest()
        request.method = 'POST'
        request.POST['schedule_pk'] = schedule.pk
        request.POST['course_pk'] = self.course.pk
        request.user = User.objects.get(username = "testuser")
        
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = views.add_class_to_schedule(request)
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/student/build_schedule/' + str(schedule.pk))
        self.assertIsNotNone(response.context['schedule'])
    
class ShoppingCartTests(TestCase):   
    student = Student()
    course = Course() 
    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        self.student = Student.objects.create(student_account = user, first_name = "test", last_name = "account", email = "testAccount@gmail.com", advisor = advisor1)
        self.course = Course.objects.create(subject = "CS", catalog_num = 1110 , class_nbr = 15865, strm = "1238", \
                                       title = "Introduction to Programming", section = "001", start_time = "02:00 PM", \
                                        end_time = "2:50 PM", meet_days = "MoWeFr", instructor = "Raymond Pettit", component = "LEC", units = "3")

    def test_empty_schedule(self):
        response = self.client.get("/student/build_schedule/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('schedules', response.context)
    
    def test_cart_one_class(self):
        cart = Cart.objects.create(student = self.student, credits = 0)
        cart.courses.add(self.course)

        response = self.client.get("/student/cart/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('courses', response.context) 

    def test_add_class(self):
        cart = Cart.objects.create(student = self.student, credits = 0)
        request = HttpRequest()
        request.method = 'POST'
        request.POST['course_pk'] = self.course.pk
        request.user = User.objects.get(username = "testuser")
        
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = views.add_class_to_cart(request)
        self.assertEqual(response.url, '/student/display_classes/')
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get('/student/cart/')
        self.assertIsNotNone(response.context['courses'])

class AdvisorRequestTest(TestCase):
    student = Student()
    course = Course() 
    schedule = Schedule()

    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        advisor1 = Advisor.objects.create(advisor_account = user, first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        self.student = Student.objects.create(first_name = "test", last_name = "account", email = "testAccount@gmail.com", advisor = advisor1)
        self.course = Course.objects.create(subject = "CS", catalog_num = 1110 , class_nbr = 15865, strm = "1238", \
                                       title = "Introduction to Programming", section = "001", start_time = "02:00 PM", \
                                        end_time = "2:50 PM", meet_days = "MoWeFr", instructor = "Raymond Pettit", component = "LEC", units = "3")
        
        self.schedule = Schedule.objects.create(student = self.student)
        self.schedule.courses.add(self.course)

    def test_update_status_approve(self):
        r = AdvisorRequest()
        r.student = self.student
        r.advisor = self.student.advisor
        r.schedule = self.schedule
        r.status = 0
        r.comment = "none"
        r.save()

        request = HttpRequest()
        request.method = 'POST'
        request.POST['request_pk'] = r.pk
        request.POST['status'] = 2
        request.POST['request_comment'] = "schedule approved"
        request.user = User.objects.get(username = "testuser")
        
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = views.update_request_status(request)
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get(response.url)
        self.assertContains(response, '<button class = "btn btn-primary" disabled>Approved</button>')
        r = AdvisorRequest.objects.get(id = r.pk)
        self.assertEqual(r.status, 2)
        self.assertEqual(r.comment,"schedule approved")
    
    def test_update_status_reject(self):
        r = AdvisorRequest()
        r.student = self.student
        r.advisor = self.student.advisor
        r.schedule = self.schedule
        r.status = 0
        r.comment = ""
        r.save()

        request = HttpRequest()
        request.method = 'POST'
        request.POST['request_pk'] = r.pk
        request.POST['status'] = 3
        request.POST['request_comment'] = ""
        request.user = User.objects.get(username = "testuser")
        
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = views.update_request_status(request)
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response.url)
        self.assertContains(response, '<button class = "btn btn-primary" disabled>Rejected</button>')
        r = AdvisorRequest.objects.get(id = r.pk)
        self.assertEqual(r.status, 3)
        # make sure function sets comment to "none" when there is no comment
        self.assertEqual(r.comment,"none")

class EmailTest(TestCase):
    student1 = Student()
    advisor1 = Advisor()

    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        self.advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        self.student1 = Student.objects.create(student_account = user, first_name="Student",last_name="Test", email="teststudent@test.test", advisor = self.advisor1)

    def test_advisor_mailing_list_summary_of_1_request(self):
        course1 = Course.objects.create(subject = 'a', catalog_num = 1000, class_nbr = 12345, 
                                        strm = 'b', title = 'c', 
                                        section = 'd', start_time = 'e', end_time = 'f', 
                                        meet_days ='g', instructor = 'h', component = 'i', units = 'j')
        
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        advisingRequest = AdvisorRequest.objects.create(advisor = self.advisor1,
                                                        student = self.student1, 
                                                        schedule = schedule1, 
                                                        status = 0, 
                                                        comment = "")

        email_format = get_email_schedule_summary(self.advisor1)
        assert email_format == [
            "Schedule Requests:",
            "You have 1 requests pending",
            "noreply@automatedmessage.com",
            ["testadvisor@test.test"]
        ]

    def test_advisor_mailing_list_summary_of_many_requests(self):
        course1 = Course.objects.create(subject = 'a', catalog_num = 1000, class_nbr = 12345, 
                                        strm = 'b', title = 'c', 
                                        section = 'd', start_time = 'e', end_time = 'f', 
                                        meet_days ='g', instructor = 'h', component = 'i', units = 'j')
        
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        for i in range(100):
            advisingRequest = AdvisorRequest.objects.create(advisor = self.advisor1,
                                                        student = self.student1, 
                                                        schedule = schedule1, 
                                                        status = 0, 
                                                        comment = "")
        email_format = get_email_schedule_summary(self.advisor1)
        assert email_format == [
            "Schedule Requests:",
            "You have 100 requests pending",
            "noreply@automatedmessage.com",
            ["testadvisor@test.test"]
        ]

    def test_single_person_email_sending_task(self):
        course1 = Course.objects.create(subject = 'a', catalog_num = 1000, class_nbr = 12345, 
                                        strm = 'b', title = 'c', 
                                        section = 'd', start_time = 'e', end_time = 'f', 
                                        meet_days ='g', instructor = 'h', component = 'i', units = 'j')
        
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        advisingRequest = AdvisorRequest.objects.create(advisor = self.advisor1,
                                                        student = self.student1, 
                                                        schedule = schedule1, 
                                                        status = 0, 
                                                        comment = "")
        send_reminder_email(self.advisor1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, "You have 1 requests pending", msg = mail.outbox[0].body)

    def test_multi_request_email_sending_task(self):
        course1 = Course.objects.create(subject = 'a', catalog_num = 1000, class_nbr = 12345, 
                                        strm = 'b', title = 'c', 
                                        section = 'd', start_time = 'e', end_time = 'f', 
                                        meet_days ='g', instructor = 'h', component = 'i', units = 'j')
        
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        for i in range(100):
            advisingRequest = AdvisorRequest.objects.create(advisor = self.advisor1,
                                                        student = self.student1, 
                                                        schedule = schedule1, 
                                                        status = 0, 
                                                        comment = "")
        send_reminder_email(self.advisor1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, "You have 100 requests pending", msg = mail.outbox[0].body)
from django.test import Client
class DownloadICSTest(TestCase):
    student1 = Student()
    advisor1 = Advisor()

    def setUp(self):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        self.advisor1 = Advisor.objects.create(first_name="Advisor",last_name="Test", email="testadvisor@test.test")
        self.student1 = Student.objects.create(student_account = user, first_name="Student",last_name="Test", email="teststudent@test.test", advisor = self.advisor1)

    def test_singleclassdownload(self):
        course1 = Course.objects.create(subject = 'CS', catalog_num = 3240, class_nbr = 3240, 
                                strm = '1234', title = 'Advanced Software Development', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton', component = 'LEC', units = '3')
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)

        rev = reverse('download_ics')
        response = self.client.post(f'{rev}', {'schedule_pk':schedule1.pk})

        self.assertEqual(response['Content-Type'], 'text/calendar')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="schedule.ics"')
        self.assertEqual(response.status_code, 200)
        
        #Check title
        self.assertIn(course1.title, str(response.content))
        #Check Instructor
        self.assertIn(course1.instructor, str(response.content))
        #Check year
        self.assertIn('2023', str(response.content))
    
    def test_multisessiondownload(self):
        course1 = Course.objects.create(subject = 'CS', catalog_num = 3240, class_nbr = 3240, 
                                strm = '1234', title = 'Advanced Software Development2', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton2', component = 'LEC', units = '3')
        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        #summer class
        course2 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1235', title = 'Advanced Software Development 3', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton3', component = 'LEC', units = '3')

        schedule1.courses.add(course2)
        #fall class
        course3 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1238', title = 'Advanced Software Development 1', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton1', component = 'LEC', units = '3')
        schedule1.courses.add(course3)
        rev = reverse('download_ics')
        response = self.client.post(f'{rev}', {'schedule_pk':schedule1.pk})

        self.assertEqual(response['Content-Type'], 'text/calendar')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="schedule.ics"')
        self.assertEqual(response.status_code, 200)
        
        #Check title
        self.assertIn(course1.title, str(response.content))
        #Check Instructor
        self.assertIn(course1.instructor, str(response.content))
        #Check year and month course 1
        self.assertTrue('20'+course1.strm[1:3] in (str(response.content)) or 
                        '20'+course1.strm[1:3]+'0'+course1.strm[4] in (str(response.content)))
        #Check year and month course 2
        self.assertTrue('20'+course2.strm[1:3] in (str(response.content)) or 
                        '20'+course2.strm[1:3]+'0'+course2.strm[4] in (str(response.content)))
        #Check year and month course 3
        self.assertTrue('20'+course3.strm[1:3] in (str(response.content)) or 
                '20'+course3.strm[1:3]+'0'+course3.strm[4] in (str(response.content)))

        #Check title
        self.assertIn(course2.title, str(response.content))
        #Check Instructor
        self.assertIn(course2.instructor, str(response.content))
        #Check title
        self.assertIn(course3.title, str(response.content))
        #Check Instructor
        self.assertIn(course3.instructor, str(response.content))
        
    def test_multi_class_in_session_download(self):
        course1 = Course.objects.create(subject = 'CS', catalog_num = 3240, class_nbr = 3240, 
                                strm = '1234', title = 'Advanced Software Development2', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton2', component = 'LEC', units = '3')
        course12 = Course.objects.create(subject = 'CS', catalog_num = 3240, class_nbr = 3240, 
                                strm = '1234', title = 'Advanced Software Development2', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Mo Wed', instructor = 'Tom Horton2', component = 'LEC', units = '3')

        schedule1 = Schedule.objects.create(student = self.student1)
        schedule1.courses.add(course1)
        schedule1.courses.add(course12)
        #summer class
        course2 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1235', title = 'Advanced Software Development 3', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton3', component = 'LEC', units = '3')
        course22 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1235', title = 'Advanced Software Development 3', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Mo Wed', instructor = 'Tom Horton3', component = 'LEC', units = '3')
        schedule1.courses.add(course2)
        schedule1.courses.add(course22)
        #fall class
        course3 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1238', title = 'Advanced Software Development 1', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Tu Thur', instructor = 'Tom Horton1', component = 'LEC', units = '3')
        course32 = Course.objects.create(subject = 'MATH', catalog_num = 3250, class_nbr = 3250, 
                                strm = '1238', title = 'Advanced Software Development 1', 
                                section = 'd', start_time = '02:00 PM', end_time = '03:15 PM', 
                                meet_days ='Mo Wed', instructor = 'Tom Horton1', component = 'LEC', units = '3')
        schedule1.courses.add(course3)
        schedule1.courses.add(course32)
        rev = reverse('download_ics')
        response = self.client.post(f'{rev}', {'schedule_pk':schedule1.pk})

        self.assertEqual(response['Content-Type'], 'text/calendar')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="schedule.ics"')
        self.assertEqual(response.status_code, 200)
        
        #print(response.content)

        #Check title
        self.assertIn(course1.title, str(response.content))
        #Check Instructor
        self.assertIn(course1.instructor, str(response.content))
        #Check year and month course 1
        self.assertTrue('20'+course1.strm[1:3] in (str(response.content)) or 
                        '20'+course1.strm[1:3]+'0'+course1.strm[4] in (str(response.content)))
        #Check year and month course 2
        self.assertTrue('20'+course2.strm[1:3] in (str(response.content)) or 
                        '20'+course2.strm[1:3]+'0'+course2.strm[4] in (str(response.content)))
        #Check year and month course 3
        self.assertTrue('20'+course3.strm[1:3] in (str(response.content)) or 
                '20'+course3.strm[1:3]+'0'+course3.strm[4] in (str(response.content)))
        #Check year and month course 12
        self.assertTrue('20'+course12.strm[1:3] in (str(response.content)) or 
                        '20'+course12.strm[1:3]+'0'+course12.strm[4] in (str(response.content)))
        #Check year and month course 22
        self.assertTrue('20'+course22.strm[1:3] in (str(response.content)) or 
                        '20'+course22.strm[1:3]+'0'+course22.strm[4] in (str(response.content)))
        #Check year and month course 32
        self.assertTrue('20'+course32.strm[1:3] in (str(response.content)) or 
                '20'+course32.strm[1:3]+'0'+course32.strm[4] in (str(response.content)))

        #Check title
        self.assertIn(course2.title, str(response.content))
        #Check Instructor
        self.assertIn(course2.instructor, str(response.content))
        #Check title
        self.assertIn(course3.title, str(response.content))
        #Check Instructor
        self.assertIn(course3.instructor, str(response.content))
        #Check title
        self.assertIn(course12.title, str(response.content))
        #Check Instructor
        self.assertIn(course12.instructor, str(response.content))
        #Check title
        self.assertIn(course22.title, str(response.content))
        #Check Instructor
        self.assertIn(course22.instructor, str(response.content))
        #Check title
        self.assertIn(course32.title, str(response.content))
        #Check Instructor
        self.assertIn(course32.instructor, str(response.content))