#! /usr/bin/env python3

#
# Network Service Monitoring Application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
# usage : $ sudo ./test-connexion-textual.py
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

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

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

# Timeout parameter
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
		elif reply[:1]==b'\x81' : return True
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
async def test_one_area( area_number ) :
	# Modify the destination addresses according to the area number
	ipv4_destination = IPV4_ADDRESS.format( area=area_number )
	ipv6_destination = IPV6_ADDRESS.format( area=area_number )
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Do all the tests for this area
		tasks = [ task_group.create_task( test_host( address, port ) )
			for address in [ ipv4_destination, ipv6_destination ]
			for port in [ *PROTOCOLS.keys() ] ]
	# Return the results of the tasks for this area
	return [ task.result() for task in tasks ]

# Test all areas
async def test_all_areas( area_number ) :
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Test all areas
		tasks = [ task_group.create_task( test_one_area(i+1) ) for i in range(area_number) ]
	# Return the results of the tasks for each area
	return [ task.result() for task in tasks ]

# Richified the test result
def output( test ) :
	if test[1] : return Panel( f'{PROTOCOLS[test[0]]}', style='green', padding=(-1,0) )
	else : return Panel( f'{PROTOCOLS[test[0]]}', style='red dim', padding=(-1,0) )

# Main application
if __name__ == '__main__' :
	# Command line parameters
	parser = argparse.ArgumentParser( description='Checks the incoming traffic of the different network areas' )
	parser.add_argument( '-n', '--number', type=int, default=8,	help='Number of areas (default to 8)' )
	parser.add_argument( '-i', '--interval', type=int, default=30, help='Refresh interval (default to 30 seconds)' )
	parser.add_argument( '-t', '--timeout', type=int, default=TIMEOUT, help=f'Timeout for the tests (default to {TIMEOUT} seconds)' )
	parser.add_argument( '-4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'IPv4 destination address (default to {IPV4_ADDRESS})' )
	parser.add_argument( '-6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'IPv6 destination address (default to {IPV6_ADDRESS})' )
	args = parser.parse_args()
	# Get destination IP addresses
	IPV4_ADDRESS = args.destination4
	IPV6_ADDRESS = args.destination6
	# Get timeout parameter
	TIMEOUT = args.timeout
	# Get the terminal
	console = Console()
	# Catch keyboard interrupt
	try :
		# Start monitoring
		with console.status('') :
			while True :
				# Run the tests
				tests = asyncio.run( test_all_areas(args.number) )
				# Clear the screen
				console.clear()
				# Create the table for result display
				table = Table( title='\n[bold blue]IUT RT Auxerre - Network Lab Monitoring\n', box=box.ROUNDED )
				table.add_column( 'Area', style='blue bold', justify='center' )
				table.add_column( 'IPv4', justify='center' )
				table.add_column( 'IPv6', justify='center' )
				# Add the results to the table
				for area, results in enumerate( tests ) :
					result = [ output( test ) for test in results ]
					table.add_row( Align( f'{area + 1}', align='center', vertical='middle' ),
						Columns( result[:PROTOCOL_NUMBER] ),
						Columns( result[PROTOCOL_NUMBER:] ) )
				# Print the results
				console.print( table )
				# Print update time
				console.print( f'\nLast updated on {time.strftime('%X')}\n' )
				# Wait for the next update
				time.sleep( args.interval )
	# Ctrl+C to stop the application
	except KeyboardInterrupt :
		console.clear()