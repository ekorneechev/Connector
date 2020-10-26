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

from argparse import ( ArgumentParser,
                       RawTextHelpFormatter )
from configparser import ( ConfigParser,
                           ParsingError )
from myconnector.connector import options
from os.path import basename
from re import sub
from pickle import load
from myconnector.config import CONFIGS

_version = "0.1"
_info    = "Converter from .ctor (outdated format Connector) to new .myc"

def rdp_import( filename ):
    """Get parameters from RDP file"""
    tmpconf = "/tmp/%s" % basename( filename )
    tmpfile = open( tmpconf, "w" )
    print( "[rdp]", file = tmpfile )
    with open( filename, "r", errors = "ignore" ) as f:
        text = f.read().replace( "\x00", "" ).replace( "\n\n", "\n" )
        print( sub( ":.*:", "=", text ), file = tmpfile )
    tmpfile.close()
    conf = ConfigParser()
    try:
        conf.read( tmpconf )
        try:
            config = conf[ "rdp" ]
        except KeyError:
            options.log.exception( "Файл \"%s\" не содержит секцию [rdp]." % filename )
            return None
        config[ "program"    ] = "freerdp"
        config[ "protocol"   ] = "RDP"
        config[ "fullscreen" ] = "True"
        config[ "desktop"    ] = config[ "downloads" ] = config[ "documents" ]= "True" if config.get( "drivestoredirect", "" ) else "False"
        config[ "username"   ] = config.get( "username",        "" ).replace( "\\", "\\\\" )
        config[ "server"     ] = config.get( "full address",    "" )
        config[ "gserver"    ] = config.get( "gatewayhostname", "" )
        config[ "color"      ] = config.get( "session bpp",     "" )
        config[ "gserver"    ] = config.get( "gatewayhostname", "" )
        config[ "usb"        ] = "True"  if config.get( "devicestoredirect", "" ) else "False"
        config[ "sound"      ] = "True"  if config.get( "audiomode", "2" ) == "0" else "False"
        config[ "printers"   ] = "True"  if config.getboolean( "redirectprinters" ) else "False"
        config[ "smartcards" ] = "True"  if config.getboolean( "redirectsmartcards" ) else "False"
        config[ "clipboard"  ] = "True"  if config.getboolean( "redirectclipboard" ) else "False"
        config[ "reconnect"  ] = "True"  if config.getboolean( "autoreconnection enabled" )  else "False"
        config[ "microphone" ] = "True"  if config.getboolean( "audiocapturemode" )  else "False"
        config[ "multimon"   ] = "True"  if config.getboolean( "use multimon" )  else "False"
        config[ "fonts"      ] = "True"  if config.getboolean( "allow font smoothing" )  else "False"
        config[ "aero"       ] = "True"  if config.getboolean( "allow desktop composition" )  else "False"
        config[ "theme"      ] = "True"  if config.getboolean( "disable themes" )  else "False"
        config[ "wallpapers" ] = "True"  if config.getboolean( "disable wallpaper" )  else "False"
        config[ "drag"       ] = "False" if config.getboolean( "disable full window drag" )  else "True"
        config[ "animation"  ] = "False" if config.getboolean( "disable menu anims" )  else "True"
        return config
    except ParsingError:
        options.log.exception( "Файл \"%s\" содержит ошибки." % filename )
        return None

def remmina_import( filename ):
    """Get parameters from remmina file"""
    conf = ConfigParser()
    try:
        conf.read( filename )
        try:
            conf[ "remmina" ][ "program" ] = "remmina"
            return conf[ "remmina" ]
        except KeyError:
            options.log.exception( "Файл \"%s\" не содержит секцию [remmina]." % filename )
            return None
    except ParsingError:
        options.log.exception( "Файл \"%s\" содержит ошибки." % filename )
        return None

def ctor_import( filename ):
    """Get parameters from ctor (old format) file"""
    with open( filename, "rb" ) as ctorfile:
        params_from_ctor = load( ctorfile )
    protocol = params_from_ctor[ 0 ]
    params_to_myc = {}
    params_to_myc[ "protocol" ] = protocol
    params_to_myc[ "server"   ] = params_from_ctor[ 1 ]

    if protocol == "VNC":
        if len( params_from_ctor ) == 4:
            params_to_myc[ "program"    ] = "vncviewer"
            params_to_myc[ "fullscreen" ] = bool( params_from_ctor[ 2 ] )
            params_to_myc[ "viewonly"   ] = bool( params_from_ctor[ 3 ] )
        else:
            params_to_myc[ "program"           ] = "remmina"
            params_to_myc[ "username"          ] = params_from_ctor[ 2 ]
            params_to_myc[ "quality"           ] = params_from_ctor[ 3 ]
            params_to_myc[ "colordepth"        ] = params_from_ctor[ 4 ]
            params_to_myc[ "viewmode"          ] = params_from_ctor[ 5 ]
            params_to_myc[ "viewonly"          ] = params_from_ctor[ 6 ]
            params_to_myc[ "disableencryption" ] = params_from_ctor[ 7 ]
            params_to_myc[ "disableclipboard"  ] = params_from_ctor[ 8 ]
            params_to_myc[ "showcursor"        ] = params_from_ctor[ 9 ]

    if protocol == "RDP":
        if len( params_from_ctor ) == 13:
            params_to_myc[ "program" ] = "remmina"
        else:
            params_to_myc[ "program" ] = "freerdp"

    conf = ConfigParser()
    conf [ "myconnector" ] = params_to_myc
    return conf [ "myconnector" ]

def myc_save( ctorfile ):
    """Save imported parameters to myc file"""
    _config = ConfigParser()
    mycfile = ctorfile.replace( ".ctor", ".myc" )
    _config [ "myconnector" ] = ctor_import( ctorfile )
    with open( mycfile, "w" ) as configfile:
        _config.write( configfile )
    print( "The file (%s) has been successfully converted to the new format  - %s " % ( ctorfile, mycfile ) )

def parseArgs():
    """Description of the command line argument parser"""
    args = ArgumentParser( prog = "ctor2myc", formatter_class = RawTextHelpFormatter, description = _info )
    args.add_argument( "-v", "--version", action = "version", help = "show the application version",
                       version = "ctor2myc v%s\n%s (MyConnector)." % ( _version, _info ) )
    args.add_argument( "filename", type = str, help = "name of the file .ctor for convert" )
    return args.parse_args()

def main():
    args = parseArgs()
    myc_save( args.filename )

