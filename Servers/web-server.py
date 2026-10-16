#! /usr/bin/env python

#
# Web Server Application (HTTP + HTTPS with IPv4 + IPv6)
# https://github.com/microy/rt-auxerre
# Copyright (c) 2023-2026 Michaël Roy
# usage : $ sudo ./web-server.py
#

#
# Required external dependency :
#	openssl
#

# External modules
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, ThreadingHTTPSServer

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Web page
WEBPAGE = rf'''
<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="UTF-8">
	<link rel="icon" href="data:,">
	<link rel="stylesheet" href="style.css">
	<title>IUT RT Auxerre Web Server</title>
</head>
<body>
	<h1>IUT RT Auxerre Web Server</h1>
	<p><b>Bienvenue sur la machine :</b> <code>{platform.node()}</code></p>
	<p><b>L'adresse du serveur est :</b> <code>{{}}</code></p>
	<p><b>Vous êtes connectés en :</b> <code>{{}}</code></p>
	<p><b>Votre adresse est :</b> <code>{{}}</code></p>
</body>
</html>
'''

# Stylesheet
STYLESHEET = '''
body {
	font-family: sans-serif;
}
h1 {
    color: blue;
	text-align: center;
}
'''

# Protocol list
PROTOCOL = {
	80: 'HTTP',
	443: 'HTTPS'
}

# Cleanup an IP Address
# If it is an IPv4-mapped to IPv6 address, remove ::ffff:
def CLEANUP_ADDRESS( ip_address ) :
	return re.sub( r'^::ffff:', '', ip_address )

# Generate temporary files for the server TLS certificate and key
CERTFILE = tempfile.NamedTemporaryFile()
KEYFILE = tempfile.NamedTemporaryFile()

# Generate a TLS certificate and key
SSLCOMMAND = f'openssl req -x509 -newkey rsa:2048 -noenc -days 365 -out {CERTFILE.name} -keyout {KEYFILE.name} -subj /CN=rt-auxerre.fr'
subprocess.run( SSLCOMMAND.split(), capture_output=True )

# HTTP Server class to handle IPv6
class HTTPServer( ThreadingHTTPServer ) :
	address_family = socket.AF_INET6

# HTTPS Server class to handle IPv6
class HTTPSServer( ThreadingHTTPSServer ) :
	address_family = socket.AF_INET6

# HTTP request handler class to send a simple web page
class HTTPRequestHandler( SimpleHTTPRequestHandler ) :
	# Handle GET request
	def do_GET( self ) :
		# Send the stylesheet
		if self.path == '/style.css' :
			self.send_response( HTTPStatus.OK )
			self.send_header( 'Content-type', 'text/css' )
			self.end_headers()
			self.wfile.write( bytes( STYLESHEET, 'utf-8' ) )
		# Redirect if necessary
		elif self.path != '/' :
			self.send_response( HTTPStatus.MOVED_PERMANENTLY )
			self.send_header( 'Location', '/' )
			self.end_headers()
		# Sent the Web page
		else :
			# Get server IP address
			server_external_ip_address = re.search( r'Host: (\[)?(.*)(?(1)\])', self.headers.as_string() ).group( 2 )
			server_ip_address = CLEANUP_ADDRESS( self.connection.getsockname()[0] )
			if server_ip_address != server_external_ip_address :
				server_ip_address = f'{server_external_ip_address} ({server_ip_address})'
			# Get client IP address
			self.client_ip_address = CLEANUP_ADDRESS( self.client_address[0] )
			# Get Web protocol
			self.web_protocol = PROTOCOL[ self.server.server_port ]
			# Send the web page
			self.send_response( HTTPStatus.OK )
			self.send_header( 'Content-type', 'text/html' )
			self.end_headers()
			self.wfile.write( bytes( WEBPAGE.format( server_ip_address, self.web_protocol, self.client_ip_address ), 'utf-8' ) )
	# Define the console log messages
	def log_message( self, format, *args ) :
		# Log only the web page connection (not the stylesheet)
		if self.path == '/' :
			sys.stderr.write( f'[ {self.log_date_time_string()} ] - Connexion from {self.client_ip_address} - ( {self.web_protocol} )\n' )

# Create the HTTP server
httpd = HTTPServer( ('::', 80), HTTPRequestHandler )

# Create the HTTPS server
httpsd = HTTPSServer( ('::', 443), HTTPRequestHandler, certfile=CERTFILE.name, keyfile=KEYFILE.name )

# Print banner
print( '\n~~~~   IUT RT Auxerre Web Server   ~~~~\n' )
print( 'Press Ctrl+C to stop the application...\n' )

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
