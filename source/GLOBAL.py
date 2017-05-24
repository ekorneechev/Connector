#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, subprocess

#Определение домашней папки пользователя
HOMEFOLDER = os.getenv('HOME')

#Директория в домашней папке пользователя для хранения настроек и подключений
WORKFOLDER = HOMEFOLDER + '/.connector/'

#Установки по умолчанию для параметров программы (какие приложения использовать)
DEFAULT = dict(RDP = 1, VNC = 1, TAB = '0')

#Исходные данные для ярлыка подключения
DESKTOP_INFO = """#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=/usr/share/connector/data/emblem.png
"""

#Запускаемый файл приложения
EXEC = "/usr/bin/connector "

#Ведение логов
LOGFOLDER = WORKFOLDER + "logs/"
LOGFILE = LOGFOLDER + "connector.log"
STDLOGFILE = LOGFOLDER + "all.log"
STD_TO_LOG = ' >> ' + STDLOGFILE + " 2>&1 &"

#Определение путей до папок пользователя
dirs = {}
try:
    for string in open(HOMEFOLDER + "/.config/user-dirs.dirs"):
        if string[0] != "#":
            name, value = string.strip().split('=')
            dirs[name] = value
    DESKFOLDER = dirs["XDG_DESKTOP_DIR"]
    DOWNFOLDER = dirs["XDG_DOWNLOAD_DIR"]
    DOCSFOLDER = dirs["XDG_DOCUMENTS_DIR"]
except FileNotFoundError:
    DESKFOLDER = HOMEFOLDER + "Desktop"
    DOWNFOLDER = HOMEFOLDER + "Downloads"
    DOCSFOLDER = HOMEFOLDER + "Documents"

#Ниже указаны параметры, зависящие от ОС
OS = subprocess.check_output("grep '^ID=' /etc/os-release; exit 0",shell=True, universal_newlines=True).strip().split('=')[1]

if OS == "altlinux":
    #Версия и релиз приложения
    package_info = subprocess.check_output("rpm -q connector; exit 0",shell=True, universal_newlines=True).strip().split('-')
    VERSION = package_info[1]
    RELEASE = package_info[2]

    #Папка монтирования устройств
    udisks2 = subprocess.check_output("/usr/sbin/control udisks2; exit 0",shell=True, universal_newlines=True).strip()
    if udisks2 == 'default':
        USBPATH = "/run/media/$USER"
    if udisks2 == 'shared':
        USBPATH = "/media"

    #Команда проверки наличия в системе Citrix Receiver
    CITRIX_CHECK = "rpm -q ICAClient > "

    #FreeRDP: ключ проброса смарткарт
    SCARD = ' /smartcard:""'

else:
    package_info = subprocess.check_output("dpkg-query -W connector; exit 0",shell=True, universal_newlines=True).strip().split('\t')
    package_info = package_info[1].split("-")
    VERSION = package_info[0]
    RELEASE = package_info[1]

    USBPATH = "/media/$USER"

    CITRIX_CHECK = "dpkg -s icaclient > "

    SCARD = ' /smartcard'

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

try:
    for string in open("/etc/connector/kiosk.access"):
        string = string.upper()
        if string.find("ACCESS") != -1:
            name, value = string.strip().split('=')
            value = value.upper().strip()
            if value == "1" or value == "ON" or value == "YES":
                KIOSK_OFF = False
            else: KIOSK_OFF = True
            break
except FileNotFoundError:
    KIOSK_OFF = True
