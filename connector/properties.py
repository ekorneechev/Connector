#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Модуль управления параметрами Коннектора"""
import pickle, gui
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from GLOBAL import *
import logging, tarfile

os.system("mkdir -p " + LOGFOLDER)
logging.basicConfig (
    filename = LOGFILE,
    format = "--- %(levelname)-10s %(asctime)s --- %(message)s",
    level = logging.INFO
)

log = logging.getLogger("connector")

def loadFromFile(fileName, window = None):
    """Загрузка сохраненных параметров из файла"""
    try: 
        dbfile = open(WORKFOLDER + fileName, 'rb')
        obj = pickle.load(dbfile)
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
    except pickle.UnpicklingError:
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                 "Файл " + fileName + "\nимеет неверный формат")
        response = dialog.run()
        dialog.destroy()
        log.exception("Файл %s имеет неверный формат! Подробнее:", fileName)
        return None

def importFromFile(fileName, window = None):
    """Импорт параметров из файла .ctor"""
    try:
        dbfile = open(fileName, 'rb')
        obj = pickle.load(dbfile)
        dbfile.close()
        return obj
    except pickle.UnpicklingError:
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                 "Файл " + fileName + "\nимеет неверный формат")
        response = dialog.run()
        dialog.destroy()
        log.exception("Файл %s имеет неверный формат! Подробнее:", fileName)
        return None

def saveInFile(fileName, obj):
    """Запись параметров в файл:
    saveInFile(<имя файла>, <имя объекта для записи>)"""
    dbfile = open(WORKFOLDER+fileName, 'wb')
    pickle.dump(obj, dbfile)
    dbfile.close()

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
    exists = not bool(int(subprocess.check_output("stat " + filePath + " > /dev/null 2>&1; echo $?; exit 0", 
                                                  shell=True, universal_newlines=True).strip()))
    if exists:
        sizeLog = int(subprocess.check_output("stat -c%s " + filePath + "; exit 0",
                                              shell=True, universal_newlines=True).strip())
        if sizeLog > 10000000:
            import tarfile; from datetime import datetime
            defaultPath = os.getcwd()
            os.chdir(LOGFOLDER)
            fileName = os.path.basename(filePath)
            #'2017-04-05 15:09:52.981053' -> 20170405:
            dt = datetime.today()
            today = str(dt).split(' ')[0].split('-'); today = ''.join(today)
            tarName = filePath + '.' + today + '.tgz'
            tar = tarfile.open (tarName, "w:gz")
            tar.add(fileName); os.remove(fileName)
            os.chdir(defaultPath)
            tar.close()
            msg = "Логфайл %s превысил допустимый размер (10Мб), упакован в архив %s" % (fileName, os.path.basename(tarName))
            if filePath == LOGFILE:
                os.system('echo "--- INFO       ' + str(dt) + ' ' + msg + '" > ' + LOGFILE)
            else: log.info(msg)

class Properties(Gtk.Window):
    def __init__(self, rdp, vnc):
        Gtk.Window.__init__(self, title = "Параметры программы")
        builder = Gtk.Builder()
        self.labelRDP, self.labelVNC = rdp, vnc
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_default_icon_name("gtk-preferences")
        builder.add_from_file("data/properties.glade")
        builder.connect_signals(self)
        box = builder.get_object("box_properties")
        cancel = builder.get_object("button_cancel")
        self.changeRdpRem = builder.get_object("radio_RDP_remmina")
        self.changeVncRem = builder.get_object("radio_VNC_remmina")
        self.statusbar = builder.get_object("statusbar")
        self.combo_tabs = builder.get_object("combo_tabs")
        changeRdpFree = builder.get_object("radio_RDP_freeRDP")
        changeVncView = builder.get_object("radio_VNC_viewer")
        self.program = loadFromFile('default.conf')
        if self.program['RDP']:
            changeRdpFree.set_active(True)
        if self.program['VNC']:
            changeVncView.set_active(True)
        try: self.combo_tabs.set_active_id(self.program['TAB'])
        except KeyError: self.combo_tabs.set_active_id('0')
        self.add(box)        
        self.connect("delete-event", self.onClose)
        cancel.connect("clicked", self.onCancel, self)
        self.show_all()

    def onCancel (self, button, window):
        window.destroy()

    def onClose (self, window, *args):
        window.destroy()
    
    def onSave (self, *args):
        """Сохранение настроек программ по умолчанию"""
        if self.changeRdpRem.get_active():
            self.program['RDP'] = 0
        else: self.program['RDP'] = 1
        if self.changeVncRem.get_active():
            self.program['VNC'] = 0
        else: self.program['VNC'] = 1
        self.program['TAB'] = self.combo_tabs.get_active_id()
        saveInFile('default.conf',self.program)
        gui.viewStatus(self.statusbar, "Настройки сохранены в файле default.conf...")
        log.info("Новые настройки для программы сохранены в файле default.conf.")
        gui.Gui.initLabels(True, self.labelRDP, self.labelVNC)

    def clearFile(self, filename, title, message):
        """Функция для очисти БД серверов или списка подключений"""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, title)
        dialog.format_secondary_text(message)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            f = open(WORKFOLDER + filename,"w")
            f.close()
            gui.viewStatus(self.statusbar, "Выполнено, изменения вступят в силу после перезапуска...")
            log.info("Очищен файл %s", filename)
        dialog.destroy()    

    def onClearServers(self, widget):
        self.clearFile("servers.db", "Подтвердите очистку БД",
                      "Вы потеряете всю историю посещений!!!")

    def onClearConnects(self, widget):
        self.clearFile("connections.db", "Подтвердите очистку списка подключений",
                      "Все Ваши сохраненные подключения удалятся!!!")

if __name__ == '__main__':
    pass
