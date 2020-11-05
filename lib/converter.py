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
_info    = "Converter from .ctor (outdated format Connector) to new .myc (MyConnector)"

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
            params_to_myc[ "program"         ] = "remmina"
            params_to_myc[ "username"        ] = params_from_ctor[ 2 ]
            params_to_myc[ "domain"          ] = params_from_ctor[ 3 ]
            params_to_myc[ "colordepth"      ] = params_from_ctor[ 4 ]
            params_to_myc[ "quality"         ] = params_from_ctor[ 5 ]
            params_to_myc[ "resolution"      ] = params_from_ctor[ 6 ]
            params_to_myc[ "viewmode"        ] = params_from_ctor[ 7 ]
            params_to_myc[ "sharefolder"     ] = params_from_ctor[ 8 ]
            params_to_myc[ "shareprinter"    ] = params_from_ctor[ 9 ]
            params_to_myc[ "disableclipboard"] = params_from_ctor[ 10 ]
            params_to_myc[ "sound"           ] = params_from_ctor[ 11 ]
            params_to_myc[ "sharesmartcard"  ] = params_from_ctor[ 12 ]
        else:
            params_to_myc[ "program"         ] = "freerdp"
            params_to_myc[ "username"        ] = params_from_ctor[ 2 ]
            params_to_myc[ "domain"          ] = params_from_ctor[ 3 ]
            params_to_myc[ "fullscreen"      ] = bool( params_from_ctor[ 4 ] )
            params_to_myc[ "clipboard"       ] = bool( params_from_ctor[ 5 ] )
            params_to_myc[ "resolution"      ] = params_from_ctor[ 6 ]
            params_to_myc[ "color"           ] = params_from_ctor[ 7 ]
            params_to_myc[ "folder"          ] = params_from_ctor[ 8 ]
            params_to_myc[ "gserver"         ] = params_from_ctor[ 9 ]
            params_to_myc[ "guser"           ] = params_from_ctor[ 10 ]
            params_to_myc[ "gdomain"         ] = params_from_ctor[ 11 ]
            params_to_myc[ "gpasswd"         ] = params_from_ctor[ 12 ]
            params_to_myc[ "admin"           ] = bool( params_from_ctor[ 13 ] )
            params_to_myc[ "smartcards"      ] = bool( params_from_ctor[ 14 ] )
            params_to_myc[ "printers"        ] = bool( params_from_ctor[ 15 ] )
            params_to_myc[ "sound"           ] = bool( params_from_ctor[ 16 ] )
            params_to_myc[ "microphone"      ] = bool( params_from_ctor[ 17 ] )
            params_to_myc[ "multimon"        ] = bool( params_from_ctor[ 18 ] )
            params_to_myc[ "compression"     ] = bool( params_from_ctor[ 19 ] )
            params_to_myc[ "compr_level"     ] = str( params_from_ctor[ 20 ] )
            params_to_myc[ "fonts"           ] = bool( params_from_ctor[ 21 ] )
            params_to_myc[ "aero"            ] = bool( params_from_ctor[ 22 ] )
            params_to_myc[ "drag"            ] = bool( params_from_ctor[ 23 ] )
            params_to_myc[ "animation"       ] = bool( params_from_ctor[ 24 ] )
            params_to_myc[ "theme"           ] = bool( params_from_ctor[ 25 ] )
            params_to_myc[ "wallpapers"      ] = bool( params_from_ctor[ 26 ] )
            params_to_myc[ "nsc"             ] = bool( params_from_ctor[ 27 ] )
            params_to_myc[ "jpeg"            ] = bool( params_from_ctor[ 28 ] )
            params_to_myc[ "jpeg_quality"    ] = str( params_from_ctor[ 29 ] )
            params_to_myc[ "usb"             ] = bool( params_from_ctor[ 30 ] )
            params_to_myc[ "disable_nla"     ] = bool( params_from_ctor[ 31 ] )
            params_to_myc[ "workarea"        ] = bool( params_from_ctor[ 32 ] )
            params_to_myc[ "span"            ] = bool( params_from_ctor[ 33 ] )
            params_to_myc[ "desktop"         ] = bool( params_from_ctor[ 34 ] )
            params_to_myc[ "downloads"       ] = bool( params_from_ctor[ 35 ] )
            params_to_myc[ "documents"       ] = bool( params_from_ctor[ 36 ] )
            params_to_myc[ "gdi"             ] = bool( params_from_ctor[ 37 ] )
            params_to_myc[ "reconnect"       ] = bool( params_from_ctor[ 38 ] )
            params_to_myc[ "certignore"      ] = bool( params_from_ctor[ 39 ] )
            params_to_myc[ "glyph"           ] = bool( params_from_ctor[ 42 ] )
            params_to_myc[ "userparams"      ] = params_from_ctor[ 43 ]

    if protocol == "NX":
        params_to_myc[ "username"            ] = params_from_ctor[ 2 ]
        params_to_myc[ "quality"             ] = params_from_ctor[ 3 ]
        params_to_myc[ "resolution"          ] = params_from_ctor[ 4 ]
        params_to_myc[ "viewmode"            ] = params_from_ctor[ 5 ]
        params_to_myc[ "nx_privatekey"       ] = params_from_ctor[ 6 ]
        params_to_myc[ "disableencryption"   ] = params_from_ctor[ 7 ]
        params_to_myc[ "disableclipboard"    ] = params_from_ctor[ 8 ]
        params_to_myc[ "exec"                ] = params_from_ctor[ 9 ]

    if protocol == "XDMCP":
        params_to_myc[ "colordepth"          ] = params_from_ctor[ 2 ]
        params_to_myc[ "viewmode"            ] = params_from_ctor[ 3 ]
        params_to_myc[ "resolution"          ] = params_from_ctor[ 4 ]
        params_to_myc[ "once"                ] = params_from_ctor[ 5 ]
        params_to_myc[ "showcursor"          ] = params_from_ctor[ 6 ]
        params_to_myc[ "exec"                ] = params_from_ctor[ 7 ]

    if protocol == "SPICE":
        params_to_myc[ "usetls"              ] = params_from_ctor[ 2 ]
        params_to_myc[ "viewonly"            ] = params_from_ctor[ 3 ]
        params_to_myc[ "resizeguest"         ] = params_from_ctor[ 4 ]
        params_to_myc[ "disableclipboard"    ] = params_from_ctor[ 5 ]
        params_to_myc[ "sharesmartcard"      ] = params_from_ctor[ 6 ]
        params_to_myc[ "enableaudio"         ] = params_from_ctor[ 7 ]
        params_to_myc[ "cacert"              ] = params_from_ctor[ 8 ]

    if protocol == "SSH":
        params_to_myc[ "username"            ] = params_from_ctor[ 2 ]
        params_to_myc[ "ssh_auth"            ] = params_from_ctor[ 3 ]
        params_to_myc[ "ssh_privatekey"      ] = params_from_ctor[ 4 ]
        params_to_myc[ "ssh_charset"         ] = params_from_ctor[ 5 ]
        params_to_myc[ "exec"                ] = params_from_ctor[ 6 ]

    if protocol == "SFTP":
        params_to_myc[ "username"            ] = params_from_ctor[ 2 ]
        params_to_myc[ "ssh_auth"            ] = params_from_ctor[ 3 ]
        params_to_myc[ "ssh_privatekey"      ] = params_from_ctor[ 4 ]
        params_to_myc[ "ssh_charset"         ] = params_from_ctor[ 5 ]
        params_to_myc[ "execpath"            ] = params_from_ctor[ 6 ]

    if protocol == "FS":
        params_to_myc[ "user"                ] = params_from_ctor[ 2 ]
        params_to_myc[ "domain"              ] = params_from_ctor[ 3 ]
        params_to_myc[ "folder"              ] = params_from_ctor[ 4 ]
        params_to_myc[ "type"                ] = params_from_ctor[ 5 ]

    if protocol == "VMWARE":
        params_to_myc[ "username"            ] = params_from_ctor[ 2 ]
        params_to_myc[ "domain"              ] = params_from_ctor[ 3 ]
        params_to_myc[ "passwd"              ] = params_from_ctor[ 4 ]
        params_to_myc[ "fullscreen"          ] = params_from_ctor[ 5 ]

    conf = ConfigParser()
    conf [ "myconnector" ] = params_to_myc
    return conf [ "myconnector" ]

def myc_save( args ):
    """Save imported parameters to myc file"""
    _config = ConfigParser()
    ctorfile = args.input
    try:
        mycfile = args.output
    except:
        mycfile = ctorfile.replace( ".ctor", ".myc" )
    _config [ "myconnector" ] = ctor_import( ctorfile )
    with open( mycfile, "w" ) as configfile:
        _config.write( configfile )
    print( "The file (%s) has been successfully converted to the new format  - %s " % ( ctorfile, mycfile ) )

def parseArgs():
    """Description of the command line argument parser"""
    args = ArgumentParser( prog = "ctor2myc", formatter_class = RawTextHelpFormatter, add_help=False )
    args.add_argument( "-v", "--version", action = "version", help = "show the application version",
                       version = "ctor2myc v%s\n%s." % ( _version, _info ) )
    args.add_argument( "input",  type = str, metavar = "input.ctor" )
    args.add_argument( "output", type = str, metavar = "output.myc", nargs = "?" )
    return args.parse_args()

def main():
    args = parseArgs()
    myc_save( args )

