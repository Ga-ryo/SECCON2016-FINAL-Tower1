#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask,request,jsonify
import os
import hashlib
from subprocess import *
import threading

#original script
import Go
import AI
app=Flask(__name__)

Win = {}
WinLock = threading.RLock()

def get_win_stones(id):
  global Win, WinLock
  with WinLock:
    if not Win.has_key(id):
      Win[id] = -1
    return Win[id]

def is_fame(id):
  if get_win_stones(id) != -1:
    return True
  return False

def win(id):
  global Win, WinLock
  with WinLock:
    l = 19*19 - Go.get_board_as_list(id).count(0)
    Win[id] = l

def get_remote_addr():
  return request.access_route[-1]

@app.route('/',methods=['GET'])
def index():
  return 'Can you defeat the AI?\nServer-side source:<a href="http://go.1.finals.seccon.jp/files/websrc.zip">websrc.zip</a>\nClient example: <a href="http://go.1.finals.seccon.jp/files/client.py">client.py</a>'

@app.route('/hall_of_fame',methods=['GET'])
def hall_of_fame():
  id = hashlib.md5(get_remote_addr()).hexdigest()
  if not is_fame(id):
    return 'You should defeat AI.'
  f = open('/flag.txt','r')
  msg = f.read()
  f.close()
  return msg

@app.route('/gettoken',methods=['GET'])
def gettoken():
  id = hashlib.md5(get_remote_addr()).hexdigest()
  token = ''
  if is_fame(id):
    #gentoken is secret binary
    return check_output(['../src/gentoken',str(get_win_stones(id))]).rstrip()
  return token

@app.route('/cmd',methods=['POST'])
def command():
  id = hashlib.md5(get_remote_addr()).hexdigest()
  if(request.json['cmd'] == 'SURRENDER'):
    Go.restart(id)
    return jsonify({'res':'OK'})
  elif(request.json['cmd'] == 'GETBOARD'):
    return jsonify({'res':Go.get_board(id)})
  elif(request.json['cmd'] == 'GETBOARDASLIST'):
    return jsonify({'res':Go.get_board_as_list(id)})
  elif(request.json['cmd'] == 'GETSCORE'):
    return jsonify({'res':Go.estimate_score(id, 'white')})
  elif(request.json['cmd'] == 'PLAY'):
    #check
    if Go.isWhiteTurn(id) and type(request.json['pos']) is list:
      Go.play(id, 'white', request.json['pos'])
      msg = AI.play(id,request.json['pos'])
      if 'Congratz' in msg:
        win(id)
        Go.soft_reset(id)
      return jsonify({'res':msg})
    else:
      return jsonify({'res':'Invalid play'})
  elif(request.json['cmd'] == 'PASS'):
    #you can't pass :), so you should make AI surrender.
    return 
  else:
    return 

#This command is called by admin every round.(5 minutes?)
@app.route('/admin_clear',methods=['GET'])
def admin_clear():
  global Win, WinLock
  if(request.args.get('key') == Go.key):
    Go.clear_all()
    with WinLock:
      Win = {}
    return 'OK'
  return 'Fail'

if __name__ == '__main__':
  app.run(threaded=True)
