#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MyConnector
# Copyright (C) 2020 Evgeniy Korneechev <ek@myconnector.ru>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the version 2 of the GNU General
# Public License as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

import myconnector.options as options
from myconnector.config import *
from re import escape
try: import keyring
except Exception as error:
    class Keyring:
        def set_password(self, *args): pass
        def get_password(self, *args): return ""
    keyring = Keyring()
    options.log.warning("Python 3: %s. Password storage is not available for FreeRDP." % error)

try: enableLog = CONFIG.getboolean( 'log' )
except KeyError: enableLog = DEFAULT[ 'log' ]
if enableLog: STD_TO_LOG = ' >> ' + STDLOGFILE + " 2>&1 &"
else: STD_TO_LOG = ' &'

class VncViewer:
    """Класс для настройки VNC-соединения через VncViewer"""
    def start(self, args):
        if type(args) == str:
            options.log.info ("VNC: подключение к серверу %s", args)
            command = 'vncviewer ' + args
            server = args
        else:
            server = args[ "server" ]
            command = 'vncviewer %s ' % server
            if args.get( "fullscreen", "False" ) == "True": command += "-fullscreen "
            if args.get( "viewonly", "False"   ) == "True": command += "-viewonly "
        options.log.info ("VNC: подключение к серверу %s. Команда запуска:", server)
        options.log.info (command)
        os.system(command + STD_TO_LOG)

class XFreeRdp:
    """Класс для настройки RDP-соединения через xfreerdp"""
    def start(self, args):
        _link = "http://wiki.myconnector.ru/install#freerdp"
        if freerdpCheck():
            freerdpVersion = freerdpCheckVersion()
            if freerdpVersion > "1.2":
                server = args [ "server" ]
                username = args.get( "username" , "" )
                command = "xfreerdp /v:%s /t:'%s'" % ( server, args.get( "name", server ) )
                if username                                    : command += " /u:%s" % username
                if args.get( "domain" , ""                    ): command += " /d:%s" % args[ "domain" ]
                if args.get( "fullscreen", "True"   ) == "True": command += " /f"
                if args.get( "clipboard" , "True"   ) == "True": command += " +clipboard"
                if args.get( "resolution" , ""                ): command += " /size:%s" % args[ "resolution" ]
                if args.get( "color" , ""                     ): command += " /bpp:%s" % args[ "color" ]
                if args.get( "folder" , ""                    ): command += " /drive:SharedFolder,'%s'" % args[ "folder" ]
                if args.get( "gserver" , ""                   ): command += " /g:%s" % args[ "gserver" ]
                if args.get( "guser" , ""                     ): command += " /gu:%s" % args[ "guser" ]
                if args.get( "gdomain" , ""                   ): command += " /gd:%s" % args[ "gdomain" ]
                if args.get( "gpasswd" , "" ):
                    command = "GATEPWD='%s' && %s" % ( args[ "gpasswd" ], command )
                    command += " /gp:$GATEPWD"
                if args.get( "admin", "False"       ) == "True": command += " /admin"
                if args.get( "smartcards", "False"  ) == "True": command += SCARD
                if args.get( "printers", "False"    ) == "True": command += " /printer"
                if args.get( "sound", "False"       ) == "True": command += " /sound:sys:alsa"
                if args.get( "microphone", "False"  ) == "True": command += " /microphone:sys:alsa"
                if args.get( "multimon", "False"    ) == "True": command += " /multimon"
                if args.get( "compression", "False" ) == "True": command += " +compression /compression-level:%s" % args.get( "compr_level" , "0" )
                if args.get( "fonts", "False"       ) == "True": command += " +fonts"
                if args.get( "aero", "False"        ) == "True": command += " +aero"
                if args.get( "drag", "False"        ) == "True": command += " +window-drag"
                if args.get( "animation", "False"   ) == "True": command += " +menu-anims"
                if args.get( "theme", "False"       ) == "True": command += " -themes"
                if args.get( "wallpapers", "False"  ) == "True": command += " -wallpaper"
                if args.get( "nsc", "False"         ) == "True": command += " /nsc"
                if args.get( "jpeg", "False"        ) == "True": command += " /jpeg /jpeg-quality:%s" % args.get( "jpeg_quality" , "80.0" )
                if args.get( "usb", "False" ) and os.path.exists( USBPATH ):
                    command += " /drive:MEDIA,%s" % USBPATH
                if args.get( "workarea", "False"    ) == "True": command += " /workarea"
                if args.get( "span", "False"        ) == "True": command += " /span"
                if args.get( "desktop" , "False"    ) == "True": command += " /drive:Desktop,%s" % DESKFOLDER
                if args.get( "downloads" , "False"  ) == "True": command += " /drive:Downloads,%s" % DOWNFOLDER
                if args.get( "documents" , "False"  ) == "True": command += " /drive:Documents,%s" % DOCSFOLDER
                if args.get( "gdi", "False"         ) == "True": command += " /gdi:hw"
                else: command += " /gdi:sw"
                if args.get( "certignore", "True"   ) == "True": command += " /cert-ignore"
                if args.get( "reconnect", "True"    ) == "True": command += " +auto-reconnect"
                if args.get( "glyph", "False"       ) == "True": command += " +glyph-cache"
                if args.get( "userparams" , ""                ): command += " %s" % args[ "userparams" ]
                disable_nla = args.get( "disable_nla", "True" )
                if disable_nla == "True"                       : command += " -sec-nla"
                password = args.get( "passwd" , "" )
                if not password:
                    password = keyring.get_password( server, username )
                if not password and disable_nla != "True":
                    password = passwd( server, username )
                if password:
                    command += " /p:%s" % escape( password )
                if password != False: #if there is password after zenity
                    options.log.info ("FreeRDP: подключение к серверу %s. Команда запуска:", server)
                    try: cmd2log = command.replace("/p:" + command.split("/p:")[1].split(' ')[0],"/p:<hidden>")
                    except: cmd2log = command
                    options.log.info (cmd2log)
                    os.system(command + STD_TO_LOG)
                    if enableLog:
                        signal.signal( signal.SIGCHLD, signal.SIG_IGN ) # without zombie
                        Popen( [ MAINFOLDER + "/myconnector-check-xfreerdp-errors" ] )
            else:
                options.log.warning ("FreeRDP version below 1.2!")
                os.system( "zenity --error --text='\nУстановленная версия FreeRDP (%s) не соответствует минимальным требованиям,"
                          " подробности <a href=\"%s\">здесь</a>!' --no-wrap --icon-name=myconnector" % ( freerdpVersion, _link ))
        else:
            options.log.warning ("FreeRDP is not installed!")
            os.system( "zenity --error --text='\nFreeRDP не установлен, подробности <a href=\"%s\">здесь</a>!' --no-wrap --icon-name=myconnector" % _link )

class Remmina:
    """Connection via Remmina"""
    cfg = {}
    f_name = ".tmp.remmina"
    def create_cfg_file( self, args ):
        """Create configuration file for connect"""
        server, login = options.searchSshUser( args[ "server" ] )
        args[ "server" ] = server
        if login: args[ "username" ] = login
        self.cfg[ "name" ] += args.get( "name" , server )
        f = open( "%s/%s" % ( WORKFOLDER, self.f_name ), "w" )
        f.write( "[remmina]\n" )
        for key in self.cfg.keys():
            self.cfg[ key ] = args.get( key, self.cfg[ key ] )
            print( key, self.cfg[ key ], sep = "=", file = f )
        f.close()

    def start( self, parameters ):
        """Run connection via Remmina"""
        self.create_cfg_file( parameters )
        options.log.info ( "Remmina: подключение по протоколу %s к серверу: %s", self.cfg[ "protocol" ], self.cfg[ "server" ] )
        command = "remmina -c \"%s/%s\"" % ( WORKFOLDER, self.f_name )
        options.log.info ( command )
        os.system( "cd $HOME && %s%s" % ( command, STD_TO_LOG ) )

class RdpRemmina( Remmina ):
    """Remmina RDP connection"""
    def __init__( self ):
        self.cfg = { "disableclipboard"       : "0",
                     "clientname"             : "",
                     "quality"                : "0",
                     "console"                : "0",
                     "sharesmartcard"         : "0",
                     "resolution"             : "",
                     "group"                  : "",
                     "password"               : "",
                     "name"                   : "RDP-connection: ",
                     "shareprinter"           : "0",
                     "security"               : "",
                     "protocol"               : "RDP",
                     "execpath"               : "",
                     "disablepasswordstoring" : "1",
                     "sound"                  : "off",
                     "username"               : "",
                     "sharefolder"            : "",
                     "domain"                 : "",
                     "viewmode"               : "3",
                     "server"                 : "",
                     "colordepth"             : "32",
                     "window_maximize"        : "1",
                     "window_width"           : "800",
                     "window_height"          : "600",
                     "exec"                   : "" }
        self.f_name = ".tmp_RDP.remmina"

class VncRemmina( Remmina ):
    """Remmina VNC connection"""
    def __init__( self ):
        self.cfg = { "keymap"                 : "",
                     "quality"                : "9",
                     "disableencryption"      : "0",
                     "colordepth"             : "24",
                     "hscale"                 : "0",
                     "group"                  : "",
                     "password"               : "",
                     "name"                   : "VNC-connection: ",
                     "viewonly"               : "0",
                     "disableclipboard"       : "0",
                     "protocol"               : "VNC",
                     "vscale"                 : "0",
                     "username"               : "",
                     "disablepasswordstoring" : "1",
                     "showcursor"             : "0",
                     "disableserverinput"     : "0",
                     "server"                 : "",
                     "aspectscale"            : "0",
                     "window_maximize"        : "1",
                     "window_width"           : "800",
                     "window_height"          : "600",
                     "viewmode"               : "1" }
        self.f_name = ".tmp_VNC.remmina"

class NxRemmina( Remmina ):
    """Remmina NX connection"""
    def __init__( self ):
        self.cfg = { "name"                   : "NX-connection: ",
                     "protocol"               : "NX",
                     "quality"                : "0",
                     "server"                 : "",
                     "disableencryption"      : "0",
                     "resolution"             : "",
                     "group"                  : "",
                     "password"               : "",
                     "username"               : "",
                     "NX_privatekey"          : "",
                     "showcursor"             : "0",
                     "disableclipboard"       : "0",
                     "window_maximize"        : "1",
                     "window_width"           : "800",
                     "window_height"          : "600",
                     "viewmode"               : "4",
                     "disablepasswordstoring" : "1",
                     "exec"                   : "" }
        self.f_name = ".tmp_NX.remmina"

class XdmcpRemmina( Remmina ):
    """Remmina XDMCP connection"""
    def __init__( self ):
        self.cfg = { "resolution"             : "",
                     "group"                  : "",
                     "password"               : "",
                     "name"                   : "XDMCP-connection: ",
                     "protocol"               : "XDMCP",
                     "once"                   : "0",
                     "showcursor"             : "0",
                     "server"                 : "",
                     "colordepth"             : "0",
                     "window_maximize"        : "1",
                     "viewmode"               : "1",
                     "window_width"           : "800",
                     "window_height"          : "600",
                     "disablepasswordstoring" : "1",
                     "exec"                   : "" }
        self.f_name = ".tmp_XDMCP.remmina"

class SftpRemmina( Remmina ):
    """Remmina SFTP connection"""
    def __init__( self ):
        self.cfg = { "name"                   : "SFTP-connection: ",
                     "protocol"               : "SFTP",
                     "ssh_auth"               : "0",
                     "ssh_charset"            : "UTF-8",
                     "ssh_privatekey"         : "",
                     "username"               : "",
                     "ssh_username"           : "",
                     "group"                  : "",
                     "password"               : "",
                     "execpath"               : "/",
                     "server"                 : "",
                     "window_maximize"        : "0",
                     "window_height"          : "600",
                     "window_width"           : "800",
                     "ftp_vpanedpos"          : "360",
                     "viewmode"               : "0",
                     "disablepasswordstoring" : "1" }
        self.f_name = ".tmp_SFTP.remmina"

class SshRemmina( Remmina ):
    """Remmina SSH connection"""
    def __init__( self ):
        self.cfg = { "name"                   : "SSH-connection: ",
                     "protocol"               : "SSH",
                     "ssh_auth"               : "0",
                     "ssh_charset"            : "UTF-8",
                     "ssh_privatekey"         : "",
                     "group"                  : "",
                     "password"               : "",
                     "username"               : "",
                     "ssh_username"           : "",
                     "server"                 : "",
                     "window_maximize"        : "0",
                     "window_width"           : "500",
                     "window_height"          : "500",
                     "viewmode"               : "0",
                     "disablepasswordstoring" : "1",
                     "exec"                   : "" }
        self.f_name = ".tmp_SSH.remmina"

class SpiceRemmina( Remmina ):
    """Remmina SPICE connection"""
    def __init__( self ):
        self.cfg = { "name"                   : "SPICE-connection: ",
                     "protocol"               : "SPICE",
                     "ssh_auth"               : "0",
                     "disableclipboard"       : "0",
                     "ssh_privatekey"         : "",
                     "usertls"                : "0",
                     "ssh_username"           : "",
                     "enableaudio"            : "0",
                     "password"               : "",
                     "cacert"                 : "",
                     "server"                 : "",
                     "ssh_loopback"           : "0",
                     "resizeguest"            : "0",
                     "sharesmartcard"         : "0",
                     "ssh_server"             : "",
                     "viewonly"               : "0",
                     "disablepasswordstoring" : "1" }
        self.f_name = ".tmp_SPICE.remmina"

class Vmware:
    """Класс для настройки соединения к VMWare серверу"""
    def start(self, args):
        if vmwareCheck():
            if type(args) == str:
                command = 'vmware-view -q -s ' + args
                options.log.info ("VMware: подключение к серверу %s", args)
                options.log.info (command)
            else:
                if type( args ) == dict: args = ConfigParser()
                command = 'vmware-view -q -s %s' %  args[ "server" ]
                if args.get( "user" , ""                     ): command += " -u %s" % args[ "user" ]
                if args.get( "domain" , ""                   ): command += " -d %s" % args[ "domain" ]
                if args.get( "fullscreen", "False" ) == "True": command += " --fullscreen"
                options.log.info ( "VMware: подключение к серверу %s", args[ "server" ] )
                options.log.info (command)
                if args.get( "password", "" ): command += ' -p %s' % args[ "password" ]
            os.system(command + STD_TO_LOG)
        else:
            options.log.warning ("VMware Horizon Client is not installed!")
            os.system( "zenity --error --text='\nVMware Horizon Client не установлен!' --no-wrap --icon-name=myconnector" )

def _missCitrix():
    """Message for user, if Citrix Receiver not installed"""
    options.log.warning ("Citrix Receiver is not installed!")
    os.system( "zenity --error --text='\nCitrix Receiver не установлен!' --no-wrap --icon-name=myconnector" )

class Citrix:
    """Класс для настройки ICA-соединения к Citrix-серверу"""
    def start(self, args):
        if type(args) == str:
            addr = args
        else:
            addr = args [ "server" ]
        if citrixCheck():
            options.log.info ("Citrix: подключение к серверу %s", addr)
            os.system('/opt/Citrix/ICAClient/util/storebrowse --addstore ' + addr + STD_TO_LOG)
            os.system('/opt/Citrix/ICAClient/selfservice --icaroot /opt/Citrix/ICAClient' + STD_TO_LOG)
        else: _missCitrix()

    def preferences():
        if citrixCheck():
            options.log.info ("Citrix: открытие настроек программы")
            os.system('/opt/Citrix/ICAClient/util/configmgr --icaroot /opt/Citrix/ICAClient' + STD_TO_LOG)
        else: _missCitrix()

class Web:
    """Класс для настройки подключения к WEB-ресурсу"""
    def start(self, args):
        if type(args) == str:
            addr = args
        else:
            addr = args [ "server" ]
        if  not addr.find("://") != -1:
            addr = "http://" + addr
        command = 'xdg-open "' + addr + '"'
        options.log.info ("WWW: открытие web-ресурса %s", addr)
        options.log.info (command)
        os.system ( command + STD_TO_LOG)

class FileServer:
    """Класс для настройки подключения к файловому серверу"""
    def start(self, args):
        _exec = CONFIG[ 'fs' ] + ' "'
        if type(args) == str:
            if  not args.find("://") != -1:
                os.system( "zenity --warning --text='Введите протокол подключения!\n"
                          "Или выберите из списка в дополнительных параметрах.' --no-wrap --icon-name=myconnector" )
                return 1
            else:
                command = _exec + args + '"'
                server = args
        else:
            try: protocol, server = args[ "server" ].split("://") #TODO try/except
            except: server = args[ "server" ]; protocol = args[ "type" ] #TODO try/except
            command = _exec + protocol + "://"
            if args.get( "domain" , "" ): command += "%s;" % args[ "domain" ]
            if args.get( "user" , ""   ): command += "%s@" % args[ "user" ]
            command += server
            if args.get( "folder" , "" ): command += "/%s" % args[ "folder" ]
            command += '"'
        options.log.info ("Открытие файлового сервера %s. Команда запуска:", server)
        options.log.info (command)
        os.system (command + STD_TO_LOG)

def definition( name ):
    """Функция определения протокола"""
    protocols = { "VNC"    : VncRemmina(),
                  "VNC1"   : VncViewer(),
                  "RDP"    : RdpRemmina(),
                  "RDP1"   : XFreeRdp(),
                  "NX"     : VncViewer(),
                  "XDMCP"  : XdmcpRemmina(),
                  "SSH"    : SshRemmina(),
                  "SFTP"   : SftpRemmina(),
                  "VMWARE" : Vmware(),
                  "CITRIX" : Citrix(),
                  "WEB"    : Web(),
                  "SPICE"  : SpiceRemmina(),
                  "FS"     : FileServer() }
    return protocols[ name ]

def citrixCheck():
    """Фунцкия проверки наличия в системе Citrix Receiver"""
    check = int( check_output( "%s/dev/null 2>&1; echo $?" % CITRIX_CHECK, shell=True, universal_newlines=True ).strip() )
    check = not bool(check)
    return check

def vmwareCheck():
    """Фунцкия проверки наличия в системе VMware Horizon Client"""
    check = int( check_output( "which vmware-view > /dev/null 2>&1; echo $?", shell=True, universal_newlines=True ).strip() )
    check = not bool(check)
    return check

def freerdpCheck():
    """Фунцкия проверки наличия в системе FreeRDP"""
    check = int( check_output( "which xfreerdp > /dev/null 2>&1; echo $?", shell=True, universal_newlines=True ).strip() )
    check = not bool(check)
    return check

def freerdpCheckVersion():
    """Фунцкия определения версии FreeRDP"""
    version = check_output( "xfreerdp /version; exit 0",shell=True, universal_newlines=True ).strip().split( '\t' )
    version = version[0].split(" "); version = version[4].split("-")[0];
    return version

def passwd(server, username):
    """Ввод пароля и запрос о его сохранении в связке ключей"""
    separator = "|CoNnEcToR|"
    try:
        password, save = check_output( "zenity --forms --title=\"Аутентификация (with NLA)\" --text=\"Имя пользователя: %s\""
            " --add-password=\"Пароль:\" --add-combo=\"Хранить пароль в связке ключей:\" --combo-values=\"Да|Нет\""
            " --separator=\"%s\" 2>/dev/null" % (username, separator),shell=True, universal_newlines=True).strip().split(separator)
        if save == "Да" and password: keyring.set_password(str(server),str(username),str(password))
    except ValueError:
        password = False
        options.log.info ("FreeRDP: подключение отменено пользователем (окно запроса пароля закрыто или нажата кнопка Отмена).")
    return password

if __name__ == "__main__":
    pass
