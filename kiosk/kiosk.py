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
        self.entryKioskConn = builder.get_object("entry_kiosk_ctor")
        box = builder.get_object("box")
        self.add(box)
        self.connect("delete-event", self.onClose)
        self.show_all()

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
        pass
        #else need disable tray...

if __name__ == '__main__':
    pass
