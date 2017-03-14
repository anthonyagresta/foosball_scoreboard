#!/usr/bin/env python

from dothat import backlight
from dothat import lcd
from dothat import touch
from math import fmod
import os
import RPi.GPIO as GPIO
import socket
import subprocess
from time import sleep
from time import time

button_pushed = False
goals_locked = False
has_anyone_won = False

score_yellow = 0
score_black = 0


def main():
  setup()
  while(True):
    global goals_locked
    global score_yellow
    global score_black
    global has_anyone_won
    score_yellow = 0
    score_black = 0
    has_anyone_won = False

    pregame_display()
    wait_for_touch()
    display_scoreboard()
    goals_locked = False
    while(not has_anyone_won):
      x = 1

def setup():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(5, GPIO.IN)
  GPIO.setup(6, GPIO.IN)

  lcd.set_contrast(53)

  # Custom font sprites for drawing huge "GOAL"
  # full block
  lcd.create_char(0, [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])

  # bottom half block
  lcd.create_char(1, [0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff])

  # bottom right corner
  lcd.create_char(2, [0x01, 0x03, 0x03, 0x07, 0x07, 0x0f, 0x0f, 0x1f])

  # top right corner
  lcd.create_char(3, [0x1f, 0x0f, 0x0f, 0x07, 0x07, 0x03, 0x03, 0x01])

  # bottom left corner
  lcd.create_char(4, [0x10, 0x18, 0x18, 0x1c, 0x1c, 0x1e, 0x1e, 0x1f])

  # top right corner
  lcd.create_char(5, [0x1f, 0x1e, 0x1e, 0x1c, 0x1c, 0x18, 0x18, 0x10])

  # Top pyramid corner of A
  lcd.create_char(6, [0, 0, 0x04, 0x04, 0x0e, 0x0e, 0x1f, 0x1f])
  
  global goals_locked 
  goals_locked = True
  GPIO.add_event_detect(5, GPIO.RISING, callback=on_goal_1, bouncetime=3000)
  GPIO.add_event_detect(6, GPIO.RISING, callback=on_goal_2, bouncetime=3000)

def goooal(team):
  global score_yellow
  global score_black
  global button_pushed
  global goals_locked

  if(goals_locked):
    return
  button_pushed = False
  goals_locked = True

  # GOAL printed huge in block chars
  lcd.set_cursor_position(0,0)
  lcd.write(chr(2) + chr(0) + chr(0) + ' ' + chr(2) + chr(0) + chr(0) + chr(4) + '  ' + chr(6) + '  ' + chr(0) + '  ')
  lcd.set_cursor_position(0,1)
  lcd.write(chr(0)+ ' ' + chr(1) + ' ' + chr(0) + '  '+ chr(0) + ' '+ chr(2) + chr(1) + chr(4) + ' ' + chr(0) + '  ')
  lcd.set_cursor_position(0,2)
  lcd.write(chr(3) + chr(0) + chr(0) + ' ' +  chr(3) + chr(0) + chr(0) + chr(5) + chr(2) + chr(5) + ' '+ chr(3) + chr(4) + chr(0) + chr(0) + chr(0))

  touch.high_sensitivity()
  touch.enable_repeat(False)
  lights = 1.0
  notify_replay_bot('goooooooooal!')
  while(lights > 0.0):
    if(button_pushed):
      display_scoreboard()
      goals_locked = False
      return
    backlight.set_graph(lights)
    set_backlight_rainbow(lights)

    lights = lights - 0.01
    sleep(0.0025)
  if(team == 0):
    score_yellow = score_yellow + 1
  else:
    score_black = score_black + 1
  check_if_someone_won()

def check_if_someone_won():
  global goals_locked
  global score_yellow
  global score_black
  global has_anyone_won

  if(score_yellow >= 5 and (score_yellow - score_black) >= 2):
    set_team_color(0)
    lcd.clear()
    lcd.set_cursor_position(0,0)
    lcd.write('  Yellow wins!')
    lcd.set_cursor_position(0,1)
    lcd.write('     ' + str(score_yellow) + ' - ' + str(score_black))
    notify_slack()
    notify_replay_bot('game_end')
    sleep(5)
    has_anyone_won = True
  elif(score_black >= 5 and (score_black - score_yellow) >= 2):
    set_team_color(1)
    lcd.clear()
    lcd.set_cursor_position(0,0)
    lcd.write('  Black wins!')
    lcd.set_cursor_position(0,1)
    lcd.write('     ' + str(score_black) + ' - ' + str(score_yellow))
    notify_slack()
    notify_replay_bot('game_end')
    sleep(5)
    has_anyone_won = True
  else:
    display_scoreboard()
    goals_locked = False
    

def display_scoreboard():
  lcd.clear()
  backlight.set_graph(0.0)
  set_entire_backlight(0xff, 0xff, 0xff)

  str_score_1 = str(score_yellow).rjust(2)
  str_score_2 = str(score_black).ljust(2)
  lcd.set_cursor_position(0,0)
  lcd.write('Yellow     Black')
  lcd.set_cursor_position(0,1)
  lcd.write(' ')
  lcd.set_cursor_position(1,1)
  lcd.write(str_score_1)
  lcd.set_cursor_position(13,1)
  lcd.write(str_score_2)

def set_team_color(team):
  if(team == 0):
    set_entire_backlight(0xff, 0xff, 0)
  else:
    set_entire_backlight(0, 0xff, 0xff)

def set_entire_backlight(r, g, b):
  backlight.left_rgb( r, g, b)
  backlight.mid_rgb(  r, g, b)
  backlight.right_rgb(r, g, b)

def set_backlight_rainbow(hue):
  backlight.left_hue(hue)
  backlight.mid_hue(fmod((hue+0.33),1.0))
  backlight.right_hue(fmod((hue+0.66),1.0))

def pregame_display():
  set_entire_backlight(0xff, 0xff, 0xff)
  lcd.clear()
  lcd.set_cursor_position(0,0)
  lcd.write('    Game Over')
  lcd.set_cursor_position(0,2)
  lcd.write(' Touch To Start')

def wait_for_touch():
  global button_pushed
  button_pushed = False
  while(True):
    if(button_pushed):
      return

def on_goal_1(_a):
  goooal(0)

def on_goal_2(_a):
  goooal(1)

def notify_slack():
  global score_yellow
  global score_black
  score_msg = 'Game complete! *Yellow:* ' + str(score_yellow) + ' *Black:* ' + str(score_black) 
  slack_url = os.environ['SLACK_ENDPOINT']
  slack_channel = 'foosball-sd'
  payload_msg = 'payload={"channel":"' + slack_channel + '", "text":"' + score_msg + '"}'
  curl_exe = '/usr/bin/curl'
  p = subprocess.Popen([curl_exe, '-X', 'POST', '--data-urlencode', payload_msg, slack_url]) 

def notify_replay_bot(text):
  # obviously this is just something hardcoded for our network
  IP = '192.168.254.220'
  PORT = 4005
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(text, (IP, PORT))

@touch.on([touch.LEFT, touch.RIGHT, touch.UP, touch.DOWN, touch.BUTTON, touch.CANCEL])
def handle_touch(_a, _b):
  global button_pushed
  button_pushed = True

try:
  main()
finally:
  lcd.clear()
  set_entire_backlight(0,0,0)
  backlight.set_graph(0.0)
  GPIO.cleanup()
 
