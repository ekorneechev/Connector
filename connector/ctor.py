#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time, properties, webbrowser
from GLOBAL import *

def f_write(f_name, cfg):
    """Создание файла с конфигурацией для remmina"""
    f = open(WORKFOLDER+f_name,"w")
    f.write("[remmina]\n")
    for key in cfg.keys():
        print(key,cfg[key], sep='=',file=f)
    f.close()

def createFolder():
    """Создание в домашней папке пользователя дитректории для работы программы"""
    if not os.path.exists(WORKFOLDER):
        os.mkdir(WORKFOLDER)

class Remmina:
    """Класс, обеспечивающий подключение через remmina"""
    cfg = {}
    f_name = ".tmp.remmina"
    def create_cfg_file(self, args):
        """Создание файла конфигурации для соединения"""
        if type(args) == list:
            protocol = self.cfg['protocol']
            self.cfg['server'] = args[0]
            self.cfg['name'] += args[0]
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
                self.cfg['NX_privatekey'] = args[5]
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
                self.cfg['SSH_username'] = args[1]
                self.cfg['SSH_auth'] = args[2]
                self.cfg['SSH_privatekey'] = args[3]
                self.cfg['SSH_charset'] = args[4]
                self.cfg['exec'] = args[5]
            if protocol == 'SFTP':
                #[user, SSH_auth, keyfile, charset, execpath]
                self.cfg['SSH_username'] = args[1]
                self.cfg['SSH_auth'] = args[2]
                self.cfg['SSH_privatekey'] = args[3]
                self.cfg['SSH_charset'] = args[4]
                self.cfg['execpath'] = args[5]
        else:
            self.cfg['server'] = args
            self.cfg['name'] += args
        f_write(self.f_name, self.cfg)        

    def start(self, parameters):
        """Запуск remmina с необходимыми параметрами"""
        self.create_cfg_file(parameters)
        os.system('remmina -c "'+WORKFOLDER+self.f_name+'" &')

class VncRemmina(Remmina):
    """Класс для настройки VNC-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(keymap='', quality=9, disableencryption=0, colordepth=24, 
                       hscale=0, group='', password='', name='VNC-connection: ', viewonly=0, 
                       disableclipboard=0, protocol='VNC', vscale=0, username='', 
                       showcursor=0, disableserverinput=0, server='',aspectscale=0,
                       window_maximize=1, window_width=800, window_height=600, viewmode=1)
        self.f_name = '.tmp_VNC.remmina' 

class VncViewer:
    """Класс для настройки VNC-соединения через VncViewer"""
    def start(self, args):
        if type(args) == str:        
            os.system('vncviewer ' + args + ' &')
        else:
            command = 'vncviewer ' + args[0]
            if args[1]: command += ' ' + args[1]
            if args[2]: command += ' ' + args[2]
            if args[3]: command += ' ' + args[3]
            command += ' &'          
            os.system(command)


class RdpRemmina(Remmina):
    """Класс для настройки RDP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(disableclipboard=0, clientname='', quality=0, console=0, sharesmartcard=0, 
                       resolution='', group='', password='', name='RDP-connection: ',
                       shareprinter=0, security='', protocol='RDP', execpath='', 
                       sound='off', username='', sharefolder='', domain='', viewmode=3,
                       server='', colordepth=32, window_maximize=1, window_width=800, window_height=600)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_RDP.remmina'

class XFreeRdp:
    """Класс для настройки RDP-соединения через xfreerdp"""
    def start(self, args):
        if type(args) == str:
            os.system('xfreerdp -sec-nla /v:' + args + ' /f /cert-ignore &')
        else:
            command = 'xfreerdp -sec-nla /v:' + args[0]
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
            if args[13]: command += ' /smartcard'
            if args[14]: command += ' /printer'
            if args[15]: command += ' /sound:sys:alsa'
            if args[16]: command += ' /microphone:sys:alsa'
            if args[17]: command += ' /multimon'
            command += ' /cert-ignore &' #для игнора ввода Y/N при запросе сертификата 
            os.system(command)

class NxRemmina(Remmina):
    """Класс для настройки NX-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='NX-connection: ', protocol='NX', quality=0, disableencryption=0,
                        resolution='',group='',password='',username='',NX_privatekey='',
                        showcursor=0, server='', disableclipboard=0, window_maximize=1,
                        window_width=800, window_height=600, viewmode=4)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_NX.remmina'

class XdmcpRemmina(Remmina):
    """Класс для настройки XDMCP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(resolution='', group='', password='', name='XDMCP-connection: ',
                        protocol='XDMCP', once=0, showcursor=0, server='',colordepth=0,
                        window_maximize=1, viewmode=1, window_width=800, window_height=600)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_XDMCP.remmina'

class SftpRemmina(Remmina):
    """Класс для настройки SFTP-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='SFTP-connection: ', protocol='SFTP', SSH_enabled=1, SSH_auth=0, 
                        SSH_charset='UTF-8', SSH_privatekey='', SSH_username='',
                        group='', password='', execpath='/', server='', window_maximize=0, 
                        window_height=600, window_width=800, ftp_vpanedpos=360, viewmode=0)
        self.f_name = '.tmp_SFTP.remmina'

class SshRemmina(Remmina):
    """Класс для настройки SSH-соединения через Remmina"""
    def __init__(self):
        self.cfg = dict(name='SSH-connection: ', protocol='SSH', SSH_auth=0, SSH_charset='UTF-8', 
                        SSH_privatekey='', group='', password='', SSH_username='', SSH_enabled=1,
                        server='', window_maximize=0, window_width=500, window_height=500, viewmode=0)
        self.cfg['exec'] = ''
        self.f_name = '.tmp_SSH.remmina'

class Vmware:
    """Класс для настройки соединения к VMWare серверу"""
    def start(self, args):
        if type(args) == str:        
            os.system('vmware-view -q -s ' + args + ' &')
        else:
            command = 'vmware-view -q -s ' + args[0]
            if args[1]: command += ' -u ' + args[1]
            if args[2]: command += ' -d ' + args[2]
            if args[3]: command += ' -p ' + args[3]
            if args[4]: command += ' --fullscreen'
            command += ' &'   
            os.system(command)

class Citrix:
    """Класс для настройки ICA-соединения к Citrix-серверу"""
    def start(self, args):
        if type(args) == list:
            addr = args[0]
        else: addr = args
        os.system('/opt/Citrix/ICAClient/util/storebrowse --addstore ' + addr)
        os.system('/opt/Citrix/ICAClient/selfservice --icaroot /opt/Citrix/ICAClient &')

    def preferences():
        os.system('/opt/Citrix/ICAClient/util/configmgr --icaroot /opt/Citrix/ICAClient &')

class Web:
    """Класс для настройки подключения к WEB-ресурсу"""
    def start(self, args):
        if type(args) == list:
            addr = args[0]
        else: addr = args
        if  not addr.find("://") != -1:
            addr = "http://" + addr
        webbrowser.open (addr, new = 2)        

def definition(protocol):
    """Функция определения протокола"""
    whatProgram = properties.loadFromFile('default.conf') #загрузка параметров с выбором программ для подключения
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
    return connect  

def __main():
    """Функция для самотестирования модуля, просто запустите данный скрипт"""
    while True:
        protocol = input("Введите протокол: ").upper()    
        if protocol == 'VNC':
            connect = VncRemmina()
        elif protocol == 'RDP':
            connect = RdpRemmina()
        elif protocol == 'NX':
            connect = NxRemmina()
        elif protocol == 'XDMCP':
            connect = XdmcpRemmina()
        elif protocol == 'SSH':
            connect = SshRemmina()
        elif protocol == 'SFTP':
            connect = SftpRemmina()
        elif protocol == 'VMWARE':
            connect = Vmware() #demo.vm-it.com | login: Demo | pass Qwerty123
        elif protocol == 'CITRIX':
            connect = Citrix() #demo.CITRIXcloud.net | login: John.Smith6 | pass demo | domain CITRIXcloud
        else:
            print('Неизвестный протокол!')
            continue
        addr = input("Введите адрес сервера: ")
        connect.start(addr)
        time.sleep(2)

if __name__ == "__main__":
    __main()
