#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gi, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def enabled():
    """Checking 'is root' and OS for access to settings"""
    return (os.getuid() == 0) and (os.path.exists("/etc/altlinux-release"))

def check_wm():
    """Checking window manager"""
    for wm in ("marco", "openbox"):
        if int(os.popen("which %s > /dev/null 2> /dev/null; echo $?" % wm).read()) == 0: return wm
    return None

class Config():
    __file_cfg = "/etc/connector/kiosk.conf"
    def __init__(self):
        self.params = {'mode': '0',
                       'user': '_kiosk',
                       'file': '<path_to_file_ctor>',
                       'url': '<url_for_kiosk>'}
        self.read()

    def read(self):
        try:
            with open(self.__file_cfg) as file_cfg:
                for line in file_cfg:
                    param_cfg = line.split('=')
                    try: self.params[param_cfg[0].strip()] = param_cfg[1].strip()
                    except: pass
        except FileNotFoundError: self.write()

    def write(self):
        os.system("sed -i '/^#/!d' %s" % self.__file_cfg)
        with open(self.__file_cfg, "a") as file_cfg:
            for key in self.params:
                print("%s = %s" % (key, self.params[key]), file = file_cfg)

class Kiosk(Gtk.Window):
    def __init__(self):
        """Window with settings of the mode KIOSK"""
        Gtk.Window.__init__(self, title = "Параметры режима \"КИОСК\"")
        builder = Gtk.Builder()
        builder.add_from_file("kiosk/kiosk.ui")
        builder.connect_signals(self)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_default_icon_name("connector")
        self.changeKioskOff = builder.get_object("radio_kiosk_off")
        self.changeKioskAll = builder.get_object("radio_kiosk_all")
        self.changeKioskCtor = builder.get_object("radio_kiosk_ctor")
        self.entryKioskCtor = builder.get_object("entry_kiosk_ctor")
        self.changeKioskWeb = builder.get_object("radio_kiosk_web")
        self.entryKioskWeb = builder.get_object("entry_kiosk_web")
        box = builder.get_object("box")
        self.add(box)
        self.connect("delete-event", self.onClose)
        self.show_all()
        self.config = Config()
        self.initParams()

    def onClose (self, window, *args):
        """Close window"""
        window.destroy()

    def entryOn(self, widget):
        """Enable widget sensitivity"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.ON)
        except: widget.set_sensitive(True)

    def entryOff(self, widget):
        """Disable widget sensitivity"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.OFF)
        except: widget.set_sensitive(False)

    def onSave (self, *args):
        """Action for button 'Save'"""
        mode = 0; file = ''; url = ''
        if self.changeKioskOff.get_active(): mode = 0
        if self.changeKioskAll.get_active(): mode = 1
        if self.changeKioskCtor.get_active():
            mode = 2
            file = self.entryKioskCtor.get_uri().replace("file://","")
        if self.changeKioskWeb.get_active():
            mode = 3
            url = self.entryKioskWeb.get_text()
        self.config.params['mode']  = mode
        self.config.params['file']  = file
        self.config.params['url']  = url
        self.config.write()
        #else need disable tray...
        self.onClose()

    def initParams (self):
        mode = int(self.config.params['mode'])
        self.entryKioskCtor.set_current_folder("/etc/kiosk")
        if mode == 1: self.changeKioskAll.set_active(True)
        elif mode == 2:
            self.changeKioskCtor.set_active(True)
            self.entryKioskCtor.set_uri("file://%s" % self.config.params['file'])
        elif mode == 3:
            self.changeKioskWeb.set_active(True)
            self.entryKioskWeb.set_text(self.config.params['url'])
        else:
            self.changeKioskOff.set_active(True)

    def onReset (self, *args):
        """Action for button 'Reset'"""
        self.entryKioskCtor.set_uri('')
        self.entryKioskWeb.set_text('')
        self.initParams()

if __name__ == '__main__':
    pass
