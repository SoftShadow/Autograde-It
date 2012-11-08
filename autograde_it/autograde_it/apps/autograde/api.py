# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication,ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie import fields
from autograde.models import *
from django.contrib.auth.models import User

class TestResultResource(ModelResource):
    test_case = fields.ForeignKey("autograde.api.TestCaseResource","test_case")
    class Meta:
        queryset = TestResult.objects.all()
        resource_name = 'test_result'
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        list_allowed_methods = ['post']
        detail_allowed_methods = ['post']
    def obj_create(self, bundle, request=None, **kwargs):
        return super(TestResultResource,self).obj_create(bundle,request,user=request.user)

class ProjectFileResource(ModelResource):
    project = fields.ForeignKey("autograde.api.ProjectResource","project")
    class Meta:
        queryset = ProjectFile.objects.all()
        resource_name = 'project_file'

class TestCaseResource(ModelResource):
    project = fields.ForeignKey("autograde.api.ProjectResource","project")
    class Meta:
        queryset = TestCase.objects.all()
        resource_name = 'test_case'

class ProjectMetaResource(ModelResource):
    project = fields.ForeignKey("autograde.api.ProjectResource","project")
    class Meta:
        queryset = ProjectMeta.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        list_allowed_methods = ['get','post']
        resource_name = 'project_meta'

class ProjectResource(ModelResource):
    tests = fields.ToManyField("autograde.api.TestCaseResource","testcase_set",full=True)
    project_files = fields.ToManyField("autograde.api.ProjectFileResource","projectfile_set",full=True)
    project_meta = fields.ForeignKey("autograde.api.ProjectMetaResource","get_meta",full=True)
    class Meta:
        queryset = Project.objects.all()
        resource_name = 'project'
