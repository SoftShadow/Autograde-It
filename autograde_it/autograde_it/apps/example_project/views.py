from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.shortcuts import *
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from autograde.models import *
from autograde.forms import *

from example_project.forms import UserFeedbackForm

def user_feedback(request):
    form = UserFeedbackForm()
    return render_to_response("user_feedback.html",{"form":form},context_instance=RequestContext(request))

@login_required
def api_key(request):
    print request.user
    api_key = request.user.api_key
    return render_to_response("api_key.html",{"api_key":api_key},context_instance=RequestContext(request))
