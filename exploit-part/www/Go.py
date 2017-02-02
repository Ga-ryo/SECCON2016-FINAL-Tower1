#!/usr/bin/env python
# -*- coding: utf-8 -*-
from subprocess import *
import threading
import copy
import resource

resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))

global_board = {}
gbLock = threading.RLock()

"""
Secret key for admin
"""
key = 'secret'
args = ['/usr/games/gnugo','--mode','gtp']

def convert_to_gnugo(l):
  #GnuGo Board don't have 'I'(9th)
  if l[1] >= 9:
    return chr(l[1]+65)+str(20-l[0])
  return chr(l[1]+64)+str(20-l[0])

def convert_to_user(s):
  try:
    if ord(s[0]) >= ord('I'):
      return (20-int(s[1:]),ord(s[0])-65)
    return (20-int(s[1:]),ord(s[0])-64)
  except:
    return None

def get_bentry(id):
  global global_board, gbLock
  with gbLock:
    if global_board.has_key(id):
      #rewrite ok?
      if global_board[id]['proc'] is None:
        return global_board[id]
      if global_board[id]['proc'].poll() is None:
        return global_board[id]
    bentry = {'proc':None,'last':'black','lock':threading.RLock()}
    global_board[id] = bentry
    bentry['lock'].acquire()
  try:
    bentry['proc'] = Popen(args,stdin=PIPE,stdout=PIPE,close_fds=True)
    bentry['proc'].stdin.write('play black '+convert_to_gnugo([10,10])+'\n')
    bentry['proc'].stdout.readline()
    bentry['proc'].stdout.readline()
  finally:
    bentry['lock'].release()
  return bentry

def estimate_score(id,color):
  bentry = get_bentry(id)
  with bentry['lock']:
    bentry['proc'].stdin.write('estimate_score\n')
    score = bentry['proc'].stdout.readline()
    #= B+2.7 (upper bound: 1.0, lower: -6.5)
    if score[3] == 'W':
      if color == 'white':
        sign = '+'
      else:
        sign = '-'
    else:
      if color == 'white':
        sign = '-'
      else:
        sign = '-'
    score = sign + score[4:score.index('(')]
    bentry['proc'].stdout.readline()
  return score


def get_board(id):
  bentry = get_bentry(id)
  with bentry['lock']:
    bentry['proc'].stdin.write('showboard\n')
    lines = ''
    for i in xrange(23):
      if i==1:
        lines += '   1 2 3 4 5 6 7 8 910111213141516171819\n'
        bentry['proc'].stdout.readline()
      elif i<1 or i>20:
        bentry['proc'].stdout.readline()
      else:
        l = bentry['proc'].stdout.readline()
        l = l[2:41]
        lines += '{0:2d}'.format(i-1)+l+'\n'
    return lines

def get_board_as_list(id):
  bentry = get_bentry(id)
  with bentry['lock']:
    board = [0 for x in xrange(19*19)]
    bentry['proc'].stdin.write('list_stones black\n')
    black_list = map(convert_to_user,bentry['proc'].stdout.readline()[2:].split(' '))
    bentry['proc'].stdout.readline()
    bentry['proc'].stdin.write('list_stones white\n')
    white_list = map(convert_to_user,bentry['proc'].stdout.readline()[2:].split(' '))
    bentry['proc'].stdout.readline()
  for black in black_list:
    if black is None:
      continue
    board[19*(black[0]-1) + black[1]-1] = 1
  for white in white_list:
    if white is None:
      continue
    board[19*(white[0]-1) + white[1]-1] = 2
  return board

def ai_pass(id):
  bentry = get_bentry(id)
  with bentry['lock']:
    bentry['last'] = 'black'

def isWhiteTurn(id):
  bentry = get_bentry(id)
  with bentry['lock']:
    if bentry['last'] == 'white':
      return False
    return True

def play(id, color, l):
  try:
    bentry = get_bentry(id)
    with bentry['lock']:
      if (color == bentry['last']):
        return False
      bentry['proc'].stdin.write('play '+color+ ' '+convert_to_gnugo(l)+'\n')
      res = bentry['proc'].stdout.readline()
      bentry['proc'].stdout.readline()
      if 'illegal move' not in res and 'invalid' not in res:
        bentry['last'] = color
    return True
  except:
    return False
  
def restart(id):
  global global_board, gbLock
  with gbLock:
    if not global_board.has_key(id):
      get_bentry(id)
      return
    else:
      bentry = global_board.pop(id)
  stop(bentry)
  get_bentry(id)

def stop(bentry):
  # Don't lock the board to force to kill p
  try:
    p = bentry['proc']
    if p.poll() is None:
      p.kill()
      p.wait()
  except:
    pass

def soft_reset(id):
  bentry = get_bentry(id)
  with bentry['lock']:
    bentry['proc'].stdin.write('clear_board\n')
    bentry['proc'].stdout.readline()
    bentry['proc'].stdout.readline()
    bentry['last'] = 'black'
    bentry['proc'].stdin.write('play black '+convert_to_gnugo([10,10])+'\n')
    bentry['proc'].stdout.readline()
    bentry['proc'].stdout.readline()

def clear_all():
  global global_board, gbLock
  with gbLock:
    #for multithread iteration
    c = copy.copy(global_board)
    global_board = {}
  # kill them all
  for k in c:
    stop(c[k])
