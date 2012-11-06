from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.conf.urls import patterns, include, url

urlpatterns = patterns('example_project.views',
    url(r'^feedback/',"user_feedback",name="feedback"),
    url(r'^api_key/',"api_key",name="api_key"),
)
