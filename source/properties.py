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
        self.changeKioskOff = builder.get_object("radio_kiosk_off")
        self.changeKioskAll = builder.get_object("radio_kiosk_all")
        self.changeKioskCtor = builder.get_object("radio_kiosk_ctor")
        self.entryKioskConn = builder.get_object("entry_kiosk_ctor")
        self.defaultConf = loadFromFile('default.conf')
        if self.defaultConf['RDP']:
            changeRdpFree.set_active(True)
        if self.defaultConf['VNC']:
            changeVncView.set_active(True)
        try:
            if self.defaultConf['KIOSK'] == 1:
                self.changeKioskAll.set_active(True)
            elif self.defaultConf['KIOSK'] == 2:
                self.changeKioskCtor.set_active(True)
                self.entryKioskConn.set_text(self.defaultConf['KIOSK_CONN'])
                self.onKioskEntry(self.entryKioskConn)
            else:
                self.changeKioskOff.set_active(True)
        except KeyError:#если нет такого ключа (например после обновления)
            self.changeKioskOff.set_active(True)
            saveInFile('default.conf', DEFAULT)
        try: self.combo_tabs.set_active_id(self.defaultConf['TAB'])
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
            self.defaultConf['RDP'] = 0
        else: self.defaultConf['RDP'] = 1
        if self.changeVncRem.get_active():
            self.defaultConf['VNC'] = 0
        else: self.defaultConf['VNC'] = 1
        self.defaultConf['TAB'] = self.combo_tabs.get_active_id()
        save = False
        nameConn = self.entryKioskConn.get_text()
        if self.changeKioskAll.get_active():
            self.defaultConf['KIOSK'] = 1
            self.enableKiosk(True)
            save = True
        elif self.changeKioskCtor.get_active():
            if nameConn:
                if not searchName(nameConn):
                    gui.viewStatus(self.statusbar, nameConn + " - подключение с таким именем не найдено!")
                else:
                    self.defaultConf['KIOSK'] = 2
                    self.defaultConf['KIOSK_CONN'] = nameConn
                    self.enableKiosk(False)
                    save = True
            else:
                gui.viewStatus(self.statusbar, "Не введено имя подключения")
        else:
            self.defaultConf['KIOSK'] = 0
            self.disableKiosk()
            save = True
        if save:
            saveInFile('default.conf',self.defaultConf)
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

    def saveXsession(self, wm, all_prog):
        """Сохранение файла ~/.xsession"""
        xsession = open (HOMEFOLDER + "/.xsession", "w")
        if all_prog: #если вся программа должна работать в режиме киоска (передается True)
            xsession.write(wm + KIOSK)
        else:  #если одно из подключений (False):
            xsession.write(wm + " &\nconnector " + self.entryKioskConn.get_text() + KIOSK_ONE)
        xsession.close()
        return True

    def enableKiosk (self, all_prog):
        """Включение режима киоска, создание необходимых для этого файлов"""
        existsXs = False #будет ли записан файл
        marco = int(os.popen('which marco > /dev/null 2> /dev/null; echo $?').read()) #0 если установлено.
        if marco == 0:
            existsXs = self.saveXsession('marco', all_prog)
        else:
            openbox = int(os.popen('which openbox > /dev/null 2> /dev/null; echo $?').read())
            if openbox == 0: existsXs = self.saveXsession('openbox', all_prog)
            else:
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Оконный менеджер не найден!")
                dialog.format_secondary_text("Для работы в режиме киска необходимо\nустановить один из оконных менеджеров:\n- marco\n- openbox")
                response = dialog.run()
                dialog.destroy()
                self.changeKioskAll.set_active(False)#автоматическое снятие галки

        if existsXs:
            try: os.chmod(HOMEFOLDER+"/.xsession", 0o766) #chmod +x
            except FileNotFoundError: pass
            autostartFile = HOMEFOLDER + "/.config/autostart/Ctor_kiosk.desktop"
            os.system("mkdir -p ~/.config/autostart")
            autostart = open (autostartFile, "w")
            autostart.write(KIOSK_X)
            autostart.close()
            os.chmod(autostartFile, 0o766)
        self.onKiosk (self.changeKioskOff, all_prog)

    def disableKiosk (self):
        """Отключение режима киоска"""
        try:
            os.remove(HOMEFOLDER + "/.config/autostart/Ctor_kiosk.desktop")
            os.remove(HOMEFOLDER + "/.xsession")
        except: pass
        self.onKiosk (self.changeKioskOff, False)

    def onKiosk(self, widget, all_prog):
        """Вывод информационных сообщений при вкл/отк режима киоска"""
        if widget.get_active() == False:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, 'Программа настроена на режим "Киоск"')
            if all_prog:
                dialog.format_secondary_text("""При следующем входе в сеанс пользователя
запуститься только программа Connector.
Ctrl+Alt+F1 - вернуться на "Рабочий стол"
*Пункты меню завершения сеанса и работы работают в авторежиме""")
            else:
                dialog.format_secondary_text("""При следующем входе в сеанс пользователя
запуститься только выбранное подключение.
Ctrl+Alt+F1 - вернуться на "Рабочий стол" """)
            response = dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, 'Режим киоска отключен')
            dialog.format_secondary_text("Изменения вступят в силу при следующем входе в сеанс пользователя")
            response = dialog.run()
            dialog.destroy()

    def onKioskEntry(self, widget):
        """Отображение поля ввода имения файла"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.ON)
        except: widget.set_sensitive(True)

    def offKioskEntry(self, widget):
        """Скрытие поля ввода имения файла"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.OFF)
        except: widget.set_sensitive(False)


if __name__ == '__main__':
    pass
