from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.simple import direct_to_template
from django.conf.urls import patterns, include, url
from tastypie.api import Api
from autograde.api import *
from autograde.views import *
from autograde.models import *

from django.contrib.auth.decorators import login_required

api = Api(api_name='data')
api.register(ProjectResource())
api.register(TestCaseResource())
api.register(TestResultResource())
api.register(ProjectFileResource())
api.register(ProjectMetaResource())

urlpatterns = patterns('autograde.views',
    url(r'^api/', include(api.urls)),
    url(r'^api/key$',direct_to_template,{"template":"autograde/api_key.html"},name="api_key"),
    url(r'^$', login_required(ListView.as_view(model=Project,template_name="autograde/index.html")), name='autograde_home'),

    #project
    url(r'^project/(?P<pk>[\w\._-]+)$', DetailView.as_view(model=Project), name='project_detail'),
    url(r'^project/(?P<pk>[\w\._-]+)/addzip$', addzip, name='project_addzip'),
    url(r'^projectzip/(?P<pk>[\w\._-]+)$', get_project_zip, name='get_project_zip'),
    url(r'^create/project/$', "project_create", name='project_create'),

    #project meta
    url(r'^directory/(?P<pk>[\w\._-]+)$', DetailView.as_view(model=Directory), name='directory_detail'),
    url(r'^projectmeta/(?P<pk>[\w\._-]+)/edit$', projectmeta_edit, name='projectmeta_edit'),

    #testcase
    url(r'^testcase/(?P<pk>[\w\._-]+)$', DetailView.as_view(model=TestCase), name='testcase_detail'),
    url(r'^testcase/(?P<pk>[\w\._-]+)/edit$', testcase_edit, name='testcase_edit'),
    url(r'^testcase/(?P<pk>[\w\._-]+)/delete$', testcase_delete, name='testcase_delete'),
    url(r'^testcase/(?P<project_pk>[\w\._-]+)/create$', testcase_create, name='testcase_create'),
    url(r'^testcase/(?P<project_pk>[\w\._-]+)/(?P<directory_pk>[\w\._-]+)/create$', testcase_create, name='sub_testcase_create'),

    #directory
    url(r'^directory/(?P<project_pk>[\w\._-]+)/create$', directory_create, name='directory_create'),
    url(r'^directory/(?P<project_pk>[\w\._-]+)/(?P<directory_pk>[\w\._-]+)/create$', directory_create, name='sub_directory_create'),

    #project file
    url(r'^projectfile/(?P<pk>[\w\._-]+)$', DetailView.as_view(model=ProjectFile), name='projectfile_detail'),
    url(r'^projectfile/(?P<pk>[\w\._-]+)/edit$', projectfile_edit, name='projectfile_edit'),
    url(r'^projectfile/(?P<project_pk>[\w\._-]+)/create$', projectfile_create, name='projectfile_create'),
    url(r'^projectfile/(?P<project_pk>[\w\._-]+)/(?P<directory_pk>[\w\._-]+)/create$', projectfile_create, name='sub_projectfile_create'),
    url(r'^projectfile/(?P<pk>[\w\._-]+)/delete$', projectfile_delete, name='projectfile_delete'),

    #test results
    url(r'^testresult/(?P<pk>[\w\._-]+)$', DetailView.as_view(model=TestResult), name='testresult_detail'),
)
