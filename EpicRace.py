# Made with <3 by Marocco2
# Sound player code by Rombik @ AC forums.
# Sound player updates for fmod-ex by rafffel @ AC forums.

import configparser
import os
import platform
import random
import sys
import time
import traceback
import ac

if platform.architecture()[0] == "64bit":
    sysdir = "stdlib64"
else:
    sysdir = "stdlib"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "box", sysdir))
os.environ['PATH'] += ";."

importError = False

try:
    from BOX import box, sim_info
    import update
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
debug = config.getboolean('SETTINGS', 'debug')
leader = config.getboolean('Overtake', 'loop leader')

audio = config['Audio']['source']
audio_volume = int(config['Audio']['volume'])

sweat = int(config['Victory']['sweat'])
suspense_laps = int(config['Suspense']['laps'])
enable_before_race = config.getboolean('Before Race', 'active')
enable_overtake = config.getboolean('Overtake', 'active')
enable_suspense = config.getboolean('Suspense', 'active')
enable_hotlap = config.getboolean('Hotlap', 'active')
enable_win = config.getboolean('Victory', 'active')
enable_lose = config.getboolean('Lose', 'active')
enable_pit = config.getboolean('Pit', 'active')

appWindow = sound_player = SoundPackSpinner = VolumeSpinner = \
    Beforerace = Overtake = Suspense = Win = Lose = ""
labeldesc = StatusLabel = NotificationLabel = audiolist = \
    BeforeraceLabel = OvertakeLabel = SuspenseLabel = ""
WinLabel = LoseLabel = audiolabel = ""
session = sessionTime = numberOfLaps = completedLaps = overflow = wait_a = 0
ar_once = ov_once = sus_once = sr_once = br_once = hot_once = False

lap = lastlap = bestlap = 0

list_tracks = audio_folder = before_race_tracks = epic_tracks = \
    win_tracks = win_with_sweat_tracks = start_race_tracks = \
    start_time = finish_time = position = newposition = overtake = \
    iovertake = done = count_overtake = suspense_tracks = surprise_tracks = 0
lose_tracks = 0

isPlayingStartRace = isPlayingBeforeRace = isPlayingSuspense = \
    isPlayingAfterRace = isPlayingOvertake = isPlayingHotlap = isPlayingPit = False


def initSoundPack(audio_source):
    global list_tracks, audio_folder, before_race_tracks, epic_tracks, win_tracks, win_with_sweat_tracks
    global start_race_tracks, lose_tracks, suspense_tracks, surprise_tracks, pit_tracks
    audio_folder = "apps\\python\\EpicRace\\SoundPacks\\" + audio_source
    list_tracks = os.listdir(audio_folder)

    def contains(string):
        con = [lis for lis in list_tracks if string in lis]
        return con

    before_race_tracks = contains("before_race")
    epic_tracks = contains("epic")
    pit_tracks = contains("pit")
    win_tracks = contains("win")
    lose_tracks = contains("lose")
    win_with_sweat_tracks = contains("w_with_sweat")
    start_race_tracks = contains("start_race")
    suspense_tracks = contains("suspense")
    surprise_tracks = contains("surprise")


def priority_queue(location):
    try:
        global sound_player
        global isPlayingStartRace, isPlayingBeforeRace, isPlayingSuspense, isPlayingAfterRace, isPlayingOvertake
        global overflow
        # priority clip cancels other audio.
        stopPlaying()
        # new fmod audio:
        sound_player.queueSong(location)
        overflow += 2
    except:
        ac.log('EpicRace: error loading song ' + traceback.format_exc())


def queue(location):
    try:
        global sound_player
        global isPlayingStartRace, isPlayingBeforeRace, isPlayingSuspense, isPlayingAfterRace, isPlayingOvertake
        global overflow
        # new fmod audio:
        sound_player.queueSong(location)
        overflow += 1
    except:
        ac.log('EpicRace: error loading song ' + traceback.format_exc())


def stopPlaying():
    global sound_player, overflow
    global isPlayingStartRace, isPlayingBeforeRace, isPlayingSuspense, isPlayingAfterRace, isPlayingOvertake
    global isPlayingPit
    sound_player.stop()
    isPlayingStartRace = isPlayingBeforeRace = isPlayingSuspense = isPlayingAfterRace =\
        isPlayingOvertake = isPlayingPit = False


def playBeforeRace():
    global audio_folder, before_race_tracks, isPlayingBeforeRace, br_once
    isPlayingBeforeRace = True
    location = random.choice(before_race_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    br_once = False


def playPit():
    global audio_folder, pit_tracks, isPlayingPit, pit_once
    isPlayingPit = True
    location = random.choice(pit_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    pit_once = False


def playStartRace():
    global audio_folder, start_race_tracks, isPlayingStartRace, sr_once
    location = random.choice(start_race_tracks)
    location = os.path.join(audio_folder, location)
    priority_queue(location)
    isPlayingStartRace = True
    sr_once = False


def playHotlap():
    global audio_folder, suspense_tracks, isPlayingHotlap, hot_once
    location = random.choice(win_tracks)
    location = os.path.join(audio_folder, location)
    queue(location)
    isPlayingHotlap = True
    hot_once = False


def playSuspense():
    global audio_folder, suspense_tracks, isPlayingSuspense, sus_once
    location = random.choice(suspense_tracks)
    location = os.path.join(audio_folder, location)
    queue(location)
    isPlayingSuspense = True
    sus_once = False


def playAfterRace(win_or_lose):
    global audio_folder, win_tracks, isPlayingAfterRace, count_overtake, win_with_sweat_tracks, lose_tracks, overtake
    global ar_once, hot_once, sweat
    if win_or_lose == "win" and count_overtake < sweat:
        location = random.choice(win_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)

    if win_or_lose == "win" and count_overtake >= sweat:
        location = random.choice(win_with_sweat_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)

    if win_or_lose == "lose":
        location = random.choice(lose_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
    isPlayingAfterRace = True
    ar_once = False
    hot_once = False
    count_overtake = 0
    overtake = 0


def playOvertake():
    global audio_folder, epic_tracks, surprise_tracks, isPlayingSuspense, isPlayingOvertake, ov_once
    ov_once = True
    if isPlayingSuspense:
        location = random.choice(surprise_tracks)
        location = os.path.join(audio_folder, location)
        priority_queue(location)
    else:
        location = random.choice(epic_tracks)
        location = os.path.join(audio_folder, location)
        queue(location)
    isPlayingOvertake = True
    ov_once = False


def acMain(ac_version):
    global appWindow
    global sound_player, SoundPackSpinner, VolumeSpinner
    global Beforerace, Overtake, Suspense, Win, Lose, labeldesc, Hotlap
    global StatusLabel, NotificationLabel, audio, audiolist, BeforeraceLabel, OvertakeLabel, SuspenseLabel
    global WinLabel, LoseLabel, audiolabel, position, debuglabel
    # DEBUG INFO
    global enable_overtake, enable_lose, enable_win, enable_hotlap
    global enable_before_race, enable_suspense, suspense_laps, log
    global audio, overtake, position, newposition, start_time, finish_time, count_overtake
    global session, sessionTime, numberOfLaps, completedLaps

    appWindow = ac.newApp("Epic Race")
    ac.setSize(appWindow, 430, 350)
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
    Hotlap = ac.addCheckBox(appWindow, "")
    ac.setValue(Hotlap, enable_hotlap)
    ac.setPosition(Hotlap, 10, 280)
    ac.setSize(Hotlap, 20, 20)
    ac.drawBorder(Hotlap, 1)
    ac.addOnCheckBoxChanged(Hotlap, onEnableHotlap)
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
    HotlapLabel = ac.addLabel(appWindow, "Enable hotlap")
    ac.setPosition(HotlapLabel, 40, 280)
    ac.setFontColor(HotlapLabel, 1, 1, 1, 1)
    ac.setFontSize(HotlapLabel, 15)
    #
    labeldesc = ac.addLabel(appWindow, "Something is broken")
    ac.setPosition(labeldesc, 180, 40)
    ac.setSize(labeldesc, 200, 200)
    #
    StatusLabel = ac.addLabel(appWindow, Status)
    ac.setPosition(StatusLabel, 10, 305)
    ac.setFontColor(StatusLabel, 1, 1, 1, 1)
    ac.setFontSize(StatusLabel, 15)
    #
    NotificationLabel = ac.addLabel(appWindow, Notify)
    ac.setPosition(NotificationLabel, 10, 325)
    ac.setFontColor(NotificationLabel, 1, 1, 1, 1)
    ac.setFontSize(NotificationLabel, 12)
    ac.setSize(NotificationLabel, 24, 310)
    #
    # DEBUG INFO
    #
    debuglabel = ac.addLabel(appWindow, "")
    ac.setPosition(debuglabel, 215, 30)
    ac.setSize(debuglabel, 200, 200)
    #
    #
    #
    box.FModSystem.init()
    sound_player = box.SoundPlayer(box.FModSystem)
    sound_player.set_volume(audio_volume / 100)
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
    global enable_overtake, enable_lose, enable_win, enable_before_race, enable_pit
    global enable_suspense, enable_hotlap, suspense_laps, log
    global audio, overtake, iovertake, done, position, newposition
    global start_time, finish_time, count_overtake, bestlap, lastlap, hot_once, pit_once, lap
    global session, sessionTime, numberOfLaps, completedLaps, debuglabel, overflow, sound_player
    global isPlayingStartRace, isPlayingBeforeRace, isPlayingSuspense, isPlayingPit
    global isPlayingAfterRace, isPlayingOvertake, isPlayingHotlap
    global ar_once, ov_once, sus_once, sr_once, br_once, wait_a, debug, leader

    status = info.graphics.status
    session = info.graphics.session
    sessionTime = info.graphics.sessionTimeLeft
    # ac.log(log + "session time" + str(sessionTime))
    numberOfLaps = info.graphics.numberOfLaps
    completedLaps = info.graphics.completedLaps
    lenqueue = sound_player.lenQueue()
    lastlap = info.graphics.lastTime
    bestlap = info.graphics.bestTime
    pitlane = info.graphics.isInPitLane

    if ((sessionTime <= 0 and session <= 2) or session == 3) and lenqueue == 0 and (
                                isPlayingStartRace or
                                isPlayingBeforeRace or
                                isPlayingSuspense or
                                isPlayingAfterRace or
                                isPlayingOvertake or
                                isPlayingHotlap):
        wait_a += 1
        if lenqueue == 0 and wait_a == 100:
            isPlayingStartRace = isPlayingBeforeRace = isPlayingSuspense = \
                isPlayingAfterRace = isPlayingHotlap = isPlayingOvertake = isPlayingPit = False
            ac.log(log + "lenqueue reset")
            wait_a = 0

    # DEBUG INFOS
    if debug:
        ac.setText(labeldesc, "")
        ac.setText(debuglabel, "Session: " + repr(session) +
                   "\nNumber of laps: " + repr(numberOfLaps) +
                   "\nCompleted Laps: " + repr(completedLaps) +
                   "\nOvertakes: " + repr(count_overtake) +
                   "\nSession Time: " + repr(sessionTime) +
                   "\nLast lap: " + repr(lastlap) +
                   "\nBest lap: " + repr(bestlap) +
                   "\nPosition: " + repr(ac.getCarRealTimeLeaderboardPosition(0)) +
                   "\nLength queue: " + str(lenqueue) +
                   "\nLead position: " + repr(ac.getCarLeaderboardPosition(0)) +
                   "\nisPlayingStartRace: " + str(isPlayingStartRace) +
                   "\nisPlayingBeforeRace: " + str(isPlayingBeforeRace) +
                   "\nisPlayingSuspense: " + str(isPlayingSuspense) +
                   "\nisPlayingAfterRace: " + str(isPlayingAfterRace) +
                   "\nisPlayingPit: " + str(isPlayingPit) +
                   "\nisPlayingHotlap: " + str(isPlayingHotlap) +
                   "\nisPlayingOvertake: " + str(isPlayingOvertake))

    if overflow < 50:

        # DEBUG ONLY
        # overflow += 1

        if status == 2:
            if session == 2:  # Race sessions
                # ac.log(log + "Race session")
                if enable_before_race and not isPlayingBeforeRace and not br_once and sessionTime > 0:
                    ac.log(log + "Before race detected")
                    br_once = True
                    playBeforeRace()

                if enable_before_race and isPlayingBeforeRace and sessionTime <= 0:
                    stopPlaying()

                if enable_pit and isPlayingPit and not pit_once:
                    ac.log(log + "Pit detected")
                    pit_once = True
                    playPit()

                if enable_overtake and not isPlayingOvertake and not ov_once and sessionTime < 0 and (
                            numberOfLaps - completedLaps) != 0:
                    newposition = ac.getCarRealTimeLeaderboardPosition(0)
                    if position > newposition:
                        ac.log(log + "Overtake detected")
                        position = newposition
                        if done == 0:
                            start_time = time.perf_counter()
                            done = 1
                        overtake += 1
                        iovertake += 1
                        count_overtake += 1
                        if overtake == 2:
                            ac.log(log + "Overtake detected x2")
                            finish_time = time.perf_counter()
                            if finish_time - start_time < 30:
                                ac.log(log + "Epicness detected because 2 overtakes")
                                overtake = 0
                                playOvertake()
                                ov_once = True
                            else:
                                overtake = 0
                                done = 0
                        if iovertake == 3:
                            ac.log(log + "Overtake changes x2")
                            finish_time = time.perf_counter()
                            if finish_time - start_time < 30:
                                ac.log(log + "Epicness detected because 2 overtakes")
                                done = 0
                                iovertake = 0
                                overtake = 0
                                playOvertake()
                                ov_once = True
                            else:
                                done = 0
                                iovertake = 0
                                overtake = 0
                        if leader == 0 and ac.getCarRealTimeLeaderboardPosition(0) == 0:
                            ac.log(log + "Epicness detected because you are 1st")
                            overtake = 0
                            iovertake += 1
                            ov_once = True
                            playOvertake()
                    if position < newposition:
                        ac.log(log + "Undertake detected")
                        position = newposition
                        overtake = 0
                    if leader == 1 and ac.getCarRealTimeLeaderboardPosition(0) == 0:
                        ac.log(log + "Epicness detected because you are 1st (loop)")
                        overtake = 0
                        ov_once = True
                        playOvertake()

                if enable_suspense and not isPlayingSuspense and not sus_once and (
                            numberOfLaps - completedLaps) <= suspense_laps and (
                            numberOfLaps - completedLaps) != 0:
                    ac.log(log + "Suspense detected")
                    sus_once = True
                    playSuspense()
                if enable_win and not isPlayingAfterRace and not ar_once and ac.getCarRealTimeLeaderboardPosition(
                        0) == 0 and (
                            numberOfLaps - completedLaps) == 0:
                    ac.log(log + "Win detected")
                    ar_once = True
                    playAfterRace('win')
                if enable_lose and not isPlayingAfterRace and not ar_once and ac.getCarRealTimeLeaderboardPosition(
                        0) != 0 and (numberOfLaps - completedLaps) == 0:
                    ac.log(log + "Lose detected")
                    ar_once = True
                    playAfterRace('lose')

            if session == 1:  # Qualify session
                # ac.log(log + "Qualify session")
                if enable_suspense and not isPlayingSuspense and not sus_once and sessionTime < 120000:
                    ac.log(log + "Suspense detected")
                    sus_once = True
                    playSuspense()
                if enable_win and not isPlayingAfterRace and not ar_once and ac.getCarLeaderboardPosition(0) == 1:
                    ac.log(log + "Win detected")
                    ar_once = True
                    playAfterRace('win')

            if session == 3:  # Hotlap session
                if enable_hotlap:
                    if lastlap == bestlap and lap != lastlap and completedLaps > 1 \
                            and not hot_once and not isPlayingHotlap:
                        lap = lastlap
                        ac.log(log + "Hotlap detected")
                        hot_once = True
                        playHotlap()

    if overflow >= 50:
        stopPlaying()
        ac.log(log + "BSOD avoided. THERE WAS AN OVERFLOW")
        exit()


def CheckNewUpdate():
    global Status, StatusLabel, branch
    try:
        Status = update.update()
        if Status == 0:
            Status = "New update is installed. Restart to see changes"
            ac.log('EpicRace: ' + Status)
            ac.setText(StatusLabel, Status)
        if Status == 2:
            Status = "No new update."
            ac.log('EpicRace: ' + Status)
            ac.setText(StatusLabel, Status)
        else:
            Status = "There was an error while installing new update.\nError code: " + str(Status)
            ac.log('EpicRace: Error Update ' + Status)
            ac.setText(StatusLabel, Status)
    except:
        Status = "no internet connection"
        ac.log('EpicRace: Autoupdate ' + Status + traceback.format_exc())
        ac.setText(StatusLabel, Status)


def getNotification():
    global Notify, NotificationLabel, StatusLabel
    try:
        Notify = box.notification('186810231:AAGvhq85_lqUb3wPOStvazULUsmN5ET37gM')
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
    ac.drawBackground(uihighlight, 0)
    # set the new one
    uihighlight = item
    ac.setBackgroundColor(uihighlight, 1, 0, 0)
    ac.drawBackground(uihighlight, 1)


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


def onEnableHotlap(x):
    global enable_hotlap
    value = int(ac.getValue(Hotlap))
    enable_hotlap = value
    config['Hotlap']['active'] = str(value)


def onEnablePit(x):
    global enable_pit
    value = int(ac.getValue(Pit))
    enable_pit = value
    config['Pit']['active'] = str(value)


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
    sound_player.set_volume(audio_volume / 100)
    config['Audio']['volume'] = str(audio_volume)
    setDescription(VolumeSpinner, '''
    Set the overall volume of
    the app.''')


def acShutdown():
    config.write(open(configfile, 'w'))
