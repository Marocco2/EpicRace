# Spotter app. 1.2.1
# most code written by Stereo.
# Sound player code by Rombik @ AC forums.
# Sound player updates for fmod-ex by rafffel @ AC forums.

import ac
import acsys
import os
import sys
import platform
import time
import struct

try:
    import configparser
except ImportError as e:
    ac.log("{}".format(e))

from threading import Thread, Event
from io import StringIO

# all strings external to make translation easy
# from spotter_strings import i18strings

# user configuration parameters.  All in Spotter.ini now.

# Config is read. So.
configfile = os.path.join(os.path.dirname(__file__), 'Spotter.ini')
config = configparser.ConfigParser()
config.read(configfile)

# stuff that's read from the config
fontsize = int(config['Display']['fontsize'])  # should just be in normal point sizes.
messageexpiry = int(
    config['Display']['messageduration'])  # minimum length message should persist, in tenths of a second
ignorestoppedcars = int(config['Display']['ignorestopped'])  # number of seconds stationary before a car is ignored.
textcolour = [float(i) for i in config['Display']['textcolour'].split(",")]
language = config['Text']['source']
audio = config['Audio']['source']
audio_volume = int(config['Audio']['volume'])

# stopspeed = int(config['Stop']['speed']) # max speed under which a car is treated as stopped, in m/s. 6->20km/h ish.
carlength = int(config['Proximity']['length'])  # length of car to assume it's side by side
scanwidth = int(config['Proximity']['width'])  # width to check in metres, on each side of your car
slowratio = int(config['Slow']['ratio'])  # percent of your own speed where car is "slow"
carahead = int(
    config['Slow']['linewidth'])  # width on either side of your driving line to call "ahead" instead of left/right
scanlimit = int(config['Slow'][
                    'scandistance'])  # max percent difference in spline position to check other driver behavior. 10% of the track.
scanrange = int(config['Slow']['scantime'])  # max distance in terms of milliseconds to hazard to start warning.
enablesbs = config.getboolean('Proximity', 'active')
enableslow = config.getboolean('Slow', 'active')
enablestop = config.getboolean('Stop', 'active')

# the dll is not always working, if it's not, disable sounds.
sounds = False
sound_player = []
FModSystem = 0
try:
    if platform.architecture()[0] == "64bit":
        sysdir = "stdlib64"
    else:
        sysdir = "stdlib"

    dllfolder = os.path.join(os.path.dirname(__file__), "box", sysdir)
    sys.path.insert(0, dllfolder)
    os.environ['PATH'] = os.environ['PATH'] + ";."

    import traceback
    import ctypes
    import threading

    #
    if platform.architecture()[0] == "64bit":
        ctypes.windll[os.path.join(dllfolder, 'fmodex64.dll')]
    else:
        ctypes.windll[os.path.join(dllfolder, 'fmodex.dll')]
    try:
        from box import box
    except:
        ac.log('BoxApp: error loading box module: ' + traceback.format_exc())
        importError = True
    try:
        from box import sim_info
    except:
        ac.log('BoxApp: error loading sim_info module: ' + traceback.format_exc())
        importError = True

    try:
        from box import win32con
    except:
        ac.log('BoxApp: error loading win32con module: ' + traceback.format_exc())
        importError = True
    # import pyfmodex

    # import winsound
    sounds = True
except ImportError as e:
    ac.log("[Spotter] Import Error: {} {}".format(e, dllfolder))

# UI identifiers
labelv = 0  # the main text label
labelw = 0  # the debug text label
labeldesc = 0  # the description of each spinner label
settingslabel = 0
langspinner = 0
langlabel = 0
langlist = 0  # the list of language options
audiolabel = 0
audiospinner = 0
audiolist = 0  # the list of audio options
audiovolumespinner = 0
spotter = 0  # the app
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

maxcars = 64  # I'm skeptical but there seems to be no way to pull the actual total atm
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
segments = 1000.0  # number of sectors to divide the track into for determining slow cars.
segdata = [0]
segstarted = 0  # overall control for when to start writing seg speeds.
prevseg = 0  # track where the player used to be

i18n = []
counter = 0


class Vec3f(tuple):
    """This supports the useful set of 3d stuff. add, subtract, normalize, dot/cross.
  """

    def __new__(cls, args):
        assert len(args) == 3, "Tried to produce a Vec3 with non-3 arguments {}".format(args)
        return super(Vec3f, cls).__new__(cls, args)

    def __add__(self, other):
        assert isinstance(other, Vec3f), "Attempted to add non-Vec3 {} to Vec3 {}".format(other, self)
        return Vec3f(list((s + o for s, o in zip(self, other))))

    def __sub__(self, other):
        assert isinstance(other, Vec3f), "Attempted to subtract non-Vec3 {} from Vec3 {}".format(other, self)
        return Vec3f(list((s - o for s, o in zip(self, other))))

    def __mul__(s, o):
        assert isinstance(o, Vec3f), "Attempted to cross non-Vec3 {} with Vec3 {}".format(o, s)
        # I know this isn't pretty
        return Vec3f([s[1] * o[2] - s[2] * o[1], s[2] * o[0] - s[0] * o[2], s[0] * o[1] - s[1] * o[0]])

    def __rmul__(self, other):
        # assert isinstance(other,float), "Attempted to multiply non-float {} with Vec3 {}".format(other,self)
        return Vec3f(list(other * s for s in self))

    def dot(self, other):
        assert isinstance(other, Vec3f), "Attempted to dot non-Vec3 {} with Vec3 {}".format(other, self)
        return sum(s * o for s, o in zip(self, other))

    def length(self):
        return self.dot(self) ** 0.5

    def norm(self):
        if self.length() > 0:
            return 1 / self.length() * self
        else:
            return Vec3f([1.0, 0.0, 0.0])  # doesn't really mean anything to norm a 0 vector though.

    def distance(self, other):
        assert isinstance(other, Vec3f), "Attempted to find distance between non-Vec3 {} with Vec3 {}".format(other,
                                                                                                              self)
        return (other - self).length()


class SoundPlayer(object):
    def __init__(self, filename, player):
        self.filename = filename
        self._play_event = Event()
        self.player = player
        self.playbackpos = [0.0, 0.0, 0.0]
        self.playbackvol = 1.0
        self.EQ = []
        self.initEq()
        self.sound_mode = pyfmodex.constants.FMOD_2D
        self.speaker_mix = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        for i in self.EQ:
            self.player.add_dsp(i)
        self.channel = self.player.get_channel(0)
        self.queue = []
        self.thread = Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def initEq(self):
        freq = [16.0, 31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0]
        for i in freq:
            dsp = self.player.create_dsp_by_type(pyfmodex.constants.FMOD_DSP_TYPE_PARAMEQ)
            dsp.set_param(pyfmodex.constants.FMOD_DSP_PARAMEQ_GAIN, 1.0)
            dsp.set_param(pyfmodex.constants.FMOD_DSP_PARAMEQ_BANDWIDTH, 1.0)
            dsp.set_param(pyfmodex.constants.FMOD_DSP_PARAMEQ_CENTER, i)
            self.EQ.append(dsp)

    def set_volume(self, volume):
        self.playbackvol = volume

    def set_sound_mode(self, sound_mode):
        self.sound_mode = sound_mode

    def set_position(self, position):
        self.playbackpos = position

    def set_gain(self, gain):
        if self.sound_mode == pyfmodex.constants.FMOD_3D:
            for i in self.EQ:
                i.set_param(pyfmodex.constants.FMOD_DSP_PARAMEQ_GAIN, gain)
        elif self.sound_mode == pyfmodex.constants.FMOD_2D:
            volume = gain
            self.speaker_mix = [volume, volume, volume, 1.0, volume, volume, volume, volume]

    def stop(self):
        while self.queue:
            self.queue.pop()

    def queueSong(self, filename=None):
        if filename is not None:
            if os.path.isfile(filename):
                sound = self.player.create_sound(bytes(filename, encoding='utf-8'), self.sound_mode)
                self.queue.append({'sound': sound, 'mode': self.sound_mode})
                state = self._play_event.is_set()
                if state == False:
                    self._play_event.set()
            else:
                ac.log('[Spotter]File not found : %s' % filename)

    def _worker(self):
        while True:
            self._play_event.wait()
            queue_len = len(self.queue)
            while queue_len > 0:
                self.player.play_sound(self.queue[0]['sound'], False, 0)
                if self.sound_mode == pyfmodex.constants.FMOD_3D and self.queue[0][
                    'mode'] == pyfmodex.constants.FMOD_3D:
                    self.channel.position = self.playbackpos
                elif self.sound_mode == pyfmodex.constants.FMOD_2D and self.queue[0][
                    'mode'] == pyfmodex.constants.FMOD_2D:
                    self.channel.spectrum_mix = self.speaker_mix
                self.channel.volume = self.playbackvol
                self.player.update()
                while self.channel.is_playing == 1:
                    time.sleep(0.1)
                self.queue[0]['sound'].release()
                self.queue.pop(0)
                queue_len = len(self.queue)
            self._play_event.clear()


class oldSoundPlayer(object):
    def __init__(self, filename, sounds):
        self.filename = filename
        self._play_event = Event()
        self.sounds = sounds
        if sounds:
            self.thread = Thread(target=self._worker)
            self.thread.daemon = True
            self.thread.start()

    def play(self, filename=None):
        if self.sounds:
            if filename is not None:
                self.filename = filename
            self._play_event.set()

    def stop(self):
        if self.sounds:
            self._play_event.clear()

    def _worker(self):
        while True:
            self._play_event.wait()
            winsound.PlaySound(self.filename, winsound.SND_FILENAME)


class Driver:
    'Represents one driver in the current race.'

    def __init__(self, index):
        self.index = index
        # self.name = ac.getDriverName(self.index)
        self.velocity = Vec3f(ac.getCarState(self.index, acsys.CS.Velocity))
        self.position = Vec3f(ac.getCarState(self.index, acsys.CS.WorldPosition))
        self.splinepos = ac.getCarState(self.index, acsys.CS.NormalizedSplinePosition)
        self.active = False
        self.sitting = 0.0

    def update(self, deltaT):
        self.oldvelocity = self.velocity
        self.oldposition = self.position
        self.oldsplinepos = self.splinepos
        self.velocity = Vec3f(ac.getCarState(self.index, acsys.CS.Velocity))
        self.position = Vec3f(ac.getCarState(self.index, acsys.CS.WorldPosition))
        self.splinepos = ac.getCarState(self.index, acsys.CS.NormalizedSplinePosition)
        self.segment = Segment.picksegment(self.splinepos)
        self.laptime = ac.getCarState(self.index, acsys.CS.LapTime)
        if deltaT > 0.0:
            self.acceleration = 1 / deltaT * (self.velocity - self.oldvelocity)
        if self.velocity.length() > 0.5:
            self.sitting = 0.0
            if not self.active:
                self.active = True
        else:
            self.sitting = self.sitting + deltaT
        if self.sitting > ignorestoppedcars:
            self.active = False

    def relativepos(self, driver):
        # first construct some axes
        up = Vec3f((0.0, 1.0, 0.0))
        forward = self.velocity.norm()
        right = forward * up
        # now produce a better up that makes the biz orthogonal.
        up = right * forward
        other = driver.position - self.position
        return [other.dot(right), other.dot(up), other.dot(forward)]

    def splinegap(self, driver):
        # really the only special case necessary is "are they on the +1 lap"
        diff = driver.splinepos - self.splinepos
        # but we can handle that as "are they more than 0.5 of a lap away"
        if diff > 0.5:
            diff = diff - 1.0
        if diff < -0.5:
            diff = diff + 1.0
        return diff


class Segment:
    def __init__(self, start, length, nseg):
        self.start = start
        self.length = length
        self.end = start + length
        self.nseg = nseg
        self.velocity = Vec3f((0.0, 0.0, 0.0))
        self.position = Vec3f((0.0, 0.0, 0.0))
        if start < 0.95:
            self.laptime = 1.0
        else:
            self.laptime = 600000.0

    def update(self, driver):
        # just check that the update is for this segment
        if self.start < driver.splinepos and self.end > driver.splinepos:
            self.velocity = driver.velocity
            self.position = driver.position
            self.laptime = driver.laptime

    # helpful function that doesn't really need to be associated with any specific segment.
    def picksegment(spline):
        global segments
        return int(spline * segments)

    # forward gap in time - always assume this should be the lower segment #.
    def timegap(self, segment):
        if self.start < segment.start:  # straightforward
            return segment.laptime - self.laptime
        else:
            return segment.laptime + segdata[self.nseg - 1].laptime - self.laptime

    # offset of driver from the player's line
    def offset(self, driver):
        up = Vec3f((0.0, 1.0, 0.0))
        forward = driver.velocity.norm()
        return (driver.position - self.position).dot(forward * up)


def tuplef(t):
    return ", ".join("{:4.1f}".format(i) for i in t)


def sidebyside(player, drivers, deltaT):
    global sbsdisplay, sbsright, sbsleft, sbsstring, counter
    if sbsdisplay > 0.0:
        sbsdisplay = sbsdisplay - deltaT
    else:
        sbsstring = i18n.CAR_NONE
        sbsdisplay = -1.0
    sbsright = False
    sbsleft = False
    counter = 100000.0
    if (player.velocity).length() > 1.0:  # doesn't work motionless
        for d in drivers:
            if d.index != player:  # don't compare to yourself
                r = player.relativepos(d)
                # set counter to closest driver sideways
                if abs(r[2]) < carlength / 1000.0:
                    if abs(r[0]) < counter:
                        counter = abs(r[0])
                # ac.setText(labelv,"Driver {} is {} away.".format(d.name, tuplef(r)))
                if abs(r[2]) < carlength / 1000.0 and abs(r[0]) < scanwidth / 1000.0:
                    sidebyside = messageexpiry / 10.0
                    if r[0] > 0.0:
                        sbsright = True
                    else:
                        sbsleft = True
    if sbsright:
        if sbsleft:
            sbsstring = i18n.CAR_BOTH
        else:
            sbsstring = i18n.CAR_RIGHT
    else:
        if sbsleft:
            sbsstring = i18n.CAR_LEFT
    # return true if car's side by side, false otherwise
    # note the app isn't really using this...
    if sbsstring == i18n.CAR_NONE:
        return False
    else:
        return True


# function that handles logic of updating driver pace segments.
def segmentupdate(driver):
    global segstarted, prevseg
    if segstarted == 0:
        if driver.splinepos > 0.0 and driver.splinepos < 0.1:  # enough time to get up to pace
            segstarted = 1
    elif segstarted == 1:
        if driver.splinepos > 0.1:
            segstarted = 2
    else:  # the actual function
        spline = driver.splinepos
        nextseg = Segment.picksegment(spline)
        if prevseg != nextseg:  # we've just entered a new segment.
            segdata[nextseg].update(driver)
            prevseg = nextseg
    return True


def spotter_stopped(player, drivers, deltaT):
    global stopdisplay, stopstring
    # tell if any drivers coming up are stopped.
    if stopdisplay > 0.0:
        stopdisplay = stopdisplay - deltaT
    else:
        stopdisplay = -1.0
        stopstring = i18n.STOPPED_NONE
    if segstarted >= 1 and (player.velocity.length() > float(
            config['Stop']['speed'])):  # know if the player's started driving. avoids grid spam.
        for d in drivers:
            if d.velocity.length() < float(config['Stop']['speed']):  # if the player's not moving
                if segdata[player.segment].timegap(segdata[d.segment]) < scanrange:
                    relativeloc = segdata[d.segment].offset(d)
                    if abs(relativeloc) < scanwidth / 1000.0:
                        stopdisplay = messageexpiry / 10.0
                        if relativeloc < -carahead / 1000.0:
                            stopstring = i18n.STOPPED_LEFT
                        elif relativeloc > carahead / 1000.0:
                            stopstring = i18n.STOPPED_RIGHT
                        else:
                            stopstring = i18n.STOPPED
    if stopstring == "":
        return False
    else:
        return True


def spotter_slow(player, drivers, deltaT):
    global slowdisplay, slowstring
    # tell if any drivers coming up are stopped.
    if slowdisplay > 0.0:
        slowdisplay = slowdisplay - deltaT
    else:
        slowdisplay = -1.0
        slowstring = i18n.SLOW_NONE
    if segstarted >= 1 and (
        player.velocity.length() > float(config['Stop']['speed'])):  # know if the player's started driving.
        for d in drivers:
            if d.velocity.length() < 0.01 * float(slowratio) * segdata[
                d.segment].velocity.length():  # if the driver's going slow
                scan_comp = 1.0 - 0.75 * d.velocity.length() / segdata[
                    d.segment].velocity.length()  # and is ahead of the player
                if segdata[player.segment].timegap(segdata[d.segment]) < scan_comp * scanrange:
                    relativeloc = segdata[d.segment].offset(d)
                    # relative is in metres, positive if right of the line
                    if abs(relativeloc) < scanwidth / 1000.0:
                        slowdisplay = messageexpiry / 10.0
                        if relativeloc < -carahead / 1000.0:
                            slowstring = i18n.SLOW_LEFT
                        elif relativeloc > carahead / 1000.0:
                            slowstring = i18n.SLOW_RIGHT
                        else:
                            slowstring = i18n.SLOW
    if slowstring == "":
        return False
    else:
        return True


def acMain(ac_version):
    global labelv, labelw, settingslabel, audiospinner, audiolabel, audiolist, audiovolumespinner
    global fontspinner, apptitlecheck, appshowcheck, langspinner, langlabel
    global langlist, spotter, drivers, maxcars, player, segdata, segments
    global FModSystem, sound_player, showsettings, slowratiospinner, stopspeedspinner
    global carlengthspinner, scanwidthspinner, i18n, labeldesc
    global caraheadspinner, scanlimitspinner, scanrangespinner
    global sbscheck, slowcheck, stopcheck

    ac.log("[Spotter] Starting.")
    spotter = ac.newApp("Spotter")
    ac.setTitle(spotter, "Spotter - click to hide settings")
    labelv = ac.addLabel(spotter, "---")
    labelw = ac.addLabel(spotter, "")  # "{}".format(config['Display']['showtitle']))
    labeldesc = ac.addLabel(spotter, "Button Description")
    settingslabel = ac.addLabel(spotter, "settings")
    ac.addOnClickedListener(settingslabel, onSettingsClick86)

    langspinner = ac.addSpinner(spotter, "Text")
    langlabel = ac.addLabel(spotter, "{}".format(language))

    audiospinner = ac.addSpinner(spotter, "Audio")
    audiolabel = ac.addLabel(spotter, "{}".format(audio))
    audiovolumespinner = ac.addSpinner(spotter, "Volume")

    apptitlecheck = ac.addCheckBox(spotter, "Display app title")
    appshowcheck = ac.addCheckBox(spotter, "Show settings at startup")

    sbscheck = ac.addCheckBox(spotter, "Send proximity notices")
    slowcheck = ac.addCheckBox(spotter, "Send slow car notices")
    stopcheck = ac.addCheckBox(spotter, "Send stopped car notices")

    fontspinner = ac.addSpinner(spotter, "Font Size")
    slowratiospinner = ac.addSpinner(spotter, "'Slow' Percent")
    caraheadspinner = ac.addSpinner(spotter, "Lane Width")
    scanlimitspinner = ac.addSpinner(spotter, "Scan Distance")
    scanrangespinner = ac.addSpinner(spotter, "Scan Time")

    stopspeedspinner = ac.addSpinner(spotter, "'Stop' Max Speed")
    carlengthspinner = ac.addSpinner(spotter, "Car Length")
    scanwidthspinner = ac.addSpinner(spotter, "Track Width")

    ac.setSize(spotter, 600, 330)
    ac.setPosition(labelv, 200, -100)
    ac.setFontAlignment(labelv, "center")
    ac.setFontSize(labelv, fontsize)
    ac.setFontColor(labelv, *textcolour)
    ac.setPosition(labelw, 600, 0)

    ac.setPosition(labeldesc, 400, 50)
    ac.setSize(labeldesc, 200, 600)

    ac.setSize(settingslabel, 250, 40)
    ac.setPosition(settingslabel, 175, 0)
    ac.setText(settingslabel, "")

    # first column of settings
    ac.setPosition(langlabel, 100, 50)
    ac.setPosition(langspinner, 10, 50)
    ac.setSize(langspinner, 80, 20)

    ac.setPosition(audiolabel, 100, 90)
    ac.setPosition(audiospinner, 10, 90)
    ac.setSize(audiospinner, 80, 20)

    ac.setPosition(fontspinner, 10, 130)
    ac.setSize(fontspinner, 80, 20)
    ac.setRange(fontspinner, 8, 64)
    ac.setStep(fontspinner, 4)
    ac.setValue(fontspinner, fontsize)

    '''The following are equivalent:
  ac.setPosition(slowratiospinner, 10, 170)
  ac.setSize(slowratiospinner, 80, 20)
  ac.setRange(slowratiospinner, 0, 100)
  ac.setStep(slowratiospinner, 5)
  ac.setValue(slowratiospinner, slowratio)
  ac.addOnValueChangeListener(slowratiospinner, onSlowRatioSpin)'''
    spinnerConfig(slowratiospinner, 10, 250, 80, 20, 0, 5, 100, slowratio, onSlowRatioSpin)
    spinnerConfig(caraheadspinner, 110, 250, 80, 20, 0, 200, 3000, carahead, onCarAheadSpin)
    spinnerConfig(scanlimitspinner, 10, 290, 80, 20, 0, 1, 50, scanlimit, onScanLimitSpin)
    spinnerConfig(scanrangespinner, 110, 290, 80, 20, 0, 500, 20000, scanrange, onScanRangeSpin)
    spinnerConfig(audiovolumespinner, 110, 130, 80, 20, 0, 5, 100, audio_volume, onAudioVolumeSpin)
    ac.setPosition(slowcheck, 200, 250)
    ac.setValue(slowcheck, enableslow)

    spinnerConfig(stopspeedspinner, 10, 170, 80, 20, 0, 2, 20, int(config['Stop']['speed']), onStopSpeedSpin)
    ac.setPosition(stopcheck, 200, 170)
    ac.setValue(stopcheck, enablestop)

    spinnerConfig(carlengthspinner, 10, 210, 80, 20, 1000, 100, 10000, carlength, onCarLengthSpin)
    spinnerConfig(scanwidthspinner, 110, 210, 80, 20, 1000, 500, 20000, scanwidth, onScanWidthSpin)
    ac.setPosition(sbscheck, 200, 210)
    ac.setValue(sbscheck, enablesbs)

    # second column of settings
    ac.setPosition(apptitlecheck, 200, 50)
    ac.setValue(apptitlecheck, int(config['Display']['showtitle']))
    onTitleCheck(apptitlecheck, int(config['Display']['showtitle']))
    ac.setPosition(appshowcheck, 200, 90)
    ac.setValue(appshowcheck, int(config['Display']['showatstart']))
    # when you call the SettingsClick it toggles, so start out opposed.
    showsettings = 1 - int(config['Display']['showatstart'])
    onSettingsClick86()

    ac.addRenderCallback(spotter, onFormRender)
    ac.addOnAppDismissedListener(spotter, shutdownSpotter)
    ac.addOnValueChangeListener(langspinner, onLangSpin)
    ac.addOnValueChangeListener(audiospinner, onAudioSpin)
    ac.addOnValueChangeListener(fontspinner, onFontSpin)
    ac.addOnCheckBoxChanged(apptitlecheck, onTitleCheck)
    ac.addOnCheckBoxChanged(appshowcheck, onShowCheck)
    ac.addOnCheckBoxChanged(sbscheck, onSbsCheck)
    ac.addOnCheckBoxChanged(slowcheck, onSlowCheck)
    ac.addOnCheckBoxChanged(stopcheck, onStopCheck)
    playerspline = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
    for i in range(maxcars):
        if ac.getTrackName(i) != -1:
            ac.log("[Spotter] Found driver {} on track: {}".format(i, ac.getTrackName(i)))
            drivers = drivers + [Driver(i)]
        if i == 0:
            player = len(drivers) - 1
    # figure out the segments based on the count.
    segdata = [Segment(i / segments, 1.0 / segments, int(segments)) for i in range(int(segments))]
    ac.log("[Spotter] Initiated.")
    ''' # old sound importing code.
  sound_player = SoundPlayer(os.path.join(os.path.dirname(__file__), "audio\\car_on_right.wav"), sounds)
  if sounds:
    ac.log("Sounds successfully loaded.")
  else:
    ac.log("No sounds loaded.")
  '''
    # new fmod importing code
    FModSystem = pyfmodex.System()
    FModSystem.init()
    # This breaks the sound
    # peakermode = FModSystem.get_driver_caps(0)
    # FModSystem.speaker_mode = speakermode.mode
    # FModSystem.init(100,pyfmodex.constants.FMOD_INIT_3D_RIGHTHANDED)
    sound_player = SoundPlayer(os.path.join(os.path.dirname(__file__), "audio\\Wattie\\car_on_right.wav"), FModSystem)

    ac.log("[Spotter] sound_player load car_on_right")

    sound_player.set_volume(audio_volume / 100.0)
    sound_player.set_gain(2.0)
    # sound_player.set_sound_mode(pyfmodex.constants.FMOD_2D)


    ac.log("[Spotter] Inicializando i18n")
    i18n = i18strings(language, sound_player, audio)
    # this actually selects from the range of input lanugages.  Yay spinner.
    langlist = os.listdir(os.path.join(os.path.dirname(__file__), "text"))
    ac.setRange(langspinner, 0, len(langlist) - 1)
    ac.setStep(langspinner, 1)
    ac.setValue(langspinner, langlist.index(language))
    # likewise for audio
    audiolist = os.listdir(os.path.join(os.path.dirname(__file__), "audio"))
    ac.setRange(audiospinner, 0, len(audiolist) - 1)
    ac.setStep(audiospinner, 1)
    ac.setValue(audiospinner, audiolist.index(audio))
    ac.log("[Spotter] Internationalization loaded.")
    return "Spotter v1.2.1"


def acShutdown(*args):
    shutdownSpotter()


def onFormRender(deltaT):
    global labelv, spotter, drivers, player, showsettings, sbsstring, stopstring, slowstring
    if not showsettings:
        ac.setBackgroundOpacity(spotter, 0)
        ac.drawBorder(spotter, 0)
    '''
  # print debug info
  debugstr = "Segment: {} (previously{})\n".format(Segment.picksegment(drivers[player].splinepos),prevseg)
  debugstr = debugstr + "Segstate: {}\n".format(segstarted)
  debugstr = debugstr + "Previous laptime: {}\n".format(segdata[Segment.picksegment(drivers[player].splinepos)].laptime)
  #debugstr = debugstr + "Next to +10 segment gap: {}\n".format(segdata[(drivers[player].segment+1)%int(segments)].timegap(segdata[(drivers[player].segment+10)%int(segments)]))
  debugstr = debugstr + "Sound queue len: {}  Volume: {}\n".format(len(sound_player.queue), sound_player.playbackvol)

  activedrivers = sum(d.active for d in drivers)
  debugstr = debugstr + "# of nearby drivers: {}. # active drivers: {}\n".format(len(neardrivers), activedrivers)
  #debugstr = debugstr + "% of segment speed: {:4.1f}\n".format(100.0*drivers[player].velocity.length()/segdata[drivers[player].segment].velocity.length())
  debugstr = debugstr + "Sidebyside Distance: {}\n".format(counter)
  ac.setText(labelw, debugstr)'''


def acUpdate(deltaT):
    # acUpdate is where the actual calls should live, as Oculus doesn't use formRender.
    global labelv, spotter, drivers, player, showsettings, sbsstring, stopstring, slowstring
    for d in drivers:
        d.update(deltaT)
    segmentupdate(drivers[player])
    neardrivers = []
    for d in drivers:
        if d.index != player:  # don't really want ourself in that list
            if abs(drivers[player].splinegap(d)) < scanlimit / 100.0 and d.active:
                neardrivers = neardrivers + [d]
    # function looking for cars to the left or right
    if enablesbs:
        sidebyside(drivers[player], neardrivers, deltaT)
    else:
        sbsstring = i18n.CAR_NONE
    # function looking for stopped cars ahead
    if enablestop:
        spotter_stopped(drivers[player], neardrivers, deltaT)
    else:
        stopstring = i18n.STOPPED_NONE
    # function looking for slow cars ahead
    if enableslow:
        spotter_slow(drivers[player], neardrivers, deltaT)
    else:
        slowstring = i18n.SLOW_NONE

    # priority of display messages can be edited here.
    if not stopstring(labelv):
        if not sbsstring(labelv):
            if not slowstring(labelv):
                i18n.NONE(labelv)


# "HIT Control : Spotter - click to hide settings" is logging ok...
def onSettingsClick86(*args):
    global counter, showsettings
    showsettings = 1 - showsettings
    s = showsettings
    ac.setVisible(labeldesc, s)
    ac.setVisible(langlabel, s)
    ac.setVisible(langspinner, s)
    ac.setVisible(audiolabel, s)
    ac.setVisible(audiospinner, s)
    ac.setVisible(appshowcheck, s)
    ac.setVisible(apptitlecheck, s)
    ac.setVisible(fontspinner, s)
    ac.setVisible(stopspeedspinner, s)
    ac.setVisible(carlengthspinner, s)
    ac.setVisible(scanwidthspinner, s)
    ac.setVisible(slowratiospinner, s)
    ac.setVisible(caraheadspinner, s)
    ac.setVisible(scanlimitspinner, s)
    ac.setVisible(scanrangespinner, s)
    ac.setVisible(sbscheck, s)
    ac.setVisible(slowcheck, s)
    ac.setVisible(stopcheck, s)
    ac.setVisible(audiovolumespinner, s)
    if s:  # and some stuff that's not as straightforward
        ac.setTitle(spotter, "Spotter - click to hide settings")
        ac.setIconPosition(spotter, 0, 0)
        ac.setSize(spotter, 600, 330)
    else:
        ac.setTitle(spotter, apptitle)
        ac.setIconPosition(spotter, 0, -9000)
        ac.setSize(spotter, 600, 30)


def shutdownSpotter():
    # this function is called when the app is dismissed or the session ends
    config.write(open(configfile, 'w'))


def spinnerConfig(spinner, x, y, xl, yl, min, step, max, value, evt):
    ac.setPosition(spinner, x, y)
    ac.setSize(spinner, xl, yl)
    ac.setRange(spinner, min, max)
    ac.setStep(spinner, step)
    ac.setValue(spinner, value)
    ac.addOnValueChangeListener(spinner, evt)


def setHighlight(item):
    global uihighlight
    # dehighlight the old one
    ac.setBackgroundColor(uihighlight, 0.5, 0.5, 0.5)
    # ac.drawBackground(uihighlight, 0)
    # set the new one
    uihighlight = item
    ac.setBackgroundColor(uihighlight, 1, 0, 0)
    # ac.drawBackground(uihighlight, 1)


def setDescription(item, text):
    ac.setText(labeldesc, text)
    setHighlight(item)


def onLangSpin(value):
    global langlist, langlabel, config, i18n
    ac.setText(langlabel, langlist[value])
    config['Text']['source'] = str(langlist[value])
    i18n.setlanguage("{}".format(langlist[value]))
    setDescription(langspinner, '''
  Select the text that you'd like
  to see on the display.  Refers
  to a file in the app's /text/
  directory.''')


def onAudioSpin(value):
    global audiolist, audiolabel, config, i18n
    ac.setText(audiolabel, audiolist[value])
    config['Audio']['source'] = str(audiolist[value])
    i18n.setaudio("{}".format(audiolist[value]))
    setDescription(audiospinner, '''
  Select the audio set that you
  would like to use.
  This refers to a folder in the
  app's /audio/ directory.''')


# failed attempt to be clever and do a closure - seems to crash acs.exe
def spinnerListenBuilder(spinner, variablegroup, variablename):
    def spinnerListener(value):
        config[variablegroup][variablename] = str(value)
        setDescription(spinner, description[variablegroup][variablename])

    return spinnerListener


def onFontSpin(value):
    global fontsize
    fontsize = value
    ac.setFontSize(labelv, fontsize)
    config['Display']['fontsize'] = str(value)


def onStopSpeedSpin(value):
    global stopspeed
    stopspeed = value
    config['Stop']['speed'] = str(value)
    setDescription(stopspeedspinner, '''
  Maximum speed in meters
  per second where a car
  is considered "stopped".''')


def onCarLengthSpin(value):
    global carlength
    carlength = value
    config['Proximity']['length'] = str(value)
    setDescription(carlengthspinner, '''
  Length in millimetres of the
  player's car.  Used to
  determine when another
  vehicle is next to you.''')


def onScanWidthSpin(value):
    global scanwidth
    scanwidth = value
    config['Proximity']['width'] = str(value)
    setDescription(scanwidthspinner, '''
  Distance on either side
  of the player's car to
  check for other vehicles,
  in millimetres.''')


def onSlowRatioSpin(value):
    global slowratio
    slowratio = value
    config['Slow']['ratio'] = str(value)
    setDescription(slowratiospinner, '''
  What percent of your speed
  another vehicle should be
  travelling to generate a
  'Slow car' warning.''')


def onCarAheadSpin(value):
    global carahead
    carahead = value
    config['Slow']['linewidth'] = str(value)
    setDescription(caraheadspinner, '''
  Width of the 'racing line'
  where the app will consider
  a slow car to be 'ahead' of
  you instead of to the left
  or right, in millimetres.''')


def onScanLimitSpin(value):
    global scanlimit
    scanlimit = value
    config['Slow']['scandistance'] = str(value)
    setDescription(scanlimitspinner, '''
  Percent of the track to scan
  for other drivers.  Anyone
  farther away will be ignored.''')


def onScanRangeSpin(value):
    global scanrange
    scanrange = value
    config['Slow']['scantime'] = str(value)
    setDescription(scanrangespinner, '''
  Maximum time ahead, in
  milliseconds, to warn you
  about a hazard.
  For a stopped driver this
  is simply how long it will
  take you to reach them at
  your current pace.''')


def onAudioVolumeSpin(value):
    global audio_volume
    audio_volume = value
    sound_player.set_volume(value / 100.0)
    config['Audio']['volume'] = str(value)
    setDescription(audiovolumespinner, '''
  Set the overall volume of
  the app.''')


def onTitleCheck(label, value):
    global apptitle, config
    config['Display']['showtitle'] = str(value)
    if value == 1:
        apptitle = "Spotter"
    else:
        apptitle = ""


def onShowCheck(label, value):
    global config
    config['Display']['showatstart'] = str(value)


def onSbsCheck(label, value):
    global enablesbs
    enablesbs = value
    config['Proximity']['active'] = str(value)


def onSlowCheck(label, value):
    global enableslow
    enableslow = value
    config['Slow']['active'] = str(value)


def onStopCheck(label, value):
    global enablestop
    enablestop = value
    config['Stop']['active'] = str(value)
