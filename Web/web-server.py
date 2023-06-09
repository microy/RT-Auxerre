#! /usr/bin/env python3

#
# Web Server Application (HTTP and HTTPS)
# https://github.com/microy/rt-auxerre
# Copyright (c) 2023 Michaël Roy
# usage : $ sudo ./web-server.py
#

# External modules
import http
import http.server
import os
import platform
import re
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import threading

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Print banner
print( '\n~~~~~~~~    HTTP(S) Server    ~~~~~~~~~')
print( 'Press Ctrl+C to stop the application...\n' )

# Simple web page
WEBPAGE = f'''\
<html>
<head><link rel="icon" href="data:," /></head>
<body style="font-family:sans-serif;">
<h1>Bienvenue sur {platform.node()} !!!</h1>
<p>Vous êtes connectés en {{}}</p>
<p>Votre adresse est {{}}</p>
</body>
</html>
'''

# Protocol list
PROTOCOL = { 80 : 'HTTP', 443 : 'HTTPS' }

# Generate temporary files for the server TLS certificate and key
CERTFILE = tempfile.NamedTemporaryFile()
KEYFILE = tempfile.NamedTemporaryFile()

# Generate a TLS certificate and key
SSLCOMMAND = f'openssl req -x509 -newkey rsa:2048 -nodes -days 365 -out {CERTFILE.name} -keyout {KEYFILE.name} -subj /CN=rt-auxerre.fr'
subprocess.run( SSLCOMMAND.split(), capture_output=True )

# HTTP Server class to handle IPv6
class HTTPServer( http.server.HTTPServer ) :
	address_family = socket.AF_INET6

# HTTP request handler class to send a simple web page
class HTTPRequestHandler( http.server.SimpleHTTPRequestHandler ) :
	# Handle GET request
	def do_GET( self ) :
		# Redirect if necessary
		if self.path != '/' :
			self.send_response( http.HTTPStatus.MOVED_PERMANENTLY )
			self.send_header( 'Location', '/' )
			self.end_headers()
			return
		# Send the web page
		self.send_response( http.HTTPStatus.OK )
		self.send_header( 'Content-type', 'text/html; charset=utf-8' )
		self.end_headers()
		self.wfile.write( bytes( WEBPAGE.format( self.protocol, self.address_string ), 'utf-8' ) )
	# Define the console log messages
	def log_message( self, format, *args ) :
		sys.stderr.write( f'[ {self.log_date_time_string()} ] - Connexion from {self.address_string} - ( {self.protocol} )\n' )
	# Return the client IP address (converted if it is a IPv4 mapped address)
	@property
	def address_string( self ) :
		return re.sub( r'^::ffff:', '', self.client_address[0] )
	# Return the protocol used (HTTP or HTTPS)
	@property
	def protocol( self ) :
		return PROTOCOL[ self.server.server_port ]

# Create the HTTP server
httpd = HTTPServer( ( '::', 80 ), HTTPRequestHandler )

# Create the HTTPS server
httpsd = HTTPServer( ( '::', 443 ), HTTPRequestHandler )
# Wrap the server with TLS
httpsd.socket = ssl.wrap_socket( httpsd.socket, certfile=CERTFILE.name, keyfile=KEYFILE.name, server_side=True )

# Handle exceptions such as Ctrl+C
try :
	# Start the HTTP server
	threading.Thread( target=httpd.serve_forever, daemon=True ).start()
	# Start the HTTPS server
	threading.Thread( target=httpsd.serve_forever, daemon=True ).start()
	# Wait for a signal (such as KeybordInterrupt)
	signal.pause()
# Catch exceptions
except : pass

# Remove the temporary files
CERTFILE.close()
KEYFILE.close()