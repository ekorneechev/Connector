#!/usr/bin/python3

from os import ( system,
                 getuid )
from argparse import ( ArgumentParser,
                       RawTextHelpFormatter )
from .params import ( VERSION,
                      RELEASE )

def parseArgs():
    """Description of the command line argument parser"""
    about = "MyConnector - %s (%s)" % (VERSION, RELEASE)
    args = ArgumentParser( prog = 'myconnector', formatter_class = RawTextHelpFormatter,
                                   description = 'MyConnector - remote desktop chooser.\n\nDo not specify parameters for starting the GUI.')
    args.add_argument ( '--disable-kiosk', action = 'store_true', default = False, help = "disable the mode KIOSK" )
    args.add_argument ('-v', '--version', action = 'version', help = "show the application version", version = about)
    args.add_argument ('-d', '--debug', action = 'store_true', default = False, help = "show log files online")
    args.add_argument ('-q', '--quit', action = 'store_true', default = False, help = "quit the application")
    args.add_argument('name', type = str, nargs = '?', help = 'name of the file (.ctor, .remmina, .rdp) or saved connection')
    return args.parse_args()

def main():
    system( "xdg-mime default myconnector.desktop application/x-myconnector" )
    args = parseArgs()
    if args.quit:
        from .ui import quitApp as quit
        quit()
    if args.disable_kiosk:
        if getuid() == 0:
            try:
                from kiosk.kiosk import ( disable_kiosk,
                                          config_init )
                disable_kiosk()
                config_init()
                exit (0)
            except ImportError:
                print ( "The mode KIOSK unavailable, package is not installed." )
                exit (127)
        else:
            print ( "Permission denied!" )
            exit (126)
    if args.debug:
        from .ui import startDebug as debug
        debug()
    from .ui import f_main as run
    run ( name = args.name )
