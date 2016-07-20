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
    from BOX import box, sim_info, win32con
except:
    ac.log('EpicRace: error loading BOX modules: ' + traceback.format_exc())
    importError = True

info = sim_info.SimInfo()
log = "EpicRace: "

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

suspense_laps = int(config['Suspense']['laps'])
enable_before_race = config.getboolean('Before Race', 'active')
enable_overtake = config.getboolean('Overtake', 'active')
enable_suspense = config.getboolean('Suspense', 'active')
enable_win = config.getboolean('Victory', 'active')
enable_lose = config.getboolean('Lose', 'active')

appWindow = sound_player = SoundPackSpinner = VolumeSpinner = Beforerace = Overtake = Suspense = Win = Lose = ""
labeldesc = StatusLabel = NotificationLabel = audiolist = BeforeraceLabel = OvertakeLabel = SuspenseLabel = ""
WinLabel = LoseLabel = audiolabel = ""
session = sessionTime = numberOfLaps = completedLaps = 0

list_tracks = audio_folder = before_race_tracks = epic_tracks = win_tracks = win_with_sweat_tracks = start_race_tracks = \
    start_time = finish_time = position = newposition = overtake = count_overtake = suspense_tracks = surprise_tracks = 0
lose_tracks = 0

isPlayingBeforeRace = isPlayingSuspense = isPlayingAfterRace = isPlayingOvertake = False


def initSoundPack(audio_source):
    global list_tracks, audio_folder, before_race_tracks, epic_tracks, win_tracks, win_with_sweat_tracks
    global start_race_tracks, lose_tracks, suspense_tracks, surprise_tracks
    audio_folder = "apps\\python\\EpicRace\\SoundPacks\\" + audio_source
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


@box.async
def priority_queue(location):
    try:
        global sound_player
        # priority clip cancels other audio. so that eg. left both right clear can be left right clear
        sound_player.stop()
        # new fmod audio:
        sound_player.queueSong(location)
    except:
        ac.log('EpicRace: error loading song ' + traceback.format_exc())


@box.async
def queue(location):
    try:
        global sound_player
        # new fmod audio:
        sound_player.queueSong(location)
    except:
        ac.log('EpicRace: error loading song ' + traceback.format_exc())


def playBeforeRace():
    global audio_folder, before_race_tracks, isPlayingBeforeRace
    location = random.choice(before_race_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    isPlayingBeforeRace = True


def playStartRace():
    global audio_folder, start_race_tracks, isPlayingStartRace
    location = random.choice(start_race_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    isPlayingStartRace = True


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
        queue(location)
        isPlayingOvertake = True


def acMain(ac_version):
    global appWindow
    global sound_player, SoundPackSpinner, VolumeSpinner, Beforerace, Overtake, Suspense, Win, Lose, labeldesc
    global StatusLabel, NotificationLabel, audio, audiolist, BeforeraceLabel, OvertakeLabel, SuspenseLabel
    global WinLabel, LoseLabel, audiolabel, position, debuglabel
    # DEBUG INFO
    global enable_overtake, enable_lose, enable_win, enable_before_race, enable_suspense, suspense_laps, log
    global audio, overtake, position, newposition, start_time, finish_time, count_overtake
    global session, sessionTime, numberOfLaps, completedLaps

    appWindow = ac.newApp("Epic Race")
    ac.setSize(appWindow, 430, 320)
    ac.setTitle(appWindow, "Epic Race")
    ac.setBackgroundOpacity(appWindow, 0.5)
    ac.drawBorder(appWindow, 0)
    #
    SoundPackSpinner = ac.addSpinner(appWindow, "")
    ac.setFontColor(SoundPackSpinner, 1, 1, 1, 1)
    ac.setFontSize(SoundPackSpinner, 12)
    spinner_config(SoundPackSpinner, 10, 55, 80, 18, 0, 1, 10, 0, onSoundPackChanged)
    #
    VolumeSpinner = ac.addSpinner(appWindow, "")
    ac.setFontColor(VolumeSpinner, 1, 1, 1, 1)
    ac.setFontSize(VolumeSpinner, 12)
    spinner_config(VolumeSpinner, 10, 105, 80, 18, 0, 1, 100, audio_volume, onVolumeChanged)
    #
    audiolabel = ac.addLabel(appWindow, "")
    ac.setPosition(audiolabel, 10, 30)
    ac.setFontColor(audiolabel, 1, 1, 1, 1)
    ac.setFontSize(audiolabel, 15)
    #
    volumelabel = ac.addLabel(appWindow, "Volume")
    ac.setPosition(volumelabel, 10, 80)
    ac.setFontColor(volumelabel, 1, 1, 1, 1)
    ac.setFontSize(volumelabel, 15)

    Beforerace = ac.addCheckBox(appWindow, "")
    ac.setValue(Beforerace, enable_before_race)
    ac.setPosition(Beforerace, 10, 130)
    ac.setSize(Beforerace, 20, 20)
    ac.drawBorder(Beforerace, 1)
    ac.addOnCheckBoxChanged(Beforerace, onEnableBeforeRace)
    #
    Overtake = ac.addCheckBox(appWindow, "")
    ac.setValue(Overtake, enable_overtake)
    ac.setPosition(Overtake, 10, 160)
    ac.setSize(Overtake, 20, 20)
    ac.drawBorder(Overtake, 1)
    ac.addOnCheckBoxChanged(Overtake, onEnableOverTake)
    #
    Suspense = ac.addCheckBox(appWindow, "")
    ac.setValue(Suspense, enable_suspense)
    ac.setPosition(Suspense, 10, 190)
    ac.setSize(Suspense, 20, 20)
    ac.drawBorder(Suspense, 1)
    ac.addOnCheckBoxChanged(Suspense, onEnableSuspense)
    #
    Win = ac.addCheckBox(appWindow, "")
    ac.setValue(Win, enable_win)
    ac.setPosition(Win, 10, 220)
    ac.setSize(Win, 20, 20)
    ac.drawBorder(Win, 1)
    ac.addOnCheckBoxChanged(Win, onEnableWin)
    #
    Lose = ac.addCheckBox(appWindow, "")
    ac.setValue(Lose, enable_lose)
    ac.setPosition(Lose, 10, 250)
    ac.setSize(Lose, 20, 20)
    ac.drawBorder(Lose, 1)
    ac.addOnCheckBoxChanged(Lose, onEnableLose)
    #
    BeforeraceLabel = ac.addLabel(appWindow, "Enable before race")
    ac.setPosition(BeforeraceLabel, 40, 130)
    ac.setFontColor(BeforeraceLabel, 1, 1, 1, 1)
    ac.setFontSize(BeforeraceLabel, 15)
    #
    OvertakeLabel = ac.addLabel(appWindow, "Enable overtake")
    ac.setPosition(OvertakeLabel, 40, 160)
    ac.setFontColor(OvertakeLabel, 1, 1, 1, 1)
    ac.setFontSize(OvertakeLabel, 15)
    #
    SuspenseLabel = ac.addLabel(appWindow, "Enable suspense")
    ac.setPosition(SuspenseLabel, 40, 190)
    ac.setFontColor(SuspenseLabel, 1, 1, 1, 1)
    ac.setFontSize(SuspenseLabel, 15)
    #
    WinLabel = ac.addLabel(appWindow, "Enable win")
    ac.setPosition(WinLabel, 40, 220)
    ac.setFontColor(WinLabel, 1, 1, 1, 1)
    ac.setFontSize(WinLabel, 15)
    #
    LoseLabel = ac.addLabel(appWindow, "Enable lose")
    ac.setPosition(LoseLabel, 40, 250)
    ac.setFontColor(LoseLabel, 1, 1, 1, 1)
    ac.setFontSize(LoseLabel, 15)
    #
    labeldesc = ac.addLabel(appWindow, "You can close the app. It works in "
                                       "background")
    ac.setPosition(labeldesc, 180, 40)
    ac.setSize(labeldesc, 200, 200)
    #
    StatusLabel = ac.addLabel(appWindow, Status)
    ac.setPosition(StatusLabel, 10, 275)
    ac.setFontColor(StatusLabel, 1, 1, 1, 1)
    ac.setFontSize(StatusLabel, 15)
    #
    NotificationLabel = ac.addLabel(appWindow, Notify)
    ac.setPosition(NotificationLabel, 10, 305)
    ac.setFontColor(NotificationLabel, 1, 1, 1, 1)
    ac.setFontSize(NotificationLabel, 12)
    #
    # DEBUG INFO
    #
    debuglabel = ac.addLabel(appWindow, "")
    ac.setPosition(debuglabel, 200, 150)
    ac.setSize(debuglabel, 200, 200)
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

    getNotification()
    if AutoUpdate:
        CheckNewUpdate()
    position = ac.getCarRealTimeLeaderboardPosition(0)

    return "EpicRace"


def spinner_config(spinner, x, y, xl, yl, min, step, max, value, evt):
    ac.setPosition(spinner, x, y)
    ac.setSize(spinner, xl, yl)
    ac.setRange(spinner, min, max)
    ac.setStep(spinner, step)
    ac.setValue(spinner, value)
    ac.addOnValueChangeListener(spinner, evt)


def acUpdate(deltaT):
    global enable_overtake, enable_lose, enable_win, enable_before_race, enable_suspense, suspense_laps, log
    global audio, overtake, position, newposition, start_time, finish_time, count_overtake
    global session, sessionTime, numberOfLaps, completedLaps, debuglabel

    session = info.graphics.session
    sessionTime = info.graphics.sessionTimeLeft
    # ac.log(log + "session time" + str(sessionTime))
    numberOfLaps = info.graphics.numberOfLaps
    completedLaps = info.graphics.completedLaps

    ac.setText(debuglabel, "Session: " + repr(session) +
               "\nNumber of laps: " + repr(numberOfLaps) +
               "\nCompleted Laps: " + repr(completedLaps) +
               "\nOvertakes: " + repr(count_overtake) +
               "\nSession Time: " + repr(sessionTime) +
               "\nPosition: " + repr(ac.getCarRealTimeLeaderboardPosition(0)))

    if session == 2:  # Race sessions
        # ac.log(log + "Race session")
        if enable_before_race and not isPlayingBeforeRace and sessionTime < 1:
            ac.log(log + "Before race detected")
            playBeforeRace()
        if enable_overtake and not isPlayingOvertake:
            newposition = ac.getCarRealTimeLeaderboardPosition(0)
            if position > newposition:
                ac.log(log + "Overtake detected")
                position = newposition
                start_time = time.perf_counter()
                overtake += 1
                count_overtake += 1
            if position > newposition and overtake == 1:
                ac.log(log + "Overtake detected x2")
                position = newposition
                finish_time = time.perf_counter()
                overtake += 1
                count_overtake += 1
            if overtake == 2 and (
                        finish_time - start_time) < 30 or overtake == 1 and ac.getCarRealTimeLeaderboardPosition(
                0) == 1:
                ac.log(log + "Epicness detected")
                count_overtake += 1
                overtake = 0
                playOvertake()
        if enable_suspense and not isPlayingSuspense and (numberOfLaps - completedLaps) <= suspense_laps:
            ac.log(log + "Suspense detected")
            playSuspense()
        if enable_win and not isPlayingAfterRace and ac.getCarRealTimeLeaderboardPosition(0) == '0' and (
                    numberOfLaps - completedLaps) == "0":
            ac.log(log + "Win detected")
            playAfterRace('win')
        if enable_lose and not isPlayingAfterRace and ac.getCarRealTimeLeaderboardPosition(0) != '0' and (
                    numberOfLaps - completedLaps) == "0":
            ac.log(log + "Lose detected")
            playAfterRace('lose')

    if info.graphics.session == 1:  # Qualify session
        # ac.log(log + "Race session")
        if enable_suspense and info.graphics.sessionTimeleft < 1:
            ac.log(log + "Suspense detected")
            playSuspense()
        if enable_win and ac.getCarRealTimeLeaderboardPosition(0) == '1':
            ac.log(log + "Win detected")
            playAfterRace('win')


def CheckNewUpdate():
    global Status, StatusLabel, branch
    try:
        Status = box.github_newupdate('Marocco2/EpicRace', branch)
        ac.setText(StatusLabel, Status)
    except:
        ac.log('EpicRace: No internet connection')
        Status = "No internet connection"
        ac.setText(StatusLabel, Status)


def getNotification():
    global Notify, NotificationLabel, StatusLabel
    try:
        Notify = box.notification('186810231:AAF3QvyDtyjZSuoFEdiDk70dl_Q6e7RAZgg')
        ac.setText(NotificationLabel, Notify)
    except:
        ac.log('EpicRace: No internet connection')
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


def onEnableBeforeRace(x):
    global enable_before_race
    value = int(ac.getValue(Beforerace))
    enable_before_race = value
    config['Before Race']['active'] = str(value)


def onEnableOverTake(x):
    global enable_overtake
    value = int(ac.getValue(Overtake))
    enable_overtake = value
    config['Overtake']['active'] = str(value)


def onEnableSuspense(x):
    global enable_suspense
    value = int(ac.getValue(Suspense))
    enable_suspense = value
    config['Suspense']['active'] = str(value)


def onEnableWin(x):
    global enable_win
    value = int(ac.getValue(Win))
    enable_win = value
    config['Victory']['active'] = str(value)


def onEnableLose(x):
    global enable_lose
    value = int(ac.getValue(Lose))
    enable_lose = value
    config['Lose']['active'] = str(value)


def onSoundPackChanged(x):
    global audiolist, audiolabel, config, audio, SoundPackSpinner
    audio = audiolist[int(ac.getValue(SoundPackSpinner))]
    ac.setText(audiolabel, audio)
    config['Audio']['source'] = str(audio)
    initSoundPack(audio)
    setDescription(SoundPackSpinner, '''
      Select the audio set that you
      would like to use.
      This refers to a folder in the
      app's /SoundPacks/ directory.''')


def onVolumeChanged(value):
    global audio_volume, VolumeSpinner, sound_player
    audio_volume = int(ac.getValue(VolumeSpinner))
    sound_player.set_volume(audio_volume / 100.0)
    config['Audio']['volume'] = str(audio_volume)
    setDescription(VolumeSpinner, '''
    Set the overall volume of
    the app.''')


def acShutdown():
    config.write(open(configfile, 'w'))
