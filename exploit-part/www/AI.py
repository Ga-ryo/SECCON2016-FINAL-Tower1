#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Go
from subprocess import *
import signal
import time
import threading

def hdl(p):
  p.kill()
  p.wait()

def get_output(p):
  t = threading.Timer(10.0,hdl,[p])
  t.start()
  line = p.stdout.readline()
  t.cancel()
  return line

def play(id, pos):
  try:
    p = Popen('../src/AI',stdin=PIPE,stdout=PIPE)
    res = ''
    while p.poll() is None:
      output = get_output(p)
      if 'ERROR' in output:
        raise Exception
      if 'CMD' not in output:
        continue
      if 'SURRENDER' in output:
        res = 'Congratz! AI surrendered.'
      if 'PLAY' in output:
        #[%d,%d] -> python list
        a = get_output(p)
        choice = map(int,a[a.find('[')+1:a.find(']')].split(','))
        Go.play(id, 'black', choice)
        res = str(choice)
      if 'GETINPUT' in output:
        p.stdin.write(str(pos)+'\n')
      if 'GETBOARD' in output:
        p.stdin.write(str(Go.get_board_as_list(id))+'\n')
      if 'GETSCORE' in output:
        p.stdin.write(Go.estimate_score(id, 'black')+'\n')
      if 'PASS' in output:
        Go.ai_pass(id)
        res = 'AI passed'
    return res
  except Exception as e:
    print e
    return 'Error ... (ToT)'
  finally:
    if p.poll() is None:
      p.kill()
      p.wait()

