# Sound player code by Rombik @ AC forums.
# Sound player updates for fmod-ex by rafffel @ AC forums.

import ac
import acsys
import os
import sys
import platform
import configparser
import shutil
import codecs
import traceback
import random
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

Notify = ""
Status = "Auto update disabled"
uihighlight = -1

# stuff that's read from the config
AppInitialised = False
branch = config['SETTINGS']['branch']
AutoUpdate = config.getboolean('SETTINGS', 'AUTOUPDATE')

audio = config['Audio']['source']
audio_volume = int(config['Audio']['volume'])

suspense_laps = config['playSuspense']['laps']
enable_before_race = config.getboolean('Before Race', 'active')
enable_overtake = config.getboolean('playOvertake', 'active')
enable_suspense = config.getboolean('playSuspense', 'active')
enable_win = config.getboolean('Victory', 'active')
enable_lose = config.getboolean('Lose', 'active')

list_tracks = audio_folder = before_race_tracks = epic_tracks = win_tracks = win_with_sweat_tracks = start_race_tracks = \
    start_time = finish_time = position = newposition = overtake = count_overtake = suspense_tracks = surprise_tracks = 0

isPlayingBeforeRace = isPlayingSuspense = isPlayingAfterRace = isPlayingOvertake = False


def initSoundPack(audio):
    global list_tracks, audio_folder, before_race_tracks, epic_tracks, win_tracks, win_with_sweat_tracks
    global start_race_tracks, lose_tracks, suspense_tracks, surprise_tracks
    audio_folder = "apps\\python\\EpicRace\\SoundPacks\\" + audio
    list_tracks = os.listdir(audio_folder)

    def contains(string):
        con = [lis for lis in list_tracks if string in lis]
        return con

    before_race_tracks = contains("before_race")
    epic_tracks = contains("epic")
    win_tracks = contains("win")
    lose_tracks = contains("lose")
    win_with_sweat_tracks = contains("w_with_sweat")
    start_race_tracks = contains("start_race")
    suspense_tracks = contains("suspense")
    surprise_tracks = contains("surprise")


def priority_queue(location):
    # priority clip cancels other audio. so that eg. left both right clear can be left right clear
    box.FModSystem.stop()
    # new fmod audio:
    box.FModSystem.queueSong(location)


def queue(location):
    # new fmod audio:
    box.FModSystem.queueSong(location)


def playBeforeRace():
    global audio_folder, before_race_tracks, isPlayingBeforeRace
    location = random.choice(before_race_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    isPlayingBeforeRace = True


def playSuspense():
    global audio_folder, suspense_tracks, isPlayingSuspense
    location = random.choice(suspense_tracks)
    location = os.path.join(audio_folder, location)
    queue(location)
    isPlayingSuspense = True


def playAfterRace(win_or_lose):
    global audio_folder, win_tracks, isPlayingAfterRace, count_overtake, win_with_sweat_tracks, lose_tracks
    if win_or_lose == "win" and count_overtake < 7:
        location = random.choice(win_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
        count_overtake = 0
        isPlayingAfterRace = True

    if win_or_lose == "win" and count_overtake >= 7:
        location = random.choice(win_with_sweat_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
        count_overtake = 0
        isPlayingAfterRace = True

    else:
        location = random.choice(lose_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
        count_overtake = 0
        isPlayingAfterRace = True


def playOvertake():
    global audio_folder, epic_tracks, surprise_tracks, isPlayingSuspense, isPlayingOvertake
    if isPlayingSuspense:
        location = random.choice(surprise_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
        isPlayingOvertake = True
    else:
        location = random.choice(epic_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
        isPlayingOvertake = True


def acMain(ac_version):
    global sound_player, SoundPackSpinner, VolumeSpinner, Beforerace, Overtake, Suspense, Win, Lose, labeldesc
    global StatusLabel, NotificationLabel, audio, audiolist

    appWindow = ac.newApp("Epic Race")
    ac.setSize(appWindow, 430, 260)
    ac.setTitle(appWindow, "Epic Race")
    ac.setBackgroundOpacity(appWindow, 0.5)
    ac.drawBorder(appWindow, 0)
    #
    SoundPackSpinner = ac.addSpinner(appWindow, "")
    ac.setFontColor(SoundPackSpinner, 1, 1, 1, 1)
    ac.setFontSize(SoundPackSpinner, 12)
    spinner_config(SoundPackSpinner, 10, 15, 80, 18, 0, 1, 100, 0, onSoundPackChanged)
    #
    VolumeSpinner = ac.addSpinner(appWindow, "")
    ac.setFontColor(VolumeSpinner, 1, 1, 1, 1)
    ac.setFontSize(VolumeSpinner, 12)
    spinner_config(VolumeSpinner, 10, 45, 80, 18, 0, 1, 100, audio_volume, onVolumeChanged)

    Beforerace = ac.addCheckBox(appWindow, "")
    ac.setPosition(Beforerace, 10, 60)
    ac.setSize(Beforerace, 20, 20)
    ac.drawBorder(Beforerace, 1)
    ac.addOnCheckBoxChanged(Beforerace, onEnableBeforeRace)
    #
    Overtake = ac.addCheckBox(appWindow, "")
    ac.setPosition(Overtake, 10, 90)
    ac.setSize(Overtake, 20, 20)
    ac.drawBorder(Overtake, 1)
    ac.addOnCheckBoxChanged(Overtake, onEnableOverTake())
    #
    Suspense = ac.addCheckBox(appWindow, "")
    ac.setPosition(Suspense, 10, 120)
    ac.setSize(Suspense, 20, 20)
    ac.drawBorder(Suspense, 1)
    ac.addOnCheckBoxChanged(Suspense, onEnableSuspense)
    #
    Win = ac.addCheckBox(appWindow, "")
    ac.setPosition(Win, 10, 150)
    ac.setSize(Win, 20, 20)
    ac.drawBorder(Win, 1)
    ac.addOnCheckBoxChanged(Win, onEnableWin)
    #
    Lose = ac.addCheckBox(appWindow, "")
    ac.setPosition(Lose, 10, 180)
    ac.setSize(Lose, 20, 20)
    ac.drawBorder(Lose, 1)
    ac.addOnCheckBoxChanged(Lose, onEnableLose)
    #
    labeldesc = ac.addLabel(appWindow, "You can close the app. It works in "
                                       "background")
    ac.setPosition(labeldesc, 160, 10)
    ac.setSize(labeldesc, 200, 200)
    #
    StatusLabel = ac.addLabel(appWindow, Status)
    ac.setPosition(StatusLabel, 10, 205)
    ac.setFontColor(StatusLabel, 1, 1, 1, 1)
    ac.setFontSize(StatusLabel, 10)
    #
    NotificationLabel = ac.addLabel(appWindow, Notify)
    ac.setPosition(NotificationLabel, 10, 235)
    ac.setFontColor(NotificationLabel, 1, 1, 1, 1)
    ac.setFontSize(NotificationLabel, 9)
    #
    #
    #
    box.FModSystem.init()
    sound_player = box.SoundPlayer(os.path.join(os.path.dirname(__file__), "SoundPacks\\Turnabout\\before_race_1.mp3"),
                                   box.FModSystem)
    sound_player.set_volume(audio_volume / 100.0)
    sound_player.set_gain(2.0)

    audiolist = os.listdir(os.path.join(os.path.dirname(__file__), "SoundPacks"))
    ac.setRange(SoundPackSpinner, 0, len(audiolist) - 1)
    ac.setStep(SoundPackSpinner, 1)
    ac.setValue(SoundPackSpinner, audiolist.index(audio))

    return "EpicRace"


def spinner_config(spinner, x, y, xl, yl, min, step, max, value, evt):
    ac.setPosition(spinner, x, y)
    ac.setSize(spinner, xl, yl)
    ac.setRange(spinner, min, max)
    ac.setStep(spinner, step)
    ac.setValue(spinner, value)
    ac.addOnValueChangeListener(spinner, evt)


def acUpdate(deltaT):
    global enable_overtake, enable_lose, enable_win, enable_before_race, enable_suspense, suspense_laps
    global AppInitialised, audio, overtake, position, newposition, start_time, finish_time, count_overtake

    if not AppInitialised:  # First call to app, set variables
        getNotification()
        if AutoUpdate:
            CheckNewUpdate()
        initSoundPack(audio)
        position = ac.getCarLeaderboardPosition(0)

        AppInitialised = True

    if info.graphics.session == 2:  # Race sessions
        if enable_before_race and info.graphics.sessionTimeleft < 1:
            playBeforeRace()
        if enable_overtake:
            newposition = ac.getCarLeaderboardPosition(0)
            if position > newposition:
                position = newposition
                start_time = time.perf_counter()
                overtake += 1
                count_overtake += 1
            if position > newposition and overtake == 1:
                position = newposition
                finish_time = time.perf_counter()
                overtake += 1
                count_overtake += 1
            if overtake == 2 and (finish_time - start_time) < 30 or overtake == 1 and ac.getCarLeaderboardPosition(
                    0) == 1:
                count_overtake += 1
                overtake = 0
                playOvertake()
        if enable_suspense and (info.graphics.numberOfLaps - info.graphics.completedLaps) <= suspense_laps:
            playSuspense()
        if enable_win and ac.getCarLeaderboardPosition(0) == '1' and (
            info.graphics.numberOfLaps - info.graphics.completedLaps) == "0":
            playAfterRace('win')
        if enable_lose and ac.getCarLeaderboardPosition(0) != '1' and (
            info.graphics.numberOfLaps - info.graphics.completedLaps) == "0":
            playAfterRace('lose')

    if info.graphics.session == 1:  # Qualify session
        if enable_suspense and info.graphics.sessionTimeleft < 1:
            playSuspense()
        if enable_win and ac.getCarLeaderboardPosition(0) == '1':
            playAfterRace('win')


def CheckNewUpdate():
    global Status, StatusLabel, branch
    try:
        Status = box.github_newupdate('Marocco2/BoxRadio', branch)
        ac.setText(StatusLabel, Status)
    except:
        ac.log('BoxRadio: No internet connection')
        Status = "No internet connection"
        ac.setText(StatusLabel, Status)


def getNotification():
    global Notify, NotificationLabel, StatusLabel
    try:
        Notify = box.notification('186810231:AAF3QvyDtyjZSuoFEdiDk70dl_Q6e7RAZgg')
        ac.setText(NotificationLabel, Notify)
    except:
        ac.log('BoxRadio: No internet connection')
        Status = "No internet connection"
        ac.setText(StatusLabel, Status)


def setDescription(item, text):
    global labeldesc
    ac.setText(labeldesc, text)
    setHighlight(item)


def setHighlight(item):
    global uihighlight
    # dehighlight the old one
    ac.setBackgroundColor(uihighlight, 0.5, 0.5, 0.5)
    # ac.drawBackground(uihighlight, 0)
    # set the new one
    uihighlight = item
    ac.setBackgroundColor(uihighlight, 1, 0, 0)
    # ac.drawBackground(uihighlight, 1)


def onEnableBeforeRace(value):
    global enable_before_race
    enable_before_race = value
    config['Before Race']['active'] = str(value)


def onEnableOverTake(value):
    global enable_overtake
    enable_overtake = value
    config['Overtake']['active'] = str(value)


def onEnableSuspense(value):
    global enable_suspense
    enable_suspense = value
    config['Suspense']['active'] = str(value)


def onEnableWin(value):
    global enable_win
    enable_win = value
    config['Victory']['active'] = str(value)


def onEnableLose(value):
    global enable_lose
    enable_lose = value
    config['Lose']['active'] = str(value)


def onSoundPackChanged(value):
    global audiolist, audiolabel, config, audio, SoundPackSpinner
    audio = audiolist[value]
    ac.setText(audiolabel, audio)
    config['Audio']['source'] = str(audio)
    initSoundPack(audio)
    setDescription(SoundPackSpinner, '''
      Select the audio set that you
      would like to use.
      This refers to a folder in the
      app's /audio/ directory.''')


def onVolumeChanged(value):
    global audio_volume, VolumeSpinner
    audio_volume = value
    sound_player.set_volume(value / 100.0)
    config['Audio']['volume'] = str(value)
    setDescription(VolumeSpinner, '''
    Set the overall volume of
    the app.''')


def acShutdown():
    config.write(open(configfile, 'w'))
