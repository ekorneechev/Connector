#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess
import signal

VERSION = "2.0.rc0"
HOMEFOLDER = os.getenv('HOME')
WORKFOLDER = "%s/.connector" % HOMEFOLDER #TODO: rename
MAINFOLDER = "/usr/share/myconnector"
ICONFOLDER = "%s/icons" % MAINFOLDER
UIFOLDER = "%s/ui" % MAINFOLDER

#Установки по умолчанию для параметров программы (какие приложения использовать)
DEFAULT = dict(RDP = 1, VNC = 1, TAB = '0', MAIN = '0')

#Исходные данные для ярлыка подключения
DESKTOP_INFO = """#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=myconnector
"""

#Запускаемый файл приложения
EXEC = "/usr/bin/myconnector "

#Ведение логов
DEFAULT['LOG'] = True
LOGFOLDER = WORKFOLDER + "logs/"
LOGFILE = LOGFOLDER + "myconnector.log"
STDLOGFILE = LOGFOLDER + "all.log"

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
    OS = subprocess.check_output("grep '^ID=' /etc/os-release; exit 0",shell=True, universal_newlines=True).strip().split('=')[1]

if OS == "altlinux":
    #Версия и релиз приложения
    _package_info = subprocess.check_output("rpm -q myconnector 2>/dev/null; exit 0",shell=True, universal_newlines=True).strip().split('-')
    try: RELEASE = _package_info[2].split('.')[0]
    except: RELEASE = "git"

    #Папка монтирования устройств
    _udisks2 = subprocess.check_output("/usr/sbin/control udisks2; exit 0",shell=True, universal_newlines=True).strip()
    if _udisks2 == 'default':
        USBPATH = "/run/media/$USER"
    if _udisks2 == 'shared':
        USBPATH = "/media"

    #Команда проверки наличия в системе Citrix Receiver
    CITRIX_CHECK = "rpm -q ICAClient > "

    #FreeRDP: ключ проброса смарткарт
    SCARD = ' /smartcard:""'

elif OS == "linuxmint" or OS == "ubuntu":
    try:
        _package_install = subprocess.check_output("dpkg-query -s myconnector | head -2 | tail -1 2>/dev/null;\
                                                    exit 0",shell=True, universal_newlines=True).strip().split(' ')[1]
    except IndexError: _package_install = 'deinstall'
    if _package_install == 'deinstall': RELEASE = "git"
    else:
        _package_info = subprocess.check_output("dpkg-query -W myconnector 2>/dev/null;\
                                                exit 0",shell=True, universal_newlines=True).strip().split('\t')
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

#Команда подключения сетевых файловых ресурсов
DEFAULT['FS'] = 'xdg-open'

#Tray icon is disabled by default
DEFAULT['TRAY'] = False

#Проверка обновлений программы
DEFAULT['CHECK_VERSION'] = True

#Параметры подключений по умолчанию
#FreeRDP:
DEFAULT['RDP1_ARGS'] = ['','', 1, 1, '', '32', '', '', '', '', '', 0, 0, 0, 0, 0, 0, 0, None, 0, 0, 0, 0, 0, 0, 0, 0, None, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, '']
#Remmina
DEFAULT['RDP_ARGS'] = ['', '', '32', '0', '', 3, '', 0, 0, 'off', 0]
DEFAULT['VNC_ARGS'] = ['', '9', '24', 1, 0, 0, 0, 1]
DEFAULT['NX_ARGS'] = ['', '0', '', 1, '', 0, 0, '']
DEFAULT['XDMCP_ARGS'] = ['0', 1, '', 0, 0, '']
DEFAULT['SPICE_ARGS'] = [0, 0, 0, 0, 0, 0, '']
DEFAULT['SSH_ARGS'] = ['', 0, '', 'UTF-8', '']
DEFAULT['SFTP_ARGS'] = ['', 0, '', 'UTF-8', '/']

#Default column by sort connections
DEFAULT['SORT'] = '0'
