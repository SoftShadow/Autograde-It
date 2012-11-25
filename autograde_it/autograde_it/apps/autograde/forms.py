from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.widgets import SplitDateTimeWidget,DateTimeInput

from autograde.models import *
from autograde.utils import *

class ProjectMetaForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super(ProjectMetaForm,self).__init__(*args,**kwargs)
        self.fields['due_date'].widget = SplitDateTimeWidget()
        self.fields['release_date'].widget = SplitDateTimeWidget()
    class Meta:
        model = ProjectMeta
        exclude = ("project",)
class ProjectCreateForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        if len(args)>=2:
            self.project_files = args[1].getlist("project_files",[])
        super(ProjectCreateForm,self).__init__(*args,**kwargs)
    def save(self,*args,**kwargs):
        super(ProjectCreateForm,self).save(*args,**kwargs)
        ProjectMeta.objects.create(project=self.instance)

        #save the files
        p = self.instance
        for file in self.project_files:
            ProjectFile.objects.create(project=p, file=file)
    class Meta:
        model = Project
        exclude = ("instructors",)

class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ("file","expected_results",)
class ProjectFileForm(forms.ModelForm):
    class Meta:
        model = ProjectFile
        fields = ("file","is_student_viewable")
class DirectoryForm(forms.ModelForm):
    class Meta:
        model = Directory
        fields = ("name",)
