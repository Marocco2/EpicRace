from BOX.box_lib import requests
import os
import configparser
import traceback
import functools
import threading

configfile = os.path.join(os.path.dirname(__file__), 'EpicRace.ini')
config = configparser.ConfigParser()
config.read(configfile)

def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    return wrapper


def log(log):
    prelog = ('update: ' + str(log))
    with open("apps\\python\\EpicRace\\log.txt", 'w') as h:
        h.write(prelog)
        h.close()


#@async
def update():
    with open("apps\\python\\EpicRace\\sha.txt", 'r') as g:
        sha = g.read()
        g.close()

    try:
        branch = config['SETTINGS']['branch']
        check_link = "https://api.github.com/repos/Marocco2/EpicRace/commits/" + branch
        headers = {'Accept': 'application/vnd.github.VERSION.sha'}
        r = requests.get(check_link, headers=headers)
        if r.text != sha:  # Check if server version and client version is the same
            with open("apps\\python\\EpicRace\\sha.txt", 'w') as j:
                j.write(r.text)
                j.close()
            download_link_epicrace = "https://raw.githubusercontent.com/Marocco2/EpicRace/" + branch + "/EpicRace.py"
            download_link_update = "https://raw.githubusercontent.com/Marocco2/EpicRace/" + branch + "/update.py"
            download_link_ini = "https://raw.githubusercontent.com/Marocco2/EpicRace/" + branch + "/EpicRace.ini"
            get_file(download_link_epicrace, "apps\\python\\EpicRace\\EpicRace.py")
            get_file(download_link_ini, "apps\\python\\EpicRace\\EpicRace.ini")
            get_file(download_link_update, "apps\\python\\EpicRace\\update.py")
            update_status = 0  # ok
            log(update_status)
            return update_status
        else:
            # "No new update"
            update_status = 2
            log(update_status)
            return update_status

#@async
def get_file(link, filed):
    f = requests.get(link)
    with open(filed, 'w') as j:
        j.write(f.text)
        j.close()
