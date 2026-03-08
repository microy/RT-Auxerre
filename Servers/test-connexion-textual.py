#! /usr/bin/env python3

#
# Network Service Monitoring Application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
#

# Dependencies
import argparse
import asyncio
import ipaddress
import os
import socket
import time
from rich import box
from rich import print
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from textual.app import App
from textual.widgets import DataTable, Header, Footer, Static

# Number of areas to test
AREA_NUMBER = 8

# Destination IP addresses with the area number
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'

# Application protocols by port
PROTOCOLS = {
	0 : 'ICMP',
	21 : 'FTP',
	22 : 'SSH',
	25 : 'SMTP',
	53 : 'DNS',
	80 : 'HTTP',
	443 : 'HTTPS'
}
PROTOCOL_NUMBER = int(len(PROTOCOLS.keys()))

# Update interval time
INTERVAL = 10

# Test timeout
TIMEOUT = 2

# Socket parameters
IP_FAMILY = {
	4 : socket.AF_INET, # IPv4
	6 : socket.AF_INET6 # IPv6
}
IP_PROTO = {
	4 : socket.IPPROTO_ICMP, # ICMPv4
	6 : socket.IPPROTO_ICMPV6 # ICMPv6
}
IP_TYPE = socket.SOCK_RAW | socket.SOCK_NONBLOCK # Non blocking raw socket

# ICMP request packets
ICMP_PACKET = {
	4 : b'\x08\x00\xf7\xfe\x00\x00\x00\x01', # ICMPv4
	6 : b'\x80\x00\x7f\xfe\x00\x00\x00\x01' # ICMPv6
}

# Ping a host
async def ping( destination ) :
	# Get event loop
	loop = asyncio.get_event_loop()
	# Get IP version
	ip_version = ipaddress.ip_address( destination ).version
	# Create network socket
	with socket.socket( IP_FAMILY[ip_version], IP_TYPE, IP_PROTO[ip_version] ) as icmp_socket :
		# Connect the socket
		icmp_socket.connect( (destination, 0) )
		# Send ping request
		await loop.sock_sendall( icmp_socket, ICMP_PACKET[ip_version] )
		# Wait for reply
		try : reply = await asyncio.wait_for( loop.sock_recv(icmp_socket, 1024), timeout=TIMEOUT )
		# Timeout
		except TimeoutError : return False
		# Check reply
		if ip_version==4 and reply[20:21]==b'\x00' : return True
		elif ip_version==6 and reply[:1]==b'\x81' : return True
		else : return False

# Connect to a TCP service
async def connect( address, port ) :
	# Initiate a connection
	try : _, writer = await asyncio.wait_for( asyncio.open_connection(host=address, port=port), timeout=TIMEOUT )
	# Connection failed
	except OSError : return False
	# Connection done
	else : writer.close(); return True

# Test a host (TCP service or ping)
async def test_host( address, port ) :
	# Test TCP service
	if port : result = await connect( address, port )
	# Test ping
	else : result = await ping( address )
	# Return test result
	return ( port, result )

# Test one area
async def test_one_area( area ) :
	# Modify the destination addresses according to the area number
	ipv4_destination = IPV4_ADDRESS.format( area=area )
	ipv6_destination = IPV6_ADDRESS.format( area=area )
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Do all the tests for this area
		tasks = [ task_group.create_task( test_host( address, port ) )
			for address in [ ipv4_destination, ipv6_destination ]
			for port in [ *PROTOCOLS.keys() ] ]
	# Return the results of the tasks for this area
	return [ task.result() for task in tasks ]

# Test all areas
async def test_all_areas() :
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Test all areas
		tasks = [ task_group.create_task( test_one_area(i+1) ) for i in range( AREA_NUMBER ) ]
	# Return the results of the tasks for each area
	return [ task.result() for task in tasks ]

# Richified the test result
def output( test ) :
	if test[1] : return Panel( f'{PROTOCOLS[test[0]]}', style='green', padding=(-1,0) )
	else : return Panel( f'{PROTOCOLS[test[0]]}', style='red dim', padding=(-1,0) )

# Monitoring Application
class MonitoringApp( App ) :
	# Keyboard bindings
	BINDINGS = [
		( 'escape', 'quit', 'Quit' ),
	]
	# Application style sheet
	CSS = '''
		#header {
			content-align: center middle;
			height: 3;
			text-style: bold;
		}
		#footer2 {
			content-align: center middle;
			height: 3;
			text-style: bold;
		}
	'''
	# Disable command palette
	ENABLE_COMMAND_PALETTE = False
	# Compose the interface
	def compose( self ) :
		yield Static( 'IUT RT Auxerre - Network Lab Monitoring', id='header' )
		yield DataTable( id='table' )
		yield Static( id='result' )
		yield Static( id='footer2' )
		yield Footer( id='footer' )
	# Initialize the application
	async def on_mount( self ) :
		self.title = 'IUT RT Auxerre - Network Lab Monitoring'
		# Setup the interface
		table = self.query_one( '#table' )
		table.cursor_type = None
		# Run the tests
		self.run_worker( self.update_results(), exclusive=True )
	# Update the test results
	async def update_results( self ) :
		while True :
			self.query_one( '#footer2' ).update( 'Updating...' )
			# Run the tests
			self.tests = await test_all_areas()
			# Record last update time
			self.display_results()
			# Record last update time
			self.query_one( '#footer2' ).update( f'Last updated on [bold cyan]{time.strftime('%X')}' )
			# Wait for the next update
			await asyncio.sleep( INTERVAL )
	def display_results( self ) :
#		self.display_results1()
		self.display_results2()
	def display_results1( self ) :
		# Clear the table
		table = self.query_one( '#table' )
		table.clear(columns=True)
		table.add_column( 'Area', width=6 )
		table.add_column( 'IPv4', width=None )
		table.add_column( 'Ipv6', width=None )
		# Add the results to the table
		for area, results in enumerate( self.tests ) :
			result = [ output( test ) for test in results ]
			table.add_row( Align( f'{area + 1}', align='center', vertical='middle' ),
				Columns( result[:PROTOCOL_NUMBER] ),
				Columns( result[PROTOCOL_NUMBER:] ) )
	# Update the test results
	def display_results2( self ) :
		table = Table( box=box.ROUNDED, header_style='bold white', style='white' )
		table.add_column( 'Area', style='bold white', justify='center' )
		table.add_column( 'IPv4', justify='center' )
		table.add_column( 'IPv6', justify='center' )
		# Add the results to the table
		for area, results in enumerate( self.tests ) :
			result = [ output( test ) for test in results ]
			table.add_row( Align( f'{area + 1}', align='center', vertical='middle' ),
				Columns( result[:PROTOCOL_NUMBER] ),
				Columns( result[PROTOCOL_NUMBER:] ) )
		self.query_one( '#result' ).update( table )

# Main application
if __name__ == "__main__" :
	# Command line parameters
	parser = argparse.ArgumentParser( description='Monitor network lab services' )
	parser.add_argument( '-n', '--number', type=int, default=AREA_NUMBER, help=f'Area number (default to {AREA_NUMBER})' )
	parser.add_argument( '-i', '--interval', type=int, default=INTERVAL, help=f'Refresh interval (default to {INTERVAL} seconds)' )
	parser.add_argument( '-t', '--timeout', type=int, default=TIMEOUT, help=f'Network test timeout (default to {TIMEOUT} seconds)' )
	parser.add_argument( '-4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'IPv4 destination address (default to {IPV4_ADDRESS})' )
	parser.add_argument( '-6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'IPv6 destination address (default to {IPV6_ADDRESS})' )
	args = parser.parse_args()
	# Check if root
	if os.geteuid() != 0 : print( '\n-> Run this application as root (sudo)...'); exit()
	# Get area number
	AREA_NUMBER = args.number
	# Get destination IP addresses
	IPV4_ADDRESS = args.destination4
	IPV6_ADDRESS = args.destination6
	# Get update interval parameter
	INTERVAL = args.interval
	# Get timeout parameter
	TIMEOUT = args.timeout
	# Start the application
	app = MonitoringApp()
	app.run()