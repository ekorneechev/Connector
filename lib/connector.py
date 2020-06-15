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
from myconnector.params import *
from re import escape
try: import keyring
except Exception as error:
    class Keyring:
        def set_password(self, *args): pass
        def get_password(self, *args): return ""
    keyring = Keyring()
    options.log.warning("Python 3: %s. Password storage is not available for FreeRDP." % error)

try: enableLog = options.loadFromFile('default.conf')['LOG']
except KeyError: enableLog = DEFAULT['LOG']
if enableLog: STD_TO_LOG = ' >> ' + STDLOGFILE + " 2>&1 &"
else: STD_TO_LOG = ' &'

def f_write(f_name, cfg):
    """Создание файла с конфигурацией для remmina"""
    f = open(WORKFOLDER+f_name,"w")
    f.write("[remmina]\n")
    for key in cfg.keys():
        print(key,cfg[key], sep='=',file=f)
    f.close()

class Remmina:
    """Класс, обеспечивающий подключение через remmina"""
    cfg = {}
    f_name = ".tmp.remmina"
    def create_cfg_file(self, args):
        """Создание файла конфигурации для соединения"""
        protocol = self.cfg['protocol']
        server, login = options.searchSshUser(args[0])
        self.cfg['server'] = server
        self.cfg['name'] = args.pop()
        if protocol == 'RDP':
            #[user, domain, color, quality, resolution, viewmode, folder, printer, clipboard, sound]
            self.cfg['username'] = args[1]
            self.cfg['domain'] = args[2]
            self.cfg['colordepth'] = args[3]
            self.cfg['quality'] = args[4]
            self.cfg['resolution'] = args[5]
            self.cfg['viewmode'] = args[6]
            self.cfg['sharefolder'] = args[7]
            self.cfg['shareprinter'] = args[8]
            self.cfg['disableclipboard'] = args[9]
            self.cfg['sound'] = args[10]
            self.cfg['sharesmartcard'] = args[11]
        if protocol == 'NX':
            #[user, quality, resolution, viewmode, keyfile, crypt, clipboard, _exec]
            self.cfg['username'] = args[1]
            self.cfg['quality'] = args[2]
            self.cfg['resolution'] = args[3]
            self.cfg['viewmode'] = args[4]
            self.cfg['nx_privatekey'] = args[5]
            self.cfg['disableencryption'] = args[6]
            self.cfg['disableclipboard'] = args[7]
            self.cfg['exec'] = args[8]
        if protocol == 'VNC':
            #[user, quality, color, viewmode, viewonly, crypt, clipboard, showcursor]
            self.cfg['username'] = args[1]
            self.cfg['quality'] = args[2]
            self.cfg['colordepth'] = args[3]
            self.cfg['viewmode'] = args[4]
            self.cfg['viewonly'] = args[5]
            self.cfg['disableencryption'] = args[6]
            self.cfg['disableclipboard'] = args[7]
            self.cfg['showcursor'] = args[8]
        if protocol == 'XDMCP':
            #[color, viewmode, resolution, once, showcursor, _exec]
            self.cfg['colordepth'] = args[1]
            self.cfg['viewmode'] = args[2]
            self.cfg['resolution'] = args[3]
            self.cfg['once'] = args[4]
            self.cfg['showcursor'] = args[5]
            self.cfg['exec'] = args[6]
        if protocol == 'SSH':
            #[user, SSH_auth, keyfile, charset, _exec]
            if login: self.cfg['ssh_username'] = login
            else: self.cfg['ssh_username'] = args[1]
            self.cfg['ssh_auth'] = args[2]
            self.cfg['ssh_privatekey'] = args[3]
            self.cfg['ssh_charset'] = args[4]
            self.cfg['exec'] = args[5]
        if protocol == 'SFTP':
            #[user, SSH_auth, keyfile, charset, execpath]
            if login: self.cfg['ssh_username'] = login
            else: self.cfg['ssh_username'] = args[1]
            self.cfg['ssh_auth'] = args[2]
            self.cfg['ssh_privatekey'] = args[3]
            self.cfg['ssh_charset'] = args[4]
            self.cfg['execpath'] = args[5]
        if protocol == 'SPICE':
            #[tls, viewonly, resize, clipboard, cards, sound, cacert]
            self.cfg['usetls'] = args[1]
            self.cfg['viewonly'] = args[2]
            self.cfg['resizeguest'] = args[3]
            self.cfg['disableclipboard'] = args[4]
            self.cfg['sharesmartcard'] = args[5]
            self.cfg['enableaudio'] = args[6]
            self.cfg['cacert'] = args[7]
        f_write(self.f_name, self.cfg)

    def start(self, parameters):
        """Запуск remmina с необходимыми параметрами"""
        self.create_cfg_file(parameters)
        options.log.info ("Remmina: подключение по протоколу %s к серверу: %s", self.cfg['protocol'], self.cfg['server'])
        command = 'remmina -c "' + WORKFOLDER + self.f_name + '"'
        options.log.info (command)
        os.system('cd $HOME && ' + command + STD_TO_LOG)

class VncRemmina(Remmina):
    """Класс для настройки VNC-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(keymap='', quality=9, disableencryption=0, colordepth=24,
                       hscale=0, group='', password='', name='VNC-connection: ', viewonly=0,
                       disableclipboard=0, protocol='VNC', vscale=0, username='', disablepasswordstoring=1,
                       showcursor=0, disableserverinput=0, server='',aspectscale=0,
                       window_maximize=1, window_width=800, window_height=600, viewmode=1)
        self.f_name = '.tmp_VNC.remmina'

class VncViewer:
    """Класс для настройки VNC-соединения через VncViewer"""
    def start(self, args):
        if type(args) == str:
            options.log.info ("VNC: подключение к серверу %s", args)
            command = 'vncviewer ' + args
            server = args
        else:
            command = 'vncviewer ' + args[0] + ' '
            if args[1]: command += args[1]
            if args[2]: command += args[2]
            server = args[0]
        options.log.info ("VNC: подключение к серверу %s. Команда запуска:", server)
        options.log.info (command)
        os.system(command + STD_TO_LOG)

class RdpRemmina(Remmina):
    """Класс для настройки RDP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(disableclipboard=0, clientname='', quality=0, console=0, sharesmartcard=0,
                       resolution='', group='', password='', name='RDP-connection: ',
                       shareprinter=0, security='', protocol='RDP', execpath='', disablepasswordstoring=1,
                       sound='off', username='', sharefolder='', domain='', viewmode=3,
                       server='', colordepth=32, window_maximize=1, window_width=800, window_height=600)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_RDP.remmina'

class XFreeRdp:
    """Класс для настройки RDP-соединения через xfreerdp"""
    def start(self, args):
        _link = "http://wiki.myconnector.ru/install#freerdp"
        if freerdpCheck():
            freerdpVersion = freerdpCheckVersion()
            if freerdpVersion > "1.2":
                nameConnect = args[len(args)-1]
                command = 'xfreerdp /v:' + args[0] + " /t:'" + nameConnect + "'"
                if args[1]: command += ' /u:' + args[1]
                if args[2]: command += ' /d:' + args[2]
                if args[3]: command += ' /f'
                if args[4]: command += ' +clipboard'
                if args[5]: command += ' /size:' + args[5]
                if args[6]: command += ' /bpp:' + args[6]
                if args[7]: command += ' /drive:LocalFolder,"' + args[7] + '"'
                if args[8]: command += ' /g:' + args[8]
                if args[9]: command += ' /gu:' + args[9]
                if args[10]: command += ' /gd:' + args[10]
                if args[11]:
                    command = "GATEPWD='" + args[11] + "' && " + command
                    command += ' /gp:$GATEPWD'
                if args[12]: command += ' /admin'
                if args[13]: command += SCARD
                if args[14]: command += ' /printer'
                if args[15]: command += ' /sound:sys:alsa'
                if args[16]: command += ' /microphone:sys:alsa'
                if args[17]: command += ' /multimon'
                if args[18]: command += ' +compression'
                if args[19]: command += ' /compression-level:' + args[19]
                if args[20]: command += ' +fonts'
                if args[21]: command += ' +aero'
                if args[22]: command += ' +window-drag'
                if args[23]: command += ' +menu-anims'
                if args[24]: command += ' -themes'
                if args[25]: command += ' -wallpaper'
                if args[26]: command += ' /nsc'
                if args[27]: command += ' /jpeg'
                if args[28]: command += ' /jpeg-quality:' + str(args[28])
                if args[29] and options.checkPath(USBPATH): command += ' /drive:MEDIA,' + USBPATH
                if args[31]: command += ' /workarea'
                try: #Добавлена совместимость с предыдущей версией; < 1.4.0
                    if args[32]: command += ' /span'
                except IndexError: pass
                try: #< 1.4.1
                    if args[33]: command += ' /drive:Desktop,' + DESKFOLDER
                    if args[34]: command += ' /drive:Downloads,' + DOWNFOLDER
                    if args[35]: command += ' /drive:Documents,' + DOCSFOLDER
                except IndexError: pass
                try: #< 1.8.0
                    if args[36]: command += ' /gdi:hw'
                    else: command += ' /gdi:sw'
                except IndexError: command += ' /gdi:sw'
                try: #< 1.8.2
                    if args[38]: command += ' /cert-ignore'
                    if args[37]: command += ' +auto-reconnect'
                except IndexError: command += ' +auto-reconnect /cert-ignore'
                try:
                    if args[40] and len(args) >= 42: command += ' /p:' + escape(args[40])
                    elif args[30]: command += ' /p:' + escape(passwd(args[0], args[1]))
                    else: command += ' -sec-nla'
                except: command += ' -sec-nla'
                try:
                    if args[41] and len(args) >= 43: command += ' +glyph-cache'
                except IndexError: pass
                try:
                    # for compatibility also need to check lenght of 'args'
                    # length = 'last index' + 1 + 'title of the connect' (since version 1.5.6...)
                    if args[42] and len(args) >= 44: command += ' ' + args[42]
                except IndexError: pass

                server = args[0]
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

class NxRemmina(Remmina):
    """Класс для настройки NX-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='NX-connection: ', protocol='NX', quality=0, disableencryption=0,
                        resolution='',group='',password='',username='',NX_privatekey='',
                        showcursor=0, server='', disableclipboard=0, window_maximize=1,
                        window_width=800, window_height=600, viewmode=4, disablepasswordstoring=1)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_NX.remmina'

class XdmcpRemmina(Remmina):
    """Класс для настройки XDMCP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(resolution='', group='', password='', name='XDMCP-connection: ',
                        protocol='XDMCP', once=0, showcursor=0, server='',colordepth=0,
                        window_maximize=1, viewmode=1, window_width=800, window_height=600, disablepasswordstoring=1)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_XDMCP.remmina'

class SftpRemmina(Remmina):
    """Класс для настройки SFTP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='SFTP-connection: ', protocol='SFTP', ssh_enabled=0, ssh_auth=0,
                        ssh_charset='UTF-8', ssh_privatekey='', username='', ssh_username='',
                        group='', password='', execpath='/', server='', window_maximize=0,
                        window_height=600, window_width=800, ftp_vpanedpos=360, viewmode=0, disablepasswordstoring=1)
        self.f_name = '.tmp_SFTP.remmina'

class SshRemmina(Remmina):
    """Класс для настройки SSH-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='SSH-connection: ', protocol='SSH', ssh_auth=0, ssh_charset='UTF-8',
                        ssh_privatekey='', group='', password='', username='', ssh_username='', ssh_enabled=0,
                        server='', window_maximize=0, window_width=500, window_height=500, viewmode=0, disablepasswordstoring=1)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_SSH.remmina'

class SpiceRemmina(Remmina):
    """Класс для настройки SPICE-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='SPICE-connection: ', protocol='SPICE', ssh_enabled=0, ssh_auth=0,
                        disableclipboard=0, ssh_privatekey='', usertls=0, ssh_username='',
                        enableaudio=0, password='', cacert='', server='', ssh_loopback=0,
                        resizeguest=0, sharesmartcard=0, ssh_server='', viewonly=0, disablepasswordstoring=1)
        self.f_name = '.tmp_SPICE.remmina'

class Vmware:
    """Класс для настройки соединения к VMWare серверу"""
    def start(self, args):
        if vmwareCheck():
            if type(args) == str:
                command = 'vmware-view -q -s ' + args
                options.log.info ("VMware: подключение к серверу %s", args)
                options.log.info (command)
            else:
                command = 'vmware-view -q -s ' + args[0]
                if args[1]: command += ' -u ' + args[1]
                if args[2]: command += ' -d ' + args[2]
                if args[4]: command += ' --fullscreen'
                options.log.info ("VMware: подключение к серверу %s", args[0])
                options.log.info (command)
                if args[3]: command += ' -p ' + args[3]
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
        if type(args) == list:
            addr = args[0]
        else: addr = args
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
        if type(args) == list:
            addr = args[0]
        else: addr = args
        if  not addr.find("://") != -1:
            addr = "http://" + addr
        command = 'xdg-open "' + addr + '"'
        options.log.info ("WWW: открытие web-ресурса %s", addr)
        options.log.info (command)
        os.system ( command + STD_TO_LOG)

class FileServer:
    """Класс для настройки подключения к файловому серверу"""
    def start(self, args):
        _exec = options.loadFromFile('default.conf')['FS'] + ' "'
        if type(args) == str:
            if  not args.find("://") != -1:
                os.system( "zenity --warning --text='Введите протокол подключения!\n"
                          "Или выберите из списка в дополнительных параметрах.' --no-wrap --icon-name=myconnector" )
                return 1
            else:
                command = _exec + args + '"'
                server = args
        else:
            try: protocol, server = args[0].split("://")
            except: server = args[0]; protocol = args[4]
            command = _exec + protocol + "://"
            if args[2]: command += args[2] + ";"
            if args[1]: command += args[1] + "@"
            command += server
            if args[3]: command += '/' + args[3]
            command += '"'
        options.log.info ("Открытие файлового сервера %s. Команда запуска:", server)
        options.log.info (command)
        os.system (command + STD_TO_LOG)

def definition(protocol):
    """Функция определения протокола"""
    whatProgram = options.loadFromFile('default.conf') #загрузка параметров с выбором программ для подключения
    if protocol == 'VNC':
        if whatProgram['VNC'] == 0:
            connect = VncRemmina()
        else: connect = VncViewer()
    elif protocol == 'RDP':
        if whatProgram['RDP'] == 0:
            connect = RdpRemmina()
        else: connect = XFreeRdp()
    elif protocol == 'NX':
        connect = NxRemmina()
    elif protocol == 'XDMCP':
        connect = XdmcpRemmina()
    elif protocol == 'SSH':
        connect = SshRemmina()
    elif protocol == 'SFTP':
        connect = SftpRemmina()
    elif protocol == 'VMWARE':
        connect = Vmware()
    elif protocol == 'CITRIX':
        connect = Citrix()
    elif protocol == 'WEB':
        connect = Web()
    elif protocol == 'SPICE':
        connect = SpiceRemmina()
    elif protocol == 'FS':
        connect = FileServer()
    return connect

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
    password = keyring.get_password(str(server),str(username))
    if password: return password
    separator = "|CoNnEcToR|"
    try:
        password, save = check_output( "zenity --forms --title=\"Аутентификация (with NLA)\" --text=\"Имя пользователя: %s\""
            " --add-password=\"Пароль:\" --add-combo=\"Хранить пароль в связке ключей:\" --combo-values=\"Да|Нет\""
            " --separator=\"%s\" 2>/dev/null" % (username, separator),shell=True, universal_newlines=True).strip().split(separator)
        if save == "Да" and password: keyring.set_password(str(server),str(username),str(password))
    #если окно zenity закрыто или нажата кнопка Отмена, делаем raise ошибки FreeRDP
    except ValueError:
        password = " /CANCELED"
        options.log.warning ("FreeRDP: подключение отменено пользователем (окно zenity закрыто или нажата кнопка Отмена):")
    return password

if __name__ == "__main__":
    pass
