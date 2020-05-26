#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gi, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import configparser
from urllib.parse import unquote

_kiosk_dir = "/usr/share/connector/kiosk"
_webkiosk = "%s/connector-webkiosk" % _kiosk_dir
_kiosk_conf = "/etc/connector/kiosk.conf"
_config = configparser.ConfigParser( interpolation = None )
_ligthdm_conf = "/etc/lightdm/lightdm.conf"
_lightdm_conf_dir = "%s.d" % _ligthdm_conf
_autologin_conf = "%s/kiosk.conf" % _lightdm_conf_dir
_etc_dir = "/etc/kiosk"
_true = ( "True", "true", "Yes", "yes" )

def enabled():
    """Checking 'is root' and OS for access to settings"""
    return (os.getuid() == 0) and (os.path.exists("/etc/altlinux-release"))

def lightdm_clear_autologin():
    """Disable existing records for autologin-user"""
    clear_cmd = "sed -i \"s/^autologin-user.*/#autologin-user=/\""
    os.system ("%s %s" % (clear_cmd, _ligthdm_conf))
    if os.path.exists (_lightdm_conf_dir): os.system ("%s %s/*.conf" % (clear_cmd, _lightdm_conf_dir))
    if os.path.exists (_autologin_conf): os.remove(_autologin_conf)

def load_kiosk_user():
    """Load username for KIOSK from the config"""
    try: username = _config.get( "kiosk", "user" )
    except: username = "kiosk"
    return username

def autologin_enable(username):
    """Enable autologin for the mode KIOSK"""
    lightdm_clear_autologin()
    with open (_autologin_conf, "w") as f:
        print("[Seat:*]\nautologin-user=%s" % username, file = f)

def create_kiosk_exec(username, shortcut):
    """Create executable file in X11 directory"""
    kiosk_exec = "/etc/X11/xsession.user.d/%s" % username
    with open (kiosk_exec, "w") as f:
        print("""#!/bin/sh
PROFILE=%s
e="$(sed -n s/^Exec[[:space:]]*=[[:space:]]*//p "/etc/kiosk/$PROFILE")"
test -n "$e" && `$e`""" % shortcut, file = f)
    os.chmod(kiosk_exec, 0o755)

def enable_kiosk( mode = "kiosk" ):
    """Exec connector in the mode KIOSK"""
    username = load_kiosk_user()
    if _config['kiosk']['autologin'] == "True":
        autologin_enable( username )
    else:
        lightdm_clear_autologin()
    shortcut = "connector-%s.desktop" % mode
    os.system ("install -m644 %s/%s %s/" % (_kiosk_dir, shortcut, _etc_dir))
    create_kiosk_exec(username, shortcut)

def fix_shortcut(mode, _input, output):
    """Replace variable in the desktop files"""
    shortcut = "%s/connector-%s.desktop" % (_etc_dir, mode)
    os.system ("sed -i \"s|\%s|'%s'|g\" %s" % (_input, output, shortcut))

def enable_kiosk_ctor(_file):
    """Exec connector (with ctor-file) in the mode KIOSK"""
    mode = "kiosk"
    enable_kiosk(mode)
    fix_shortcut(mode, "$CTOR", _file)

def enable_kiosk_web(url):
    """Exec chromium in the mode KIOSK"""
    mode = "webkiosk"
    enable_kiosk(mode)
    fix_shortcut(mode, "$URL", url)

def disable_kiosk():
    lightdm_clear_autologin()
    os.system("rm -f /etc/X11/xsession.user.d/%s" % load_kiosk_user())
    os.system("rm -f %s/connector-*.desktop" % _etc_dir)

def enable_ctrl():
    os.system( "sed -i /^xmodmap/d %s" % _webkiosk )
    os.system( "sed -i /^setxkbmap/d %s" % _webkiosk )

def disable_ctrl():
    enable_ctrl()
    os.system( "sed -i s/while/\"setxkbmap -v -option ctrl:swapcaps\\nxmodmap"
               " -e 'keycode 105 = '\\nxmodmap -e 'keycode 37 = '\\nwhile\"/g %s" % _webkiosk )

def config_init():
    _config["kiosk"] = { 'mode': '0',
                         'user': 'kiosk',
                         'autologin': 'true',
                         'file': '',
                         'url': '',
                         'ctrl_disabled': 'false' }
    with open( _kiosk_conf, 'w' ) as configfile:
        _config.write( configfile )

class Kiosk(Gtk.Window):
    def __init__(self):
        """Window with settings of the mode KIOSK"""
        os.makedirs (_lightdm_conf_dir, exist_ok = True)
        os.makedirs (_etc_dir, exist_ok = True)
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
        self.entryKioskUser = builder.get_object("entry_kiosk_user")
        self.checkKioskCtrl = builder.get_object("check_kiosk_safe")
        self.checkKioskAutologin = builder.get_object("check_kiosk_autologin")
        self.checkKioskAdduser = builder.get_object("check_kiosk_adduser")
        box = builder.get_object("box")
        self.add(box)
        self.connect("delete-event", self.onClose)
        self.show_all()
        result = _config.read( _kiosk_conf )
        if not result: config_init()
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
        mode = "0"; file = ''; url = ''
        if self.changeKioskOff.get_active():
            disable_kiosk()
        _config['kiosk']['autologin'] = str( self.checkKioskAutologin.get_active() )
        user = self.entryKioskUser.get_text()
        if user == "": user = "kiosk"
        _config['kiosk']['user'] = user
        if self.changeKioskAll.get_active():
            mode = "1"
            enable_kiosk()
            fix_shortcut("kiosk", "$CTOR", "")
        if self.changeKioskCtor.get_active():
            mode = "2"
            uri = self.entryKioskCtor.get_uri()
            if uri:
                file = unquote( uri.replace( "file://" , "" ))
                enable_kiosk_ctor( file )
            else:
                os.system( "zenity --error --title='Connector Kiosk' --text='No connection file specified!'" )
                return 1
        if self.changeKioskWeb.get_active():
            mode = "3"
            url = self.entryKioskWeb.get_text()
            enable_kiosk_web(url)
        ctrl = self.checkKioskCtrl.get_active()
        if ctrl:
            disable_ctrl()
        else:
            enable_ctrl()
        _config['kiosk']['mode'] = mode
        _config['kiosk']['file'] = file
        _config['kiosk']['url'] = url
        _config['kiosk']['ctrl_disabled'] = str( ctrl )
        if self.checkKioskAdduser.get_active() and mode != "0":
            os.system( "adduser %s" % user )
        with open( _kiosk_conf, 'w' ) as configfile:
            _config.write( configfile )
        #else need disable tray...
        self.onClose(self)

    def initParams (self):
        """Initialisation state of the UI elements"""
        mode = _config.get( "kiosk", "mode" )
        self.entryKioskCtor.set_current_folder("/etc/kiosk")
        if mode == "1": self.changeKioskAll.set_active(True)
        elif mode == "2":
            self.changeKioskCtor.set_active(True)
            self.entryKioskCtor.set_uri( "file://%s" % _config.get( "kiosk", "file" ) )
        elif mode == "3":
            self.changeKioskWeb.set_active(True)
            self.entryKioskWeb.set_text( _config.get( "kiosk", "url" ) )
        else:
            self.changeKioskOff.set_active(True)
        ctrl = _config.get( "kiosk", "ctrl_disabled" )
        if ctrl in _true:
            self.checkKioskCtrl.set_active( True )
        autologin = _config.get( "kiosk", "autologin" )
        if autologin in _true:
            self.checkKioskAutologin.set_active( True )
        user = _config.get( "kiosk", "user" )
        if user == "kiosk": user = ""
        self.entryKioskUser.set_text( user )

    def onReset (self, *args):
        """Action for button 'Reset'"""
        self.entryKioskCtor.set_uri('')
        self.entryKioskWeb.set_text('')
        self.initParams()

if __name__ == '__main__':
    pass
