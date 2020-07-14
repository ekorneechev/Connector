#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MyConnector
# Copyright (C) 2014-2020 Evgeniy Korneechev <ek@myconnector.ru>

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

from gi.repository import ( Gtk,
                            Gdk,
                            GdkPixbuf,
                            GLib,
                            Gio )
from myconnector.connector import *
from myconnector.config import *
from pathlib import Path

def viewStatus(bar, message):
    """Функция отображения происходящих действий в строке состояния"""
    message = message[:65] + '...' if len(message) > 65 else message #для обреза длинных сообщений
    bar.push(bar.get_context_id ("statusbar"), message)

def connectFile(filename, openFile = False):
    """Connect to the server with file .myc"""
    try:
        parameters = options.loadFromFile(filename)
        if parameters != None:
            protocol = parameters[ "protocol" ]
            program  = parameters.get( "program", "" )
            if program == "freerdp":
                try: parameters[ "passwd" ] = keyring.get_password( parameters[ "server" ] ,parameters[ "username" ] )
                except: pass
            connect = definition( changeProgram( protocol, program ) )
            if connect:
                if parameters.get( "server", "" ):
                    connect.start( parameters )
                else:
                    options.msg_error( "Не указан сервер для подключения!", options.log.error )
            else:
                options.msg_error( "Неподдерживаемый протокол: %s" % protocol, options.log.error )
    #except IndexError #TODO - after remmina rdp и vnc text format
    except KeyError:
        options.msg_error( "Ошибка в файле %s: не указан протокол подключения (параметр protocol)."
                           % filename.replace( "tmp_", "" ),  options.log.exception )

def connectFileRdp(filename):
    """Connect to the server with file .rdp"""
    if CONFIG[ "rdp" ] == "freerdp":
        tmpfile =  "%s/.tmp.rdp" % WORKFOLDER
        os.system('cp -r "%s" "%s"' % (filename, tmpfile))
        os.system('xfreerdp "%s" -sec-nla %s' % (tmpfile, STD_TO_LOG))
    else:
        os.system('remmina --connect "%s" %s' % (filename, STD_TO_LOG))

def connectFileRemmina(filename):
    """Connect to the server with file .remmina"""
    os.system('remmina --connect "%s" %s' % (filename, STD_TO_LOG))

def openFile(filename):
    """Open file connection (.myc, .rdp or .remmina)"""
    ext = Path(filename).suffix.lower()
    options.log.info ( "Открывается файл %s" % filename )
    if ext == ".myc":
        tmpname = 'tmp_' + os.path.basename(filename)
        os.system('cp "%s" "%s/%s"' % (filename, WORKFOLDER, tmpname))
        os.chdir( WORKFOLDER )
        connectFile(tmpname, True)
        os.remove(tmpname)
    elif ext == ".rdp": connectFileRdp(filename)
    elif ext == ".remmina": connectFileRemmina(filename)
    elif ext == ".ctor": os.system( "zenity --error --icon-name=myconnector --text=\"Устаревший формат файла\!\n"
                                    "Воспользуйтесь конвертером ctor2myc или импортируйте через меню Файл -> Импорт\" --no-wrap" )
    else: os.system( "zenity --error --icon-name=myconnector --text='\nНеподдерживаемый тип файла!' --no-wrap" )

def initSignal(gui):
    """Функция обработки сигналов SIGHUP, SIGINT и SIGTERM
       SIGINT - KeyboardInterrupt (Ctrl+C)
       Thanks: http://stackoverflow.com/questions/26388088/python-gtk-signal-handler-not-working/26457317#26457317"""
    def install_glib_handler(sig):
        unix_signal_add = None

        if hasattr(GLib, "unix_signal_add"):
            unix_signal_add = GLib.unix_signal_add
        elif hasattr(GLib, "unix_signal_add_full"):
            unix_signal_add = GLib.unix_signal_add_full

        if unix_signal_add:
            unix_signal_add(GLib.PRIORITY_HIGH, sig, gui.onDeleteWindow, sig)
        else:
            print("Can't install GLib signal handler, too old gi.")

    SIGS = [getattr(signal, s, None) for s in "SIGINT SIGTERM SIGHUP".split()]
    for sig in filter(None, SIGS):
        GLib.idle_add(install_glib_handler, sig, priority=GLib.PRIORITY_HIGH)

def startDebug():
    """Start show log files online (uses xterm)"""
    if options.enableLog:
        os.system( 'for i in all myconnector; do xterm -T "MyConnector DEBUG - $i.log" -e "tail -f %s/$i.log" & done' % LOGFOLDER )
        options.log.info ("The program is running in debug mode.")
    else:
        os.system( "zenity --error --icon-name=myconnector --text='\nВедение логов отключено. Отладка невозможна!' --no-wrap" )

def quitApp():
    """Quit application"""
    options.log.info ( "The MyConnector is forcibly closed (from cmdline)." )
    os.system( "pkill [my]?connector" )

def getSaveConnections():
    """List of save connections from files in WORKFOLDER"""
    saves = []
    for mycfile in os.listdir( WORKFOLDER ):
        if Path( mycfile ).suffix.lower() == ".myc":
            conf = ConfigParser()
            conf.read( "%s/%s" % ( WORKFOLDER, mycfile ) )
            try:
                save = [ conf[ "myconnector" ][ "name"     ],
                         conf[ "myconnector" ][ "protocol" ].upper(),
                         conf[ "myconnector" ][ "server"   ],
                         mycfile ]
                saves.append( save )
            except KeyError: pass
    return saves

def changeProgram( protocol, program = "" ):
    """Return {RDP,VNC}1 if program not remmina"""
    protocol = protocol.upper()
    if program:
        if program in [ "freerdp", "vncviewer" ]:
            return "%s1" % protocol
        else: return protocol
    try:
        if CONFIG[ protocol ] != "remmina" and protocol != "FS": protocol += "1"
    except KeyError: pass
    return protocol

class TrayIcon:
    """Класс, описывающий индикатор и меню в трее (пока только для MATE)
       Thanks: https://eax.me/python-gtk/"""
    def __init__(self, icon, menu):
        self.menu = menu
        self.ind = Gtk.StatusIcon()
        self.ind.set_from_icon_name(icon)
        self.ind.connect('popup-menu', self.onTrayMenu)
        self.ind.set_tooltip_text("Программа MyConnector")

    def onTrayMenu(self, icon, button, time):
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, icon,
                        button, time)

    def connect(self, callback):
        self.ind.connect('activate', callback)

    def hide(self):
        self.ind.set_visible(False)

    def show(self):
        self.ind.set_visible(True)

class Gui(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="ru.myconnector.MyConnector", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.prefClick = False
        self.editClick = False
        self.builder = Gtk.Builder()
        self.builder.add_from_file( "%s/gui.ui" % UIFOLDER )
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("main_window")
        self.window.set_title("MyConnector")
        self.statusbar = self.builder.get_object("statusbar")
        self.liststore = { "RDP"    : self.builder.get_object( "liststore_RDP"    ),
                           "VNC"    : self.builder.get_object( "liststore_VNC"    ),
                           "SSH"    : self.builder.get_object( "liststore_SSH"    ),
                           "SFTP"   : self.builder.get_object( "liststore_SFTP"   ),
                           "VMWARE" : self.builder.get_object( "liststore_VMWARE" ),
                           "CITRIX" : self.builder.get_object( "liststore_CITRIX" ),
                           "XDMCP"  : self.builder.get_object( "liststore_XDMCP"  ),
                           "NX"     : self.builder.get_object( "liststore_NX"     ),
                           "WEB"    : self.builder.get_object( "liststore_WEB"    ),
                           "SPICE"  : self.builder.get_object( "liststore_SPICE"  ),
                           "FS"     : self.builder.get_object( "liststore_FS"     ) }

        self.liststore_connect = Gtk.ListStore(str, str, str, str)
        self.setSavesToListstore()
        self.filterConnections = self.liststore_connect.filter_new()
        self.filterConnections.set_visible_func(self.listFilter) #добавление фильтра для поиска
        self.currentFilter = ''
        self.sortedFiltered = Gtk.TreeModelSort(model = self.filterConnections)
        try: default_sort = int( CONFIG[ 'sort' ] )
        except KeyError: default_sort = 0
        self.sortedFiltered.set_sort_column_id(default_sort, Gtk.SortType.ASCENDING)
        self.treeview = self.builder.get_object("treeview_connections")
        self.treeview.set_model(self.sortedFiltered)
        self.treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.MOVE)
        self.treeview.connect("drag-data-get", self.onDragLabel)
        self.treeview.drag_source_add_uri_targets()
        self.getServersFromDb()
        self.citrixEditClick = False
        self.webEditClick = False
        try: default_tab = CONFIG[ 'tab' ]
        except KeyError: default_tab = '0'
        try: default_main = CONFIG[ 'main' ]
        except KeyError: default_main = '0'
        self.main_note = self.builder.get_object("main_note")
        self.main_note.set_current_page(int(default_main))
        self.conn_note = self.builder.get_object("list_connect")
        self.conn_note.set_current_page(int(default_tab))
        self.labelRDP, self.labelVNC = self.builder.get_object("label_default_RDP"), self.builder.get_object("label_default_VNC")
        self.labelFS = self.builder.get_object("label_default_FS")
        self.initLabels(self.labelRDP, self.labelVNC, self.labelFS)
        self.trayDisplayed = False
        self.tray_submenu = self.builder.get_object("tray_submenu")
        if self.optionEnabled( 'tray' ): self.trayDisplayed = self.initTray()
        if self.optionEnabled( 'check_version' ):
            signal.signal( signal.SIGCHLD, signal.SIG_IGN ) # without zombie
            Popen( [ "%s/myconnector-check-version" % MAINFOLDER, VERSION ] )
        try:
            from myconnector.kiosk import enabled
            self.menu_kiosk = self.builder.get_object("menu_file_kiosk")
            self.menu_kiosk.set_sensitive( enabled() )
        except ImportError:
            options.log.warning ("The mode KIOSK unavailable, package is not installed.")

    def createDesktopFile(self, filename, nameConnect, nameDesktop):
        """Create desktop-file for connection"""
        with open(filename,"w") as label:
            label.write(DESKTOP_INFO)
        with open(filename,"a") as label:
            label.write('Exec=%s"%s"\n' % (EXEC, nameConnect))
            label.write('Name=%s\n' % nameDesktop)
        os.system('chmod 755 \"%s\"' % filename)

    def onDragLabel(self, widget, drag_context, data, info, time):
        """Drag-and-Drop for create desktop-file of the connection"""
        table, indexRow = self.treeview.get_selection().get_selected()
        nameConnect = table[indexRow][0]
        nameUnicode = nameConnect.encode()
        if len(nameConnect) == len(nameUnicode):
            filename = "/tmp/%s.desktop" % nameConnect
        else: filename = "/tmp/%s.desktop" % nameUnicode
        self.createDesktopFile(filename, nameConnect, nameConnect)
        data.set_uris(["file://%s" % filename])

    def do_activate(self):
        """Обязательный обработчик для Gtk.Application"""
        self.add_window(self.window)
        self.showWin()

    def showWin(self):
        self.window.show_all()
        self.window.present()

    def initTray(self):
        """Инициализация индикатора в системном лотке"""
        self.menu_tray = self.builder.get_object("menu_tray")
        self.iconTray = TrayIcon( "myconnector", self.menu_tray )
        self.iconTray.connect(self.onShowWindow)
        self.initSubmenuTray()
        self.menu_tray.show_all()
        return True

    def initSubmenuTray(self):
        """Инициализация списка сохраненных подключений в меню из трея"""
        exist = False
        for item in self.tray_submenu.get_children(): item.destroy() #очищение меню перед его заполнением
        for record in getSaveConnections():
            exist = True
            name, protocol = record[0], record[1]
            item = Gtk.ImageMenuItem(name)
            image = Gtk.Image()
            image.set_from_pixbuf( GdkPixbuf.Pixbuf.new_from_file( "%s/%s.png" % ( ICONFOLDER, protocol )))
            item.set_image(image)
            item.connect("activate",self.onTrayConnect, name)
            self.tray_submenu.append(item)
        if not exist:
            tray_noexist = Gtk.MenuItem("<нет сохраненных подключений>")
            tray_noexist.set_sensitive(False)
            self.tray_submenu.append(tray_noexist)
        self.tray_submenu.show_all()

    def onTrayConnect(self, menuitem, name):
        """Функция запуска сохраненного подключения из трея"""
        fileCtor = self.filenameFromName( name )
        if fileCtor: connectFile(fileCtor)

    def optionEnabled(self, option):
        try:
            check = CONFIG.getboolean( option )
        except KeyError:
            check = DEFAULT[ option ]
        return check

    def initLabels(self, rdp, vnc, fs):
        """Display on the main window the program name for RDP, VNC and FS"""
        rdp.set_text( "(%s)" % CONFIG.get( "rdp" ) )
        vnc.set_text( "(%s)" % CONFIG.get( "vnc" ) )
        fs.set_text ( "(%s)" % CONFIG.get( "fs"  ) )

    def onDeleteWindow(self, *args):
        """Закрытие программы"""
        if args[0] == 2:
            msg = "KeyboardInterrupt: the MyConnector is closed!"
            options.log.info (msg)
            print ('\n' + msg)
        self.quit()

    def onViewAbout(self, *args):
        """Создает диалоговое окно 'О программе'"""
        about = Gtk.AboutDialog( parent = self.window )
        about.set_program_name( "MyConnector (ex. Connector)" )
        about.set_comments(
            "Программа-фронтэнд для удаленного администрирования\n"
            "компьютеров с различными операционными системами.\n"
            "Поддерживается большинство распространенных типов подключения." )
        about.set_version( "%s (release: %s)" % ( VERSION, RELEASE ) )
        about.set_website( "http://myconnector.ru" )
        about.set_website_label( "http://myconnector.ru" )
        about.set_license(
            "MyConnector\n\n"
            "This program is free software; you can redistribute it and/or\n"
            "modify it under the terms of the version 2 of the GNU General\n"
            "Public License as published by the Free Software Foundation.\n\n"
            "This program is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
            "GNU General Public License for more details.\n\n"""
            "You should have received a copy of the GNU General Public License\n"
            "along with this program. If not, see http://www.gnu.org/licenses/." )
        about.set_copyright(
            "© Korneechev E.A., 2014-2020\n"
            "ek@myconnector.ru" )
        about.set_logo_icon_name( "myconnector" )
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
            openFile(filename)
            viewStatus(self.statusbar, "Открыт файл " + filename)
        else:
            viewStatus(self.statusbar, "Файл не был выбран!")
        dialog.destroy()

    def onImportFile(self, *args):
        """Открытие файла для изменения и дальнейшего подключения"""
        dialog = self.createOpenDialog("Импорт файла с конфигурацией подключения")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            parameters = options.loadFromFile( filename, _import = True )
            if parameters != None:
                protocol = parameters [ "protocol" ].upper() #TODO - add try/except and log
                if protocol in [ "CITRIX", "WEB" ]:
                    self.onWCEdit( "", parameters[ "server" ], protocol ) #TODO - add try/except and log
                else:
                    analogEntry = self.AnalogEntry( protocol, parameters )
                    self.onButtonPref( analogEntry, parameters.get( "name", "" ) )
                msg = "Импортирован файл " + filename
                options.log.info ( msg )
                viewStatus( self.statusbar, msg )
        else:
            viewStatus(self.statusbar, "Файл не был выбран!")
        dialog.destroy()

    def addFilters(self, dialog):
        filter_ctor = Gtk.FileFilter()
        filter_ctor.set_name( "Файлы подключений MyConnector" )
        filter_ctor.add_pattern("*.myc")
        dialog.add_filter(filter_ctor)
        filter_rdp = Gtk.FileFilter()
        filter_rdp.set_name("Файлы подключений RDP (Windows)")
        filter_rdp.add_pattern("*.rdp")
        filter_rdp.add_pattern("*.RDP")
        filter_rdp.add_pattern("*.rdpx")
        dialog.add_filter(filter_rdp)
        filter_remmina = Gtk.FileFilter()
        filter_remmina.set_name("Файлы подключений Remmina")
        filter_remmina.add_pattern("*.remmina")
        dialog.add_filter(filter_remmina)
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Все файлы")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def onButtonConnect(self, entry):
        """Сигнал кнопке для быстрого подключения к указанному в entry серверу"""
        server = entry.get_text()
        protocol = entry.get_name()
        if server:
            name = changeProgram( protocol )
            connect = definition( name )
            if self.prefClick: #если нажата кнопка Доп. Параметры
                parameters = self.applyPreferences( name )
                parameters[ "server" ] = server
                if name == "RDP1":
                    self.saveKeyring ( parameters.copy() )
            else:
                try: parameters = CONFIGS[ name ]
                except KeyError:
                    try: parameters = DEF_PROTO[ name ].copy()
                    except KeyError: parameters = server
                try:
                    parameters[ "server" ] = server #для заголовка окна
                except: pass
            connect.start(parameters)
            viewStatus(self.statusbar, "Подключение к серверу " + server + "...")
            self.writeServerInDb(entry)
        else:
            viewStatus(self.statusbar, "Введите адрес сервера")

    def onCitrixPref(self, *args):
        Citrix.preferences()

    def onButtonPref(self, entry_server, nameConnect = ''):
        """Дополнительные параметры подключения к серверу.
        Доступно как с кнопки, так и из пункта меню 'Подключение'"""
        self.pref_window = Gtk.Window()
        self.prefClick = True #для определения нажатия на кнопку Доп. параметры
        protocol = entry_server.get_name()
        server   = entry_server.get_text()
        self.pref_window.set_title( "Параметры " + protocol + "-подключения" )
        self.pref_window.set_icon_from_file( "%s/%s.png" % ( ICONFOLDER, protocol ) )
        self.pref_window.set_position(Gtk.WindowPosition.CENTER)
        self.pref_window.set_resizable(False)
        self.pref_window.set_modal(True)
        self.pref_window.resize(400, 400)
        self.pref_builder = Gtk.Builder()
        self.pref_builder.add_from_file( "%s/pref_gui.ui" % UIFOLDER )
        self.pref_builder.connect_signals(self)
        if 'loadParameters' in dir(entry_server): #если изменяется или копируется соединение, то загружаем параметры (фэйковый класс Entry)
            parameters = entry_server.loadParameters()
            name = changeProgram( protocol, parameters.get( "program", "" ) )
        else: #иначе (новое подключение), пытаемся загрузить дефолтные настройки
            name = changeProgram( protocol )
            try: parameters = CONFIGS[ name ]
            except KeyError:
                try:
                    parameters = DEF_PROTO[ name ].copy()
                except KeyError:
                    parameters = None
            if type(parameters) == dict:
                parameters[ "server" ] = server
        entryName = self.pref_builder.get_object( "entry_%s_name" % name )
        if nameConnect: entryName.set_text( nameConnect )
        box = self.pref_builder.get_object( "box_%s" % name )
        combo = self.pref_builder.get_object( "combo_%s" % name )
        combo.set_model( self.liststore[ protocol ] )
        serv = self.pref_builder.get_object( "entry_%s_serv" % name )
        serv.set_text( server )
        cancel = self.pref_builder.get_object( "button_%s_cancel" % name )
        cancel.connect( "clicked", self.onCancel, self.pref_window )
        self.pref_window.connect( "delete-event", self.onClose )
        self.initPreferences( name )
        self.setPreferences( name, parameters )
        self.pref_window.add(box)
        self.pref_window.show_all()

    def setPreferences(self, protocol, args):
        """В этой функции параметры загружаются из сохраненного файла"""
        if not args: return False
        if protocol == "VNC1":
            if args.getboolean( "fullscreen" ): self.VNC_viewmode.set_active( True )
            if args.getboolean( "viewonly"   ): self.VNC_viewonly.set_active( True )

        if protocol == "VNC":
            self.VNC_user.set_text(         args.get( "username",   "" ) )
            self.VNC_quality.set_active_id( args.get( "quality",    "" ) )
            self.VNC_color.set_active_id(   args.get( "colordepth", "" ) )
            if args.get( "viewmode" , "1" ) == "4"   : self.VNC_viewmode.set_active(   True )
            if args.getboolean( "viewonly"          ): self.VNC_viewonly.set_active(   True )
            if args.getboolean( "disableencryption" ): self.VNC_crypt.set_active(      True )
            if args.getboolean( "disableclipboard"  ): self.VNC_clipboard.set_active(  True )
            if args.getboolean( "showcursor"        ): self.VNC_showcursor.set_active( True )
            else: self.VNC_showcursor.set_active( False )

        if protocol == "VMWARE":
            self.VMWARE_user.set_text(     args.get( "user", ""     ) )
            self.VMWARE_domain.set_text(   args.get( "domain", ""   ) )
            self.VMWARE_password.set_text( args.get( "password", "" ) )
            if args.getboolean( "fullscreen" ): self.VMWARE_fullscreen.set_active( True )

        if protocol == "XDMCP":
            self.XDMCP_color.set_active_id( args.get( "colordepth", "" ) )
            self.XDMCP_exec.set_text(       args.get( "exec",       "" ) )
            if args.get( "viewmode", "" ) == "4": self.XDMCP_viewmode.set_active(      True )
            if not args.get( "resolution", "" ) : self.XDMCP_resol_default.set_active( True )
            else:
                XDMCP_resol_hand = self.pref_builder.get_object( "radio_XDMCP_resol_hand" )
                XDMCP_resol_hand.set_active( True )
                self.XDMCP_resolution.set_active_id( args[ "resolution" ] )
            if args.getboolean( "once"         ): self.XDMCP_once.set_active(          True )
            if args.getboolean( "showcursor"   ): self.XDMCP_showcursor.set_active(    True )

        if protocol == "SSH":
            self.SSH_user.set_text(             args.get( "username",       "" ) )
            self.SSH_path_keyfile.set_filename( args.get( "ssh_privatekey", "" ) )
            self.SSH_charset.set_text(          args.get( "ssh_charset",    "" ) )
            self.SSH_exec.set_text(             args.get( "exec",           "" ) )
            if   args.get( "ssh_auth" ) == "3": self.SSH_publickey.set_active( True )
            elif args.get( "ssh_auth" ) == "1": self.SSH_keyfile.set_active(   True )
            else:
                SSH_pwd = self.pref_builder.get_object( "radio_SSH_pwd" )
                SSH_pwd.set_active( True )


        if protocol == "SFTP":
            self.SFTP_user.set_text(             args.get( "username",          "" ) )
            self.SFTP_path_keyfile.set_filename( args.get( "ssh_privatekey",    "" ) )
            self.SFTP_charset.set_text(          args.get( "ssh_charset",       "" ) )
            self.SFTP_execpath.set_text(         args.get( "execpath",          "" ) )
            if   args.get( "ssh_auth" ) == "3": self.SFTP_publickey.set_active( True )
            elif args.get( "ssh_auth" ) == "1": self.SFTP_keyfile.set_active(   True )
            else:
                SFTP_pwd = self.pref_builder.get_object( "radio_SFTP_pwd" )
                SFTP_pwd.set_active( True )

        if protocol == "NX":
            self.NX_user.set_text(         args.get ( "username", "" ) )
            self.NX_quality.set_active_id( args.get ( "quality",  "" ) )
            self.NX_exec.set_text(         args.get ( "exec",     "" ) )
            if not args.get ( "resolution", "" ): self.NX_resol_window.set_active(   True )
            else:
                NX_resol_hand = self.pref_builder.get_object( "radio_NX_resol_hand" )
                NX_resol_hand.set_active( True )
                self.NX_resolution.set_active_id( args[ "resolution" ] )
            if args.get ( "viewmode", "" ) == "4"  : self.NX_viewmode.set_active(    True )
            if not args.get ( "nx_privatekey", "" ): self.NX_keyfile.set_active(    False )
            else:
                self.NX_keyfile.set_active( True )
                self.NX_path_keyfile.set_filename( args[ "nx_privatekey" ] )
            if args.getboolean( "disableencryption" ): self.NX_crypt.set_active(     True )
            if args.getboolean( "disableclipboard"  ): self.NX_clipboard.set_active( True )

        if protocol == "RDP":
            self.RDP_user.set_text(         args.get( "username",   "" ) )
            self.RDP_domain.set_text(       args.get( "domain",     "" ) )
            self.RDP_color.set_active_id(   args.get( "colordepth", "" ) )
            self.RDP_quality.set_active_id( args.get( "quality",    "" ) )
            self.RDP_sound.set_active_id(   args.get( "sound",      "" ) )
            if not args.get( "resolution", "" ): self.RDP_resol_default.set_active(   True )
            else:
                RDP_resol_hand = self.pref_builder.get_object( "radio_RDP_resol_hand" )
                RDP_resol_hand.set_active( True )
                self.RDP_resolution.set_active_id( args[ "resolution" ] )
            if args.get( "viewmode", "" ) == "3": self.RDP_viewmode.set_active(       True )
            else: self.RDP_viewmode.set_active( False )
            if not args.get( "sharefolder", "" ): self.RDP_share_folder.set_active(  False )
            else:
                self.RDP_share_folder.set_active( True )
                self.RDP_name_folder.set_filename( args[ "sharefolder" ] )
            if args.getboolean( "shareprinter"     ): self.RDP_printers.set_active(   True )
            if args.getboolean( "disableclipboard" ): self.RDP_clipboard.set_active( False )
            if args.getboolean( "sharesmartcard"   ): self.RDP_cards.set_active(      True )

        if protocol == "RDP1":
            self.RDP_user.set_text(       args.get( "username",   "" ) )
            self.RDP_domain.set_text(     args.get( "domain",     "" ) )
            self.RDP_gserver.set_text(    args.get( "gserver",    "" ) )
            self.RDP_guser.set_text(      args.get( "guser",      "" ) )
            self.RDP_gdomain.set_text(    args.get( "gdomain",    "" ) )
            self.RDP_gpasswd.set_text(    args.get( "gpasswd",    "" ) )
            self.RDP_color.set_active_id( args.get( "color",      "" ) )
            self.RDP_userparams.set_text( args.get( "userparams", "" ) )
            if args.getboolean( "fullscreen" ): self.RDP_fullscreen.set_active(    True )
            elif args.get( "resolution",  "" ):
                RDP_resol_hand = self.pref_builder.get_object( "radio_RDP1_resol_hand"  )
                RDP_resol_hand.set_active( True )
                self.RDP_resolution.set_text( args[ "resolution" ] )
            elif args.getboolean( "workarea" ): self.RDP_workarea.set_active(      True )
            else: self.RDP_resol_default.set_active( True )
            if args.getboolean( "clipboard"  ): self.RDP_clipboard.set_active(     True )
            else: self.RDP_clipboard.set_active( False )
            if not args.get( "folder", ""    ): self.RDP_share_folder.set_active( False )
            else:
                self.RDP_share_folder.set_active( True )
                self.RDP_name_folder.set_filename( args[ "folder" ] )
            if args.getboolean( "admin"      ): self.RDP_admin.set_active(         True )
            if args.getboolean( "smartcards" ): self.RDP_cards.set_active(         True )
            if args.getboolean( "printers"   ): self.RDP_printers.set_active(      True )
            if args.getboolean( "sound"      ): self.RDP_sound.set_active(         True )
            if args.getboolean( "microphone" ): self.RDP_microphone.set_active(    True )
            if args.getboolean( "multimon"   ): self.RDP_multimon.set_active(      True )
            if args.getboolean( "compression" ):
                self.RDP_compression.set_active( True )
                self.RDP_compr_level.set_active_id( args.get( "compr_level", "0" ) )
            if args.getboolean( "fonts"      ): self.RDP_fonts.set_active(         True )
            if args.getboolean( "aero"       ): self.RDP_aero.set_active(          True )
            if args.getboolean( "drag"       ): self.RDP_drag.set_active(          True )
            if args.getboolean( "animation"  ): self.RDP_animation.set_active(     True )
            if args.getboolean( "theme"      ): self.RDP_theme.set_active(        False )
            if args.getboolean( "wallpapers" ): self.RDP_wallpapers.set_active(   False )
            if args.getboolean( "nsc"        ): self.RDP_nsc.set_active(           True )
            if args.getboolean( "jpeg" ):
                self.RDP_jpeg.set_active( True )
                self.RDP_jpeg_quality.set_value( float( args.get( "jpeg_quality", "80" ) ) )
            if args.getboolean( "usb"        ): self.RDP_usb.set_active(           True )
            if args.getboolean( "secnla"     ): self.RDP_nla.set_active(           True )
            if args.getboolean( "span"       ): self.RDP_span.set_active(          True )
            if args.getboolean( "desktop"    ): self.RDP_desktop.set_active(       True )
            if args.getboolean( "downloads"  ): self.RDP_down.set_active(          True )
            if args.getboolean( "documents"  ): self.RDP_docs.set_active(          True )
            if args.getboolean( "gdi"        ): self.RDP_gdi.set_active(           True )
            if args.getboolean( "reconnect"  ): self.RDP_reconnect.set_active(    False )
            if args.getboolean( "certignore" ): self.RDP_certignore.set_active(    True )
            if args.getboolean( "glyph"      ): self.RDP_glyph.set_active(         True )
            password = keyring.get_password( args.get( "server", "" ), args.get( "username", "" ) )
            if args.getboolean( "passwdsave" ) or password: self.RDP_pwdsave.set_active( True )
            if not password: password = args.get( "passwd", "" )
            self.RDP_pwd.set_text( password )

        if protocol == "SPICE":
            if args.getboolean( "usetls"           ): self.SPICE_tls.set_active(        True )
            if args.getboolean( "viewonly"         ): self.SPICE_viewonly.set_active(   True )
            if args.getboolean( "resizeguest"      ): self.SPICE_resize.set_active(     True )
            if args.getboolean( "disableclipboard" ): self.SPICE_clipboard.set_active( False )
            if args.getboolean( "sharesmartcard"   ): self.SPICE_cards.set_active(      True )
            if args.getboolean( "enableaudio"      ): self.SPICE_sound.set_active(      True )
            if not args.get(    "cacert", ""       ): self.SPICE_CA.set_active(        False )
            else:
                self.SPICE_CA.set_active( True )
                self.SPICE_cacert.set_filename( args[ "cacert" ] )

        if protocol == "FS":
            self.FS_user.set_text(      args.get( "user",   "" ) )
            self.FS_domain.set_text(    args.get( "domain", "" ) )
            self.FS_folder.set_text(    args.get( "folder", "" ) )
            self.FS_type.set_active_id( args.get( "type",   "" ) )

    def initPreferences( self, protocol ):
        """В этой функции определяются различные для протоколов параметры"""
        if protocol == "RDP": #remmina
            self.RDP_user          = self.pref_builder.get_object( "entry_RDP_user"          )
            self.RDP_domain        = self.pref_builder.get_object( "entry_RDP_dom"           )
            self.RDP_color         = self.pref_builder.get_object( "entry_RDP_color"         )
            self.RDP_quality       = self.pref_builder.get_object( "entry_RDP_quality"       )
            self.RDP_resolution    = self.pref_builder.get_object( "entry_RDP_resolution"    )
            self.RDP_viewmode      = self.pref_builder.get_object( "check_RDP_fullscreen"    )
            self.RDP_resol_default = self.pref_builder.get_object( "radio_RDP_resol_default" )
            self.RDP_share_folder  = self.pref_builder.get_object( "check_RDP_folder"        )
            self.RDP_name_folder   = self.pref_builder.get_object( "RDP_share_folder"        )
            self.RDP_printers      = self.pref_builder.get_object( "check_RDP_printers"      )
            self.RDP_clipboard     = self.pref_builder.get_object( "check_RDP_clipboard"     )
            self.RDP_sound         = self.pref_builder.get_object( "entry_RDP_sound"         )
            self.RDP_cards         = self.pref_builder.get_object( "check_RDP_cards"         )
            self.RDP_name_folder.set_current_folder( HOMEFOLDER )

        if protocol == "RDP1": #freerdp
            self.RDP_user          = self.pref_builder.get_object( "entry_RDP1_user"          )
            self.RDP_domain        = self.pref_builder.get_object( "entry_RDP1_dom"           )
            self.RDP_color         = self.pref_builder.get_object( "entry_RDP1_color"         )
            self.RDP_resolution    = self.pref_builder.get_object( "entry_RDP1_resolution"    )
            self.RDP_fullscreen    = self.pref_builder.get_object( "radio_RDP1_fullscreen"    )
            self.RDP_resol_default = self.pref_builder.get_object( "radio_RDP1_resol_default" )
            self.RDP_share_folder  = self.pref_builder.get_object( "check_RDP1_folder"        )
            self.RDP_name_folder   = self.pref_builder.get_object( "RDP1_share_folder"        )
            self.RDP_clipboard     = self.pref_builder.get_object( "check_RDP1_clipboard"     )
            self.RDP_guser         = self.pref_builder.get_object( "entry_RDP1_guser"         )
            self.RDP_gdomain       = self.pref_builder.get_object( "entry_RDP1_gdom"          )
            self.RDP_gserver       = self.pref_builder.get_object( "entry_RDP1_gserv"         )
            self.RDP_gpasswd       = self.pref_builder.get_object( "entry_RDP1_gpwd"          )
            self.RDP_admin         = self.pref_builder.get_object( "check_RDP1_adm"           )
            self.RDP_cards         = self.pref_builder.get_object( "check_RDP1_cards"         )
            self.RDP_printers      = self.pref_builder.get_object( "check_RDP1_printers"      )
            self.RDP_sound         = self.pref_builder.get_object( "check_RDP1_sound"         )
            self.RDP_microphone    = self.pref_builder.get_object( "check_RDP1_microphone"    )
            self.RDP_multimon      = self.pref_builder.get_object( "check_RDP1_multimon"      )
            self.RDP_compression   = self.pref_builder.get_object( "check_RDP1_compression"   )
            self.RDP_compr_level   = self.pref_builder.get_object( "entry_RDP1_compr_level"   )
            self.RDP_fonts         = self.pref_builder.get_object( "check_RDP1_fonts"         )
            self.RDP_aero          = self.pref_builder.get_object( "check_RDP1_aero"          )
            self.RDP_drag          = self.pref_builder.get_object( "check_RDP1_drag"          )
            self.RDP_animation     = self.pref_builder.get_object( "check_RDP1_animation"     )
            self.RDP_theme         = self.pref_builder.get_object( "check_RDP1_theme"         )
            self.RDP_wallpapers    = self.pref_builder.get_object( "check_RDP1_wallpapers"    )
            self.RDP_nsc           = self.pref_builder.get_object( "check_RDP1_nsc"           )
            self.RDP_jpeg          = self.pref_builder.get_object( "check_RDP1_jpeg"          )
            self.RDP_jpeg_quality  = self.pref_builder.get_object( "scale_RDP1_jpeg"          )
            self.RDP_usb           = self.pref_builder.get_object( "check_RDP1_usb"           )
            self.RDP_nla           = self.pref_builder.get_object( "check_RDP1_nla"           )
            self.RDP_workarea      = self.pref_builder.get_object( "radio_RDP1_workarea"      )
            self.RDP_span          = self.pref_builder.get_object( "check_RDP1_span"          )
            self.RDP_desktop       = self.pref_builder.get_object( "check_RDP1_desktop"       )
            self.RDP_down          = self.pref_builder.get_object( "check_RDP1_down"          )
            self.RDP_docs          = self.pref_builder.get_object( "check_RDP1_docs"          )
            self.RDP_gdi           = self.pref_builder.get_object( "check_RDP1_gdi"           )
            self.RDP_reconnect     = self.pref_builder.get_object( "check_RDP1_reconnect"     )
            self.RDP_certignore    = self.pref_builder.get_object( "check_RDP1_certignore"    )
            self.RDP_pwd           = self.pref_builder.get_object( "entry_RDP1_pwd"           )
            self.RDP_pwdsave       = self.pref_builder.get_object( "check_RDP1_pwd"           )
            self.RDP_glyph         = self.pref_builder.get_object( "check_RDP1_glyph"         )
            self.RDP_userparams    = self.pref_builder.get_object( "entry_RDP1_userparams"    )
            self.RDP_resolution.set_sensitive( False )
            self.RDP_name_folder.set_current_folder( HOMEFOLDER )

        if protocol == "NX":
            self.NX_user         = self.pref_builder.get_object( "entry_NX_user"         )
            self.NX_keyfile      = self.pref_builder.get_object( "check_NX_keyfile"      )
            self.NX_path_keyfile = self.pref_builder.get_object( "NX_keyfile"            )
            self.NX_quality      = self.pref_builder.get_object( "entry_NX_quality"      )
            self.NX_resolution   = self.pref_builder.get_object( "entry_NX_resolution"   )
            self.NX_viewmode     = self.pref_builder.get_object( "check_NX_fullscreen"   )
            self.NX_resol_window = self.pref_builder.get_object( "radio_NX_resol_window" )
            self.NX_exec         = self.pref_builder.get_object( "entry_NX_exec"         )
            self.NX_crypt        = self.pref_builder.get_object( "check_NX_crypt"        )
            self.NX_clipboard    = self.pref_builder.get_object( "check_NX_clipboard"    )
            self.NX_path_keyfile.set_current_folder( HOMEFOLDER )

        if protocol == "VNC": #remmina
            self.VNC_user       = self.pref_builder.get_object( "entry_VNC_user"       )
            self.VNC_color      = self.pref_builder.get_object( "entry_VNC_color"      )
            self.VNC_quality    = self.pref_builder.get_object( "entry_VNC_quality"    )
            self.VNC_viewmode   = self.pref_builder.get_object( "check_VNC_fullscreen" )
            self.VNC_viewonly   = self.pref_builder.get_object( "check_VNC_viewonly"   )
            self.VNC_showcursor = self.pref_builder.get_object( "check_VNC_showcursor" )
            self.VNC_crypt      = self.pref_builder.get_object( "check_VNC_crypt"      )
            self.VNC_clipboard  = self.pref_builder.get_object( "check_VNC_clipboard"  )

        if protocol == "VNC1": #vncviewer
            self.VNC_viewmode = self.pref_builder.get_object( "check_VNC1_fullscreen" )
            self.VNC_viewonly = self.pref_builder.get_object( "check_VNC1_viewonly"   )

        if protocol == "XDMCP":
            self.XDMCP_color         = self.pref_builder.get_object( "entry_XDMCP_color"         )
            self.XDMCP_resolution    = self.pref_builder.get_object( "entry_XDMCP_resolution"    )
            self.XDMCP_viewmode      = self.pref_builder.get_object( "check_XDMCP_fullscreen"    )
            self.XDMCP_resol_default = self.pref_builder.get_object( "radio_XDMCP_resol_default" )
            self.XDMCP_showcursor    = self.pref_builder.get_object( "check_XDMCP_showcursor"    )
            self.XDMCP_once          = self.pref_builder.get_object( "check_XDMCP_once"          )
            self.XDMCP_exec          = self.pref_builder.get_object( "entry_XDMCP_exec"          )

        if protocol == "SSH":
            self.SSH_user         = self.pref_builder.get_object( "entry_SSH_user"      )
            self.SSH_publickey    = self.pref_builder.get_object( "radio_SSH_publickey" )
            self.SSH_keyfile      = self.pref_builder.get_object( "radio_SSH_keyfile"   )
            self.SSH_path_keyfile = self.pref_builder.get_object( "SSH_keyfile"         )
            self.SSH_exec         = self.pref_builder.get_object( "entry_SSH_exec"      )
            self.SSH_charset      = self.pref_builder.get_object( "entry_SSH_charset"   )
            self.SSH_path_keyfile.set_current_folder( HOMEFOLDER )

        if protocol == "SFTP":
            self.SFTP_user         = self.pref_builder.get_object( "entry_SFTP_user"      )
            self.SFTP_publickey    = self.pref_builder.get_object( "radio_SFTP_publickey" )
            self.SFTP_keyfile      = self.pref_builder.get_object( "radio_SFTP_keyfile"   )
            self.SFTP_path_keyfile = self.pref_builder.get_object( "SFTP_keyfile"         )
            self.SFTP_execpath     = self.pref_builder.get_object( "entry_SFTP_execpath"  )
            self.SFTP_charset      = self.pref_builder.get_object( "entry_SFTP_charset"   )
            self.SFTP_path_keyfile.set_current_folder( HOMEFOLDER )

        if protocol == "VMWARE":
            self.VMWARE_user       = self.pref_builder.get_object( "entry_VMWARE_user"       )
            self.VMWARE_domain     = self.pref_builder.get_object( "entry_VMWARE_dom"        )
            self.VMWARE_password   = self.pref_builder.get_object( "entry_VMWARE_pwd"        )
            self.VMWARE_fullscreen = self.pref_builder.get_object( "check_VMWARE_fullscreen" )

        if protocol == "SPICE":
            self.SPICE_tls       = self.pref_builder.get_object( "check_SPICE_tls"       )
            self.SPICE_viewonly  = self.pref_builder.get_object( "check_SPICE_viewonly"  )
            self.SPICE_resize    = self.pref_builder.get_object( "check_SPICE_resize"    )
            self.SPICE_clipboard = self.pref_builder.get_object( "check_SPICE_clipboard" )
            self.SPICE_cards     = self.pref_builder.get_object( "check_SPICE_cards"     )
            self.SPICE_sound     = self.pref_builder.get_object( "check_SPICE_sound"     )
            self.SPICE_CA        = self.pref_builder.get_object( "check_SPICE_CA"        )
            self.SPICE_cacert    = self.pref_builder.get_object( "SPICE_CA"              )

        if protocol == "FS":
            self.FS_user   = self.pref_builder.get_object( "entry_FS_user"   )
            self.FS_domain = self.pref_builder.get_object( "entry_FS_dom"    )
            self.FS_folder = self.pref_builder.get_object( "entry_FS_folder" )
            self.FS_type   = self.pref_builder.get_object( "entry_FS_type"   )
            self.FS_server = self.pref_builder.get_object( "entry_FS_serv"   )

    def applyPreferences( self, protocol ):
        """В этой функции параметры для подключения собираются из окна Доп. параметры в список"""

        if protocol == "VMWARE":
            args = dict(
                user       =      self.VMWARE_user.get_text(),
                domain     =      self.VMWARE_domain.get_text(),
                password   =      self.VMWARE_password.get_text(),
                fullscreen = str( self.VMWARE_fullscreen.get_active() ) )

        if protocol == "RDP":
            args = dict(
                username         = self.RDP_user.get_text(),
                domain           = self.RDP_domain.get_text(),
                colordepth       = self.RDP_color.get_active_id(),
                quality          = self.RDP_quality.get_active_id(),
                sound            = self.RDP_sound.get_active_id(),
                sharefolder      = self.RDP_name_folder.get_filename() if self.RDP_share_folder.get_active() else "",
                viewmode         = "3" if self.RDP_viewmode.get_active()      else "0",
                resolution       = ""  if self.RDP_resol_default.get_active() else self.RDP_resolution.get_active_id(),
                shareprinter     = "1" if self.RDP_printers.get_active()      else "0",
                disableclipboard = "0" if self.RDP_clipboard.get_active()     else "1",
                sharesmartcard   = "1" if self.RDP_cards.get_active()         else "0" )

        if protocol == "RDP1":
            args = dict(
                username    = self.RDP_user.get_text(),
                domain      = self.RDP_domain.get_text(),
                color       = self.RDP_color.get_active_id(),
                gserver     = self.RDP_gserver.get_text(),
                guser       = self.RDP_guser.get_text(),
                gdomain     = self.RDP_gdomain.get_text(),
                gpasswd     = self.RDP_gpasswd.get_text(),
                userparams  = self.RDP_userparams.get_text(),
                passwd      = self.RDP_pwd.get_text(),
                folder      = self.RDP_name_folder.get_filename() if self.RDP_share_folder.get_active() else "",
                fullscreen  = "True"  if self.RDP_fullscreen.get_active() else "False",
                clipboard   = "True"  if self.RDP_clipboard.get_active()  else "False",
                admin       = "True"  if self.RDP_admin.get_active()      else "False",
                smartcards  = "True"  if self.RDP_cards.get_active()      else "False",
                printers    = "True"  if self.RDP_printers.get_active()   else "False",
                sound       = "True"  if self.RDP_sound.get_active()      else "False",
                microphone  = "True"  if self.RDP_microphone.get_active() else "False",
                multimon    = "True"  if self.RDP_multimon.get_active()   else "False",
                fonts       = "True"  if self.RDP_fonts.get_active()      else "False",
                aero        = "True"  if self.RDP_aero.get_active()       else "False",
                drag        = "True"  if self.RDP_drag.get_active()       else "False",
                animation   = "True"  if self.RDP_animation.get_active()  else "False",
                theme       = "False" if self.RDP_theme.get_active()      else "True",
                wallpapers  = "False" if self.RDP_wallpapers.get_active() else "True",
                nsc         = "True"  if self.RDP_nsc.get_active()        else "False",
                usb         = "True"  if self.RDP_usb.get_active()        else "False",
                disable_nla = "True"  if self.RDP_nla.get_active()        else "False",
                span        = "True"  if self.RDP_span.get_active()       else "False",
                desktop     = "True"  if self.RDP_desktop.get_active()    else "False",
                downloads   = "True"  if self.RDP_down.get_active()       else "False",
                documents   = "True"  if self.RDP_docs.get_active()       else "False",
                gdi         = "True"  if self.RDP_gdi.get_active()        else "False",
                reconnect   = "False" if self.RDP_reconnect.get_active()  else "True",
                certignore  = "True"  if self.RDP_certignore.get_active() else "False",
                passwdsave  = "True"  if self.RDP_pwdsave.get_active()    else "False",
                glyph       = "True"  if self.RDP_glyph.get_active()      else "False" )
            args[ "workarea"   ] = "False"
            args[ "resolution" ] = ""
            if self.RDP_workarea.get_active(): args[ "workarea" ] = "True"
            elif self.RDP_resol_default.get_active(): pass
            else: args[ "resolution" ] = self.RDP_resolution.get_text()
            if self.RDP_compression.get_active():
                args[ "compression"  ] = "True"
                args[ "compr_level"  ] = self.RDP_compr_level.get_active_id()
            else:
                args[ "compression"  ] = "False"
                args[ "compr_level"  ] = "None"
            if self.RDP_jpeg.get_active():
                args[ "jpeg"         ] = "True"
                args[ "jpeg_quality" ] = str( self.RDP_jpeg_quality.get_value() )
            else:
                args[ "jpeg"         ] = "False"
                args[ "jpeg_quality" ] = "None"

        if protocol == "NX":
            args = dict(
                username          = self.NX_user.get_text(),
                quality           = self.NX_quality.get_active_id(),
                nx_privatekey     = self.NX_path_keyfile.get_filename() if self.NX_keyfile.get_active() else "",
                disableencryption = "1" if self.NX_crypt.get_active()        else "0",
                disableclipboard  = "1" if self.NX_clipboard.get_active()    else "0",
                viewmode          = "4" if self.NX_viewmode.get_active()     else "1",
                resolution        = ""  if self.NX_resol_window.get_active() else self.NX_resolution.get_active_id() )
            args[ "exec" ] = self.NX_exec.get_text()

        if protocol == "VNC":
            args = dict(
                username          = self.VNC_user.get_text(),
                quality           = self.VNC_quality.get_active_id(),
                colordepth        = self.VNC_color.get_active_id(),
                disableencryption = "1" if self.VNC_crypt.get_active()      else "0",
                disableclipboard  = "1" if self.VNC_clipboard.get_active()  else "0",
                viewmode          = "4" if self.VNC_viewmode.get_active()   else "1",
                showcursor        = "1" if self.VNC_showcursor.get_active() else "0",
                viewonly          = "1" if self.VNC_viewonly.get_active()   else "0" )

        if protocol == "VNC1":
            args = dict(
                fullscreen = str( self.VNC_viewmode.get_active() ),
                viewonly   = str( self.VNC_viewonly.get_active() ) )

        if protocol == "XDMCP":
            args = dict(
                colordepth = self.XDMCP_color.get_active_id(),
                viewmode   = "4" if self.XDMCP_viewmode.get_active()      else "1",
                resolution = ""  if self.XDMCP_resol_default.get_active() else self.XDMCP_resolution.get_active_id(),
                showcursor = "1" if self.XDMCP_showcursor.get_active()    else "0",
                once       = "1" if self.XDMCP_once.get_active()          else "0" )
            args[ "exec" ] = self.XDMCP_exec.get_text()

        if protocol == "SSH":
            args = dict(
                username    = self.SSH_user.get_text(),
                ssh_charset = self.SSH_charset.get_text() )
            args[ "exec"  ] = self.SSH_exec.get_text()
            if self.SSH_publickey.get_active():
                args[ "ssh_auth"   ] = "3"
            elif self.SSH_keyfile.get_active():
                args[ "ssh_auth"   ] = "1"
            else: args[ "ssh_auth" ] = "0"
            if args[ "ssh_auth" ] == "1":
                args[ "ssh_privatekey" ] = self.SSH_path_keyfile.get_filename()

        if protocol == "SFTP":
            args = dict(
                username    = self.SFTP_user.get_text(),
                ssh_charset = self.SFTP_charset.get_text(),
                execpath    = self.SFTP_execpath.get_text() )
            if self.SFTP_publickey.get_active():
                args[ "ssh_auth"   ] = "3"
            elif self.SFTP_keyfile.get_active():
                args[ "ssh_auth"   ] = "1"
            else: args[ "ssh_auth" ] = "0"
            if args[ "ssh_auth" ] == "1":
                args[ "ssh_privatekey" ] = self.SFTP_path_keyfile.get_filename()

        if protocol == "SPICE":
            args = dict(
                usetls           = "1" if self.SPICE_tls.get_active()       else "0",
                viewonly         = "1" if self.SPICE_viewonly.get_active()  else "0",
                resizeguest      = "1" if self.SPICE_resize.get_active()    else "0",
                disableclipboard = "0" if self.SPICE_clipboard.get_active() else "1",
                sharesmartcard   = "1" if self.SPICE_cards.get_active()     else "0",
                enableaudio      = "1" if self.SPICE_sound.get_active()     else "0",
                cacert           = self.SPICE_cacert.get_filename() if self.SPICE_CA.get_active() else "" )

        if protocol == "FS":
            args = dict(
                user   = self.FS_user.get_text(),
                domain = self.FS_domain.get_text(),
                folder = self.FS_folder.get_text(),
                type   = self.FS_type.get_active_id() )

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

    def createDb(self, filename):
        """Создает пустой файл БД (или любой другой)"""
        f = open( "%s/%s" % ( WORKFOLDER, filename ),"w" )
        f.close()

    def getServersFromDb(self):
        """Чтение списка ранее посещенных серверов из файла"""
        try:
            for server in open( "%s/servers.db" % WORKFOLDER ):
                try: #попытка прочитать протокол/сервер
                    protocol, address = server.strip().split(':::')
                    self.liststore[protocol].append([address])
                except: pass
        except FileNotFoundError:
            options.log.warning("Список серверов (servers.db) не найден, создан пустой.")
            self.createDb("servers.db")

    def setSavesToListstore(self):
        """Set the list of save connections to ListStore"""
        self.liststore_connect.clear()
        for record in getSaveConnections():
            self.liststore_connect.append( record )

    def writeServerInDb(self, entry):
        """Запись сервера в файл со списком ранее посещенных серверов"""
        db = open( "%s/servers.db" % WORKFOLDER , "r+" )
        protocol = entry.get_name().replace( "1", "" )
        address  = entry.get_text()
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

    def onComprSet(self, widget):
        """Настройка чувствительности списка уровней сжатия"""
        if widget.get_button_sensitivity() == Gtk.SensitivityType.ON:
            widget.set_button_sensitivity(Gtk.SensitivityType.OFF)
        else: widget.set_button_sensitivity(Gtk.SensitivityType.ON)

    def onJpegSet(self, widget):
        """Настройка видимости установки качества кодека JPEG"""
        if widget.get_opacity(): widget.set_opacity(0)
        else: widget.set_opacity(1)

    def onSpanOn(self, widget):
        """Настройка зависимости чувствительности ключа /span от /multimon"""
        if widget.get_sensitive():
            widget.set_sensitive(0)
            widget.set_active(0)
        else: widget.set_sensitive(1)

    def onProperties(self, *args):
        """Окно параметров приложения"""
        window = options.Properties(self)

    def saveFileCtor( self, name, protocol, server ):
        """Connect file (.myc) creation"""
        filename = ( "%s_%s.myc" % ( name.replace( " ", "_" ), protocol ) ).lower()
        options.log.info( "Добавлено новое %s-подключение '%s' (host: %s)", protocol, name, server )
        return filename

    def resaveFileCtor(self, name, protocol, server):
        """Пересохранение подключения с тем же именем файла .myc"""
        fileName = self.fileCtor
        options.log.info("Внесены изменения в подключение '%s'", name)
        return fileName

    def getProgram( self, name ):
        if name == "RDP1":
            return "freerdp"
        if name == "VNC1":
            return "vncviewer"
        if name in [ "RDP", "VNC" ]:
            return "remmina"
        else:
            return None

    def onButtonSave(self, entry):
        """Сохранение параметров для дальнейшего подключения с ними"""
        server   = entry.get_text()
        name     = entry.get_name()
        protocol = name.replace( "1", "" )
        parameters = self.applyPreferences( name )
        namesave = self.pref_builder.get_object( "entry_%s_name" % name ).get_text()
        if namesave == "":
            os.system( "zenity --error --text='\nУкажите имя подключения!' --no-wrap --icon-name=myconnector" )
        elif self.searchName( namesave ) and not self.editClick:
            os.system( "zenity --error --text='\nПодключение с именем \"%s\" уже существует!' --no-wrap --icon-name=myconnector" % namesave )
        else:
            parameters[ "name"     ] = namesave
            parameters[ "protocol" ] = protocol
            parameters[ "server"   ] = server
            if name == "RDP1" and parameters.get ( "username", "" ):
                self.saveKeyring ( parameters.copy() )
                parameters [ "passwd" ] = ""
            program = self.getProgram( name )
            if program: parameters[ "program" ] = program
            if self.editClick:#если нажата кнопка Изменить, то пересохранить
                fileName = self.resaveFileCtor( namesave, protocol, server )
            else:
                fileName = self.saveFileCtor( namesave, protocol, server )
                self.initSubmenuTray()
            options.saveInFile( fileName, parameters )
            self.setSavesToListstore()
            self.pref_window.destroy()
            self.editClick = False
            self.prefClick = False
            self.changePage()
            viewStatus( self.statusbar, "Подключение \"%s\" сохранено..." % namesave )

    def onWCSave(self, entry):
        """Сохранение подключения к Citrix или WEB"""
        server = entry.get_text()
        protocol = entry.get_name()
        name = self.builder.get_object("entry_" + protocol + "_name").get_text()
        if name == "":
            os.system( "zenity --error --text='\nУкажите имя подключения!' --no-wrap --icon-name=myconnector" )
        elif self.searchName( name ) and not self.citrixEditClick and not self.webEditClick:
            os.system( "zenity --error --text='\nПодключение с именем \"%s\" уже существует!' --no-wrap --icon-name=myconnector" % name )
        else:
            parameters = { "name"     : name,
                           "protocol" : protocol,
                           "server"   : server }
            if self.citrixEditClick or self.webEditClick:
                fileName = self.resaveFileCtor(name, protocol, server)
            else:
                fileName = self.saveFileCtor(name, protocol, server)
                self.initSubmenuTray()
            options.saveInFile(fileName, parameters)
            self.setSavesToListstore()
            self.citrixEditClick = False
            self.webEditClick = False
            self.changePage()
            viewStatus(self.statusbar, "Подключение \"" + name + "\" сохранено...")

    def onWCEdit(self, name, server, protocol, edit = True):
        """Функция изменения Citrix или WEB-подключения """
        if protocol == "CITRIX":
            self.citrixEditClick = edit
            index_tab = 6
        if protocol == "WEB":
            self.webEditClick = edit
            index_tab = 9
        self.main_note.set_current_page(0)
        self.conn_note.set_current_page(index_tab)
        entry_serv = self.builder.get_object("entry_serv_" + protocol)
        entry_name = self.builder.get_object("entry_" + protocol + "_name")
        entry_serv.set_text(server)
        entry_name.set_text(name)

    def onWCMenu(self, item):
        protocol = item.get_name()
        self.onWCEdit('','', protocol, False)

    def onSaveConnect(self, treeView, *args):
        """Установка подключения по двойному щелчку на элементе списка"""
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect, fileCtor = table[indexRow][0], table[indexRow][3]
        parameters = options.loadFromFile(fileCtor, self.window)
        if parameters is not None: #если файл .myc имеет верный формат
            parameters[ "name" ] = nameConnect
            name = changeProgram( parameters[ "protocol" ], parameters.get( "program", "" ) ) #TODO - add try/except and log
            if name == "RDP1" and parameters.getboolean( "passwdsave" ):
                parameters[ "passwd" ] = keyring.get_password( parameters[ "server" ] ,parameters[ "username" ] )
            viewStatus( self.statusbar, "Соединение с \"%s\"..." % nameConnect )
            connect = definition( name )
            connect.start( parameters )

    def onPopupMenu(self, widget, event):
        """Контекстное меню списка сохраненных подключений"""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            menu = self.builder.get_object("menu_popup")
            menu.popup(None, None, None, None, event.button, event.time)

    def onPopupEdit(self, treeView):
        """Изменение выбранного подключения"""
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect, self.fileCtor = table[indexRow][0], table[indexRow][3]
        parameters = options.loadFromFile(self.fileCtor, self.window)
        if parameters is not None: #если файл .myc имеет верный формат
            protocol = parameters [ "protocol" ].upper() #TODO - add try/except and log
            if protocol in [ "CITRIX", "WEB" ]:
                self.onWCEdit( nameConnect, parameters [ "server" ], protocol ) #TODO - add try/except and log or parameters.get
            else:
                self.editClick = True
                analogEntry = self.AnalogEntry( protocol, parameters )
                self.onButtonPref( analogEntry, nameConnect )

    def onPopupCopy(self, treeView):
        """Копирование выбранного подключения"""
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect, self.fileCtor = table[indexRow][0], table[indexRow][3]
        parameters = options.loadFromFile(self.fileCtor, self.window)
        if parameters is not None: #если файл .myc имеет верный формат
            protocol = parameters[ "protocol" ].upper() #TODO - add try/except and log
            nameConnect = "%s (копия)" % nameConnect
            if protocol in [ "CITRIX", "WEB" ]:
                self.onWCEdit( nameConnect, parameters[ "server" ], protocol, False ) #TODO - add try/except and log or parameters.get
            else:
                analogEntry = self.AnalogEntry( protocol, parameters )
                self.onButtonPref( analogEntry, nameConnect )

    class AnalogEntry:
        """Класс с методами аналогичными методам Gtk.Entry и реализующий
           инициализацию сохраненных параметров подключения в окне параметров"""
        def __init__(self, name, parameters):
            self.name = name
            self.parameters = parameters
        def get_name( self ):
            return self.name
        def get_text( self ):
            return self.parameters[ "server" ]  #TODO - add try/except and log
        def loadParameters( self ):
            return self.parameters

    def onPopupRemove(self, treeView):
        """Удаление выбранного подключения из списка, БД и файла с его настройками"""
        table, indexRow = treeView.get_selection().get_selected()
        name = table[indexRow][0]
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO, "Удалить данное подключение:")
        dialog.format_secondary_text(name)
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            fileCtor = table[indexRow][3]
            parameters = options.loadFromFile(fileCtor)
            try: keyring.delete_password( parameters.get( "server", "" ), parameters.get( "username", "" ) )
            except: pass
            try: os.remove( "%s/%s" % ( WORKFOLDER, fileCtor ) )
            except: pass
            self.setSavesToListstore()
            options.log.info("Подключение '%s' удалено!", name)
            self.initSubmenuTray()
        dialog.destroy()

    def onPopupSave(self, treeView):
        """Creation desktop-file for the connection from popup menu"""
        dialog = Gtk.FileChooserDialog("Сохранить ярлык подключения в ...", self.window,
            Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        current_folder = (HOMEFOLDER + DESKFOLDER.replace('$HOME','')).replace('"','')
        dialog.set_current_folder(current_folder)
        table, indexRow = treeView.get_selection().get_selected()
        nameConnect = table[indexRow][0]
        dialog.set_current_name(nameConnect + '.desktop')
        dialog.set_do_overwrite_confirmation(True) #запрос на перезапись одноименного файла
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = dialog.get_filename()
            name = name.replace(".desktop","")
            filename = name + ".desktop"
            self.createDesktopFile(filename, nameConnect, os.path.basename(name))
            viewStatus(self.statusbar, 'Сохранено в "' + filename + '"...')
            options.log.info("Для подключения '%s' сохранен ярлык быстрого запуска: '%s'", nameConnect, filename)
        dialog.destroy()

    def onChangePage(self, notepad, box, page):
        """Очистка строки состояния при переключении вкладок"""
        viewStatus(self.statusbar, '')

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
        """Открытие wiki в Интернете"""
        os.system ('xdg-open "http://wiki.myconnector.ru/"')

    def changePage(self, index = 1):
        self.main_note.set_current_page(index)

    def onShowWindow(self, *args):
        if self.window.is_active():
            self.onHideWindow(self)
        else: self.showWin()

    def onHideWindow(self, *args):
        if self.optionEnabled( 'tray' ):
            self.window.hide()
            if not self.trayDisplayed: self.trayDisplayed = self.initTray()
            return True
        else:
            self.quit()

    def onButtonDefault(self, entry):
        """Сохранение параметров подключений по умолчанию"""
        name = entry.get_name()
        args = self.applyPreferences( name )
        for key in args.keys():
            CONFIGS[ name ][ key ] = args[ key ]
        config_save()
        viewStatus( self.statusbar, "Настройки по умолчанию сохранены" )

    def saveKeyring(self, parameters):
        """Сохранение пароля в связу ключей и отметки об этом в файл подключения"""
        if parameters.get( "passwdsave", "False" ) == "True":
            keyring.set_password( parameters [ "server" ], parameters [ "username" ], parameters [ "passwd" ] )
        else:
            try: keyring.delete_password( parameters [ "server" ],  parameters [ "username" ] )
            except: pass

    def onDeveloper(self, *args):
        """Кнопка 'Связь с разработчиком'"""
        os.system ('xdg-open "mailto:ek@myconnector.ru"')

    def onBugs(self, *args):
        """Кнопка 'Сообщить об ошибке'"""
        os.system ('xdg-open "http://bugs.myconnector.ru/"')

    def fixServerForLocal(self, widget):
        """Установка значения поля сервер в 'localhost' при выборе 'Локальный каталог'"""
        if self.FS_type.get_active_id() == "file" and not widget.get_text() : widget.set_text("localhost")

    def onKiosk(self, *args):
        """Button 'Mode KIOSK'"""
        from myconnector.kiosk import Kiosk
        window = Kiosk()

    def filenameFromName( self, name ):
        """Определение имени конфигурационного файла подключения по имени подключения"""
        for record in getSaveConnections():
            if record[0] == name:
                return record[3]
        return False

    def searchName( self, name ):
        """Существует ли подключение с указанным именем"""
        for record in getSaveConnections():
            if record[0] == name:
                return True
        return False

def connect( name ):
    """Start connection by name"""
    myc_file = Gui.filenameFromName( None, name )
    if myc_file:
        options.log.info( "Запуск сохраненного подключения: %s" % name )
        connectFile( myc_file )
    else:
        options.msg_error( "\"%s\": подключение с таким именем не найдено!" % name, options.log.error )
        exit( 1 )

def main( name ):
    """Main function"""
    if name:
        if name[0] == "'": name = name.replace( "'", "" ) #for KIOSK (mode=2)
        if os.path.isfile( name ): openFile( name )
        else:
            options.msg_error( "\"%s\": нет такого файла!" % name, options.log.error )
            exit( 1 )
    else:
        gui = Gui()
        initSignal(gui)
        gui.run(None)
        options.checkLogFile(LOGFILE); options.checkLogFile(STDLOGFILE)

