#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

def enabled():
    """Checking 'is root' and OS for access to settings"""
    return (os.getuid() == 0) and (OS == "altlinux")

def check_wm():
    """Checking window manager"""
    for wm in ("marco", "openbox"):
        if int(os.popen("which %s > /dev/null 2> /dev/null; echo $?" % wm).read()) == 0: return wm
    return None

def saveXsession(self, wm, all_prog):
    """Сохранение файла ~/.xsession"""
    xsession = open (HOMEFOLDER + "/.xsession", "w")
    if all_prog: #если вся программа должна работать в режиме киоска (передается True)
        connectorKiosk()
    else:  #если одно из подключений (False):
        xsession.write(wm + " &\nconnector " + self.entryKioskConn.get_text() + KIOSK_ONE)
    xsession.close()
    return True

def enableKiosk (self, all_prog):
    """Включение режима киоска, создание необходимых для этого файлов"""
    existsXs = False #будет ли записан файл
    wm = WIN_MANAGER()
    if wm:
        existsXs = self.saveXsession(wm, all_prog)
    else:
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Оконный менеджер не найден!")
        dialog.format_secondary_text("Для работы в режиме киска необходимо\nустановить один из оконных менеджеров:\n- marco\n- openbox")
        response = dialog.run()
        dialog.destroy()
        self.changeKioskOff.set_active(True)

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
    if not self.boxKiosk.get_sensitive(): return 0 #сообщения не выводятся, если доступ к настройкам киоска отключен
    if widget.get_active() == False:
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, 'Программа настроена на режим "Киоск"')
        if all_prog:
            dialog.format_secondary_text("""При следующем входе в сеанс пользователя
запуститься только программа Connector.
Ctrl+Alt+F1 - вернуться на "Рабочий стол" """)
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
    """Отображение поля ввода имени файла"""
    try: widget.set_button_sensitivity(Gtk.SensitivityType.ON)
    except: widget.set_sensitive(True)

def offKioskEntry(self, widget):
    """Скрытие поля ввода имени файла"""
    try: widget.set_button_sensitivity(Gtk.SensitivityType.OFF)
    except: widget.set_sensitive(False)

def onSave (self, *args):
    """Сохранение настроек программы"""
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
    # Отключаем трей при включении одного из режимов киоска
    if self.changeKioskAll.get_active() or self.changeKioskCtor.get_active(): self.defaultConf['TRAY'] = False; self.checkTray.set_active(False)

class Kiosk(Gtk.Windows):
    def __init__(self):
        Gtk.Window.__init__(self, title = "Параметры режима \"КИОСК\"")
        builder = Gtk.Builder()
        builder.add_from_file("data/kiosk.glade")
        builder.connect_signals(self)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_default_icon_name("connector")
        self.changeKioskOff = builder.get_object("radio_kiosk_off")
        self.changeKioskAll = builder.get_object("radio_kiosk_all")
        self.changeKioskCtor = builder.get_object("radio_kiosk_ctor")
        self.entryKioskConn = builder.get_object("entry_kiosk_ctor")
        self.boxKiosk = builder.get_object("frame_kiosk")
        self.defaultConf = loadFromFile('default.conf')#need fix
        try:
            if self.defaultConf['KIOSK'] == 1:
                self.changeKioskAll.set_active(True)
            elif self.defaultConf['KIOSK'] == 2:
                self.changeKioskCtor.set_active(True)
                self.entryKioskConn.set_text(self.defaultConf['KIOSK_CONN'])
                self.onKioskEntry(self.entryKioskConn)
            else:
                self.changeKioskOff.set_active(True)
        except KeyError:
            self.changeKioskOff.set_active(True)
            saveInFile('default.conf', DEFAULT)

if __name__ == '__main__':
    pass
