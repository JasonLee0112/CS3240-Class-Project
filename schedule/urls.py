from django.urls import path, include
from django.urls import include, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    re_path(r'accounts/social/signup', views.SignupView.as_view(), name='account_signup'),
    path('accounts/', include('allauth.urls')),

    path('student/', views.studentIndex, name="student_home"),
    path('student/select_advisor/', views.set_advisor, name = 'select_advisor'),

    path('student/cart/', views.ShoppingCartView.as_view(), name="shopping_cart"),
    path('student/cart/add_class_to_cart/', views.add_class_to_cart, name="add_to_cart"),
    path('student/cart/delete_class_from_cart/', views.delete_class_from_cart, name="delete_class_from_cart"),

    path('student/class_search/', views.ClassSearchView.as_view(), name="class_search"),
    path('student/do_search/', views.do_search, name="do_search"),
    path('student/display_classes/', views.DisplayClassesView.as_view(), name="display_classes"),
    path('student/update_subject_list/', views.update_subject_list, name="update_subject_list"),

    path('student/build_schedule/', views.BuildSchedule.as_view(), name="build_schedule"),
    path('student/build_schedule/<int:schedule_id>', views.BuildSchedule.as_view(), name="build_schedule"),
    path('student/add_class_to_schedule/', views.add_class_to_schedule, name="add_class_to_schedule"),
    path('student/get_schedules/', views.get_schedules_for_student, name="get_schedules"),
    path('student/delete_schedule/', views.delete_schedule, name="delete_schedule"),
    path('student/delete_class_from_schedule/', views.delete_class_from_schedule, name="delete_class_from_schedule"),
    path('student/student_send_schedule/', views.student_send_schedule, name="student_send_schedule"),
    path('student/student_cancel_request/', views.cancel_req, name="student_cancel_request"),
    path('student/student_cancel_req_build_schedule/', views.cancel_req_build_schedule, name="student_cancel_req_build_schedule"),
    path('student/get_schedule_status/<int:schedule_pk>/', views.get_status_for_schedule, name="get_schedule_status"),
    path('student/add_to_google_calendar/', views.add_to_google_calendar, name="add_to_google_calendar"),
    path('student/get_google_calendars', views.get_google_calendars, name="get_google_calendars"),


    path('student/ics/', views.download_ics, name="download_ics"),

    path('advisor/', views.advisorIndex, name="advisor_home"),
    path('advisor/add_advisee/', views.add_advisee, name = 'add_advisee'),
    path('advisor/remove_advisee/', views.remove_advisee, name = 'remove_advisee'),

    path('advisor/advisors_requests/', views.AdvisorRequestsView.as_view(), name="advisors_requests"),
    path('advisor/update_request_status/', views.update_request_status, name="update_request_status"),
]