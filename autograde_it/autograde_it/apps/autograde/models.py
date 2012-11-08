from django.db import models
from django.db.models import permalink
from zipfile import ZipFile

from django.contrib.auth.models import User
from django_extensions.db.fields import *

from tastypie.models import create_api_key
models.signals.post_save.connect(create_api_key, sender=User)

class Project(models.Model):
    instructors = models.ManyToManyField(User)
    title = models.CharField(max_length=100)
    created = CreationDateTimeField()

    def modified(self):
        return self.get_meta().modified
    @property
    def get_meta(self):
        """
            Get the meta data for this project.

            This is stored in a model determined by AUTOGRADE_PROJECT_META_MODEL setting.
        """
        from django.conf import settings
        app_label, model_name = getattr(settings,"AUTOGRADE_PROJECT_META_MODEL","autograde.ProjectMeta").split(".")
        model = models.get_model(app_label, model_name)
        if model is None:
            raise ValueError("AUTOGRADE_PROJECT_META_MODEL invalid")
        return model.objects.get(project=self)

    def __unicode__(self):
        return self.title

    def zipfile(self):
        """
            Return the path to a zipfile for this project.
            Contains all of the student_viewable project files and the testing framework file.
        """
        import os
        import uuid
        from django.conf import settings
        zipfile_name = os.path.join(settings.AUTOGRADE_ZIP_TMP,str(uuid.uuid4()))
        z = ZipFile(zipfile_name,"w")
        for pf in self.projectfile_set.filter(is_student_viewable=True):
            file_name = os.path.join(settings.AUTOGRADE_ZIP_TMP,str(uuid.uuid4()))
            f = open(file_name,"w")
            f.write(pf.file.read())
            f.close()
            z.write(file_name,pf.file.name)
            os.remove(file_name)
        z.write("autograde_it/clientside/testproject.py","testproject.py")
        z.close()

        data = open(zipfile_name,"rb").read()
        os.remove(zipfile_name)
        return data

    @permalink
    def get_absolute_url(self):
        return ("project_detail",[self.pk])

class ProjectMeta(models.Model):
    """
        Meta data for a project object. This is supose to be configurable so users of this app can change how this data is used.
        To use a different model for the meta data, set the AUTOGRADE_PROJECT_META_MODEL value in the settings file.

        For example:
            One might want to have a pdf instead of just text for the description.
            Or one might want to include grading options here.

        This is intended to simply be an example.
    """
    project = models.OneToOneField(Project)
    due_date = models.DateTimeField(null=True,help_text="Time in 24 hour format")
    release_date = models.DateTimeField(null=True,help_text="Time in 24 hour format")
    description = models.TextField(null=True)
    modified = ModificationDateTimeField()

class ProjectFile(models.Model):
    project = models.ForeignKey(Project)
    file = models.FileField(upload_to="project_files")
    is_student_viewable = models.BooleanField(default=False)
    created = CreationDateTimeField()
    def __unicode__(self):
        return str(self.file)
    @permalink
    def get_absolute_url(self):
        return ("projectfile_detail",[self.pk])

class TestCase(models.Model):
    project = models.ForeignKey(Project)
    file = models.FileField(upload_to="tests")
    expected_results = models.TextField(null=True)
    created = CreationDateTimeField()
    def __unicode__(self):
        return str(self.file)
    @permalink
    def get_absolute_url(self):
        return ("testcase_detail",[self.pk])

class TestResult(models.Model):
    test_case = models.ForeignKey(TestCase)
    results = models.TextField()
    user = models.ForeignKey(User)

    passed = models.BooleanField(default=False)
    was_checked = models.BooleanField(default=False)
    created = CreationDateTimeField()
    
    def check(self):
        """
            Check this test result against its test case.
        """
        if self.results == self.test_case.expected_results:
            self.passed = True
        else:
            self.passed = False
        self.was_checked = True
        self.save()

    def __unicode__(self):
        return str(self.user) + ": " + str(self.passed)
    @permalink
    def get_absolute_url(self):
        return ("testresult_detail",[self.pk])

def check_testresult(sender, instance, created, **kwargs):
    if created:
        instance.check()
models.signals.post_save.connect(check_testresult, sender=TestResult)
