#! /usr/bin/env python3

#
# Script pour configurer un poste en salle TP réseaux
#

# Modules externes
from PySide6.QtCore import QFileInfo
from PySide6.QtGui import Qt, QKeySequence, QShortcut, QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QVBoxLayout, QWidget
import ipaddress
import string
import subprocess
import sys
import os



# Widget to configure the network
class QNetworkConfiguration( QWidget ) :
	# Initialize the window
	def __init__( self ) :
		# Initialize the class
		QWidget.__init__( self )
		# Set the window title
		self.setWindowTitle( 'Configuration TP Réseaux' )
		# Set fixed window size
		self.setFixedSize( 400, 200 )
		# Set the Escape key to close the application
		QShortcut( QKeySequence( Qt.Key_Escape ), self ).activated.connect( self.close )
		# Line edit to edit the area number
		self.adresse_ipv4 = QLineEdit()
		self.gateway_ipv4 = QLineEdit()
		self.dns_ipv4 = QLineEdit()
		self.adresse_ipv6 = QLineEdit()
		self.gateway_ipv6 = QLineEdit()
		self.dns_ipv6 = QLineEdit()
		# Signal to know when a new zone is entered
		self.adresse_ipv4.returnPressed.connect( self.UpdateConfiguration )
		self.gateway_ipv4.returnPressed.connect( self.UpdateConfiguration )
		self.dns_ipv4.returnPressed.connect( self.UpdateConfiguration )
		self.adresse_ipv6.returnPressed.connect( self.UpdateConfiguration )
		self.gateway_ipv6.returnPressed.connect( self.UpdateConfiguration )
		self.dns_ipv6.returnPressed.connect( self.UpdateConfiguration )
		# Layout
		layout = QFormLayout( self )
		layout.addRow( QLabel( 'Adresse IPv4' ), self.adresse_ipv4 )
		layout.addRow( QLabel( 'Passerelle IPv4' ), self.gateway_ipv4 )
		layout.addRow( QLabel( 'DNS IPv4' ), self.dns_ipv4 )
		layout.addRow( QLabel( 'Adresse IPv6' ), self.adresse_ipv6 )
		layout.addRow( QLabel( 'Passerelle IPv6' ), self.gateway_ipv6 )
		layout.addRow( QLabel( 'DNS IPv6' ), self.dns_ipv6 )

	def UpdateConfiguration( self ) :
		# Checks
		if not self.adresse_ipv4.text() or not self.gateway_ipv4.text() or not self.dns_ipv4.text() or not self.adresse_ipv6.text() or not self.gateway_ipv6.text() or not self.dns_ipv6.text() :
			print( 'pouet' )
			return
	#	os.system( 'nmcli connection down eno1' )
	#	os.system( 'nmcli connection down enp2s0' )
	#	os.system( 'nmcli connection modify enp2s0 ipv4.method manual ipv4.addresses $adresse_ipv4 ipv4.gateway $gateway_ipv4 ipv4.dns $dns_ipv4' )
	#	os.system( 'nmcli connection modify enp2s0 ipv6.method manual ipv6.addresses $adresse_ipv6 ipv6.gateway $gateway_ipv6 ipv6.dns $dns_ipv6' )
	#	os.system( 'nmcli connection up enp2s0' )
		ipaddress.ip_address( self.adresse_ipv4.text() )
		ipaddress.ipv4_network( self.adresse_ipv4.text() )
		print('nmcli connection modify enp2s0 ipv4.method manual ipv4.addresses', self.adresse_ipv4.text(), 'ipv4.gateway',self.gateway_ipv4.text(), 'ipv4.dns', self.dns_ipv4.text() )

# Main program
if __name__ == "__main__" :
	# Start the Qt application
	application = QApplication( sys.argv )
	window = QNetworkConfiguration()
	window.show()
	sys.exit( application.exec() )
