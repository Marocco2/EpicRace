# BOX v0.1.3

BOX is an Assetto Corsa framework created by Marco 'Marocco2' Mollace. It's created for Assetto Corsa developers who want a set of features without spending so much time.

## WARNING!!!!

### **This is an unstable SDK, so functions can be deprecated very soon. Check changelog or wiki what is changed**

### CURRENT FEATURES

- A push notification system via Telegram bot
- An auto-update/auto-install system `(WORK IN PROGRESS)`

### PLANNED FEATURES

- Voice commands
- Audio system

## IMPLEMENTATION

Your app must have the following structure:

![Files](http://i.imgur.com/rofq8St.png)

In your app python (in this example `BoxApp.py`) you need to add these lines:

    ...
    
    import sys
    import os
    import platform
    
    if platform.architecture()[0] == "64bit":
        sysdir = "stdlib64"
    else:
        sysdir = "stdlib"
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "box", sysdir))
    os.environ['PATH'] = os.environ['PATH'] + ";."
    
    ...
        
    import traceback
    import ctypes
    import threading
    
    importError = False
    
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
        
    ...

## CHANGELOG

### v0.1.3

- first attempt to make newupdate() work

### v0.1.2

- reworked functions (check Wiki page)

### v0.1.1

- added getZipFile function