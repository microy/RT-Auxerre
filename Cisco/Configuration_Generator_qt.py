#! /usr/bin/env python3

#
# Script pour générer les configurations des materiels des TP réseaux
#

# Modules externes
from PySide6.QtCore import QFileInfo
from PySide6.QtGui import Qt, QKeySequence, QShortcut, QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QVBoxLayout, QWidget
import string
import sys

# 
class QConfigurationTemplate( QWidget ) :
	# Initialize the window
	def __init__( self ) :
		# Initialize the class
		QWidget.__init__( self )
		# Set the window title
		self.setWindowTitle( 'Configuration TP Réseaux' )
		# Set fixed window size
		self.resize( 800, 600 )
		# Set the Escape key to close the application
		QShortcut( QKeySequence( Qt.Key_Escape ), self ).activated.connect( self.close )
		# Template file
		self.template_filename = ''
		select_template = QPushButton( ' Select Template ' )
		select_template.clicked.connect( self.Browse )
		# Line edit to edit the area number
		self.zone = QLineEdit()
		self.zone.setMaxLength( 3 )
		self.zone.setFixedWidth( 50 )
		self.zone.setText( '1' )
		# Signal to know when a new zone is entered
		self.zone.returnPressed.connect( self.DisplayTemplate )
		# Text edit to show the configuration
		self.configuration = QTextEdit()
		self.configuration.setFocusPolicy( Qt.NoFocus )
		self.configuration.setFont( QFont('Liberation Mono', 12) )
		# Upper layout
		hlayout = QHBoxLayout()
		hlayout.addWidget( select_template )
		hlayout.addStretch()
		hlayout.addWidget( QLabel( ' Area : ' ) )
		hlayout.addWidget( self.zone )
		# Application layout
		vlayout = QVBoxLayout( self )
		vlayout.addLayout( hlayout )
		vlayout.addWidget( self.configuration )
	def Browse( self ) :
		self.template_filename = QFileDialog.getOpenFileName( self, 'Select Template' )[0]
		if self.template_filename :
			self.setWindowTitle( QFileInfo( self.template_filename ).fileName() )
			# Lit le fichier template
			with open( self.template_filename, 'r' ) as fichier :
				self.template = fichier.read()
			self.DisplayTemplate()
	def DisplayTemplate( self ) :
		if self.template_filename :
			# Change le numéro de zone
			self.configuration.setText( string.Template( self.template ).substitute( zone = self.zone.text() ) )

# Main program
if __name__ == "__main__" :
	# Start the Qt application
	application = QApplication( sys.argv )
	window = QConfigurationTemplate()
	window.show()
	sys.exit( application.exec() )
