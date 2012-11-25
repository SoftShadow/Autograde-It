from django.db import models
from django.db.models import permalink
from zipfile import ZipFile

from django.contrib.auth.models import User
from django_extensions.db.fields import *

import os

class Project(models.Model):
    """
        The base model representing a single assignment or project.
    """
    instructors = models.ManyToManyField(User)
    title = models.CharField(max_length=100)
    created = CreationDateTimeField()

    def base_directories(self):
        return self.directory_set.filter(directory=None)

    def modified(self):
        """
            Returns a datetime of the last time this project's meta data was modified.
        """
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

    def zipfile(self):
        """
            Return the path to a zipfile for this project.
            Contains all of the student_viewable project files and the testing framework file.
        """
        import uuid
        from django.conf import settings
        #create a zip file in the AUTOGRADE_ZIP_TMP folder
        zipfile_name = os.path.join(settings.AUTOGRADE_ZIP_TMP,str(uuid.uuid4()))
        z = ZipFile(zipfile_name,"w")
        def add_project_file(pf,dir_path=""):
            file_name = os.path.join(settings.AUTOGRADE_ZIP_TMP,str(uuid.uuid4()))
            f = open(file_name,"w")
            f.write(pf.file.read())
            f.close()
            z.write(file_name,os.path.join(dir_path,os.path.basename(pf.file.name)))
            os.remove(file_name)
        def add_directory(directory):
            for pf in directory.projectfile_set.all():
                add_project_file(pf,directory.path())
            for sub_dir in directory.directory_set.all():
                add_directory(sub_dir)

        for pf in self.projectfile_set.filter(is_student_viewable=True).filter(directory=None):
            add_project_file(pf)
        for directory in self.base_directories():
            add_directory(directory)

        z.write("autograde_it/clientside/testproject.py","testproject.py")
        z.close()
        #store the data from the zipfile into memory and then delete the file from disk
        data = open(zipfile_name,"rb").read()
        os.remove(zipfile_name)
        return data # return the data stored in memory

    @permalink
    def get_absolute_url(self):
        return ("project_detail",[self.pk])
    def __unicode__(self):
        return self.title

class ProjectMeta(models.Model):
    """
        Meta data for a project object. This is supose to be configurable so users of this app can change how this data is used.
        To use a different model for the meta data, set the AUTOGRADE_PROJECT_META_MODEL value in the settings file.

        For example:
            One might want to have a pdf instead of just text for the description.
            Or one might want to include grading options here.

        _This is intended to simply be an example._
    """
    project = models.OneToOneField(Project)
    due_date = models.DateTimeField(null=True,help_text="Time in 24 hour format")
    release_date = models.DateTimeField(null=True,help_text="Time in 24 hour format")
    description = models.TextField(null=True)
    modified = ModificationDateTimeField()

class Directory(models.Model):
    """
        A model that represents a directory in the filesystem.
    """
    project = models.ForeignKey(Project)
    directory = models.ForeignKey("self",null=True,blank=True,related_name="directory_set")
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
    @permalink
    def get_absolute_url(self):
        return ("directory_detail",[self.pk])
    def path(self):
        if self.directory:
            return os.path.join(self.directory.path(),self.name)
        else:
            return self.name

class ProjectFile(models.Model):
    """
        Part of the framework/skeleton code that is provided to the students.

        project - link back to the project that this test is part of.
        file -  any type of file that the instructor may wish to give the students.
        is_student_viewable - indicates if the students should have access to this file.
    """
    directory = models.ForeignKey(Directory,null=True,blank=True)
    project = models.ForeignKey(Project)
    file = models.FileField(upload_to="project_files")
    is_student_viewable = models.BooleanField(default=True)
    created = CreationDateTimeField()
    def __unicode__(self):
        return str(self.file)
    @permalink
    def get_absolute_url(self):
        return ("projectfile_detail",[self.pk])

class TestCase(models.Model):
    """
        Stores the information about a single test case.

        project - link back to the project that this test is part of.
        file - an executable file that runs student code and outputs results.
        expected_results - the output of "file" in the case of a successful test.
    """
    directory = models.ForeignKey(Directory,null=True,blank=True)
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
    """
        The result of a test. 
        
        The testing framework will create this model via a post request.

        test_case - the test case that was run.
        results - the output of the test case.
        user - the user that submitted.

        passed - True if results == test_case.expected_results.
        was_checked - True if the correctness of "results" has been checked.
    """
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
    """
        When a TestResult is created, check the results and mark it as passed/failed.
    """
    if created:
        instance.check()
models.signals.post_save.connect(check_testresult, sender=TestResult)
