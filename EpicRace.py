# Sound player code by Rombik @ AC forums.
# Sound player updates for fmod-ex by rafffel @ AC forums.

import ac
import acsys
import os
import sys
import platform
import datetime
import configparser
import shutil
import codecs
import traceback
import threading
import time

if platform.architecture()[0] == "64bit":
    sysdir = "stdlib64"
else:
    sysdir = "stdlib"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "box", sysdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

import ctypes

importError = False

try:
    from BOX import box, win32con
except:
    ac.log('BoxRadio: error loading BOX modules: ' + traceback.format_exc())
    importError = True

from BOX.sim_info import info

# Config is read. So.
configfile = os.path.join(os.path.dirname(__file__), 'EpicRace.ini')
config = configparser.ConfigParser()
config.read(configfile)

# stuff that's read from the config

audio = config['Audio']['source']
audio_volume = int(config['Audio']['volume'])

enablesbs = config.getboolean('Proximity','active')
enableslow = config.getboolean('Slow','active')
enablestop = config.getboolean('Stop','active')



# UI identifiers
labelv = 0    # the main text label
labelw = 0    # the debug text label
labeldesc = 0 # the description of each spinner label
settingslabel = 0
langspinner = 0
langlabel = 0
langlist = 0 # the list of language options
audiolabel = 0
audiospinner = 0
audiolist = 0 # the list of audio options
audiovolumespinner = 0
spotter = 0   # the app
apptitle = "Spotter"
apptitlecheck = 0
appshowcheck = 0
fontspinner = 0

stopspeedspinner = 0
carlengthspinner = 0
scanwidthspinner = 0

slowratiospinner = 0
caraheadspinner = 0
scanlimitspinner = 0
scanrangespinner = 0

sbscheck = 0
slowcheck = 0
stopcheck = 0

showsettings = 1

uihighlight = -1

description = {}
description['Stop'] = {}
description['Stop']['speed'] = '''
  Maximum speed in meters
  per second where a car
  is considered "stopped".'''


maxcars = 64 # I'm skeptical but there seems to be no way to pull the actual total atm
drivers = []
player = 0
# side by side variables
sbsdisplay = 0.0
sbsstring = ""
# stopped car tracking variables
stopdisplay = 0.0
stopstring = ""
# slow car tracking variables
slowdisplay = 0.0
slowstring = ""
# segment pace tracking variables
segments = 1000.0 # number of sectors to divide the track into for determining slow cars.
segdata = [0]
segstarted = 0 # overall control for when to start writing seg speeds.
prevseg = 0  # track where the player used to be

i18n = []
counter = 0

def acMain(ac_version):
    box.FModSystem.init()
    sound_player = box.SoundPlayer(os.path.join(os.path.dirname(__file__), "audio\\Wattie\\car_on_right.wav"),
                                   box.FModSystem)
    sound_player.set_volume(audio_volume / 100.0)
    sound_player.set_gain(2.0)
    return "EpicRace"

def acUpdate(deltaT):

def acShutdown():
    config.write(open(configfile, 'w'))