from BOX.box_lib import requests
import os
import configparser
import traceback

configfile = os.path.join(os.path.dirname(__file__), 'EpicRace.ini')
config = configparser.ConfigParser()
config.read(configfile)

def log(log):
    prelog = ('update: ' + str(log))
    with open("apps\\python\\EpicRace\\log.txt", 'w') as h:
        h.write(prelog)
        h.close()

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
            get_file(download_link_epicrace, "EpicRace.py")
            get_file(download_link_ini, "EpicRace.ini")
            get_file(download_link_update, "update.py")
            update_status = 0  # ok
            log(update_status)
            return update_status
        else:
            # "No new update"
            update_status = 2
            log(update_status)
            return update_status
    except:
        log(traceback.format_exc())
        update_status = 3
        return update_status


def get_file(link, file):
    f = requests.get(link)
    with open(file, 'w') as j:
        j.write(f.text)
        j.close()
