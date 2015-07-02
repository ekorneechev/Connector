#!/usr/bin/python3
# -*- coding: utf-8 -*-

from ctor import *
from gi.repository import Gtk, Gdk, GdkPixbuf
import random, sys, webbrowser
from GLOBAL import *


def viewStatus(bar, message):
    """Функция отображения происходящих действий в строке состояния"""
    message = message[:65] + '...' if len(message) > 65 else message #для обреза длинных сообщений
    bar.push(bar.get_context_id ("statusbar"), message)    

def connectFile(filename):
    """Функция запуска программы с аргументом - именем файла, или с ярлыка
       или из командной строки: connector <filename>"""
    try:
        parameters = properties.loadFromFile(filename)
        if parameters != None:
            protocol = parameters.pop(0)
            connect = definition(protocol)
            connect.start(parameters)
    except (IndexError, KeyError): os.system("zenity --error --text='Проверьте настройки программ по умолчанию' --no-wrap")

class Gui:
    def __init__(self):
        self.prefClick = False
        self.editClick = False
        self.builder = Gtk.Builder()
        self.builder.add_from_file("data/gui.glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("main_window")
        self.window.set_title("Connector v." + VERSION)
        self.statusbar = self.builder.get_object("statusbar")
        self.liststore = {'RDP' : self.builder.get_object("liststore_RDP"),
                          'VNC' : self.builder.get_object("liststore_VNC"),
                          'SSH' : self.builder.get_object("liststore_SSH"),
                          'SFTP' : self.builder.get_object("liststore_SFTP"),
                          'VMWARE' : self.builder.get_object("liststore_VMWARE"),
                          'CITRIX' : self.builder.get_object("liststore_CITRIX"),
                          'XDMCP' : self.builder.get_object("liststore_XDMCP"),
                          'NX' : self.builder.get_object("liststore_NX")}

        self.liststore_connect = Gtk.ListStore(str, str, str, str)
        self.getSavesFromDb()#запись из файла в ListStore
        self.filterConnections = self.liststore_connect.filter_new()        
        self.filterConnections.set_visible_func(self.listFilter) #добавление фильтра для поиска
        self.currentFilter = ''
        self.sortedFiltered = Gtk.TreeModelSort(model = self.filterConnections)
        self.treeview = self.builder.get_object("treeview_connections")
        self.treeview.set_model(self.sortedFiltered)
        self.getServersFromDb()
        self.citrixEditClick = False

    def onDeleteWindow(self, *args):
        """Закрытие программы"""
        Gtk.main_quit(*args)
    
    def onViewAbout(self, *args):
        """Создает диалоговое окно 'О программе'"""
        about = Gtk.AboutDialog("О программе Connector", self.window)
        about.set_program_name("Connector")
        comments = """Программа-фронтэнд для удаленного администрирования 
                      компьютеров с различными операционными системами. 
                      Поддерживаются все распространненные типы подключения.""".replace('  ','')
        about.set_comments(comments)
        about.set_version(VERSION)
        about.set_copyright("© Корнеечев Е.А., 2014-2015\ne-mail(PayPal): ekorneechev@gmail.com\nWMR: R305760666573, WMZ: Z841082507423, QIWI: +79208771688")
        logo = GdkPixbuf.Pixbuf.new_from_file("data/emblem.png")
        about.set_logo(logo)
        about.run()
        about.destroy()

    def createOpenDialog(self, title):
        """Создание диалога открытия файла"""
        dialog = Gtk.FileChooserDialog(title, self.window,
            Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        self.addFilters(dialog)
        dialog.set_current_folder(HOMEFOLDER)
        return dialog

    def onOpenFile(self, *args):
        """Открытие файла для мгновенного подключения"""
        dialog = self.createOpenDialog("Открытие файла с конфигурацией подключения")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            basename = os.path.basename(filename)
            os.system('cp "' + filename + '" ' + WORKFOLDER)
            os.chdir(WORKFOLDER)
            filename = 'tmp_' + basename
            os.rename(basename, filename)            
            connectFile(filename)
            os.remove(filename)
            viewStatus(self.statusbar, "Открывается файл " + dialog.get_filename())
        else:
            viewStatus(self.statusbar, "Файл не был выбран")
        dialog.destroy()

    def onImportFile(self, *args):
        """Открытие файла для изменения и дальнейшего подключения"""
        dialog = self.createOpenDialog("Импорт файла с конфигурацией подключения")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            parameters = properties.importFromFile(filename)
            if parameters != None:
                if self.correctProgramm(parameters):
                    protocol = parameters.pop(0)
                    if protocol != 'CITRIX':
                        analogEntry = self.AnalogEntry(protocol, parameters)
                        self.onButtonPref(analogEntry)
                        viewStatus(self.statusbar, "Импортируемый файл: " + filename)
                    else:
                        self.onCitrixEdit('', parameters[0])
                else:
                    dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                            "Не удается импортировать файл:\nневерный формат " + parameters[0] + "-подключения!")
                    dialog.format_secondary_text("Попробуйте изменить программу по умолчанию в параметрах приложения")
                    response = dialog.run()
                    dialog.destroy()                    
        else:
            viewStatus(self.statusbar, "Файл не был выбран")
        dialog.destroy()

    def addFilters(self, dialog):
        filter_ctor = Gtk.FileFilter()
        filter_ctor.set_name("Файлы подключений *.ctor")
        filter_ctor.add_pattern("*.ctor")
        dialog.add_filter(filter_ctor)
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Все файлы")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)
    
    def onButtonConnect(self, entry):
        """Сигнал кнопке для быстрого подключения к указанному в entry серверу"""
        server = entry.get_text()
        protocol = entry.get_name()        
        if server:
            connect = definition(protocol) #по имени виджета (указан в glade) определить протокол
            if self.prefClick: #если нажата кнопка Доп. Параметры
                parameters = self.applyPreferences(protocol)
                parameters.insert(0, server)
                connect.start(parameters)
            else: connect.start(server)
            viewStatus(self.statusbar, "Подключение к серверу " + server + "...")
            self.writeServerInDb(entry)                  
        else:
            viewStatus(self.statusbar, "Введите адрес сервера")

    def onCitrixPref(self, *args):
        Citrix.preferences()

    def changeProgram(self, protocol):
        #Функция, возвращающая RDP1 или VNC1 при параметрах, отличных от Реммины
        try: 
            if self.whatProgram[protocol]: protocol += "1"
        except KeyError: 
            pass #если нет возможности выбора программ для протокола
        return protocol              

    def onButtonPref(self, entry_server, nameConnect = ''):
        """Дополнительные параметры подключения к серверу. 
        Доступно как с кнопки, так и из пункта меню 'Подключение'"""
        self.pref_window = Gtk.Window()
        self.prefClick = True #для определения нажатия на кнопку Доп. параметры
        name = entry_server.get_name() ; tmp = name
        server = entry_server.get_text()
        self.pref_window.set_title("Параметры " + name + "-подключения")
        self.pref_window.set_icon_from_file("data/" + name + ".png")
        self.pref_window.set_position(Gtk.WindowPosition.CENTER)
        self.pref_window.set_resizable(False)
        self.pref_window.set_modal(True)
        self.pref_window.resize(400, 400)
        self.pref_builder = Gtk.Builder()
        self.pref_builder.add_from_file("data/pref_gui.glade")     
        self.pref_builder.connect_signals(self)
        self.whatProgram = properties.loadFromFile('default.conf')
        name = self.changeProgram(name)
        entryName = self.pref_builder.get_object("entry_" + name + "_name")
        if nameConnect: entryName.set_text(nameConnect)
        box = self.pref_builder.get_object("box_" + name)
        combo = self.pref_builder.get_object("combo_" + name)   
        combo.set_model(self.liststore[tmp])
        serv = self.pref_builder.get_object("entry_" + name + "_serv")
        serv.set_text(server)
        cancel = self.pref_builder.get_object("button_" +name+"_cancel")
        cancel.connect("clicked", self.onCancel, self.pref_window)
        self.pref_window.connect("delete-event", self.onClose)
        self.initPreferences(tmp)
        try: 
            args = entry_server.loadParameters()
            self.setPreferences(tmp, args)
        except AttributeError: pass
        self.pref_window.add(box)
        self.pref_window.show_all()

    def setPreferences(self, protocol, args):
        """В этой функции параметры загружаются из сохраненного файла"""
        if protocol == 'VNC' and self.whatProgram['VNC'] == 1:
            if args[1] != '': self.VNC_viewmode.set_active(True)
            if args[2] != '': self.VNC_viewonly.set_active(True)
            if args[3] != '': self.VNC_showcursor.set_active(True)
            else: self.VNC_showcursor.set_active(False) #требуется если по умолчанию галка стоит (относится ко всем протоколам)

        if protocol == 'VNC' and self.whatProgram['VNC'] == 0:
            self.VNC_user.set_text(args[1])
            self.VNC_quality.set_active_id(args[2])
            self.VNC_color.set_active_id(args[3])
            if args[4] == 4: self.VNC_viewmode.set_active(True)
            if args[5]: self.VNC_viewonly.set_active(True)
            if args[6]: self.VNC_crypt.set_active(True)
            if args[7]: self.VNC_clipboard.set_active(True)
            if args[8]: self.VNC_showcursor.set_active(True)
            else: self.VNC_showcursor.set_active(False)

        if protocol == 'VMWARE':            
            self.VMWARE_user.set_text(args[1])
            self.VMWARE_domain.set_text(args[2])
            self.VMWARE_password.set_text(args[3])
            self.VMWARE_fullscreen.set_active(args[4])

        if protocol == 'XDMCP':
            self.XDMCP_color.set_active_id(args[1])
            if args[2] == 4: self.XDMCP_viewmode.set_active(True)
            if args[3] == '': self.XDMCP_resol_default.set_active(True)
            else:
                XDMCP_resol_hand = self.pref_builder.get_object("radio_XDMCP_resol_hand")
                XDMCP_resol_hand.set_active(True)
                self.XDMCP_resolution.set_active_id(args[3])
            if args[4]: self.XDMCP_once.set_active(True)
            if args[5]: self.XDMCP_showcursor.set_active(True)
            self.XDMCP_exec.set_text(args[6])

        if protocol == 'SSH':
            self.SSH_user.set_text(args[1])
            if args[2] == 2: self.SSH_publickey.set_active(True)
            elif args[2] == 1: self.SSH_keyfile.set_active(True)
            else:
                SSH_pwd = self.pref_builder.get_object("radio_SSH_pwd")
                SSH_pwd.set_active(True)
            self.SSH_path_keyfile.set_filename(args[3])
            self.SSH_charset.set_text(args[4])
            self.SSH_exec.set_text(args[5])

        if protocol == 'SFTP':
            self.SFTP_user.set_text(args[1])
            if args[2] == 2: self.SFTP_publickey.set_active(True)
            elif args[2] == 1: self.SFTP_keyfile.set_active(True)
            else:
                SFTP_pwd = self.pref_builder.get_object("radio_SFTP_pwd")
                SFTP_pwd.set_active(True)
            self.SFTP_path_keyfile.set_filename(args[3])
            self.SFTP_charset.set_text(args[4])
            self.SFTP_execpath.set_text(args[5])

        if protocol == 'NX':
            self.NX_user.set_text(args[1])
            self.NX_quality.set_active_id(args[2])
            if args[3] == '': self.NX_resol_window.set_active(True)
            else:
                NX_resol_hand = self.pref_builder.get_object("radio_NX_resol_hand")
                NX_resol_hand.set_active(True)
                self.NX_resolution.set_active_id(args[3])
            if args[4] == 4: self.NX_viewmode.set_active(True)
            if args[5] == '': self.NX_keyfile.set_active(False)
            else:
                self.NX_keyfile.set_active(True)
                self.NX_path_keyfile.set_filename(args[5])
            if args[6]: self.NX_crypt.set_active(True)
            if args[7]: self.NX_clipboard.set_active(True)
            self.NX_exec.set_text(args[8])

        if protocol == 'RDP' and self.whatProgram['RDP'] == 0:
            self.RDP_user.set_text(args[1])
            self.RDP_domain.set_text(args[2])
            self.RDP_color.set_active_id(args[3])
            self.RDP_quality.set_active_id(args[4])
            if args[5] == '': self.RDP_resol_default.set_active(True)
            else:
                RDP_resol_hand = self.pref_builder.get_object("radio_RDP_resol_hand")
                RDP_resol_hand.set_active(True)
                self.RDP_resolution.set_active_id(args[5])
            if args[6] == 3: self.RDP_viewmode.set_active(True)
            else: self.RDP_viewmode.set_active(False)
            if args[7] == '': self.RDP_share_folder.set_active(False)
            else:
                self.RDP_share_folder.set_active(True)
                self.RDP_name_folder.set_filename(args[7])
            if args[8]: self.RDP_printers.set_active(True)
            if args[9]: self.RDP_clipboard.set_active(False)
            self.RDP_sound.set_active_id(args[10])
            if args[11]: self.RDP_cards.set_active(True)

        if protocol == 'RDP' and self.whatProgram['RDP'] == 1:
            self.RDP_user.set_text(args[1])
            self.RDP_domain.set_text(args[2])
            if args[3]: self.RDP_fullscreen.set_active(True)
            else: self.RDP_fullscreen.set_active(False)
            if args[4]: self.RDP_clipboard.set_active(True)
            else: self.RDP_clipboard.set_active(False)
            if args[5] == '': self.RDP_resol_default.set_active(True)
            else:
                RDP_resol_hand = self.pref_builder.get_object("radio_RDP1_resol_hand")
                RDP_resol_hand.set_active(True)
                self.RDP_resolution.set_text(args[5])
            self.RDP_color.set_active_id(args[6])
            if args[7] == '': self.RDP_share_folder.set_active(False)
            else:
                self.RDP_share_folder.set_active(True)
                self.RDP_name_folder.set_filename(args[7])
            self.RDP_gserver.set_text(args[8])
            self.RDP_guser.set_text(args[9])
            self.RDP_gdomain.set_text(args[10])
            self.RDP_gpasswd.set_text(args[11])
            if args[12]: self.RDP_admin.set_active(True)
            else: self.RDP_admin.set_active(False)


    def initPreferences(self, protocol):
        """В этой функции определяются различные для протоколов параметры"""
        if protocol == 'RDP' and self.whatProgram['RDP'] == 0:
            self.RDP_user = self.pref_builder.get_object("entry_RDP_user")
            self.RDP_domain = self.pref_builder.get_object("entry_RDP_dom")            
            self.RDP_color = self.pref_builder.get_object("entry_RDP_color")
            self.RDP_quality = self.pref_builder.get_object("entry_RDP_quality")
            self.RDP_resolution = self.pref_builder.get_object("entry_RDP_resolution")
            self.RDP_viewmode = self.pref_builder.get_object("check_RDP_fullscreen")
            self.RDP_resol_default = self.pref_builder.get_object("radio_RDP_resol_default")
            self.RDP_share_folder = self.pref_builder.get_object("check_RDP_folder")
            self.RDP_name_folder = self.pref_builder.get_object("RDP_share_folder")
            self.RDP_name_folder.set_current_folder(HOMEFOLDER)
            self.RDP_printers = self.pref_builder.get_object("check_RDP_printers")
            self.RDP_clipboard = self.pref_builder.get_object("check_RDP_clipboard")
            self.RDP_sound = self.pref_builder.get_object("entry_RDP_sound")
            self.RDP_cards = self.pref_builder.get_object("check_RDP_cards")        
  

        if protocol == 'RDP' and self.whatProgram['RDP'] == 1:
            self.RDP_user = self.pref_builder.get_object("entry_RDP1_user")
            self.RDP_domain = self.pref_builder.get_object("entry_RDP1_dom")            
            self.RDP_color = self.pref_builder.get_object("entry_RDP1_color")
            self.RDP_resolution = self.pref_builder.get_object("entry_RDP1_resolution")
            self.RDP_resolution.set_sensitive(False)
            self.RDP_fullscreen = self.pref_builder.get_object("check_RDP1_fullscreen")
            self.RDP_resol_default = self.pref_builder.get_object("radio_RDP1_resol_default")
            self.RDP_share_folder = self.pref_builder.get_object("check_RDP1_folder")
            self.RDP_name_folder = self.pref_builder.get_object("RDP1_share_folder")
            self.RDP_name_folder.set_current_folder(HOMEFOLDER)
            self.RDP_clipboard = self.pref_builder.get_object("check_RDP1_clipboard")
            self.RDP_guser = self.pref_builder.get_object("entry_RDP1_guser")
            self.RDP_gdomain = self.pref_builder.get_object("entry_RDP1_gdom") 
            self.RDP_gserver = self.pref_builder.get_object("entry_RDP1_gserv")
            self.RDP_gpasswd = self.pref_builder.get_object("entry_RDP1_gpwd")
            self.RDP_admin = self.pref_builder.get_object("check_RDP1_adm")    

        if protocol == 'NX':
            self.NX_user = self.pref_builder.get_object("entry_NX_user")
            self.NX_keyfile = self.pref_builder.get_object("check_NX_keyfile")
            self.NX_path_keyfile = self.pref_builder.get_object("NX_keyfile")   
            self.NX_path_keyfile.set_current_folder(HOMEFOLDER)        
            self.NX_quality = self.pref_builder.get_object("entry_NX_quality")            
            self.NX_resolution = self.pref_builder.get_object("entry_NX_resolution")
            self.NX_viewmode = self.pref_builder.get_object("check_NX_fullscreen")
            self.NX_resol_window = self.pref_builder.get_object("radio_NX_resol_window")
            self.NX_exec = self.pref_builder.get_object("entry_NX_exec")
            self.NX_crypt = self.pref_builder.get_object("check_NX_crypt")
            self.NX_clipboard = self.pref_builder.get_object("check_NX_clipboard")

        if protocol == 'VNC' and self.whatProgram['VNC'] == 0:
            self.VNC_user = self.pref_builder.get_object("entry_VNC_user")            
            self.VNC_color = self.pref_builder.get_object("entry_VNC_color")    
            self.VNC_quality = self.pref_builder.get_object("entry_VNC_quality")
            self.VNC_viewmode = self.pref_builder.get_object("check_VNC_fullscreen")
            self.VNC_viewonly = self.pref_builder.get_object("check_VNC_viewonly")
            self.VNC_showcursor = self.pref_builder.get_object("check_VNC_showcursor")
            self.VNC_crypt = self.pref_builder.get_object("check_VNC_crypt")
            self.VNC_clipboard = self.pref_builder.get_object("check_VNC_clipboard")

        if protocol == 'VNC' and self.whatProgram['VNC'] == 1:
            self.VNC_viewmode = self.pref_builder.get_object("check_VNC1_fullscreen")
            self.VNC_viewonly = self.pref_builder.get_object("check_VNC1_viewonly")
            self.VNC_showcursor = self.pref_builder.get_object("check_VNC1_showcursor")

        if protocol == 'XDMCP':
            self.XDMCP_color = self.pref_builder.get_object("entry_XDMCP_color")
            self.XDMCP_resolution = self.pref_builder.get_object("entry_XDMCP_resolution")
            self.XDMCP_viewmode = self.pref_builder.get_object("check_XDMCP_fullscreen")
            self.XDMCP_resol_default = self.pref_builder.get_object("radio_XDMCP_resol_default")
            self.XDMCP_showcursor = self.pref_builder.get_object("check_XDMCP_showcursor")
            self.XDMCP_once = self.pref_builder.get_object("check_XDMCP_once")
            self.XDMCP_exec = self.pref_builder.get_object("entry_XDMCP_exec")

        if protocol == 'SSH':            
            self.SSH_user = self.pref_builder.get_object("entry_SSH_user")
            self.SSH_publickey = self.pref_builder.get_object("radio_SSH_publickey")
            self.SSH_keyfile = self.pref_builder.get_object("radio_SSH_keyfile")
            self.SSH_path_keyfile = self.pref_builder.get_object("SSH_keyfile")   
            self.SSH_path_keyfile.set_current_folder(HOMEFOLDER)
            self.SSH_exec = self.pref_builder.get_object("entry_SSH_exec")
            self.SSH_charset = self.pref_builder.get_object("entry_SSH_charset")

        if protocol == 'SFTP':            
            self.SFTP_user = self.pref_builder.get_object("entry_SFTP_user")
            self.SFTP_publickey = self.pref_builder.get_object("radio_SFTP_publickey")
            self.SFTP_keyfile = self.pref_builder.get_object("radio_SFTP_keyfile")
            self.SFTP_path_keyfile = self.pref_builder.get_object("SFTP_keyfile")   
            self.SFTP_path_keyfile.set_current_folder(HOMEFOLDER)
            self.SFTP_execpath = self.pref_builder.get_object("entry_SFTP_execpath")
            self.SFTP_charset = self.pref_builder.get_object("entry_SFTP_charset")

        if protocol == 'VMWARE':
            self.VMWARE_user = self.pref_builder.get_object("entry_VMWARE_user")
            self.VMWARE_domain = self.pref_builder.get_object("entry_VMWARE_dom")
            self.VMWARE_password = self.pref_builder.get_object("entry_VMWARE_pwd")
            self.VMWARE_fullscreen = self.pref_builder.get_object("check_VMWARE_fullscreen")

    def applyPreferences(self, protocol):
        """В этой функции параметры для подключения собираются из окна Доп. параметры в список"""

        if protocol == 'VMWARE':
            user = self.VMWARE_user.get_text()
            domain = self.VMWARE_domain.get_text()
            password = self.VMWARE_password.get_text()
            fullscreen = self.VMWARE_fullscreen.get_active()
            args = [user, domain, password, fullscreen]            
        
        if protocol == 'RDP' and self.whatProgram['RDP'] == 0:
            user = self.RDP_user.get_text()
            domain = self.RDP_domain.get_text()
            color = self.RDP_color.get_active_id()
            quality = self.RDP_quality.get_active_id()
            sound = self.RDP_sound.get_active_id() 
            if self.RDP_viewmode.get_active(): viewmode = 3
            else: viewmode = 0
            if self.RDP_resol_default.get_active(): resolution = ''
            else: resolution = self.RDP_resolution.get_active_id()
            if self.RDP_share_folder.get_active(): folder = self.RDP_name_folder.get_filename()
            else: folder = ''
            if self.RDP_printers.get_active(): printer = 1
            else: printer = 0
            if self.RDP_clipboard.get_active(): clipboard = 0
            else: clipboard = 1
            if self.RDP_cards.get_active(): smartcards = 1
            else: smartcards = 0
            args = [user, domain, color, quality, resolution, viewmode, folder, printer, clipboard, sound, smartcards]

        if protocol == 'RDP' and self.whatProgram['RDP'] == 1:
            user = self.RDP_user.get_text()
            domain = self.RDP_domain.get_text()
            color = self.RDP_color.get_active_id()
            if self.RDP_fullscreen.get_active(): fullscreen = 1
            else: fullscreen = 0
            if self.RDP_clipboard.get_active(): clipboard = 1
            else: clipboard = 0
            if self.RDP_resol_default.get_active(): resolution = ''
            else: resolution = self.RDP_resolution.get_text()
            if self.RDP_share_folder.get_active(): folder = self.RDP_name_folder.get_filename()
            else: folder = ''
            gserver = self.RDP_gserver.get_text()
            guser = self.RDP_guser.get_text()
            gdomain = self.RDP_gdomain.get_text()
            gpasswd = self.RDP_gpasswd.get_text()
            if self.RDP_admin.get_active(): admin = 1
            else: admin = 0
            args = [user, domain, fullscreen, clipboard, resolution, color, folder, gserver, guser, gdomain, gpasswd, admin]

        if protocol == 'NX':
            user = self.NX_user.get_text()
            quality = self.NX_quality.get_active_id()
            _exec = self.NX_exec.get_text()
            if self.NX_crypt.get_active(): crypt = 1
            else: crypt = 0
            if self.NX_clipboard.get_active(): clipboard = 1
            else: clipboard = 0
            if self.NX_keyfile.get_active(): keyfile = self.NX_path_keyfile.get_filename()
            else: keyfile = ''      
            if self.NX_viewmode.get_active(): viewmode = 4
            else: viewmode = 1
            if self.NX_resol_window.get_active(): resolution = ''
            else: resolution = self.NX_resolution.get_active_id()
            args = [user, quality, resolution, viewmode, keyfile, crypt, clipboard, _exec]
        
        if protocol == 'VNC' and self.whatProgram['VNC'] == 0:
            user = self.VNC_user.get_text()
            quality = self.VNC_quality.get_active_id()
            color = self.VNC_color.get_active_id()
            if self.VNC_crypt.get_active(): crypt = 1
            else: crypt = 0
            if self.VNC_clipboard.get_active(): clipboard = 1
            else: clipboard = 0   
            if self.VNC_viewmode.get_active(): viewmode = 4
            else: viewmode = 1
            if self.VNC_viewonly.get_active(): viewonly = 1
            else: viewonly = 0
            if self.VNC_showcursor.get_active(): showcursor = 1
            else: showcursor = 0
            args = [user, quality, color, viewmode, viewonly, crypt, clipboard, showcursor]

        if protocol == 'VNC' and self.whatProgram['VNC'] == 1:
            if self.VNC_viewmode.get_active(): viewmode = "-FullScreen "
            else: viewmode = ""
            if self.VNC_viewonly.get_active(): viewonly = "-ViewOnly "
            else: viewonly = ""
            if self.VNC_showcursor.get_active(): showcursor = "-UseLocalCursor "
            else: showcursor = ""
            args = [viewmode, viewonly, showcursor]

        if protocol == 'XDMCP':
            color = self.XDMCP_color.get_active_id()
            _exec = self.XDMCP_exec.get_text()
            if self.XDMCP_viewmode.get_active(): viewmode = 4
            else: viewmode = 1
            if self.XDMCP_resol_default.get_active(): resolution = ''
            else: resolution = self.XDMCP_resolution.get_active_id()
            if self.XDMCP_showcursor.get_active(): showcursor = 1
            else: showcursor = 0
            if self.XDMCP_once.get_active(): once = 1
            else: once = 0
            args = [color, viewmode, resolution, once, showcursor, _exec]            

        if protocol == 'SSH':
            user = self.SSH_user.get_text()
            charset = self.SSH_charset.get_text()
            if not charset: charset = 'UTF-8'
            _exec = self.SSH_exec.get_text()
            if self.SSH_publickey.get_active(): 
                SSH_auth = 2
            elif self.SSH_keyfile.get_active(): 
                SSH_auth = 1                
            else: SSH_auth = 0
            if SSH_auth == 1: 
                keyfile = self.SSH_path_keyfile.get_filename()
            else: keyfile = ''         
            args = [user, SSH_auth, keyfile, charset, _exec]

        if protocol == 'SFTP':
            user = self.SFTP_user.get_text()
            charset = self.SFTP_charset.get_text()
            if not charset: charset = 'UTF-8'
            execpath = self.SFTP_execpath.get_text()
            if self.SFTP_publickey.get_active(): 
                SSH_auth = 2
            elif self.SFTP_keyfile.get_active(): 
                SSH_auth = 1                
            else: SSH_auth = 0
            if SSH_auth == 1: 
                keyfile = self.SFTP_path_keyfile.get_filename()
            else: keyfile = ''         
            args = [user, SSH_auth, keyfile, charset, execpath]    

        return args

    def onCancel (self, button, window):
        """Нажатие кнопки Отмена в окне доп. параметров"""
        window.destroy()
        self.prefClick = False
        self.editClick = False

    def onClose (self, window, *args):
        """Закрытие окна доп. параметров"""
        window.destroy()
        self.prefClick = False
        self.editClick = False

    def onFolderChoose(self, widget, *args):
        """При нажатии на выбор папки в окне доп. параметров"""
        widget.set_active(True)       

    def onNextPage(self, widget):
        """Переход на следующую вкладку"""
        if widget.get_current_page() < widget.get_n_pages() - 1:
            widget.next_page()
        else: widget.set_current_page(0)

    def onPrevPage(self, widget):
        """Переход на предыдущую вкладку"""
        if widget.get_current_page() == 0:
            widget.set_current_page(widget.get_n_pages() - 1)
        else: widget.prev_page()

    def createDb(self, filename):
        """Создает пустой файл БД (или любой другой)"""
        f = open(WORKFOLDER + filename,"w")
        f.close()

    def getServersFromDb(self):
        """Чтение списка ранее посещенных серверов из файла"""
        try: 
            for server in open(WORKFOLDER + "servers.db"):
                try: #попытка прочитать протокол/сервер
                    protocol, address = server.strip().split(':::')        
                    self.liststore[protocol].append([address])
                except ValueError: pass #если неверный формат строки - ее пропуск
        except FileNotFoundError:
            self.createDb("servers.db")            

    def getSavesFromDb(self):
        """Чтение списка сохраненных соединений из файла"""
        self.liststore_connect.clear()
        try: 
            for connect in open(WORKFOLDER + "connections.db"):
                try: #попытка прочитать строку с параметрами подключений
                    record = list(connect.strip().split(':::'))
                    self.liststore_connect.append(record)
                except ValueError: pass #если неверный формат строки - ее пропуск
        except FileNotFoundError:
            self.createDb("connections.db") 

    def writeServerInDb(self, entry):
        """Запись сервера в файл со списком ранее посещенных серверов"""
        db = open(WORKFOLDER + "servers.db", "r+")
        protocol, address = entry.get_name(),entry.get_text()
        record, thereis = protocol + ':::' + address, False
        for server in db:
            #проверка на наличие сервера в базе
            if record == server.strip(): thereis = True
        if not thereis:
            print (record, file = db)
            self.liststore[protocol].append([address])
        db.close()

    def onResolutionSet(self, widget):
        """Отображение списка разрешений"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.ON)
        except: widget.set_sensitive(True)
        

    def offResolutionSet(self, widget):
        """Скрытие списка разрешений"""
        try: widget.set_button_sensitivity(Gtk.SensitivityType.OFF)
        except: widget.set_sensitive(False)

    def onProperties(self, *args):
        """Окно параметров приложения"""
        window = properties.Properties()

    def saveFileCtor(self, name, protocol, server):
        """Создание ассоциации файла подключения с подключением в списке"""
        fileName = [] 
        for i in range (12): #для случайного имени сохраняемого файла
            fileName.append(random.choice(['0','1','2','3','4','5','6','7','8','9']))
        fileName = "".join(fileName) + '.ctor'
        print (name + ':::' + protocol + ':::' + server + ':::' + fileName, 
               file = open(WORKFOLDER + "connections.db", "a"))
        return fileName

    def resaveFileCtor(self, name, protocol, server):
        """Пересохранение подключения с тем же именем файла .ctor"""
        fileName = self.fileCtor
        dblines = open(WORKFOLDER + "connections.db").readlines()
        dbFile = open(WORKFOLDER + "connections.db","w")
        for line in dblines:
            if line.find(fileName) != -1:#если найдено совпадение с название файла коннекта
                line = name + ':::' + protocol + ':::' + server + ':::' + fileName  + '\n'
            dbFile.write(line)
        dbFile.close()
        return fileName    

    def onButtonSave(self, entry):
        """Сохранение параметров для дальнейшего подключения с ними"""
        server = entry.get_text()
        protocol = entry.get_name()
        parameters = self.applyPreferences(protocol)
        name = self.pref_builder.get_object("entry_" + self.changeProgram(protocol) + "_name" )
        parameters.insert(0, server)
        parameters.insert(0, protocol) #протокол подключения также заносится в файл        
        if self.editClick:#если нажата кнопка Изменить, то пересохранить
            fileName = self.resaveFileCtor(name.get_text(), protocol, server)
        else: 
            fileName = self.saveFileCtor(name.get_text(), protocol, server)
        properties.saveInFile(fileName, parameters)
        self.getSavesFromDb()#добавление в листсторе
        self.pref_window.destroy()
        self.editClick = False
        viewStatus(self.statusbar, "Сохранено...")

    def onCitrixSave(self, entry):
        """Сохранение имени сервера на основе Citrix для дальнейшего подключения с ними"""
        server = entry.get_text()
        name = self.builder.get_object("entry_CITRIX_name" )
        parameters = []
        parameters.append('CITRIX')
        parameters.append(server)
        if self.citrixEditClick:
            fileName = self.resaveFileCtor(name.get_text(), 'CITRIX', server)
        else:
            fileName = self.saveFileCtor(name.get_text(), 'CITRIX', server)
        properties.saveInFile(fileName, parameters)
        self.getSavesFromDb()
        self.citrixEditClick = False 
        viewStatus(self.statusbar, "Сохранено...")

    def onCitrixEdit(self, name, server, edit = True):
        """Функция изменения Citrix-подключения"""
        main_note = self.builder.get_object("main_note")
        main_note.set_current_page(0)
        conn_note = self.builder.get_object("list_connect")
        conn_note.set_current_page(5)       
        entry_serv = self.builder.get_object("entry_serv_CITRIX")
        entry_serv.set_text(server)       
        entry_name = self.builder.get_object("entry_CITRIX_name")
        entry_name.set_text(name)
        self.citrixEditClick = edit 

    def correctProgramm(self, parameters):
        """Функция проверки корректоности параметров для запускаемой программы"""
        self.whatProgram = properties.loadFromFile('default.conf')
        if parameters[0] == 'VNC':
            if self.whatProgram['VNC'] == 1 and len(parameters) == 5: return True
            elif self.whatProgram['VNC'] == 0 and len(parameters) > 5: return True
            else: return False
        if parameters[0] == 'RDP':
            if self.whatProgram['RDP'] == 1 and len(parameters) == 14: return True
            elif self.whatProgram['RDP'] == 0 and len(parameters) < 14: return True
            else: return False
        return True         
        
    def onSaveConnect(self, treeView, *args):
        """Установка подключения по двойному щелчку на элемение списка"""
        table, indexRow = treeView.get_selection().get_selected()
        fileCtor = table[indexRow][3]
        parameters = properties.loadFromFile(fileCtor, self.window)
        if parameters is not None: #если файл .ctor имеет верный формат
            if self.correctProgramm(parameters):
                protocol = parameters.pop(0) #извлекаем протокол из файла коннекта
                viewStatus(self.statusbar, 'Соединение с "' + table[indexRow][0] + '"...')
                connect = definition(protocol)
                connect.start(parameters)
            else:
                dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                        "Не удается подключиться: неверный формат подключения!")
                dialog.format_secondary_text("Попробуйте изменить программу по умолчанию в параметрах приложения")
                response = dialog.run()
                dialog.destroy()

    def onPopupMenu(self, widget, event):
        """Контекстное меню списка сохраненных подключений"""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            menu = self.builder.get_object("menu_popup")
            menu.popup(None, None, None, None, event.button, event.time)

    def onPopupEdit(self, treeView):
        """Изменение выбранного подключения"""
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect, self.fileCtor = table[indexRow][0], table[indexRow][3]
        parameters = properties.loadFromFile(self.fileCtor, self.window)
        if parameters is not None: #если файл .ctor имеет верный формат
            if self.correctProgramm(parameters):
                protocol = parameters.pop(0)  #извлекаем протокол из файла коннекта
                if protocol == 'CITRIX':
                    self.onCitrixEdit(nameConnect, parameters[0])
                else:
                    self.editClick = True
                    analogEntry = self.AnalogEntry(protocol, parameters)
                    self.onButtonPref(analogEntry, nameConnect)
            else:
                dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                        "Не удается загрузить параметры: неверный формат подключения!")
                dialog.format_secondary_text("Попробуйте изменить программу по умолчанию в параметрах приложения")
                response = dialog.run()
                dialog.destroy()

    def onPopupCopy(self, treeView):
        """Копирование выбранного подключения"""
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect, self.fileCtor = table[indexRow][0], table[indexRow][3]
        parameters = properties.loadFromFile(self.fileCtor, self.window)
        nameConnect = nameConnect + ' (копия)'
        if parameters is not None: #если файл .ctor имеет верный формат
            if self.correctProgramm(parameters):
                protocol = parameters.pop(0)  #извлекаем протокол из файла коннекта
                if protocol == 'CITRIX':
                    self.onCitrixEdit(nameConnect, parameters[0], False)
                else:
                    analogEntry = self.AnalogEntry(protocol, parameters)
                    self.onButtonPref(analogEntry, nameConnect)
            else:
                dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                        "Не удается загрузить параметры: неверный формат подключения!")
                dialog.format_secondary_text("Попробуйте изменить программу по умолчанию в параметрах приложения")
                response = dialog.run()
                dialog.destroy()

    class AnalogEntry:
        """Класс с методами аналогичными методам Gtk.Entry и реализующий 
           инициализацию сохраненных параметров подключения в окне параметров"""
        def __init__(self, name, parameters):
            self.name = name
            self.parameters = parameters
        def get_name(self): return self.name
        def get_text(self): return self.parameters[0]
        def loadParameters(self): return self.parameters

    def onPopupRemove(self, treeView):
        """Удаление выбранного подключения из списка, БД и файла с его настройками"""
        table, indexRow = treeView.get_selection().get_selected()
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO, "Удалить данное подключение:")
        dialog.format_secondary_text(table[indexRow][0])
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            fileCtor = table[indexRow][3]
            #удаление из базы подключений
            with open(WORKFOLDER + "connections.db") as fileDb:
                tmpArr = fileDb.readlines()            
            endFile = open(WORKFOLDER + "connections.db", 'w')
            for row in tmpArr:
                if row.find(fileCtor) == -1:
                    print(row.strip(), file = endFile)
            endFile.close()
            self.getSavesFromDb() #удаление из liststore
            try: os.remove(WORKFOLDER + fileCtor) #удаление файла с настройками
            except: pass            
        dialog.destroy() 

    def onPopupSave(self, treeView):
        """Создание ярлыка для запуска подключения напрмую из системы"""
        dialog = Gtk.FileChooserDialog("Сохранить ярлык подключения в ...", self.window,
            Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_current_folder(HOMEFOLDER)
        dialog.set_current_name('Connect')
        dialog.set_do_overwrite_confirmation(True) #запрос на перезапись одноименного файла
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = dialog.get_filename()
            name = name.replace(".desktop","")
            filename = name + ".desktop"
            with open(filename,"w") as label:
                label.write(DESKTOP_INFO)
            table, indexRow = treeView.get_selection().get_selected()
            fileCtor = table[indexRow][3]
            f = open(filename,"a")
            f.write("Exec=" + EXEC + fileCtor + "\n")
            f.write("Name=" + os.path.basename(name))
            f.close()
            os.system('chmod 777 \"' + filename + '"')
            viewStatus(self.statusbar, 'Сохранено в "' + filename + '"...')                    
        dialog.destroy()

    def onChangePage(self, notepad, box, page):
        """Действия при переключении вкладок коннектов и списка
           - очистка строки состояния;
           - активация/деактивация пунктов меню перелистывания вкладок подключений"""
        viewStatus(self.statusbar, '')
        prev_menu = self.builder.get_object("menu_edit_prev")
        next_menu = self.builder.get_object("menu_edit_next")
        if page:#если на странице списка
            prev_menu.set_sensitive(False)
            next_menu.set_sensitive(False)
        else:
            prev_menu.set_sensitive(True)
            next_menu.set_sensitive(True)

    def listFilter(self, model, iter, data):
        """Функция для фильтра подключений в списке"""
        row = ''        
        if self.currentFilter == '':
            return True
        else:
            for i in range(3):            
                row += model[iter][i] #объединяем поля в одну строку для поиска в ней символов
            if row.upper().find(self.currentFilter.upper()) != -1: 
                return True
            else: return False

    def onSearchConnect(self, entry):
        """Функция осуществления поиска по списку подключений"""
        self.currentFilter = entry.get_text()
        self.filterConnections.refilter()

    def onSearchReset(self, entry):
        """Сброс фильтрации и очистка поля поиска"""
        entry.set_text('') 
        self.currentFilter = ''
        self.filterConnections.refilter()

    def inputName(self, button):
        """Функция, активирующая кнопку Сохранить после ввода имени соединения"""
        button.set_sensitive(True)

    def onWiki(self, *args):
        webbrowser.open ('https://github.com/ekorneechev/Connector/wiki', new = 2)

def f_main():
    createFolder()
    try:
        fileCtor = sys.argv[1]
        connectFile(fileCtor)
    except IndexError:
        gui = Gui()
        gui.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    f_main()
