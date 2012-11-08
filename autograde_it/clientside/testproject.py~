#!/usr/bin/python
from urllib import urlretrieve
from urllib2 import Request, build_opener, urlopen, HTTPError
from json import loads, dumps
from os import mkdir, rmdir, path
from os import kill, system
from subprocess import Popen, PIPE, STDOUT
from getpass import getpass
from shutil import rmtree
from uuid import uuid4
from time import time
from threading import Thread
from signal import SIGTERM

# Options and settings
debug = False
trimresults = True

class TestCase:
    """
    This class encapsulates a test case.
    """
    def __init__(self, case_name, case_id, test_dir, ext, user_uri='autograde/api/data/user/1', resource_uri='', timelimit=10.0, on_timeout_fail=True):
        self.case_name = case_name
        self.case_id = case_id
        self.test_dir = test_dir
        self.user_uri = user_uri
        self.resource_uri = resource_uri
        self.timelimit = timelimit
        self.on_timeout_fail = on_timeout_fail
       
        # For use by the runTests function
        self.error = False 

        self.elapsed_time = 0.0
        self.ext = ext
        self.exec_types = {'py': 'python', 'sh': 'sh'}

    class Cmd(Thread):
        """
        Incorporates necessary methods for executing a command on the host system, including proper
        handling of runaway processes that must be killed.
        """
        def __init__(self, cmd, timeout=5.0):
            Thread.__init__(self)
            self.cmd = cmd
            self.timeout = timeout
            self.elapsed_time = 0.0
            self.timed_out = False

        def run(self):
            #self.proc = Popen(self.cmd, shell=True, stdout=PIPE, stderr=STDOUT, preexec_fn=setsid)
            self.proc = Popen(self.cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            self.proc.wait()

        def Run(self):
            start_time = time()
            self.start()
            self.join(self.timeout)

            if self.is_alive():
                self.timed_out = True
                self.proc.terminate()
                #killpg(self.proc.pid, SIGTERM)
                kill(self.proc.pid, SIGTERM)
                self.join()
            self.elapsed_time = time() - start_time

        def result(self):
            if self.timed_out:
                return  'ERROR: the test timed out' 
            return self.proc.stdout.read()

    def runTest(self):
        print "Running test " + str(self.case_id) 
        filename = self.test_dir+'/'+self.case_name
        arg = self.exec_types[self.ext] + ' ' + filename
        cmd = self.Cmd(arg)
        cmd.Run()
        self.result = cmd.result()
        if trimresults:
            self.result = self.result.strip()
        self.elapsed_time = cmd.elapsed_time

    # Generate a test report in the format expected by the server
    # Meant to be used in Tester.putResults
    def asDict(self):
        if self.error: 
            result_string = 'Test threw an exception.' 
        else: 
            result_string = self.result
        return {'results':result_string, 'user':self.user_uri, 'test_case':self.resource_uri, 'time': self.elapsed_time}

class Tester:
    '''
    Framework for testing a particular project, for a particular user.
    '''
    def __init__(self, uname='will', api_key='8a3cc5b747e93699f33beb4e250e3e47c4f8df05', server_url='http://autograde.herokuapp.com/', proj=None):
        self.key = api_key
        self.uname = uname
        self.url = server_url
        self.proj = proj

        self.cases = []
        self.results = []

        self.test_dir = ''
        self.user_uri = ''
        
        self.api_url = ''
        self.response_url = self.url + 'autograde/api/data/test_result/'
        self.api_url = self.url + 'autograde/api/data/project/?format=json'
        self.user_uri_url = ''

    def start(self):
        print "Ready to begin testing. Please enter your credentials."
        uname = raw_input('Username: ')
        if uname is not '':
            self.uname = uname
        key = raw_input('API Key: ')
        if key is not '':
            self.key = key
        proj = raw_input('Project Number: ')
        if proj is not '':
            self.proj = int(proj)
        print "Please press enter when you are ready to start the test."
        u_input = raw_input('=>')

        self.response_url += '?username=%s&api_key=%s' % (self.uname, self.key)
        self.project_url = '/autograde/api/data/project/%d/' % self.proj
        self.test_dir = '.%stest' % self.uname
        self.user_uri_url = 'autograde/api/data/user/?format=json&username=%s' % self.uname
        
        self.setup()
        self.getCases()

    def setup(self):
        try:
            rmtree(self.test_dir)
        except:
            pass
        mkdir(self.test_dir)
        system('cp -r project_files/* %s' % self.test_dir)

    def getCases(self):
        print "Downloading test cases..."
        tests = self.getTests()
        if debug: print tests
        for case in tests:
            case_id  = case['id']
            media_url = case['file']
            resource_uri = case['resource_uri']
            if debug: print media_url
            case_name = str(uuid4())
            name, obj = urlretrieve(media_url, path.join(self.test_dir, case_name))
            ext = media_url.split('?')[0].split('.')[-1]
            self.cases.append(TestCase(case_name, case_id, self.test_dir, ext, self.getUserUri(), resource_uri))
            print "Got test %s" % case_id
        print "Done downloading tests\n"

    def getTests(self):
        req = Request(self.api_url)
        opener = build_opener()
        response = opener.open(req).read()
        response_json = loads(response)
        objects = response_json['objects']
        for project in objects:
            if debug: print project
            if project['id'] == str(self.proj):
                return project['tests']
        return None


    def getUserUri(self):
        request = Request(self.url+self.user_uri_url)
        opener = build_opener()
        response = loads(opener.open(request).read())
        return response['objects'][0]['resource_uri']


    def runTests(self):
        if debug: print "Running the test cases..."
        for test in self.cases:
            try: 
                test.runTest()
            except Exception, e:
                if debug: print 'Test threw an exception'
                test.error = True


    def putResults(self, key):
        for test in self.cases:
            payload = dumps(test.asDict())
            if debug: print payload, self.response_url
            request = Request(self.response_url, payload, {'Content-Type': 'application/json'})
            try: 
                response = urlopen(request)
                if debug: print response.read()
                print 'Successfully sent case %s' % test.case_id
                response.close()
            except HTTPError, e:
                if debug: print 'The submission for test %s failed' % test.case_id
                if debug: print e
                if debug: print e.read()

    def cleanup(self):
        rmtree(self.test_dir)
        

if __name__ == '__main__':
    t = Tester()
    from sys import argv
    if len(argv) > 1:
        self.key = argv[1]
    t.start()
    t.runTests()
    t.putResults(t.key)
    t.cleanup()
    
