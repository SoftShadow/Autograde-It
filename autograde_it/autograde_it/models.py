from django.db import models

from tastypie.models import create_api_key
models.signals.post_save.connect(create_api_key, sender=User)

class UserFeedback(models.Model):
    make_project = models.TextField(name="Please first create a project using the 'Create Project' button on the homepage. If this process is confusing, or could otherwise be improved, please let us know:")
    upload_files = models.TextField(name="After creating the project, please upload a few project files and test files for the project. The project files will be included in the zip file that the students download, and the test files will be used to test the project. Each test file should have some expected results that indicate what the response of the output of the test case should be for a successful test. If this process is confusing, or could otherwise be improved, please let us know:")
    download_zip = models.TextField(name="After the project has been created, click 'Get Zipped Files' on the project detail page to download the code. If this process is confusing, or could otherwise be improved, please let us know:")
    run_tests = models.TextField(name="Please unzip the archive and run the python file in the base directory. It will ask you for your username and api_key in order to comunicate with the server. After running the test, you can check back to the project detail page to see the results of each of the test cases. If this process is confusing, or could otherwise be improved, please let us know:")
