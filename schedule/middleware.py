from schedule.models import Advisor, Student
from django.contrib import messages
from django.shortcuts import redirect
from schedule import views
'''
Title: Django Middleware: Types, Examples, And Custom Middleware
Author: Nitin Raturi
Date: 4/18/2023
URL: https://raturi.in/blog/understand-and-create-custom-django-middleware/#types-of-middleware-in-django
'''
class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        url = request.path.split('/')[1]
        if(check_user(request, url) is not None):
            return check_user(request, url)

        response = self.get_response(request)
        
        return response

def check_user(request, url):
    if("student" in url or "advisor" in url):
        current_user = request.user
        if(not current_user.is_authenticated):
            messages.error(request, "Sorry, please log in to access other features")
            return redirect(views.index)
        
        student = Student.objects.filter(student_account=current_user).first()
        advisor = Advisor.objects.filter(advisor_account=current_user).first()
        if(student is None and "student" in url):
            message_added = False
            for m in messages.get_messages(request):
                if(m.message == "Sorry, you do not have access to this functionality"):
                    message_added = True
            if(not message_added):
                messages.error(request, "Sorry, you do not have access to this functionality")
            return redirect(views.advisorIndex)
        elif(advisor is None and "advisor" in url):
            message_added = False
            for m in messages.get_messages(request):
                if(m == "Sorry, you do not have access to this functionality"):
                    message_added = True
            if(not message_added):
                messages.error(request, "Sorry, you do not have access to this functionality")
            return redirect(views.studentIndex)
    
    return None