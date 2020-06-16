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

from gi import require_version
require_version('Gtk', '3.0')

from pickle import ( load,
                     dump,
                     UnpicklingError )
import myconnector.ui
from gi.repository import Gtk
from myconnector.params import *
from logging import ( getLogger,
                      basicConfig,
                      INFO )
import myconnector.config as config

class FakeLog():
    def info (self, *args, **kwargs): pass
    def error (self, *args, **kwargs): pass
    def warning (self, *args, **kwargs): pass
    def exception (self, *args, **kwargs): pass

log = FakeLog()
os.system("mkdir -p " + LOGFOLDER)

def saveInFile(fileName, obj):
    """Запись параметров в файл:
    saveInFile(<имя файла>, <имя объекта для записи>)"""
    dbfile = open(WORKFOLDER+fileName, 'wb')
    dump( obj, dbfile )
    dbfile.close()

def loadFromFile(fileName, window = None):
    """Загрузка сохраненных параметров из файла"""
    try:
        dbfile = open(WORKFOLDER + fileName, 'rb')
        obj = load( dbfile )
        dbfile.close()
        return obj
    except FileNotFoundError:
        if fileName.find('default.conf') != -1: #если загружаем параметры программы
            #при неудаче - создает файл со значениями по умолчанию
            log.warning ("Файл с настройками по умолчанию (default.conf) не найден, сгенерирован новый!")
            saveInFile(fileName, DEFAULT)
            return DEFAULT
        else: #если загружаем параметры одного из сохраненных подключений
            dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                    "Файл " + fileName + "\nc сохраненными настройками не найден")
            response = dialog.run()
            dialog.destroy()
            log.exception("Файл %s c сохраненными настройками не найден! Подробнее:", fileName)
            return None
    except ( UnpicklingError, EOFError ):
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                 "Файл %s\nимеет неверный формат" % fileName.replace("tmp_",""))
        response = dialog.run()
        dialog.destroy()
        log.exception("Файл %s имеет неверный формат! Подробнее:", fileName.replace("tmp_",""))
        if fileName.find('default.conf') != -1: saveInFile(fileName, DEFAULT); return DEFAULT
        return None

try: enableLog = loadFromFile('default.conf')['LOG']
except KeyError: enableLog = DEFAULT['LOG']
if enableLog:
    log = getLogger( "myconnector" )
    basicConfig (
        filename = LOGFILE,
        format = "--- %(levelname)-10s %(asctime)s --- %(message)s",
        level = INFO)

def importFromFile(fileName, window = None):
    """Импорт параметров из файла .ctor"""
    try:
        dbfile = open(fileName, 'rb')
        obj = load( dbfile )
        dbfile.close()
        return obj
    except ( UnpicklingError, EOFError ):
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                 "Файл " + fileName + "\nимеет неверный формат")
        response = dialog.run()
        dialog.destroy()
        log.exception("Файл %s имеет неверный формат! Подробнее:", fileName)
        return None

def searchSshUser(query):
    """Определение имени пользователя и сервера
    в формате адреса SSH и SFTP - логин@адрес"""
    try:
        login, server = query.strip().split('@')
    except ValueError:
        login = ''
        server = query
    return server, login

def filenameFromName(name):
    """Определение имени конфигурационного файла подключения по имени подключения"""
    try:
        for connect in open(WORKFOLDER + "connections.db"):
            record = connect.strip().split(':::')
            if record[0] == name:
                return record[3]
    except FileNotFoundError:
        log.warning("Файл сохраненных подключений (connections.db) не найден!")
    return False

def nameFromFilename(filename):
    """Определение имени подключения по имени конфигурационного файла"""
    try:
        for connect in open(WORKFOLDER + "connections.db"):
            record = connect.strip().split(':::')
            if record[3] == filename:
                return record[0]
    except FileNotFoundError:
        log.warning("Файл сохраненных подключений (connections.db) не найден!")
    return False

def searchName(name):
    """Существует ли подключение с указанным именем"""
    try:
        for connect in open(WORKFOLDER + "connections.db"):
            record = connect.strip().split(':::')
            if record[0] == name:
                return True
    except FileNotFoundError:
        log.warning("Файл сохраненных подключений (connections.db) не найден!")
    return False

def checkLogFile(filePath):
    """Функция проверки размера лог-файла и его архивация, если он больше 10Мб"""
    if os.path.exists( filePath ):
        sizeLog = int( check_output( "stat -c%%s %s; exit 0" % filePath,
                                     shell=True, universal_newlines=True ).strip() )
        if sizeLog > 10000000:
            import tarfile
            from datetime import datetime
            os.chdir(LOGFOLDER)
            fileName = os.path.basename(filePath)
            #'2017-04-05 15:09:52.981053' -> 20170405:
            dt = datetime.today()
            today = str(dt).split(' ')[0].split('-'); today = ''.join(today)
            tarName = filePath + '.' + today + '.tgz'
            tar = tarfile.open (tarName, "w:gz")
            tar.add(fileName); os.remove(fileName)
            os.chdir(MAINFOLDER)
            tar.close()
            msg = "Логфайл %s превысил допустимый размер (10Мб), упакован в архив %s" % (fileName, os.path.basename(tarName))
            os.system( 'echo "--- INFO       %s  %s" >> %s' % ( str( dt ), msg, LOGFILE ))

class Properties(Gtk.Window):
    def __init__(self, mainWindow):
        Gtk.Window.__init__(self, title = "Параметры программы")
        builder = Gtk.Builder()
        self.main_window = mainWindow
        self.labelRDP = mainWindow.labelRDP
        self.labelVNC = mainWindow.labelVNC
        self.conn_note = mainWindow.conn_note
        self.labelFS = mainWindow.labelFS
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_default_icon_name( "myconnector" )
        builder.add_from_file( "%s/properties.ui" % UIFOLDER )
        builder.connect_signals(self)
        box = builder.get_object("box_properties")
        cancel = builder.get_object("button_cancel")
        self.changeRdpRem = builder.get_object("radio_RDP_remmina")
        self.changeVncRem = builder.get_object("radio_VNC_remmina")
        self.statusbar = builder.get_object("statusbar")
        self.combo_tabs = builder.get_object("combo_tabs")
        self.combo_main = builder.get_object("combo_main")
        self.changeRdpFree = builder.get_object("radio_RDP_freeRDP")
        self.changeVncView = builder.get_object("radio_VNC_viewer")
        self.entryFS = builder.get_object("entry_FS")
        self.checkTray = builder.get_object("check_TRAY")
        self.checkVersion = builder.get_object("check_VERSION")
        self.checkLog = builder.get_object("check_LOG")
        self.combo_sort = builder.get_object("combo_sort")
        self.initParameters()
        self.add(box)
        self.connect("delete-event", self.onClose)
        cancel.connect("clicked", self.onCancel, self)
        self.show_all()

    def initParameters(self):
        """Initializing parameters from a file default.conf"""
        self.defaultConf = loadFromFile('default.conf')
        if self.defaultConf['RDP']:
            self.changeRdpFree.set_active(True)
        if self.defaultConf['VNC']:
            self.changeVncView.set_active(True)
        try: self.combo_tabs.set_active_id(self.defaultConf['TAB'])
        except KeyError: self.combo_tabs.set_active_id('0')
        try: self.combo_main.set_active_id(self.defaultConf['MAIN'])
        except KeyError: self.combo_tabs.set_active_id('0')
        try: self.entryFS.set_text(self.defaultConf['FS'])
        except KeyError: self.entryFS.set_text(DEFAULT['FS'])
        try: self.checkTray.set_active(self.defaultConf['TRAY'])
        except KeyError: self.checkTray.set_active(DEFAULT['TRAY'])
        try: self.checkVersion.set_active(self.defaultConf['CHECK_VERSION'])
        except KeyError: self.checkVersion.set_active(DEFAULT['CHECK_VERSION'])
        try: self.checkLog.set_active(self.defaultConf['LOG'])
        except KeyError: self.checkLog.set_active(DEFAULT['LOG'])
        try: self.combo_sort.set_active_id(self.defaultConf['SORT'])
        except KeyError: self.combo_tabs.set_active_id('0')

    def onCancel (self, button, window):
        window.destroy()

    def onClose (self, window, *args):
        window.destroy()
        self.main_window.onShowWindow()

    def onSave (self, *args):
        """Сохранение настроек программы"""
        if self.changeRdpRem.get_active():
            self.defaultConf['RDP'] = 0
        else: self.defaultConf['RDP'] = 1
        if self.changeVncRem.get_active():
            self.defaultConf['VNC'] = 0
        else: self.defaultConf['VNC'] = 1
        self.defaultConf['TAB'] = self.combo_tabs.get_active_id()
        self.defaultConf['MAIN'] = self.combo_main.get_active_id()
        self.defaultConf['FS'] = self.entryFS.get_text()
        self.defaultConf['TRAY'] = self.checkTray.get_active()
        self.defaultConf['CHECK_VERSION'] = self.checkVersion.get_active()
        self.defaultConf['LOG'] = self.checkLog.get_active()
        self.defaultConf['SORT'] = self.combo_sort.get_active_id()
        saveInFile('default.conf',self.defaultConf)
        myconnector.ui.viewStatus(self.statusbar, "Настройки сохранены в файле default.conf...")
        log.info("Новые настройки для программы сохранены в файле default.conf.")
        if not self.checkLog.get_active(): log.warning("ВЕДЕНИЕ ЖУРНАЛА ПОСЛЕ ПЕРЕЗАПУСКА ПРОГРАММЫ БУДЕТ ОТКЛЮЧЕНО!")
        myconnector.ui.Gui.initLabels(True, self.labelRDP, self.labelVNC, self.labelFS)
        self.conn_note.set_current_page(int(self.defaultConf['TAB']))
        if self.defaultConf['TRAY']:
            if self.main_window.trayDisplayed:
                self.main_window.iconTray.show()
            else: self.main_window.trayDisplayed = myconnector.ui.Gui.initTray(self.main_window)
        else:
            try: self.main_window.iconTray.hide()
            except: pass

    def clearFile(self, filename, title, message):
        """Функция для очисти БД серверов или списка подключений"""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, title)
        dialog.format_secondary_text(message)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            f = open(WORKFOLDER + filename,"w")
            f.close()
            myconnector.ui.viewStatus(self.statusbar, "Выполнено, изменения вступят в силу после перезапуска...")
            log.info("Очищен файл %s", filename)
        dialog.destroy()

    def onClearServers(self, widget):
        self.clearFile("servers.db", "Подтвердите очистку данных автозаполнения",
                      "Вы потеряете всю историю посещений!!!")

    def onClearConnects(self, widget):
        self.clearFile("connections.db", "Подтвердите очистку списка подключений",
                      "Все Ваши сохраненные подключения удалятся!!!")

    def onButtonReset(self,*args):
        """Сброс параметров программы"""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, "Сброс параметров")
        dialog.format_secondary_text("Подтвердите сброс параметров программы к значениям по умолчанию")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            config.init()
            log.info("Выполнен сброс программы к значения по умолчанию.")
        dialog.destroy()
        self.initParameters()

if __name__ == '__main__':
    pass
