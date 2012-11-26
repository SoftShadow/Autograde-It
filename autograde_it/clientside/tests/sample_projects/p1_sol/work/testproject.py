#!/usr/bin/python
from urllib import urlretrieve
from urllib2 import Request, build_opener, urlopen, HTTPError
from json import loads, dumps, load, dump
from os import mkdir, rmdir, path, system
from subprocess import Popen, PIPE, STDOUT
from getpass import getpass
from shutil import rmtree
from uuid import uuid4
from time import time
from threading import Thread
from signal import SIGTERM
from sys import platform

if platform == 'win32' or platform == 'win64':
    from os import kill
else:
    from os import killpg, setsid

# Options and settings
debug = True
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
        self.exec_types = {'py': 'python', 'sh': 'sh', 'rb': 'ruby'}

        filename = path.join(self.test_dir, self.case_name)
        self.command_str = self.exec_types[ext] + ' ' + filename + ' -'
        self.json_data = {'case_name': case_name, 'case_id': case_id, 
                'test_dir': test_dir, 'ext': ext, 'user_uri': user_uri, 
                'resource_uri': resource_uri, 'timelimit': timelimit,
                'on_timeout_fail': True}

    def __getitem__(self, k):
        return self.json_data[k]

    class Cmd(Thread):
        """
        Incorporates necessary methods for executing a command on the host system, including proper
        handling of runaway processes that must be killed.
        """
        def __init__(self, cmd, timeout=10.0):
            Thread.__init__(self)
            self.cmd = cmd
            self.timeout = timeout
            self.elapsed_time = 0.0
            self.timed_out = False

        def run(self):
            if debug: print 'Made a new Cmd object'
            if platform == 'win32' or platform == 'win64':
                self.proc = Popen(self.cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            else:
                self.proc = Popen(self.cmd, shell=True, stdout=PIPE, stderr=STDOUT, preexec_fn=setsid)
            self.proc.wait()

        def Run(self):
            start_time = time()
            self.start()
            self.join(self.timeout)

            if self.is_alive():
                self.timed_out = True
                self.proc.terminate()
                if platform == 'win32' or platform == 'win64':
                    kill(self.proc.pid, SIGTERM)
                else:
                    killpg(self.proc.pid, SIGTERM)
                self.join()
            self.elapsed_time = time() - start_time

        def result(self):
            if self.timed_out:
                return  'ERROR: the test timed out' 
            return self.proc.stdout.read()

    def runTest(self):
        print "Running test " + str(self.case_id) 
        cmd = self.Cmd(self.command_str)
        cmd.Run()
        self.result = cmd.result()
        if trimresults:
            self.result = self.result.strip()
        self.elapsed_time = cmd.elapsed_time

    def getResults(self):
        """
            Try to parse the output of the test into a JSON
            object (which should contain fields like 'meta'
            and 'solution'. If this fails, make a new json object 
            with empty 'meta' and 'solution' fields.
        """
        if self.error:
            return 'Test threw an exception'
        else:
            json_result = {'meta': [], 'solution': {}, 'raw': self.result}
            for line in self.result.split('\n'):
                if debug: print line
                try:
                    solution = loads(line.strip())
                    json_result['solution'] = solution
                except BaseException as e:
                    if debug: print e
                    json_result['meta'].append(line)
            with open('result.json', 'w') as f:
                f.write(dumps(json_result))
            return json_result

    def asDict(self):
        """
            Generate a test report in the format expected by the server.
            Meant to be used in Tester.putResults.
        """
        return {'results': self.getResults(), 'user': self.user_uri, 'test_case': self.resource_uri, 'time': self.elapsed_time}

class Tester:
    '''
    Framework for testing a particular project, for a particular user.
    '''
    def __init__(self, uname='will', api_key='8a3cc5b747e93699f33beb4e250e3e47c4f8df05', server_url='http://autograde.herokuapp.com/', proj=None):
        self.key = api_key
        self.uname = uname
        self.url = server_url
        self.proj = proj

        self.results = []

        self.test_dir = ''
        self.user_uri = ''
        
        self.api_url = ''
        self.response_url = self.url + 'autograde/api/data/test_result/'
        self.api_url = self.url + 'autograde/api/data/project/?format=json'
        self.user_uri_url = ''

    def getUserInfo(self):
        """
        Either get the user's personal info and project number
        through the prompt, or retrieve it from the settings.json
        if it exists.
        """
        try:
            self.loadSettings()
        except:        
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
            self.settings = {'uname': self.uname,
                        'key': self.key,
                        'proj': self.proj,
                        'cases': {},
                        'case_names': [],
                        'case_ids': [],
                        'case_dir': '.' + str(uuid4())}
            mkdir(self.settings['case_dir'])

    def loadSettings(self):
        self.settings = load(open('.settings.json', 'r'))
        self.uname = self.settings['uname']
        self.key = self.settings['key']
        self.proj = self.settings['proj']
        cases = {}
        for id,case in self.settings['cases'].items():
            cases[id] = TestCase(case['case_name'], case['case_id'], case['test_dir'],
                            case['ext'], case['user_uri'], case['resource_uri'])
        self.settings['cases'] = cases
        self.case_ids = self.settings['case_ids']
        self.case_names = self.settings['case_names']

    def dumpSettings(self, current_settings=None):
        """
            Write the data in self.settings to the .settings.json file
        """
        if not current_settings:
            current_settings = self.settings

        with open('.settings.json', 'w') as settings:
            cases = {}
            for id,case in current_settings['cases'].items():
                cases[id] = case.json_data 
            current_settings['cases'] = cases
            settings.write(dumps(current_settings))

    def start(self):
        self.getUserInfo()
        print "Please press enter when you are ready to start the test."
        u_input = raw_input('=>')

        self.response_url += '?username=%s&api_key=%s' % (self.uname, self.key)
        self.project_url = '/autograde/api/data/project/%d/' % self.proj
        self.test_dir = '.%stest' % self.uname
        self.user_uri_url = 'autograde/api/data/user/?format=json&username=%s' % self.uname
        
        self.setup()
        self.getCases()
        self.populateTestDir()

    def setup(self):
        """
            Clean up the test directory and make a new one
        """
        try:
            rmtree(self.test_dir)
            rmtree('.cases')
        except:
            pass
        mkdir(self.test_dir)

    def populateTestDir(self):
        """
            Fill the test directory with the project files
        """
        if debug: print 'Populating the test directory', self.test_dir
        if platform == 'win32' or platform == 'win64':
            pass
        else:
            system('cp %s/* %s' % (self.settings['case_dir'], self.test_dir))
            system('cp -r project_files/* %s' % self.test_dir)
            #if debug: system('ls %s' % self.test_dir)


    def getCases(self):
        tests = self.getTests()
        if debug: print tests

        print "Downloading test cases..."
        for case in tests:
            case_id = case['id']
            if case_id in self.settings['case_ids']:
                print "Test %s already cached" % case_id
                continue

            media_url = case['file']
            resource_uri = case['resource_uri']

            if debug: print media_url
            case_name = str(uuid4())
            if debug: print "Saving test case to %s" % path.join(self.settings['case_dir'], case_name)
            name, obj = urlretrieve(media_url, path.join(self.settings['case_dir'], case_name))
            ext = media_url.split('?')[0].split('.')[-1]
            self.settings['cases'][case_id] = TestCase(case_name, case_id, self.test_dir, ext, self.getUserUri(), resource_uri)
            print "Got test %s" % case_id
            self.settings['case_names'].append(case_name)
            self.settings['case_ids'].append(case_id)
        print "Done downloading tests\n"

    def getTests(self):
        """
            
        """
        req = Request(self.api_url)
        opener = build_opener()
        response = opener.open(req).read()
        response_json = loads(response)
        objects = response_json['objects']
        for project in objects:
            if debug: print project
            if project['id'] == str(self.proj):
                return project['tests']
        print 'no matching project found'
        return None


    def getUserUri(self):
        #request = Request(self.url+self.user_uri_url)
        #opener = build_opener()
        #response = loads(opener.open(request).read())
        #return response['objects'][0]['resource_uri']
        return ''

    def runTests(self):
        if debug: print "Running the test cases..."
        if debug: print self.settings['cases']
        for id,test in self.settings['cases'].items():
            if debug: print id,test
            try: 
                test.runTest()
            except Exception, e:
                if debug: print 'Test threw an exception'
                test.error = True


    def putResults(self, key):
        for id,test in self.settings['cases'].items():
            payload = dumps(test.asDict())
            if debug: print payload, self.response_url
            request = Request(self.response_url, payload, {'Content-Type': 'application/json'})
            try: 
                response = urlopen(request)
                if debug: print response.read()
                print 'Successfully sent case %s' % test.case_id
                if debug: print payload
                response.close()
            except HTTPError, e:
                if debug: print 'The submission for test %s failed' % test.case_id
                if debug: print e
                if debug: print e.read()

    def cleanup(self):
        #rmtree(self.test_dir)
        self.dumpSettings(self.settings)
        

if __name__ == '__main__':
    t = Tester()
    t.start()
    t.runTests()
    t.putResults(t.key)
    t.cleanup()
    
