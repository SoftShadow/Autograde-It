"Common code for autograders"

import time
import sys
import traceback
import pdb

## code to handle timeouts
import signal
class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass

class TimeoutFunction:

    def __init__(self, function, timeout):
        "timeout must be at least 1 second. WHY??"
        self.timeout = timeout
        self.function = function

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args):
        if not 'SIGALRM' in dir(signal):
            return self.function(*args)
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        # try:
        result = self.function(*args)
        # finally:
        # signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result

class Grades:
  "A data structure for project grades, along with formatting code to display them"
  def __init__(self, projectName, questionsAndMaxesList):
    """
    Defines the grading scheme for a project
      projectName: project name
      questionsAndMaxesDict: a list of (question name, max points per question)
    """
    self.questions = [el[0] for el in questionsAndMaxesList]
    self.maxes = dict(questionsAndMaxesList)
    self.points = Counter()
    self.messages = dict([(q, []) for q in self.questions])
    self.project = projectName
    self.start = time.localtime()[1:6]
    self.sane = True # Sanity checks
    self.currentQuestion = None # Which question we're grading
    self.scores = {}
    
    #print 'Autograder transcript for %s' % self.project
    #print 'Starting on %d-%d at %d:%02d:%02d' % self.start

  def addScore(self, question, score, max_score):
      self.scores[question] = {'score': score, 'max': max_score}

  def grade(self, gradingModule):
    """
    Grades each question
      gradingModule: the module with all the grading functions (pass in with sys.modules[__name__])
    """
    
    #print '%%% ' + 'Autograder messages:' + ' %%%'
    
    for q in self.questions:
      #print '\nQuestion %s' % q
      #print '=' * (9 + len(q))
      self.currentQuestion = q
      
      
      try:
        TimeoutFunction(getattr(gradingModule, q),1200)(self) # Call the question's function
        # #print 'Question %s: %d/%d' % (q, self.points[q], self.maxes[q])
        # gradingModule.grades.addMessageToEmail('Question %s: %d/%d' % (q, self.points[q], self.maxes[q]))
      except Exception, inst:
        self.fail('Question %s terminated with exception: %s.\n%s' % (q, str(inst), traceback.format_exc()))
        #traceback.#print_exc(file=sys.stdout)
      except:
        self.fail('Question %s terminated with a string exception.' % q)

    #print '\nFinished at %d:%02d:%02d' % time.localtime()[3:6]
    
    self.addMessageToEmail('')
    self.addMessageToEmail('Autograder scores:')
    
    if self.sane:
        pass
      #print '@@@PASSED SANITY CHECKS@@@'
      # self.addMessageToEmail('PASSED SANITY CHECKS')
    #print '+++ MINIMUM SCORE FOR THIS SUBMISSION +++'
    # self.addMessageToEmail('MINIMUM SCORE FOR THIS SUBMISSION:')
    for q in self.questions:
      #print 'Question %s: %d/%d' % (q, self.points[q], self.maxes[q])
      self.addScore(q, self.points[q], self.maxes[q])
      self.addMessageToEmail('-- Question ' + str(q) + ': ' + str(self.points[q]) + '/' + str(self.maxes[q]))
      for message in self.messages[q]:
          pass
        # pdb.set_trace()
        # self.addMessageToEmail(message)
        #print '\t' + message

    import json
    print json.dumps(self.scores)
    self.addMessageToEmail('-------------------')
    self.addMessageToEmail('Total: %d/%d' % (self.points.totalCount(), sum(self.maxes.values())))
    #print self.points.totalCount()
    
    self.addMessageToEmail("")
    self.addMessageToEmail("Note: This total score represents the autograder's assessment of your project score.  This score is never the final word on your grade, but it is a lower bound.  The staff may return points mistakenly taken away by the autograder -- let us know if you think the autograder has gone rogue.")
    
    # if self.sane: #print '@@@PASSED SANITY CHECKS@@@'
    # #print '+++ MINIMUM SCORE FOR THIS SUBMISSION +++'
    # for q in self.questions:
    #   #print 'Question %s: %d/%d' % (q, self.points[q], self.maxes[q])
    #   for message in self.messages[q]:
    #     #print '\t' + message
    # #print 'Total: %d/%d' % (self.points.totalCount(), sum(self.maxes.values()))
    # #print self.points.totalCount()

  def fail(self, message):
    "Sets sanity check bit to false and outputs a message"
    self.sane = False
    #print '&&& %s &&&' % message
    #self.(message)

  def assignZeroCredit(self):
    self.points[self.currentQuestion] = 0
  
  def addPoints(self, amt):
    self.points[self.currentQuestion] += amt

  def deductPoints(self, amt):
    self.points[self.currentQuestion] -= amt

  def assignFullCredit(self):
    self.points[self.currentQuestion] = self.maxes[self.currentQuestion]

  def addMessage(self, message):
    #print '*** ' + message
    self.messages[self.currentQuestion].append(message)

  def addMessageToEmail(self, message):
    for line in message.split('\n'):
      #print '%%% ' + line + ' %%%'
      self.messages[self.currentQuestion].append(line)


class Counter(dict):
  """
  Dict with default 0
  """
  def __getitem__(self, idx):
    try:
      return dict.__getitem__(self, idx)
    except KeyError:
      return 0

  def totalCount(self):
    """
    Returns the sum of counts for all keys.
    """
    return sum(self.values())



