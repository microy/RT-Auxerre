#! /usr/bin/env python3

#
# Multicast Chat Application using Textual
# https://github.com/microy/RT-Auxerre
# Copyright (c) 2024 Michaël Roy
#

# External dependencies
import asyncio, base64, re, socket
from textual.app import App
from textual.widgets import Footer, Input, RichLog, Static

# Multicast addresses and port
MULTICAST_ADDRESS4 = '239.0.0.1'
MULTICAST_ADDRESS6 = 'FF02::239:0:0:1'
MULTICAST_PORT = 10000

# Chat server protocol
class ChatProtocol :
	# Initialisation
	def __init__( self, message_callback ) :
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

# Multicast Chat using Textual
class TMulticastChat( App ) :
	# Auto focus
	AUTO_FOCUS = '#input'
	# Keyboard bindings
	BINDINGS = [
		( 'escape', 'quit', 'Quit' ),
		( 'f1', 'enable_ipv4', 'Enable IPv4' ),
		( 'f2', 'enable_ipv6', 'Enable IPv6' ),
		( 'f3', 'enable_secret', 'Toggle secret' ),
	]
	# Application style sheet
	CSS = '''
		#footer, #header, .border {
			background: #212223;
			background-tint: #212223;
			color: white;
		}
		#header {
			content-align: center middle;
			height: 3;
			text-style: bold;
		}
		#messages {
			height: 1fr;
			padding: 1 2 1 2;
		}
		#input {
			height: 5;
			padding: 1 2 1 2;
		}
		.border {
			border: round white;
			border-title-style: bold;
		}
	'''
	# Compose the interface
	def compose( self ) :
		yield Static( 'RT Auxerre Multicast Chat', id='header' )
		yield RichLog( markup=True, wrap=True, classes="border", id='messages' )
		yield Input( classes="border", id='input' )
		yield Footer( show_command_palette=False, id='footer' )
	# Initialize the application
	async def on_mount( self ) :
		# Setup the interface
		self.use_command_palette = False
		self.query_one( '#messages' ).border_title = 'Message received'
		self.query_one( '#messages' ).can_focus = False
		self.query_one( '#input' ).border_title='Send a message'
		# Setup message options
		self.ipv4_enabled = True
		self.secret_enabled = False
		self.query_one( '#messages' ).write( '[bold cyan]Sending messages via IPv4\nSecret disabled[/bold cyan]' )
		# Run the server
		await asyncio.get_running_loop().create_datagram_endpoint(
			lambda : ChatProtocol( self.ReceiveMessage ), local_addr = ( '::', MULTICAST_PORT ) )
		# Create the client
		self.client = socket.socket( socket.AF_INET6, socket.SOCK_DGRAM )
	# Enable IPv4
	def action_enable_ipv4( self ) :
		self.ipv4_enabled = True
		self.query_one( '#messages' ).write( '[bold cyan]Sending messages via IPv4[/bold cyan]' )
	# Enable IPv6
	def action_enable_ipv6( self ) :
		self.ipv4_enabled = False
		self.query_one( '#messages' ).write( '[bold cyan]Sending messages via IPv6[/bold cyan]' )
	# Enable secret message
	def action_enable_secret( self ) :
		self.secret_enabled = not self.secret_enabled
		self.query_one( '#messages' ).write( f'[bold cyan]Secret {'enabled' if self.secret_enabled else 'disabled'}[/bold cyan]' )
	# Input submitted
	def on_input_submitted( self ) :
		# Return if input is empty
		if not self.query_one( '#input' ).value : return
		# Get the message
		message = self.query_one( '#input' ).value.encode()
		# Encode the message if secret
		if self.secret_enabled : message = base64.b64encode( message )
		# Send the message
		if self.ipv4_enabled : self.client.sendto( message, ( f'::ffff:{MULTICAST_ADDRESS4}', MULTICAST_PORT ) )
		else : self.client.sendto( message, ( MULTICAST_ADDRESS6, MULTICAST_PORT ) )
		# Clear input
		self.query_one( '#input' ).clear()
	# Receive a message
	def ReceiveMessage( self, message, address ) :
		# Decode the message
		if self.secret_enabled : message = base64.b64decode( message )
		message = message.decode()
		# Append the message to the chat history
		self.query_one( '#messages' ).write( f'[b]{address} >[/b] {message}' )

# Main application
if __name__ == "__main__" :
	app = TMulticastChat()
	app.run()