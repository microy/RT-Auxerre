#! /usr/bin/env python3

#
# Web Server Application (HTTP and HTTPS)
# https://github.com/microy/rt-auxerre
# Copyright (c) 2023-2024 Michaël Roy
# usage : $ sudo ./web-server.py
#

# External modules
import http.server, socket, ssl
import os, platform, re, signal, sys, tempfile
import subprocess, threading

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Simple web page
WEBPAGE = rf'''
<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="UTF-8">
	<link rel="icon" href="data:,"/>
	<title>RT Auxerre Web Server</title>
</head>
<body style="font-family: sans-serif;">
	<br/>
	<h1 style="text-align: center;">
🇷​​​​​🇹​​​​​ 🇦​​​​​🇺​​​​​🇽​​​​​🇪​​​​​🇷​​​​​🇷​​​​​🇪​​​​​
	</h1>
	<br/>
	<br/>
	<p><b>Bienvenue sur la machine :</b> <code>{platform.node()}</code></p>
	<p><b>L'adresse du serveur est :</b> <code>{{}}</code></p>
	<p><b>Vous êtes connectés en :</b> <code>{{}}</code></p>
	<p><b>Votre adresse est :</b> <code>{{}}</code></p>
</body>
</html>
'''

# Protocol list
PROTOCOL = { 80 : 'HTTP', 443 : 'HTTPS' }

# Cleanup an IP Address
# If it is an IPv4-mapped to IPv6 address, remove ::ffff:
def CLEANUP_ADDRESS( ip_address ) :
	return re.sub( r'^::ffff:', '', ip_address )

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
		# Get server IP address
		server_external_ip_address = re.search( r'Host: (\[)?(.*)(?(1)\])', self.headers.as_string() ).group( 2 )
		server_ip_address = CLEANUP_ADDRESS( self.connection.getsockname()[0] )
		if server_ip_address != server_external_ip_address :
			server_ip_address = f'{server_external_ip_address} ({server_ip_address})'
		# Get client IP address
		self.client_ip_address = CLEANUP_ADDRESS( self.client_address[0] )
		# Get Web protocol
		self.web_protocol = PROTOCOL[ self.server.server_port ]
		# Redirect if necessary
		if self.path != '/' :
			self.send_response( http.HTTPStatus.MOVED_PERMANENTLY )
			self.send_header( 'Location', '/' )
			self.end_headers()
			return None
		# Send the web page
		self.send_response( http.HTTPStatus.OK )
		self.send_header( 'Content-type', 'text/html' )
		self.end_headers()
		self.wfile.write( bytes( WEBPAGE.format( server_ip_address, self.web_protocol, self.client_ip_address ), 'utf-8' ) )
	# Define the console log messages
	def log_message( self, format, *args ) :
		sys.stderr.write( f'[ {self.log_date_time_string()} ] - Connexion from {self.client_ip_address} - ( {self.web_protocol} )\n' )

# Create the HTTP server
httpd = HTTPServer( ( '::', 80 ), HTTPRequestHandler )

# Create the HTTPS server
httpsd = HTTPServer( ( '::', 443 ), HTTPRequestHandler )
# Wrap the server with TLS
ssl_context = ssl.SSLContext( ssl.PROTOCOL_TLS_SERVER )
ssl_context.load_cert_chain( certfile=CERTFILE.name, keyfile=KEYFILE.name )
httpsd.socket = ssl_context.wrap_socket( httpsd.socket, server_side=True )

# Print banner
print( '\n~~~~~~~~    HTTP(S) Server    ~~~~~~~~~' )
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
