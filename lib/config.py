#!/usr/bin/python3
# -*- coding: utf-8 -*-

# MyConnector
# Copyright (C) 2020 Evgeniy Korneechev <ek@myconnector.ru>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the version 2 of the GNU General
# Public License as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

from configparser import ConfigParser
from myconnector.params import *

_config = ConfigParser( interpolation = None )
_config_file = "%smyconnector.conf" % WORKFOLDER

def init():
    """Default config for MyConnector"""
    _config["myconnector"] = DEFAULT
    with open( _config_file, 'w' ) as configfile:
        _config.write( configfile )
