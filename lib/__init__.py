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

from os import ( system,
                 getuid )
from argparse import ( ArgumentParser,
                       RawTextHelpFormatter )
from .config import ( VERSION,
                      RELEASE )

def parseArgs():
    """Description of the command line argument parser"""
    about = "MyConnector - %s (%s)" % (VERSION, RELEASE)
    args = ArgumentParser( prog = "myconnector", formatter_class = RawTextHelpFormatter, usage = "%(prog)s [options]",
                           description = "MyConnector - remote desktop client.",
                           epilog = "Do not specify parameters for starting the GUI.\n\nCopyright (C) 2014-2020 Evgeniy Korneechev <ek@myconnector.ru>")
    args.add_argument( "-c", "--connection", help = "name of the saved connection" )
    args.add_argument( "-f", "--file", help = "name of the file (.myc, .remmina, .rdp)" )
    args.add_argument( "-l", "--list", action = "store_true", default = False, help = "list of the saved connections" )
    args.add_argument( "--kiosk", metavar="<option>", help = "KIOSK mode control ('--kiosk help' for more information)" )
    args.add_argument( "-v", "--version", action = "version", help = "show the application version", version = about)
    args.add_argument( "-d", "--debug", action = "store_true", default = False, help = "show log files online")
    args.add_argument( "-q", "--quit", action = "store_true", default = False, help = "quit the application")
    args.add_argument( "name", type = str, nargs = "?", metavar="FILE", help = "name of the file (.myc, .remmina, .rdp)" )
    return args.parse_args()

def parseKiosk( option ):
    """MyConnector KIOSK mode control"""
    if option == "disable":
        if getuid() == 0:
            try:
                from kiosk.kiosk import disable_kiosk
                disable_kiosk()
                exit( 0 )
            except ImportError:
                print( "The mode KIOSK unavailable, package is not installed." )
                exit( 127 )
        else:
            print( "Permission denied!" )
            exit( 126 )
    if option == "help":
        print( """myconnector --kiosk - MyConnector KIOSK mode control

Usage: myconnector --kiosk <option>

Options:
  disable            disable the mode;
  enable             enable the mode with additional options;
  help               show this text and exit.""" )
        exit( 0 )
    else:
        print( "myconnector --kiosk: invalid command: %s\n"
               "Try 'myconnector --kiosk help' for more information." % option )
        exit( 1 )

def main():
    system( "xdg-mime default myconnector.desktop application/x-myconnector" )
    args = parseArgs()
    if args.quit:
        from .ui import quitApp as quit
        quit()
    if args.kiosk:
        parseKiosk( args.kiosk )
    if args.debug:
        from .ui import startDebug as debug
        debug()
    if args.list:
        from .ui import getSaveConnections as list_connections
        _list, _group = list_connections()
        for record in _list:
            print( '"%s"' % record[ 0 ] )
        exit( 0 )
    if args.connection:
        from .ui import connect
        connect( args.connection )
        exit( 0 )
    file = ""
    if args.file or args.name:
        file = args.file if args.file else args.name
    from .ui import main as run
    run ( file )

