#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MyConnector
# Copyright (C) 2014-2020 Evgeniy Korneechev <ek@myconnector.ru>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the version 2 of the GNU General
# Public License as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

import os
import signal
from subprocess import ( check_output,
                         Popen )
from configparser import ConfigParser

VERSION     = "2.0.rc0"
HOMEFOLDER  = os.getenv( "HOME" )
MAINFOLDER  = "/usr/share/myconnector"
WORKFOLDER  = "%s/.myconnector"    % HOMEFOLDER
ICONFOLDER  = "%s/icons"           % MAINFOLDER
UIFOLDER    = "%s/ui"              % MAINFOLDER
LOGFOLDER   = "%s/logs"            % WORKFOLDER
LOGFILE     = "%s/myconnector.log" % LOGFOLDER
STDLOGFILE  = "%s/all.log"         % LOGFOLDER

os.system( "mkdir -p %s" % LOGFOLDER )

DEFAULT    = { "rdp"            : "freerdp",
               "vnc"            : "vncviewer",
               "tab"            : "0",
               "main"           : "0",
               "log"            : "True",
               "fs"             : "xdg-open",
               "tray"           : "False",
               "check_version"  : "True",
               "sort"           : "0" }

#Исходные данные для ярлыка подключения
DESKTOP_INFO = """#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=myconnector
"""
EXEC = "/usr/bin/myconnector "

#Определение путей до папок пользователя
_dirs = {}
try:
    for _string in open(HOMEFOLDER + "/.config/user-dirs.dirs"):
        if _string[0] != "#":
            _name, _value = _string.strip().split('=')
            _dirs[_name] = _value
    DESKFOLDER = _dirs["XDG_DESKTOP_DIR"]
    DOWNFOLDER = _dirs["XDG_DOWNLOAD_DIR"]
    DOCSFOLDER = _dirs["XDG_DOCUMENTS_DIR"]
except FileNotFoundError:
    DESKFOLDER = HOMEFOLDER + "Desktop"
    DOWNFOLDER = HOMEFOLDER + "Downloads"
    DOCSFOLDER = HOMEFOLDER + "Documents"

#Ниже указаны параметры, зависящие от ОС
try:
    _tmp = open("/etc/altlinux-release")
    OS = "altlinux"
    _tmp.close()
except FileNotFoundError:
    OS = check_output( "grep '^ID=' /etc/os-release; exit 0", shell=True, universal_newlines=True ).strip().split( '=' )[1]

if OS == "altlinux":
    #Версия и релиз приложения
    _package_info = check_output( "rpm -q myconnector 2>/dev/null; exit 0", shell=True, universal_newlines=True ).strip().split( '-' )
    try: RELEASE = _package_info[2].split('.')[0]
    except: RELEASE = "git"

    #Папка монтирования устройств
    _udisks2 = check_output( "/usr/sbin/control udisks2; exit 0", shell=True, universal_newlines=True ).strip()
    if _udisks2 == 'default':
        USBPATH = "/run/media/$USER"
    else:
        USBPATH = "/media"

    #Команда проверки наличия в системе Citrix Receiver
    CITRIX_CHECK = "rpm -q ICAClient > "

    #FreeRDP: ключ проброса смарткарт
    SCARD = ' /smartcard:""'

elif OS == "linuxmint" or OS == "ubuntu":
    try:
        _package_install = check_output( "dpkg-query -s myconnector  2>/dev/null | head -2 | tail -1; exit 0",
                                         shell=True, universal_newlines=True ).strip().split( ' ' )[1]
    except IndexError: _package_install = 'deinstall'
    if _package_install == 'deinstall':
        RELEASE = "git"
    else:
        _package_info = check_output( "dpkg-query -W myconnector 2>/dev/null; exit 0",
                                      shell=True, universal_newlines=True ).strip().split( '\t' )
        try:
            _package_info = _package_info[1].split("-")
            RELEASE = _package_info[1]
        except IndexError: RELEASE = "git"

    USBPATH = "/media/$USER"

    CITRIX_CHECK = "dpkg -s icaclient > "

    SCARD = ' /smartcard'

else:
    VERSION = RELEASE = USBPATH = CITRIX_CHECK = SCARD = ""
    os.system( "zenity --error --no-wrap --icon-name=myconnector --text='Ваша операционная система не поддерживается.\n"
              "Некоторые функции программы могут не работать!\nПодробнее о поддерживаемых ОС <a href=\"http://wiki.myconnector.ru\">здесь</a>.'" )

#Protocols' default options
DEF_PROTO = {}
#vncviewer
DEF_PROTO[ "VNC1" ] = {  "fullscreen"        : "False",
                         "viewonly"          : "False",
                         "program"           : "vncviewer" }
#FreeRDP:
DEF_PROTO[ "RDP1" ] = {  "username"          : "",
                         "domain"            : "",
                         "fullscreen"        : "True",
                         "clipboard"         : "True",
                         "resolution"        : "",
                         "color"             : "32",
                         "folder"            : "",
                         "gserver"           : "",
                         "guser"             : "",
                         "gdomain"           : "",
                         "gpasswd"           : "",
                         "admin"             : "False",
                         "smartcards"        : "False",
                         "printers"          : "False",
                         "sound"             : "False",
                         "microphone"        : "False",
                         "multimon"          : "False",
                         "compression"       : "False",
                         "compr_level"       : "0",
                         "fonts"             : "False",
                         "aero"              : "False",
                         "drag"              : "False",
                         "animation"         : "False",
                         "theme"             : "False",
                         "wallpapers"        : "False",
                         "nsc"               : "False",
                         "jpeg"              : "False",
                         "jpeg_quality"      : "80.0",
                         "usb"               : "False",
                         "disable_nla"       : "True",
                         "workarea"          : "False",
                         "span"              : "False",
                         "desktop"           : "False",
                         "downloads"         : "False",
                         "documents"         : "False",
                         "gdi"               : "False",
                         "reconnect"         : "True",
                         "certignore"        : "True",
                         "passwdsave"        : "False",
                         "glyph"             : "False",
                         "userparams"        : "",
                         "program"           : "freerdp" }
#Remmina
DEF_PROTO[ "RDP" ] = {   "username"          : "",
                         "domain"            : "",
                         "colordepth"        : "32",
                         "quality"           : "0",
                         "resolution"        : "",
                         "viewmode"          : "3",
                         "sharefolder"       : "",
                         "shareprinter"      : "0",
                         "disableclipboard"  : "0",
                         "sound"             : "off",
                         "sharesmartcard"    : "0" ,
                         "program"           : "remmina" }
DEF_PROTO[ "VNC" ] = {   "username"          : "",
                         "quality"           : "9",
                         "colordepth"        : "24",
                         "viewmode"          : "1",
                         "viewonly"          : "0",
                         "disableencryption" : "0",
                         "disableclipboard"  : "0",
                         "showcursor"        : "1",
                         "program"           : "remmina" }
DEF_PROTO[ "NX" ] = {    "username"          : "",
                         "quality"           : "0",
                         "resolution"        : "",
                         "viewmode"          : "1",
                         "nx_privatekey"     : "",
                         "disableencryption" : "0",
                         "disableclipboard"  : "0",
                         "exec"              : "" }
DEF_PROTO[ "XDMCP" ] = { "colordepth"        : "0",
                         "viewmode"          : "1",
                         "resolution"        : "",
                         "once"              : "0",
                         "showcursor"        : "0",
                         "exec"              : "" }
DEF_PROTO[ "SPICE" ] = { "usetls"            : "0",
                         "viewonly"          : "0",
                         "resizeguest"       : "0",
                         "disableclipboard"  : "0",
                         "sharesmartcard"    : "0",
                         "enableaudio"       : "0",
                         "cacert"            : "" }
DEF_PROTO[ "SSH" ] = {   "username"          : "",
                         "ssh_auth"          : "0",
                         "ssh_privatekey"    : "",
                         "ssh_charset"       : "UTF-8",
                         "exec"              : "" }
DEF_PROTO[ "SFTP" ] = {  "username"          : "",
                         "ssh_auth"          : "0",
                         "ssh_privatekey"    : "",
                         "ssh_charset"       : "UTF-8",
                         "execpath"          : "/" }
_config = ConfigParser( interpolation = None )
_config_file = "%s/myconnector.conf" % WORKFOLDER

def config_save( default = False ):
    """Default config for MyConnector"""
    if default:
        _config[ "myconnector" ] = DEFAULT
        _config[ "vncviewer"   ] = DEF_PROTO[ "VNC1"  ].copy()
        _config[ "remmina_vnc" ] = DEF_PROTO[ "VNC"   ].copy()
        _config[ "ssh"         ] = DEF_PROTO[ "SSH"   ].copy()
        _config[ "sftp"        ] = DEF_PROTO[ "SFTP"  ].copy()
        _config[ "remmina_rdp" ] = DEF_PROTO[ "RDP"   ].copy()
        _config[ "nx"          ] = DEF_PROTO[ "NX"    ].copy()
        _config[ "xdmcp"       ] = DEF_PROTO[ "XDMCP" ].copy()
        _config[ "spice"       ] = DEF_PROTO[ "SPICE" ].copy()
        _config[ "freerdp"     ] = DEF_PROTO[ "RDP1"  ].copy()
    with open( _config_file, 'w' ) as configfile:
        _config.write( configfile )

def config_init():
    """Parsing config file"""
    _config.read( _config_file )
    main = _config[ "myconnector" ]
    protocols = { "VNC1"   : _config[ "vncviewer"   ],
                  "VNC"    : _config[ "remmina_vnc" ],
                  "RDP"    : _config[ "remmina_rdp" ],
                  "RDP1"   : _config[ "freerdp"     ],
                  "NX"     : _config[ "nx"          ],
                  "XDMCP"  : _config[ "xdmcp"       ],
                  "SPICE"  : _config[ "spice"       ],
                  "SSH"    : _config[ "ssh"         ],
                  "SFTP"   : _config[ "sftp"        ] }
    return main, protocols

try:
    CONFIG, CONFIGS = config_init()
except KeyError:
    if os.path.exists( _config_file ):
        os.system( "zenity --error --no-wrap --icon-name=myconnector --text='Конфигурационный файл поврежден, создан новый!'" )
        os.rename( _config_file, "%s.bak" % _config_file )
    config_save( default = True )
    CONFIG, CONFIGS = config_init()

