#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Модуль управления параметрами Коннектора"""
import pickle, gui
from gi.repository import Gtk
from GLOBAL import *

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
            saveInFile(fileName, DEFAULT)
            return DEFAULT
        else: #если загружаем параметры одного из сохраненных подключений
            dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                    "Файл " + fileName + "\nc сохраненными настройками не найден")
            response = dialog.run()
            dialog.destroy()
            return None
    except pickle.UnpicklingError:
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                 "Файл " + fileName + "\nимеет неверный формат")
        response = dialog.run()
        dialog.destroy()
        return None

def importFromFile(fileName):
    """Импорт параметров из файла .ctor"""
    dbfile = open(fileName, 'rb')
    obj = pickle.load(dbfile)
    dbfile.close()
    return obj	        

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

class Properties(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title = "Параметры программы")
        builder = Gtk.Builder()        
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
        changeRdpFree = builder.get_object("radio_RDP_freeRDP")
        changeVncView = builder.get_object("radio_VNC_viewer")
        self.program = loadFromFile('default.conf')
        if self.program['RDP']:
            changeRdpFree.set_active(True)
        if self.program['VNC']:
            changeVncView.set_active(True)
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
        saveInFile('default.conf',self.program)
        gui.viewStatus(self.statusbar, "Настройки сохранены в файле default.conf...")

    def clearFile(self, filename, title, message):
        """Функция для очисти БД серверов или списка подключений"""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, title)
        dialog.format_secondary_text(message)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            f = open(WORKFOLDER + filename,"w")
            f.close()
            gui.viewStatus(self.statusbar, "Выполнено, изменения вступят в силу после перезапуска...")
        dialog.destroy()    

    def onClearServers(self, widget):
        self.clearFile("servers.db", "Подтвердите очистку БД",
                      "Вы потеряете всю историю посещений!!!")

    def onClearConnects(self, widget):
        self.clearFile("connections.db", "Подтвердите очистку списка подключений",
                      "Все Ваши сохраненные подключения удалятся!!!")

if __name__ == '__main__':
    pass
