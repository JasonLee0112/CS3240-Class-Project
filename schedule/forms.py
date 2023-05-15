from django import forms
from schedule.models import Advisor, Student
from allauth.socialaccount.forms import SignupForm
from django.core.exceptions import ValidationError


'''
Title: Multiple user type sign up with django-allauth
Date: 2/23/2023
Author: mrnfrancesco
URL: https://stackoverflow.com/questions/44505242/multiple-user-type-sign-up-with-django-allauth
'''
class SignupForm(SignupForm):
    first_name = forms.CharField(max_length=50, required=True, strip=True)
    last_name = forms.CharField(max_length=50, required=True, strip=True)
    user_type= forms.CharField(label="I'm a ...", widget=forms.Select(choices=[('student', 'student'),['advisor','advisor']]))
    advisor_select = forms.ModelChoiceField(queryset=Advisor.objects, required=False, empty_label='Not Listed')

    '''
    Title: Form and field validation¶
    Date: 3/20/2023
    URL: https://docs.djangoproject.com/en/4.1/ref/forms/validation/#raising-validation-error
    '''
    def clean_advisor_select(self):
        advisor_select = self.cleaned_data.get('advisor_select')
        user_type = self.cleaned_data.get('user_type')
        if(user_type == "student" and not advisor_select):
            return None
        return advisor_select
        
    
    # Override the save method to save the extra fields
    # (otherwise the form will save the User instance only)
    def save(self, request):
        user = super(SignupForm, self).save(request)
        
        if(self.cleaned_data.get('user_type') == 'advisor'):
            advisor = Advisor(     
                advisor_account=user,
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                email=user.email
            )
            advisor.save()
        else:
            student = Student(     
            student_account=user,
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=user.email,
            advisor = self.cleaned_data.get('advisor_select')
        )
            student.save()

        return user
    
class SetAdvisorForm(forms.Form):
    advisor_select = forms.ModelChoiceField(queryset=Advisor.objects, required=True, empty_label='Select an Advisor')
    
    '''
    Title: How do I remove Label text in Django generated form?
    Date: 4/12/2023
    Author: John R Perry
    URL: https://stackoverflow.com/questions/25839043/how-do-i-remove-label-text-in-django-generated-form
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['advisor_select'].label = ''
        self.fields['advisor_select'].widget.attrs.update({
            'class': 'form-select'
        })

class AddAdviseesForm(forms.Form):
    advisees_list = forms.ModelMultipleChoiceField(queryset = Student.objects)
    
    '''
    Title: Django Forms: pass parameter to form
    Date: 4/12/2023
    Author: Sven M
    URL: https://stackoverflow.com/questions/14660037/django-forms-pass-parameter-to-form
    '''
    def __init__(self, advisor_id,*args,**kwargs):
          super().__init__(*args,**kwargs)
          advisor = Advisor.objects.get(id = advisor_id)
          self.fields['advisees_list'] = forms.ModelMultipleChoiceField(queryset=Student.objects.exclude(advisor = advisor), required=True)
          self.fields['advisees_list'].label = ''