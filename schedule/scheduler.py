from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from schedule.models import Advisor, AdvisorRequest

scheduler = BackgroundScheduler()

target = Advisor.objects.all()

def get_request_count(target):
    scheduleRequests = AdvisorRequest.objects.filter(advisor=target)
    scheduleListCount = scheduleRequests.count()
    return scheduleListCount

def get_email_schedule_summary(target):
    subject_line = "Schedule Requests:"
    message_line = "You have {} requests pending".format(get_request_count(target))
    return [subject_line,
        message_line,
        "noreply@automatedmessage.com",
        [target.email]]

def send_reminder_email(target):
    data = get_email_schedule_summary(target)
    send_mail(data[0], data[1], data[2], data[3])
    # print(data[0], data[1], data[2], data[3])
    # print(type(data[3]), data[3])

def job(advisor):
    for each in advisor:
        request_count = get_request_count(each)
        if request_count > 0:
            print(send_reminder_email(each))

scheduler.add_job(job, 'cron', day_of_week = 'mon, wed, fri', hour = 9, kwargs={'advisor' : target})

scheduler.start()
    