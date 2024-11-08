#! /usr/bin/env python3

#
# FTP Server Application with TLS support
# https://github.com/microy/rt-auxerre
# Copyright (c) 2024 Michaël Roy
# usage : $ sudo ./ftp-server.py
#

#
# Required external dependency :
#	python-pyftpdlib (Arch) or python3-pyftpdlib (Ubuntu)
#

# External modules
import os, platform, tempfile
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Simple FTP message
FTP_MESSAGE = rf'Bienvenue sur le serveur FTP RT Auxerre de la machine {platform.node()} !'

# Create a temporary directory for the FTP server
FTP_DIRECTORY = tempfile.TemporaryDirectory()

# Create a temporary text file as an example
with open( FTP_DIRECTORY.name + '/hello.txt', 'w' ) as f :
	f.write( FTP_MESSAGE + '\n' )
	f.close()

# Instantiate a dummy authorizer for managing 'anonymous' users
authorizer = DummyAuthorizer()
authorizer.add_anonymous( FTP_DIRECTORY.name )

# Instantiate FTP handler class
handler = FTPHandler
handler.authorizer = authorizer
handler.banner = FTP_MESSAGE

# Start the FTP server
server = FTPServer( ( '::', 21 ), handler )
server.serve_forever()
