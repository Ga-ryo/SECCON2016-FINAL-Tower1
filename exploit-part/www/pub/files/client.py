#!/usr/bin/env python
# -*- coding: utf-8 -*-
#公開するファイル
import requests
import json

#url = 'http://go.1.finals.seccon.jp/'
url = 'http://localhost:5000/'
headers = {'content-type': 'application/json'}

def get_board():
  return json.loads(requests.post(url+'cmd',data = json.dumps({'cmd':'GETBOARD'}),headers=headers).text)['res']

def get_board_as_list():
  return json.loads(requests.post(url+'cmd',data = json.dumps({'cmd':'GETBOARDASLIST'}),headers=headers).text)['res']

def hall_of_fame():
  return requests.get(url+'hall_of_fame').text

def index():
  return requests.get(url+'index').text

def gettoken():
  return requests.get(url+'gettoken').text

#list of input
def play(l):
  return json.loads(requests.post(url+'cmd',data = json.dumps({'cmd':'PLAY','pos':l}),headers=headers).text)['res']

def get_score():
  return json.loads(requests.post(url+'cmd',data = json.dumps({'cmd':'GETSCORE'}),headers=headers).text)['res']

def surrender():
  return json.loads(requests.post(url+'cmd',data = json.dumps({'cmd':'SURRENDER'}),headers=headers).text)['res']


def main():
  while True:
    print get_board()
    print "input: [x,y] or surrender"
    cmd = raw_input()
    if cmd == "surrender":
      surrender()
      break
    else:
      try:
        if cmd[0] == '[':
          cmd = cmd[1:-1]
        if "," not in cmd:
          continue
        pos = map(int, cmd.split(",", 2))
      except:
        continue
      result = play(pos)
      print "AI: %s" % result
      if result[0] != "[" and result != "AI passed":
        break
  print hall_of_fame()

main()
