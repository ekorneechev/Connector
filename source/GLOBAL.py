#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, subprocess, signal

#Версия приложения
VERSION = "1.8.6"

#Определение домашней папки пользователя
HOMEFOLDER = os.getenv('HOME')

#Директория в домашней папке пользователя для хранения настроек и подключений
WORKFOLDER = HOMEFOLDER + '/.connector/'

#Папка программы
MAINFOLDER = "/usr/share/connector"

#Установки по умолчанию для параметров программы (какие приложения использовать)
DEFAULT = dict(RDP = 1, VNC = 1, TAB = '0', MAIN = '0')

#Исходные данные для ярлыка подключения
DESKTOP_INFO = """#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=connector
"""

#Запускаемый файл приложения
EXEC = "/usr/bin/connector "

#Ведение логов
DEFAULT['LOG'] = True
LOGFOLDER = WORKFOLDER + "logs/"
LOGFILE = LOGFOLDER + "connector.log"
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
    _package_info = subprocess.check_output("rpm -q connector 2>/dev/null; exit 0",shell=True, universal_newlines=True).strip().split('-')
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
        _package_install = subprocess.check_output("dpkg-query -s connector | head -2 | tail -1 2>/dev/null;\
                                                    exit 0",shell=True, universal_newlines=True).strip().split(' ')[1]
    except IndexError: _package_install = 'deinstall'
    if _package_install == 'deinstall': RELEASE = "git"
    else:
        _package_info = subprocess.check_output("dpkg-query -W connector 2>/dev/null;\
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
    os.system("zenity --error --no-wrap --icon-name=connector --text='Ваша операционная система не поддерживается.\n"
              "Некоторые функции программы могут не работать!\nПодробнее о поддерживаемых ОС <a href=\"http://wiki.myconnector.ru\">здесь</a>.'")

#Режим киоска:
DEFAULT['KIOSK'] = 0; DEFAULT['KIOSK_CONN'] = ""

KIOSK= """ &
while true
do
connector
done
"""

KIOSK_X = """#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon[ru_RU]=start
Name[ru_RU]=Ctor_kiosk
Exec=startx
Name=Ctor_kiosk
Icon=start
"""

KIOSK_ONE=""" &
while true
do
echo > /dev/null
done
"""

def CHECK_KIOSK():
    if OS != "altlinux": return True # Если не ALT - режим "киоска" недоступен
    try:
        for _string in open("/etc/connector/kiosk.access"):
            _string = _string.upper()
            if _string.find("ACCESS") == 0:
                _name, _value = _string.strip().split('=')
                _value = _value.upper().strip()
                if _value == "1" or _value == "ON" or _value == "YES":
                    _state = False
                else: _state = True
            else: _state = True
    except FileNotFoundError:
        _state = True
    return _state

#Команда подключения сетевых файловых ресурсов
DEFAULT['FS'] = 'xdg-open'

#По умолчанию индикатор в системном лотке включен
DEFAULT['TRAY'] = True

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
DEFAULT['SORT'] = 0
