#
#
#    BBBBBBBBBBBBBBBBB        OOOOOOOOO     XXXXXXX       XXXXXXX
#    B::::::::::::::::B     OO:::::::::OO   X:::::X       X:::::X
#    B::::::BBBBBB:::::B  OO:::::::::::::OO X:::::X       X:::::X
#    BB:::::B     B:::::BO:::::::OOO:::::::OX::::::X     X::::::X
#      B::::B     B:::::BO::::::O   O::::::OXXX:::::X   X:::::XXX
#      B::::B     B:::::BO:::::O     O:::::O   X:::::X X:::::X
#      B::::BBBBBB:::::B O:::::O     O:::::O    X:::::X:::::X
#      B:::::::::::::BB  O:::::O     O:::::O     X:::::::::X
#      B::::BBBBBB:::::B O:::::O     O:::::O     X:::::::::X
#      B::::B     B:::::BO:::::O     O:::::O    X:::::X:::::X
#      B::::B     B:::::BO:::::O     O:::::O   X:::::X X:::::X
#      B::::B     B:::::BO::::::O   O::::::OXXX:::::X   X:::::XXX
#    BB:::::BBBBBB::::::BO:::::::OOO:::::::OX::::::X     X::::::X
#    B:::::::::::::::::B  OO:::::::::::::OO X:::::X       X:::::X
#    B::::::::::::::::B     OO:::::::::OO   X:::::X       X:::::X
#    BBBBBBBBBBBBBBBBB        OOOOOOOOO     XXXXXXX       XXXXXXX
#
#
# Assetto Corsa framework created by Marco 'Marocco2' Mollace
#
# version 0.1.3
#
# Usage of this library is under LGPLv3. Be careful :)
#
#

import ac
import traceback
import os
import sys
import platform

try:
    import ctypes
except:
    ac.log('BOX: error loading ctypes: ' + traceback.format_exc())
    raise

# TODO: read from config file for filters | IMPORTS
from os.path import dirname, realpath
# import configparser

import functools
import threading
import zipfile
import time


def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    return wrapper


if platform.architecture()[0] == "64bit":
    dllfolder = "stdlib64"
    dllfolder = os.path.join(os.path.dirname(__file__), dllfolder)
    fmodex = "fmodex64.dll"
else:
    dllfolder = "stdlib"
    dllfolder = os.path.join(os.path.dirname(__file__), dllfolder)
    fmodex = "fmodex.dll"

sys.path.insert(0, dllfolder)
os.environ['PATH'] = os.environ['PATH'] + ";."
ctypes.windll[os.path.join(dllfolder, fmodex)]
box_lib_folder = os.path.join(os.path.dirname(__file__), 'box_lib')
sys.path.insert(0, box_lib_folder)

try:
    import pyfmodex
except Exception as e:
    ac.log('BOX: error loading pyfmodex: ' + traceback.format_exc())
    raise

try:
    import requests
except Exception as e:
    ac.log('BOX: error loading requests: ' + traceback.format_exc())
    raise


# A useful push notification via Telegram if I need send some news
def notification(telegram_bot_oauth):
    try:
        telegram_api_url = "https://api.telegram.org/bot" + telegram_bot_oauth + "/getUpdates"
        r = requests.get(telegram_api_url)
        message = r.json()
        if message["ok"]:
            var_notify = message["result"][-1]["message"]["text"]
            ac.log('BOX: Notification from Telegram: ' + var_notify)
            return var_notify
        else:
            var_notify = "No new messages"
            ac.log('BOX: ' + var_notify)
    except:
        ac.log('BOX: No Internet connection')
        var_notify = ""
        return var_notify


# It downloads a zip file and extract it in a folder
def get_zipfile(download_link, dir_path='', absolute_path=False):
    try:
        local_filename = download_link.split('/')[-1]
        # NOTE the stream=True parameter
        r = requests.get(download_link, stream=True)
        log_getZipFile = "Download of " + local_filename + " completed"
        where_is_zip = os.path.join(os.path.dirname(__file__), local_filename)
        ac.log("BOX: " + log_getZipFile)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush() commented by recommendation from J.F.Sebastian

        ac.log("BOX: " + where_is_zip)
        try:
            with zipfile.ZipFile(local_filename, "r") as z:
                if dir_path == "" and not absolute_path:
                    z.extractall(os.path.dirname(__file__))  # Extracting files
                elif absolute_path:
                    z.extractall(dir_path)  # Extracting files
                else:
                    z.extractall(os.path.join(os.path.dirname(__file__), dir_path))  # Extracting files
            # os.remove(local_filename)
            log_getZipFile = "Files extracted"
            return log_getZipFile
        except:
            log_getZipFile = "Error extracting files"
            return log_getZipFile
    except:
        log_getZipFile = "Error downloading zip file"
        ac.log('BOX: error downloading zip file: ' + traceback.format_exc())
        return log_getZipFile


# A new function to automatize app updates for AC
# WORK IN PROGRESS
# TODO: make reorder files logic
def newupdate(version, check_link, download_link, dir_path=''):
    try:
        r = requests.get(check_link)
        if r.json() != version:  # Check if server version and client version is the same
            update_status = get_zipfile(download_link, dir_path)
            return update_status
        else:
            update_status = "No new update"
            ac.log('BOX: ' + update_status)
            return update_status
    except:
        update_status = "Error checking new update"
        ac.log('BOX: error checking new update: ' + traceback.format_exc())
        return update_status


# Uses GitHub to check updates
# WORK IN PROGRESS
# TODO: make reorder files logic
def github_newupdate(git_repo, branch='master', sha='', dir_path=''):
    try:
        check_link = "https://api.github.com/repos/" + git_repo + "/commits/" + branch
        headers = {'Accept': 'application/vnd.github.VERSION.sha'}
        r = requests.get(check_link, headers=headers)
        if sha == "":
            try:
                with open("apps\\python\\" + git_repo.split('/')[-1] + "\sha.txt", 'r') as g:
                    sha = g.read()
                    g.close()
            except:
                update_status = "No SHA available"
                ac.log('BOX: ' + update_status)
                return update_status
        if r.text != sha:  # Check if server version and client version is the same
            download_link = "https://github.com/" + git_repo + "/archive/" + branch + ".zip"
            update_status = get_zipfile(download_link, dir_path)
            with open("apps\\python\\" + git_repo.split('/')[-1] + "\sha.txt", 'w') as j:
                j.write(r.text)
                j.close()
            return update_status
        else:
            update_status = "No new update"
            ac.log('BOX: ' + update_status)
            return update_status
    except:
        update_status = "Error checking new update"
        ac.log('BOX: error checking new update: ' + traceback.format_exc())
        return update_status


from threading import Thread, Event


class SoundPlayer(object):
    def __init__(self, player):
        self._play_event = Event()
        self.player = player
        self.playbackpos = [0.0, 0.0, 0.0]
        self.playbackvol = 1.0
        self.EQ = []
        self.initEq()
        self.sound_mode = pyfmodex.constants.FMOD_CREATECOMPRESSEDSAMPLE
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

    @async
    def stop(self):
        try:
            self.channel.paused = 1
            # self.queue.pop(0)
        except:
            ac.log('BOX: stop() error ' + traceback.format_exc())

    @async
    def queueSong(self, filename=None):
        try:
            if filename is not None:
                if os.path.isfile(filename):
                    sound = self.player.create_sound(bytes(filename, encoding='utf-8'), self.sound_mode)
                    self.queue.append({'sound': sound, 'mode': self.sound_mode})
                    state = self._play_event.is_set()
                    if state == False:
                        self._play_event.set()
                    return 1  # mp3 loaded
                else:
                    ac.log('BOX: File not found : %s' % filename)
        except:
            ac.log('BOX: queueSong() error ' + traceback.format_exc())

    def lenQueue(self):
        leng = self.queue.__len__()
        return leng

    def _worker(self):
        while True:
            self._play_event.wait()
            queue_len = len(self.queue)
            while queue_len > 0:
                self.player.play_sound(self.queue[0]['sound'], False, 0)
                self.channel.spectrum_mix = self.speaker_mix
                self.channel.volume = self.playbackvol
                self.player.update()
                while self.channel.paused == 0 and self.channel.is_playing == 1:
                    time.sleep(0.1)
                self.queue[0]['sound'].release()
                self.queue.pop(0)
                queue_len = len(self.queue)
            self._play_event.clear()


FModSystem = pyfmodex.System()
