#! /usr/bin/env python3

#
# FTP Server Application with TLS support
# https://github.com/microy/rt-auxerre
# Copyright (c) 2024 Michaël Roy
# usage : $ sudo ./ftp-server.py
#

#
# Required external dependencies :
#   python-pyftpdlib
#   python-pyopenssl
#

# External modules
import os, subprocess, tempfile
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler, TLS_FTPHandler
from pyftpdlib.servers import FTPServer

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Create a temporary directory for the FTP server
FTP_DIRECTORY = tempfile.TemporaryDirectory()

# Create a temporary text file as an example
with open( FTP_DIRECTORY.name + '/hello.txt', 'w' ) as f :
	f.write( 'Bienvenue sur le serveur FTP RT Auxerre !\n' )
	f.close()

# Generate temporary files for the server TLS certificate and key
CERTFILE = tempfile.NamedTemporaryFile()
KEYFILE = tempfile.NamedTemporaryFile()

# Generate a TLS certificate and key
SSLCOMMAND = f'openssl req -x509 -newkey rsa:2048 -nodes -days 365 -out {CERTFILE.name} -keyout {KEYFILE.name} -subj /CN=rt-auxerre.fr'
subprocess.run( SSLCOMMAND.split(), capture_output=True )

# Instantiate a dummy authorizer for managing 'anonymous' users
authorizer = DummyAuthorizer()
authorizer.add_anonymous( FTP_DIRECTORY.name )

# Instantiate FTP handler class with TLS support
handler = TLS_FTPHandler
handler.certfile = CERTFILE.name
handler.keyfile = KEYFILE.name
handler.authorizer = authorizer
handler.banner = 'RT Auxerre FTP Server'

# Start the FTP server
server = FTPServer( ( '::', 21 ), handler )
server.serve_forever()
