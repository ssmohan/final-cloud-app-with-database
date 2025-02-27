from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission, Lesson
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))



def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enroll = Enrollment.objects.filter(user=user, course=course).get()
    choices = extract_answers(request)
    submission = Submission.objects.create(enrollment_id = enroll.id )
    for choice in choices:
        c = Choice.objects.filter(id = int(choice)).get()
        submission.choices.add(c)
    submission.save()         
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id,submission.id )))
    


# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers



def show_exam_result(request, course_id, submission_id):
    context = {}
    user = request.user
    course = Course.objects.get(id = course_id)
    submit = Submission.objects.get(id = submission_id)
    selected = Submission.objects.filter(id = submission_id).values_list('choices',flat = True)
    score = 0
    correct = [0,0] * 10

    questions = Question.objects.values_list('question_text')
        
    question_count=Question.objects.filter(course=course).count()
    for q in range(question_count+1):
        r = q+1
        all_q = submit.choices.all().filter(question = q)
        for a in all_q:
            if a in submit.choices.all().filter(is_correct=True):
                if correct[q] == 1:
                    correct[q] = 1
                else:
                    correct[q] = correct[q] + 1
            else:
                correct[q] = 0
        score = score + correct[q]

    context['user'] = user
    context['selected'] = selected
    context['grade'] = int((score/question_count) * 100)
    context['course'] = course
    context['question_text'] = questions
    return  render(request, 'onlinecourse/exam_result_bootstrap.html', context)
