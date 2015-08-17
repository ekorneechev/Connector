#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

#Определение домашней папки пользователя
HOMEFOLDER = os.getenv('HOME')

#Директория в домашней папке пользователя для хранения настроек и подключений
WORKFOLDER = HOMEFOLDER + '/.connector/'

#Установки по умолчанию для параметров программы (какие приложения использовать)
DEFAULT = dict(RDP = 1, VNC = 0) 

#Версия приложения
VERSION = "1.3.19"

#Исходные данные для ярлыка подключения
DESKTOP_INFO ="""#!/usr/bin/env xdg-open
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=/usr/share/connector/data/emblem.png
"""

#Запускаемый файл приложения
EXEC = "/usr/bin/connector "
