#! /usr/bin/env python3

#
# Multicast Chat Application using Qt
# https://github.com/rtauxerre/Multicast
# Copyright (c) 2023 Michaël Roy
#

# External dependencies
import os
import re
import socket
import sys
from PySide6.QtGui import Qt, QKeySequence, QShortcut
from PySide6.QtNetwork import QHostAddress, QUdpSocket, QNetworkInterface
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QWidget

# Multicast address and port
MULTICAST_ADDRESS4 = '239.0.0.1'
MULTICAST_ADDRESS6 = 'FF02::239:0:0:1'
MULTICAST_PORT = 10000

# Application title
APP_TITLE = 'RT Auxerre Multicast Chat'

# Multicast Chat using Qt
class QMulticastChat( QWidget ) :
	# Initialize the window
	def __init__( self ) :
		# Initialize the class
		QWidget.__init__( self )
		# Set the window title
		self.setWindowTitle( APP_TITLE )
		# Set fixed window size
		self.setFixedWidth( 800 )
		self.setFixedHeight( 600 )
		# Set the Escape key to close the application
		QShortcut( QKeySequence( Qt.Key_Escape ), self ).activated.connect( self.close )
		# Text edit to show the received messages
		self.chat = QTextEdit()
		self.chat.setFocusPolicy( Qt.NoFocus )
		# Line edit to enter the message to send
		self.message = QLineEdit()
		# Signal to know when a new message is entered
		self.message.returnPressed.connect( self.send_message )
		# Application layout
		self.layout = QVBoxLayout( self )
		self.layout.addWidget( QLabel( 'Message received :' ) )
		self.layout.addWidget( self.chat )
		self.layout.addWidget( QLabel( 'Send a message :' ) )
		self.layout.addWidget( self.message )
		# Server connection to receive messages
		self.server4 = QUdpSocket( self )
		self.server4.bind( QHostAddress.AnyIPv4, MULTICAST_PORT )
		self.server4.joinMulticastGroup( QHostAddress( MULTICAST_ADDRESS4 ) )
		self.server4.readyRead.connect( self.receive_message4 )
		self.server6 = QUdpSocket( self )
		self.server6.bind( QHostAddress.AnyIPv6, MULTICAST_PORT )
		self.server6.joinMulticastGroup( QHostAddress( MULTICAST_ADDRESS6 ) )
		self.server6.readyRead.connect( self.receive_message6 )
		# Client connection to send messages
		self.client = QUdpSocket( self )
	# Send a message
	def send_message( self ) :
		# Return if the message is empty
		if not self.message.text() : return
		# Send the message through the network
#		self.client.writeDatagram( self.message.text().encode(), QHostAddress( MULTICAST_ADDRESS4 ), MULTICAST_PORT )
		self.client.writeDatagram( self.message.text().encode(), QHostAddress( MULTICAST_ADDRESS6 ), MULTICAST_PORT )
		# Clear the text input widget
		self.message.clear()
	# Receive the messages
	def receive_message4( self ) :
		# Handle all the pending messages
		while self.server4.hasPendingDatagrams() :
			# Get the message
			message, host, _ = self.server4.readDatagram( self.server4.pendingDatagramSize() )
			# Print the message
			self.chat.append( f'<b>{host.toString()} :</b> {message.data().decode()}' )
	# Receive the messages
	def receive_message6( self ) :
		# Handle all the pending messages
		while self.server6.hasPendingDatagrams() :
			# Get the message
			message, host, _ = self.server6.readDatagram( self.server6.pendingDatagramSize() )
			# Print the message
			self.chat.append( f'<b>{self.address_string(host.toString())} :</b> {message.data().decode()}' )
	# Return the IP converted address (remove the interface name) 
	def address_string( self, address ) :
		return re.sub( r'%.*', '', address )


# Main program
if __name__ == "__main__" :
	# Detect IPv6
	if not socket.has_dualstack_ipv6() :
		print( 'IPv6 not detected. Program terminated !')
		exit()
	# Start the Qt application
	application = QApplication( sys.argv )
	window = QMulticastChat()
	window.show()
	sys.exit( application.exec() )