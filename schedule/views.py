from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth import logout
from django.contrib import messages
from allauth.socialaccount.views import SignupView
from django.views import generic
from django.urls import reverse
from django.template import Context
from datetime import datetime
import datetime as dtime
import ast
import requests
import json
from django.conf import settings
from schedule.forms import AddAdviseesForm, SetAdvisorForm
from schedule.models import Student, Advisor, ClassSearch, Schedule, AdvisorRequest, Course, Cart

#########################                     Index Views / Login Functionality                     #########################

'''
Title: Get current user in view
Date: 3/2/2023
URL: https://stackoverflow.com/questions/23451194/get-current-user-in-view
Author: Alex
'''
def index(request):
    current_user = request.user
    if(current_user.is_authenticated):
        if(Student.objects.filter(student_account=current_user).first() is not None):
            studentid = Student.objects.get(student_account=current_user).id

            if(AdvisorRequest.objects.filter(student_id=studentid).first() is not None):
                # Retreive the advisor request opbject for this student
                for advisorRequestObject in AdvisorRequest.objects.filter(student_id=studentid).order_by('id'):
                    print(advisorRequestObject)
                    message = "Schedule #" + str(advisorRequestObject.schedule_id)
                    try:
                        schedulestatus = advisorRequestObject.status
                        seen = advisorRequestObject.seen

                        if (not seen):
                            if (schedulestatus == 2):
                                message += " has been approved by your advisor"
                                messages.success(request, message)
                            elif (schedulestatus == 3):
                                message += " has been rejected by your advisor"
                                messages.error(request, message)
                            elif (schedulestatus == 0 or schedulestatus == 1):
                                message += " is still being reviewed by your advisor"
                                messages.warning(request, message)
                            advisorRequestObject.seen = True
                            advisorRequestObject.save()
                            # loop through the schedule request. Change seen status within the advisor
                    except AdvisorRequest.DoesNotExist:
                        pass

            return redirect('student/')

        elif(Advisor.objects.filter(advisor_account=current_user).first() is not None):
            return redirect('advisor/')
        else:
            return render(request, 'schedule/index.html')
    else:
        return render(request, 'schedule/index.html')

def studentIndex(request):
    #added advisor into context
    student = Student.objects.filter(student_account=request.user).first()
    advisor = student.advisor
    requests = AdvisorRequest.objects.filter(student=student).all()
    schedules = Schedule.objects.filter(student = student).all()
    context = {'student': student, 'requests':requests, 'schedules': schedules}

    # if the student doesn't have an advisor
    context['disableFunctions'] = advisor is None

    # limits the number of courses shown in the shopping cart section to 3
    cart = Cart.objects.filter(student = student).first()
    context['cartCourses'] = None
    context['cartCredits'] = None
    context['cartOver3'] = False
    if(cart is not None and len(cart.courses.all()) > 0):
        allCartCourses = cart.courses.all()
        cartCourses = []
        max_range = min(len(allCartCourses), 3)
        for i in range(0, max_range):
            course = allCartCourses[i]
            cartCourses.append([str(course.subject) + " " + str(course.catalog_num) +": " + str(course.title) + " (" + str(course.component) + ")", course.printTerm(), course.units])
        context['cartCourses'] = cartCourses
        context['cartCredits'] = cart.credits
        context['cartOver3'] = len(allCartCourses) > 3

    form = SetAdvisorForm()
    context['setAdvisorForm'] = form

    return render(request, 'schedule/student/student_home.html', context)

def set_advisor(request):
    selectAdvisorForm = SetAdvisorForm(request.POST)
    if(selectAdvisorForm.is_valid()):
        student = Student.objects.filter(student_account=request.user).first()
        student.advisor = selectAdvisorForm.cleaned_data.get('advisor_select')
        student.save()
        messages.success(request, "Your advisor has been updated!")
        return redirect(studentIndex)

def advisorIndex(request):
    advisor = Advisor.objects.filter(advisor_account=request.user).first()
    students = advisor.get_students()
    requestsQueryset = AdvisorRequest.objects.filter(advisor = advisor)
    studentsStatus = None
    if(len(students) > 0):
        studentsStatus = []
        for student in students:
            studentRequests = requestsQueryset.filter(student = student).all()
            status = 'not received'
            for studentRequest in studentRequests:
                if(studentRequest.status == 2 or status == 'approved'):
                    status = 'approved'
                elif(studentRequest.status == 3 or status == 'rejected'):
                    status = 'rejected'
                elif(studentRequest.status == 0 or studentRequest.status == 1 or status == 'pending'):
                    status = 'pending'
                else:
                    status = 'not received'
            studentsStatus.append([student, status])
    
    pendingRequests = None
    if(len(requestsQueryset.all()) > 0):
        pendingRequests = []
        for advisorRequest in requestsQueryset.all():
            if(advisorRequest.status == 0 or advisorRequest.status == 1):
                pendingRequests.append(advisorRequest)

    form = AddAdviseesForm(advisor.pk)
    context = {'students': studentsStatus, 'pendingRequests': pendingRequests, 'adviseeForm': form}

    return render(request, 'schedule/advisor/advisor_home.html', context)

def add_advisee(request):
    advisor = Advisor.objects.filter(advisor_account = request.user).first()
    addAdviseesForm = AddAdviseesForm(advisor.pk, request.POST)
    if(addAdviseesForm.is_valid()):
        students = addAdviseesForm.cleaned_data.get('advisees_list')
        for student in students:
            student.advisor = advisor
            student.save()
        messages.success(request, "Advisees sucessfully added")
        return redirect(advisorIndex)

def remove_advisee(request):
    student_pks = request.POST['student_pks'].split(',')
    for pk in student_pks:
        student = Student.objects.get(id = pk)
        student.advisor = None
        student.save()
    messages.success(request, "Advisees sucessfully removed")
    return redirect(advisorIndex)

def logout_view(request):
    logout(request)
    return redirect(index)

class SignupView(SignupView):
    template_name = 'accounts/signup.html'

#########################                     Search Functionality                     #########################

class ClassSearchView(generic.ListView):
    model = ClassSearch
    template_name = "schedule/student/class_search.html"
    # context_object_name = 'subject_list'
    # def get_queryset(self, **kwargs):
    #     return class_search_initializer
    
class DisplayClassesView(generic.ListView):
    model = ClassSearch
    template_name = "schedule/student/display_classes.html"
    context_object_name = 'classes'
    def get_queryset(self, **kwargs):
        cur_student = Student.objects.filter(student_account=self.request.user).first()
        return ClassSearch.objects.filter(student = cur_student).first().search_results.all()
    
    '''
    Title: Django include template tag include multiple context object
    Date: 3/19/2023
    Author: Ahtisham
    URL: https://stackoverflow.com/questions/70719673/django-include-template-tag-include-multiple-context-object
    '''
    def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      date = datetime.today()
      current_strm = "1" + str(date.year)[2:]
      if(date.month >= 7):
        current_strm += "8"
      context['current_strm'] = current_strm
      return context

# converts date from %m/%d/%Y to %Y-%m-%d
def convert_date(string_date):
    split_date = string_date.split("/")
    format_date = split_date[2] + "-" + split_date[0] + "-" + split_date[1]
    date = datetime.strptime(format_date, "%Y-%m-%d").date()
    return date

def do_search(request):
    # clear search associated with current student
    student = Student.objects.filter(student_account = request.user).first()
    class_search = ClassSearch.objects.filter(student = student).first()
    if(class_search is None):
        class_search = ClassSearch()
        class_search.student = student
        class_search.save()
    class_search.search_results.clear()

    # retrieve all values from POST request
    subject = request.POST['subject']
    catalog_num = request.POST['catalog_num']
    name = request.POST['name']
    term = request.POST['term']
    year = request.POST['year']

    errorMessage = ''

    # base URL
    class_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01&term=1"

    validInput = False
    # check which fields were filled out and add to URL as needed
    if(subject == "null" and not catalog_num and not name):
        errorMessage = "Please answer at least one of the class filters"
    elif (term == "null" or year == "null"):
        errorMessage = "Please answer both Year and Term"
    else:
        validInput = True
    if(year != "null"):
        class_url += str(year[2:])
    if(term != "null"):
        t = str(term)
        if(t == "fall"):
            class_url += "8"
        elif(t == "spring"):
            class_url += "2"
        else:
            class_url += '6'
    
    if(subject !="null"):    
        class_url += str("&subject=" + subject)
    if (catalog_num):
        class_url += str("&catalog_nbr=" + catalog_num)
    if (name):
        class_url += str("&keyword=" + name)

    if(validInput):
        # use API to get classes
        req = requests.get(class_url)

        # convert JSON to dictionary
        search_results = json.loads(json.dumps(req.json()))

        # add each class returned to the database
        if (len(search_results) != 0):
            for item in search_results:
                currentCourse = Course.objects.filter(class_nbr = item['class_nbr']).filter(strm = item['strm']).first()
                if(currentCourse is None):
                    currentCourse = Course()
                    currentCourse.subject = item['subject']
                    currentCourse.catalog_num = item['catalog_nbr']
                    currentCourse.title = item['descr']

                    profs = []
                    for prof in item['instructors']:
                        profs.append(prof['name'])
                    currentCourse.instructor = ', '.join(profs)

                    currentCourse.section = item['class_section']

                    if(item['meetings']):
                        if(item['meetings'][0]['start_time'] != ""):
                            time = datetime.strptime(item['meetings'][0]['start_time'][:5].replace('.', ':'), "%H:%M").time()
                            currentCourse.start_time = time.strftime("%I:%M %p")
                        else:
                            currentCourse.start_time = '0:00 AM'
                        
                        if(item['meetings'][0]['end_time'] != ""):
                            time = datetime.strptime(item['meetings'][0]['end_time'][:5].replace('.', ':'), "%H:%M").time()
                            currentCourse.end_time = time.strftime("%I:%M %p")
                        else:
                            currentCourse.end_time = '0:00 AM'

                        if(item['meetings'][0]['days'] == '-'):
                            currentCourse.meet_days = 'TBA'
                        else:
                            currentCourse.meet_days = item['meetings'][0]['days']
                    else:
                        currentCourse.start_time = '0:00 AM'
                        currentCourse.end_time = '0:00 AM'
                        currentCourse.meet_days = 'TBA'
                   
                    currentCourse.start_date = convert_date(item['start_dt'])
                    currentCourse.end_date = convert_date(item['end_dt'])
                    currentCourse.class_nbr = item['class_nbr']
                    currentCourse.component = item['component']
                    currentCourse.strm = item['strm']
                    currentCourse.units = item['units']
                    currentCourse.save()
                class_search.search_results.add(currentCourse)
                class_search.save()
            # redirect to display classes page on success
            return HttpResponseRedirect(reverse('display_classes'))
        else:
            messages.error(request, "No classes found. Please check your input and try again.")
            return redirect(reverse('class_search'))
    else:
        messages.error(request, errorMessage)
        return redirect(reverse('class_search'))

def update_subject_list(request):
    parsed = json.load(request)
    year = str(parsed['year'])
    term = str(parsed['term'])
    class_url = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1"
    class_url += year[2:]
    if(term == "fall"):
        class_url += "8"
    else:
        class_url += "2"
    
    req = requests.get(class_url)
    subject_json = json.loads(json.dumps(req.json()))
    subject_list = []
    for item in subject_json['subjects']:
        subject_list.append(item['subject'])
    return JsonResponse({'list' : subject_list})


#########################                     Shopping Cart Functionaltiy                     #########################

class ShoppingCartView(generic.ListView):
    model = Cart
    template_name = "schedule/student/shopping_cart.html"
    context_object_name = 'courses'
    def get(self, request):
        cur_student = Student.objects.filter(student_account=self.request.user).first()
        cart = Cart.objects.filter(student=cur_student).first()
        if(cart is not None):
            courseList = {}
            credits = {}

            if(len(cart.courses.all()) > 0):
                for course in cart.courses.all():
                    # print(course.strm)
                    if(course.strm in courseList):
                        courseList[course.strm].append(course)
                        if(len(course.units) > 1):
                            credits[course.strm] += int(course.units[0])
                        else:
                            credits[course.strm] += int(course.units)
                    else:
                        courseList[course.strm] = [course]
                        if(len(course.units) > 1):
                            credits[course.strm] = int(course.units[0])
                        else:
                            credits[course.strm] = int(course.units)
                courses = []
                for key in courseList.keys():
                    term = ""
                    if(int(key[3]) == 2):
                        term = "Spring 20" + str(key[1:3])
                    elif(int(key[3]) == 6):
                        term = "Summer 20" + str(key[1:3])
                    elif(int(key[3]) == 8):
                        term = "Fall 20" + str(key[1:3])
                    courses.append([term, courseList[key], credits[key]])

                return render(request, self.template_name, {'courses' : courses})
            else:
                return render(request, self.template_name)
        else:
            return render(request, self.template_name)
    
    def get_queryset(self):
        cur_student = Student.objects.filter(student_account=self.request.user).first()
        cart = Cart.objects.filter(student=cur_student).first()
        if(cart is None):
            return None
        else:  
            return Cart.objects.filter(student=cur_student).first().courses.all()

def add_class_to_cart(request):
    cur_student = Student.objects.filter(student_account = request.user).first()
    shopping_cart = Cart.objects.filter(student = cur_student).first()
    course_pk = request.POST["course_pk"]
    course = Course.objects.filter(id = course_pk).first()
    
    if(shopping_cart is None):
        shopping_cart = Cart(student = cur_student)
        shopping_cart.credits = 0
        shopping_cart.save()
    else:
        shopping_cart = Cart.objects.filter(student = cur_student).first()
    shopping_cart.courses.add(course)
    shopping_cart.credits += int(course.units[0:1])
    shopping_cart.save()

    return HttpResponseRedirect(reverse('display_classes'))

def delete_class_from_cart(request):
    course_pk = request.POST["course_pk"]
    cur_student = Student.objects.filter(student_account = request.user).first()
    shopping_cart = Cart.objects.filter(student = cur_student).first()
    course = Course.objects.filter(id = course_pk).first()
    shopping_cart.credits -= int(course.units)
    shopping_cart.save()
    
    shopping_cart.courses.remove(course)

    return HttpResponseRedirect(reverse("shopping_cart"))


#########################                     Build Schedule Functionality                     #########################
class BuildSchedule(generic.ListView):
    model = Schedule
    template_name = "schedule/student/build_schedule.html"
    context_object_name = 'schedules'
    def get_queryset(self):
        cur_student = Student.objects.filter(student_account=self.request.user).first()
        return Schedule.objects.filter(student = cur_student).all()
    def get(self, request, *args, **kwargs):
        cur_student = Student.objects.filter(student_account=self.request.user).first()
        student_schedules = Schedule.objects.filter(student = cur_student).all()
        disableFunctions = cur_student.advisor is None

        if(len(student_schedules) == 0):
            return render(request, self.template_name, {'disableFunctions': disableFunctions})
        elif( kwargs.get('schedule_id', -1 ) == -1):
            return HttpResponseRedirect(reverse("build_schedule", kwargs={'schedule_id': student_schedules[0].pk}))
        
        schedules_pk = []
        for schedule in student_schedules:
            schedules_pk.append(schedule.pk)
        
        cur_schedule = Schedule.objects.get(id = kwargs.get('schedule_id'))
        return render(request, self.template_name, {'schedule' : [cur_schedule, cur_schedule.get_schedule()], 'times' : range(7,24), 'disableFunctions': disableFunctions, 'schedules_pk' : schedules_pk})
        
'''
Title: Django removing object from ManyToMany relationship
Date: 3/27/2023
Author: DrTyrsa
URL: https://stackoverflow.com/questions/6333068/django-removing-object-from-manytomany-relationship
'''
def add_class_to_schedule(request):
    schedule_pk = request.POST["schedule_pk"]
    course_pk = request.POST["course_pk"]
    course = Course.objects.get(pk = course_pk)
    student = Student.objects.filter(student_account = request.user).first()
    schedule = Schedule()

    if(schedule_pk == "new"):
        schedule.student = student
        schedule.term = course.strm[1:]
        schedule.save()
        schedule_pk = schedule.pk
        schedule.courses.add(course)
    else:
        schedule = Schedule.objects.get(pk = schedule_pk)
        if(schedule.courses.all().filter(id = course_pk).first() is None):
            schedule.courses.add(course)
    if(conflict_exists(schedule)):
        messages.error(request, "Error: there is a time conflict")
        schedule.courses.remove(course)
    else:
        messages.success(request, "Added " + str(course.subject) + " " + str(course.catalog_num) + ": " + course.title + " to Schedule " + str(schedule.pk))
    
    referer = request.META.get("HTTP_REFERER")

    # return HttpResponseRedirect(reverse("build_schedule", kwargs={'schedule_id': schedule_pk}))

    return HttpResponseRedirect(referer)

def conflict_exists(schedule):
    scheduleList = schedule.get_schedule()
    for day in scheduleList:
        for i in range(0,len(day) - 1):
            for j in range(i+1,len(day)):
                course_one_start = float(day[i].start_time.split(' ')[0].replace(':', '.'))
                course_one_end = float(day[i].end_time.split(' ')[0].replace(':', '.'))
                course_two_start = float(day[j].start_time.split(' ')[0].replace(':', '.'))
                course_two_end = float(day[j].end_time.split(' ')[0].replace(':', '.'))

                if(course_one_start < course_two_start):
                    if(course_one_end > course_two_start or course_one_end > course_two_end):
                        return True
                else:
                    if(course_one_start < course_two_end or course_one_end < course_two_end):
                        return True
    return False

'''
Title: How to Return a JSON Response in Django
Author: Brian Oliver
Date: 3/14/23
URL: https://dev.to/brian101co/how-to-return-a-json-response-in-django-gen
'''
def get_schedules_for_student(request):
    student = Student.objects.filter(student_account = request.user).first()
    term = request.GET["term"]
    schedules = Schedule.objects.filter(student = student).filter(term = term).all()
    schedule_id_list = []
    for schedule in schedules:
        if(schedule.editable == True):
            schedule_id_list.append(schedule.pk)
    if(len(schedule_id_list) == 0):
        return JsonResponse({"schedules": "create_new"})
    return JsonResponse({"schedules": schedule_id_list})

def delete_schedule(request):
    schedule_pk = request.POST["schedule_pk"]
    curSchedule = Schedule.objects.get(pk = schedule_pk)
    otherSchedule = Schedule.objects.filter(student = curSchedule.student).exclude(pk = schedule_pk).first()
    curSchedule.delete()
    if(otherSchedule is not None):
        return HttpResponseRedirect(reverse("build_schedule", kwargs={'schedule_id': otherSchedule.pk}))
    else:
        return HttpResponseRedirect(reverse("build_schedule"))

def delete_class_from_schedule(request):
    schedule_pk = request.POST["schedule_pk"]
    course_pk = request.POST["course_pk"]
    schedule = Schedule.objects.get(pk = schedule_pk)
    course = Course.objects.get(pk = course_pk)
    schedule.courses.remove(course)

    return HttpResponseRedirect(reverse("build_schedule", kwargs={'schedule_id': schedule_pk}))

def get_status_for_schedule(request, schedule_pk):
    student = Student.objects.filter(student_account = request.user).first()
    schedule = Schedule.objects.get(pk = schedule_pk)
    advisor_request = AdvisorRequest.objects.filter(student = student).filter(schedule = schedule).first()
    message = ""
    status = 0
    if(advisor_request is None):
        status = -1
    elif(advisor_request.status == 0 or advisor_request.status == 1):
        message = "The current schedule has been submitted for review. If you would like to edit, please cancel the request."
        status = advisor_request.status
    elif(advisor_request.status == 2):
        message = "The current schedule has been approved. You cannot make any edits to this schedule."
        status = advisor_request.status
    else:
        message = "The current schedule has been rejected. Please review the comments and make changes to it."
        status = advisor_request.status

    return JsonResponse({"status": status, "status_message": message})

#########################                     Email Functionality                     #########################
    
from django.core.mail import send_mail

def send_email_to_student(studentEmail, status, schedNum, comment):
    subject = "Schedule "
    msg = 'Your request for Schedule {num} has been '.format(num=schedNum)
    if(status == 2):
        subject += "Approval"
        msg += "approved"
    else:
        subject += "Rejection"
        msg += "rejected"
    msg += ".\nHere are comments from your advisor: \n\n"
    msg += comment
    print("To: " + studentEmail + " | From: " + settings.EMAIL_HOST_USER + " | " +   subject + "  | " + msg)
    send_mail(subject=subject, message=msg, from_email=settings.EMAIL_HOST_USER, recipient_list=[studentEmail])


#########################                     Submit Schedule Functionality                     #########################

class AdvisorRequestsView(generic.ListView):
    model = AdvisorRequest
    template_name = "schedule/advisor/advisor_requests.html"
    context_object_name = "requests"
    def get(self, request):
        requests = self.get_queryset()
        pending = []
        completed = []
        for advisorRequest in requests:
            if(advisorRequest.status == 2 or advisorRequest.status == 3):
                completed.append(advisorRequest)
            else:
                pending.append(advisorRequest)
        context = {}
        if(len(pending) > 0):
            context['pending'] = pending
        if(len(completed) > 0):
            context['completed'] = completed
        
        return render(request, self.template_name, context)
    def get_queryset(self):
        cur_advisor = Advisor.objects.filter(advisor_account=self.request.user).first()
        return AdvisorRequest.objects.filter(advisor = cur_advisor).all()

def student_send_schedule(request):
    sched_num = request.POST["schedule_pk"]
    # print(sched_num)
    req = AdvisorRequest.objects.filter(schedule=sched_num).first()
    if(req is not None and (req.status == 0 or req.status == 1)):
        messages.error(request, 'Schedule has been sent already')
    elif(req is not None and (req.status == 2)):
        messages.error(request, 'Schedule has been approved already')
    else:
        if(req is None):
            req = AdvisorRequest()
            student = Student.objects.filter(student_account = request.user).first()
            req.student = student
            req.advisor = student.advisor
            req.schedule = Schedule.objects.get(pk=sched_num)
            req.status = 0
            req.seen = False
            req.comment = ""
            req.save()
        else:
            req.status = 0
            req.seen = False
            req.save()
        messages.success(request, 'Schedule Sent')
    return HttpResponseRedirect(reverse('build_schedule', kwargs={'schedule_id': sched_num}))
    
def update_request_status(request):
    request_pk = request.POST["request_pk"]
    status = int(request.POST["status"])

    req = AdvisorRequest.objects.get(id = request_pk)
    req.status = status
    req.seen = False
    if(status != 1):
        comment = request.POST["request_comment"]
        if(comment == ""):
            comment="none"
        req.comment = comment
        req.save()
        send_email_to_student(req.student.email, status, req.schedule.pk, comment)
    req.save()
    return HttpResponseRedirect(reverse('advisors_requests')) 

def cancel_req(request):
    request_pk = request.POST["request_pk"]
    adv_req = AdvisorRequest.objects.get(id = request_pk)
    adv_req.schedule.editable = True
    adv_req.schedule.save()
    adv_req.delete()

    return HttpResponseRedirect(reverse('student_home'))

def cancel_req_build_schedule(request):
    sched_num = request.POST["schedule_pk"]
    adv_req = AdvisorRequest.objects.filter(schedule=sched_num).first()
    adv_req.schedule.editable = True
    adv_req.schedule.save()
    adv_req.delete()

    return HttpResponseRedirect(reverse('build_schedule', kwargs={'schedule_id': sched_num}))

#Below are imports for downloading schedule as ics
from icalendar import Calendar, Event
from dateutil import rrule #For weekly recurring rules
from dateutil.rrule import WEEKLY, rrulestr 
from icalendar import vRecur
import pytz
'''
Title: Find the date for the first Monday after a given date
Author: user1034533, wjandrea
Date: 04/28/22
URL: https://stackoverflow.com/questions/6558535/find-the-date-for-the-first-monday-after-a-given-date
'''
def onDay(date, day):
    days = (day - date.weekday() + 7) % 7
    
    return date + dtime.timedelta(days=days)

'''
Title:How to convert AM/PM timestmap into 24hs format in Python?
Author: Vikas Periyadath
URL: https://stackoverflow.com/questions/19229190/how-to-convert-am-pm-timestmap-into-24hs-format-in-python
'''
def timeConversion(s):
   if(s[0] != '0'):
       s = '0' + s
   if s[-2:] == "AM" :
      if s[:2] == '12':
          a = str('00' + s[2:5])
      else:
          a = s[:-2]
   else:
      if s[:2] == '12':
          a = s[:-2]
      else:
          a = str(int(s[:2]) + 12) + s[2:5]
   return a


def download_ics(request): #take request containing student info

    cal = Calendar()
    cal.add('prodid',"-//cs3240-2023/schedule-advisor-ics/") #universally unique identifier
    cal.add("version","2.0") #version

    rule = 'RRULE:FREQ=WEEKLY'
    schedule_pk = request.POST["schedule_pk"]
    schedule = Schedule.objects.get(id=schedule_pk)
    schedule_list = schedule.get_schedule()

    tz = pytz.timezone('US/Eastern')
    for day in range(len(schedule_list)): #parse each day in the schedule_list obj
        
        # Get the date of the most recent occurrence of the day of the week
        for course in schedule_list[day]:
            year = "20" + course.strm[1:3]
            month = course.strm[3:]
 
            sem_start_day = 18 #if spring, set start date to 18
            if(int(month) >=8): #if fall, set start date to 23rd
                sem_start_day = 23
            #Summer courses
            elif(int(month) == 5):
                sem_start_day = 22
            elif(int(month) == 6):
                sem_start_day = 20
            elif(int(month) == 7):
                sem_start_day = 17

            d = dtime.datetime(int(year), int(month), sem_start_day, tzinfo=tz)

            most_recent_day = onDay(d, day) #Get start date of class
         
            #Check each course for the day and create event for each course
            ev = Event()
            start_time = datetime.strptime(course.start_time, '%H:%M %p').time()
            
            start_datetime = datetime.combine(most_recent_day, start_time)
            start_datetime = tz.localize(start_datetime)

            
            end_time = timeConversion(course.end_time)
            end_time = datetime.strptime(course.end_time, '%H:%M %p')
            end_time = datetime.strftime(end_time, "%H:%M")
            end_time = datetime.strptime(end_time, '%H:%M').time()

            end_datetime = datetime.combine(most_recent_day, end_time)
            end_datetime = tz.localize(end_datetime)
            ev.add('dtstart', start_datetime)
            ev.add('dtend', end_datetime)
            ev.add('name', course.title)
            summary_text = "Instructor: %s, Section: %s"%(course.instructor,course.section)
            ev.add('summary', summary_text)
            
            
            end_date = most_recent_day + dtime.timedelta(days=90)

            #Add recurring rules
            rule = vRecur(freq='WEEKLY', until=end_date)
            ev.add('rrule', rule)

            cal.add_component(ev) #Add to calendar

    #Format file and send file
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="schedule.ics"'

    return response

#########################                     Google Calendar Functionality                    #########################

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta

import os.path

# title: Google Calendar Python quickstart
# author: Google
# date: 04/10/2023
# URL: https://developers.google.com/calendar/api/quickstart/python

def get_google_calendars(request):
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    # else:
    #     try:
    #         credentials_json = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    #         creds = Credentials.from_json(credentials_json)
    #     except:
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'static/schedule/google-credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        page_token = None
        calendars = []
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendars.append({'title': calendar_list_entry['summary'], 'id': calendar_list_entry['id']})
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    except HttpError as error:
        print('An error occurred: %s' % error)

    return JsonResponse({'google_calendars' : calendars})

    
def add_to_google_calendar(request):
    CAL_ID = str(request.POST['google_calendar_id'])
    CAL_TITLE = request.POST['google_calendar_title']
    SCHEDULE_PK = request.POST['schedule_pk']
    format = '%Y-%m-%d %I:%M %p'

    creds = None
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # else:
    #     try:
    #         credentials_json = os.getenv['GOOGLE_APPLICATION_CREDENTIALS']
    #         creds = Credentials.from_json(credentials_json)
    #     except:
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'static/schedule/google-credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        schedule = Schedule.objects.get(pk=SCHEDULE_PK).get_schedule()
        index = 0
        # iterate through each weekday
        for day in schedule:
            # iterate through courses of each day
            for course in day:
                # difference between starting day and class days
                diff = index - course.start_date.weekday()
                
                summary = course.subject + " " + str(course.catalog_num)
                # first day of classes - starting time
                start_datetime = str(course.start_date) + " " + course.start_time
                # # first day of classes - ending time
                end_datetime = str(course.start_date) + " " + course.end_time
                
                # check if day of week is before the start day
                if(diff < 0):
                    # start recurring event the week after
                    start_datetime = dtime.datetime.strptime(start_datetime, format) + timedelta(days=7+diff)
                    end_datetime = dtime.datetime.strptime(end_datetime, format) + timedelta(days=7+diff)
                else:
                    start_datetime = dtime.datetime.strptime(start_datetime, format) + timedelta(days=diff)
                    end_datetime = dtime.datetime.strptime(end_datetime, format) + timedelta(days=diff)
                
                # formatting
                start_datetime = str(start_datetime.date()) + "T" + str(start_datetime.time()) + ".000"
                end_datetime = str(end_datetime.date()) + "T" + str(end_datetime.time()) + ".000"

                recur_end_time = str(course.end_date) + " " + course.end_time
                recur_end_time = dtime.datetime.strptime(recur_end_time, format)
                recur_end_time = str(recur_end_time.date()) + "T" + str(recur_end_time.time()) 
                recur_end_time = recur_end_time.replace("-","")
                recur_end_time = recur_end_time.replace(":","")
                recur_end_time = recur_end_time.replace(" ","")
                recur_end_time += "Z"

                # create event
                event = {
                    'summary': summary,
                    'start' : {
                        'dateTime' : start_datetime,
                        'timeZone' : 'America/New_York',
                    },
                    'end' : {
                        'dateTime' : end_datetime,
                        'timeZone' : 'America/New_York',
                    },
                      'recurrence': [
                        'RRULE:FREQ=WEEKLY;UNTIL=' + str(recur_end_time),
                    ],
                }

                # add event
                recurring_event = service.events().insert(calendarId=CAL_ID, body=event).execute()
                print(recurring_event['id'])
            # increment index for day of the week
            index+=1

        messages.success(request, 'Schedule ' + SCHEDULE_PK + ' has been added to "' + CAL_TITLE + '"')
    
    except HttpError as error:
        print('An error occurred: %s' % error)
        messages.error(request, 'Schedule ' + SCHEDULE_PK + ' failed to be added to "' + CAL_ID + '"')

    return HttpResponseRedirect(reverse('build_schedule', kwargs={'schedule_id': SCHEDULE_PK}))
