#! /usr/bin/env python3

#
# Multicast Chat Application using Qt
# https://github.com/microy/RT-Auxerre
# Copyright (c) 2024 Michaël Roy
#

# External dependencies
import asyncio, base64, re, socket, sys
from threading import Thread
from PySide6.QtGui import Qt, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QTextEdit, QVBoxLayout, QWidget

# Multicast addresses and port
MULTICAST_ADDRESS4 = '239.0.0.1'
MULTICAST_ADDRESS6 = 'FF02::239:0:0:1'
MULTICAST_PORT = 10000

# Chat server protocol
class ChatProtocol :
	# Initialisation
	def __init__( self, message_callback = None ) :
		# Register the message callback from the application
		self.message_callback = message_callback
	# Socket initialisation
	def connection_made( self, transport ) :
		# Register the IPv4 multicast group
		transport.get_extra_info('socket').setsockopt( socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
			socket.inet_aton( MULTICAST_ADDRESS4 ) + socket.inet_aton( '0.0.0.0' ) )
		# Register the IPv6 multicast group
		transport.get_extra_info('socket').setsockopt( socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP,
			socket.inet_pton( socket.AF_INET6, MULTICAST_ADDRESS6 ) + socket.inet_pton( socket.AF_INET6, '::' ) )
	# Message reception
	def datagram_received( self, message, address ) :
		# Cleanup the address
		address = re.sub( r'^::ffff:', '', address[0] )
		# Send the message to the application
		self.message_callback( message, address )

# Multicast Chat using Qt
class QMulticastChat( QWidget ) :
	# Initialize the window
	def __init__( self ) :
		# Initialize the class
		QWidget.__init__( self )
		# Set the window title
		self.setWindowTitle( 'RT Auxerre Multicast Chat' )
		# Set fixed window size
		self.setFixedWidth( 800 )
		self.setFixedHeight( 600 )
		# Set the Escape key to close the application
		QShortcut( QKeySequence( Qt.Key_Escape ), self ).activated.connect( self.close )
		# Text edit to show the received messages
		self.chat = QTextEdit()
		self.chat.setFocusPolicy( Qt.NoFocus )
		# Application vertical layout
		self.layout = QVBoxLayout( self )
		# Text box for the message received
		self.layout.addWidget( QLabel( 'Message received :' ) )
		self.layout.addWidget( self.chat )
		# Input + options
		protocols = QHBoxLayout()
		protocols.addWidget( QLabel( 'Send a message :' ) )
		protocols.addStretch()
		self.button_ipv4 = QRadioButton("IPv4")
		self.button_ipv4.setChecked( True )
		protocols.addWidget( self.button_ipv4 )
		protocols.addWidget( QRadioButton("IPv6") )
		protocols.addStretch()
		self.secret = QCheckBox( 'Secret' )
		protocols.addWidget( self.secret )
		self.layout.addLayout( protocols )
		# Line edit to enter the message to send
		self.message = QLineEdit()
		self.message.returnPressed.connect( self.SendMessage )
		self.layout.addWidget( self.message )
		self.message.setFocus()
		# Client connection to send messages
		self.client = socket.socket( socket.AF_INET6, socket.SOCK_DGRAM )
		# Run asyncio loop in another thread
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop( loop )
		Thread( target = loop.run_forever, daemon = True ).start()
		# Run server in asyncio loop
		asyncio.run_coroutine_threadsafe( self.RunServer(), loop = loop )
	# Run server
	async def RunServer( self ) :
		await asyncio.get_running_loop().create_datagram_endpoint(
			lambda : ChatProtocol( self.ReceiveMessage ), local_addr = ( '::', MULTICAST_PORT ) )
	# Send a message
	def SendMessage( self ) :
		# Return if the message is empty
		if not self.message.text() : return
		# Get the input message
		message = self.message.text().encode()
		# Encode the message if secret
		if self.secret.isChecked() : message = base64.b64encode( message )
		# Send the message through the IPv4 or IPv6 network
		if self.button_ipv4.isChecked() : self.client.sendto( message, ( f'::ffff:{MULTICAST_ADDRESS4}', MULTICAST_PORT ) )
		else : self.client.sendto( message, ( MULTICAST_ADDRESS6, MULTICAST_PORT ) )
		# Clear the text input widget
		self.message.clear()
	# Receive a message
	def ReceiveMessage( self, message, address ) :
		# Decode the message
		if self.secret.isChecked() : message = base64.b64decode( message ).decode()
		else : message = message.decode()
		# Append the message to the chat history
		self.chat.append( f'<b>{address} ></b> {message}' )

# Main program
if __name__ == "__main__" :
	application = QApplication( sys.argv )
	window = QMulticastChat()
	window.show()
	sys.exit( application.exec() )