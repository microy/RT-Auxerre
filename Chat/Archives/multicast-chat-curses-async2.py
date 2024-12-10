#! /usr/bin/env python3

# External dependencies
import asyncio, curses, re, socket

# Multicast addresses and port
MULTICAST_ADDRESS4 = '239.0.0.1'
MULTICAST_ADDRESS6 = 'FF02::239:0:0:1'
MULTICAST_PORT = 10000

# Chat server protocol
class ChatProtocol :
	# Initialisation
	def __init__( self, message_callback ) :
		# Register the new message callback from the GUI
		self.message_callback = message_callback
	# Connection
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

# Main application
class ChatApp :
	# Determine the terminal size, and the size of each window
	def __init__( self ) :
		# Initialize curses
		self.screen = curses.initscr()
		curses.cbreak()
		self.screen.keypad( 1 )
		# Received messages
		self.messages = []
		# Setup the screen interface
		self.SetupInterface()
		# Start the main loop
		try : asyncio.run( self.run() )
		except : pass
		finally :
			# Stop curses
			curses.nocbreak()
			self.screen.keypad(0)
			self.screen = None
			curses.endwin()
	# Start the main loop
	async def run( self ) :
		# Run server in asyncio loop
		loop = asyncio.get_running_loop()
		await loop.create_datagram_endpoint( lambda : ChatProtocol(self.ReceiveMessage), local_addr = ( '::', MULTICAST_PORT ) )
		# Create the client
		self.client = socket.socket( socket.AF_INET6, socket.SOCK_DGRAM )
		# Run the input main loop
		while True:
			asyncio.run_coroutine_threadsafe( self.InputMessage(), loop = loop )
			# Wait a moment (curses issue)
			await asyncio.sleep(0.1)
	# Setup the console interface
	def SetupInterface( self ) :
		# Application title
		APP_TITLE = 'RT Auxerre Multicast Chat'
		# Get terminal size
		screen_height, screen_width = self.screen.getmaxyx()
		# Define the height of each window
		title_height = 3
		prompt_height = 5
		history_height = screen_height - title_height - prompt_height - 2
		# Title window
		self.title = curses.newwin( title_height, screen_width - 2, 0, 1 )
		self.title.addstr( 1, int( ( screen_width - len( APP_TITLE ) ) / 2 ), APP_TITLE, curses.A_BOLD )
		self.title.refresh()
		# History window
		self.history = curses.newwin( history_height, screen_width - 2, title_height, 1 )
		# Save the number of visible rows (history window height - border - padding ) 
		self.history_visible_rows = history_height - 2 - 2
		self.history.border( 0 )
		self.history.addstr( 0, 2, ' Message received ', curses.A_BOLD )
		self.history.refresh()
		# Prompt window
		self.prompt = curses.newwin( prompt_height, screen_width - 2, screen_height - prompt_height - 1, 1 )
		self.prompt.border( 0 )
		self.prompt.addstr( 0, 2, ' Send a message ', curses.A_BOLD )
		self.prompt.addstr( 2, 2, ' > ', curses.A_BOLD )
		self.prompt.refresh()
	async def InputMessage( self ) :
		message = self.prompt.getstr()
		if message == curses.KEY_F1 :
			message = 'F1'
		if message :
			self.client.sendto( message, ( f'::ffff:{MULTICAST_ADDRESS4}', MULTICAST_PORT ) )
#		self.client.sendto( message, ( MULTICAST_ADDRESS6, MULTICAST_PORT ) )
		# Refresh the prompt
		self.prompt.clear()
		self.prompt.border( 0 )
		self.prompt.addstr( 0, 2, ' Send a message ', curses.A_BOLD )
		self.prompt.addstr( 2, 2, ' > ', curses.A_BOLD )
		self.prompt.refresh()
	# Append a message to the chat history
	def ReceiveMessage( self, message, address ) :
		self.messages.append( ( message, address ) )
		# Draw the last N messages, where N is the number of visible rows
		row = 2
		for message, address in self.messages[ -self.history_visible_rows : ] :
			self.history.move( row, 3 )
			self.history.clrtoeol()
			self.history.addstr( f'{address} > ', curses.A_BOLD )
			self.history.addstr( message )
			row += 1
		self.history.refresh()
		self.prompt.refresh()
	
# Main application
if __name__ == '__main__' :
	# Run the app
	app = ChatApp()
