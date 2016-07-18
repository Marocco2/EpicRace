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
os.environ['PATH'] += ";."

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

suspense_laps = 2

enable_before_race = config.getboolean('Before Race', 'active')
enable_overtake = config.getboolean('Overtake', 'active')
enable_suspense = config.getboolean('Suspense', 'active')
enable_win = config.getboolean('Victory', 'active')
enable_lose = config.getboolean('Lose', 'active')

def BeforeRace():

def Suspense():

def AfterRace():

def Overtake():

def acMain(ac_version):
    box.FModSystem.init()
    sound_player = box.SoundPlayer(os.path.join(os.path.dirname(__file__), "SoundPacks\\Turnabout\\before_race_1.mp3"),
                                   box.FModSystem)
    sound_player.set_volume(audio_volume / 100.0)
    sound_player.set_gain(2.0)
    return "EpicRace"

def acUpdate(deltaT):

    if enable_before_race:


    if enable_overtake:


    if enable_suspense and (info.graphics.numberOfLaps - info.graphics.completedLaps) < suspense_laps:
        Suspense()
    if enable_win:

    if enable_lose:




def acShutdown():
    config.write(open(configfile, 'w'))