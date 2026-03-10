#! /usr/bin/env python

#
# Network Lab Monitoring Application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
#

#
# Required external dependency: Rich
#	package : python-rich (Arch) or python3-rich (Ubuntu)
#   or python -m pip install rich
#

# Dependencies
import argparse
import asyncio
import ipaddress
import os
import socket
import time
from rich import box, print
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Number of areas to test
AREA_NUMBER = 8
# Destination IP addresses with the area number
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'
# Update interval time
INTERVAL = 10
# Test timeout
TIMEOUT = 2
# Application protocols by port
PROTOCOLS = {
	0: 'ICMP',
	21: 'FTP',
	22: 'SSH',
	25: 'SMTP',
	53: 'DNS',
	80: 'HTTP',
	443: 'HTTPS'
}
PROTOCOL_NUMBER = int(len(PROTOCOLS.keys()))

# Ping socket parameters
IP_FAMILY = {
	4: socket.AF_INET, # IPv4
	6: socket.AF_INET6 # IPv6
}
IP_PROTO = {
	4: socket.IPPROTO_ICMP, # ICMPv4
	6: socket.IPPROTO_ICMPV6 # ICMPv6
}
ICMP_TYPE = {
	4: slice(20, 21), # ICMPv4 type field
	6: slice(0, 1) # ICMPv6 type field
}
ICMP_ECHO_REQUEST = {
	4: b'\x08\x00\xf7\xfe\x00\x00\x00\x01', # ICMPv4 echo request
	6: b'\x80\x00\x7f\xfe\x00\x00\x00\x01' # ICMPv6 echo request
}
ICMP_ECHO_REPLY = {
	4: b'\x00', # ICMPv4 echo reply
	6: b'\x81' # ICMPv6 echo reply
}
SOCKET_TYPE = socket.SOCK_RAW | socket.SOCK_NONBLOCK # Non blocking raw socket

# Ping a host
async def ping( destination ):
	# Get asyncio event loop
	loop = asyncio.get_event_loop()
	# Get IP version
	ip_version = ipaddress.ip_address( destination ).version
	# Catch errors
	try:
		# Create network socket
		with socket.socket( IP_FAMILY[ip_version], SOCKET_TYPE, IP_PROTO[ip_version] ) as icmp_socket:
			# Connect the socket
			await loop.sock_connect( icmp_socket, (destination, None) )
			# Send ping request
			await loop.sock_sendall( icmp_socket, ICMP_ECHO_REQUEST[ip_version] )
			# Get reply
			reply = await asyncio.wait_for( loop.sock_recv(icmp_socket, 1024), timeout=TIMEOUT )
	# Connection failed
	except OSError: return False
	# Check reply
	else: return True if reply[ICMP_TYPE[ip_version]] == ICMP_ECHO_REPLY[ip_version] else False

# Connect to a TCP service
async def connect( address, port ):
	# Initiate a connection
	try: _, writer = await asyncio.wait_for( asyncio.open_connection(host=address, port=port), timeout=TIMEOUT )
	# Connection failed
	except OSError: return False
	# Connection done
	else: writer.close(); return True

# Test a host (TCP service or ping)
async def test_host( address, port ):
	# Test TCP service
	if port: result = await connect( address, port )
	# Test ping
	else: result = await ping( address )
	# Return test result
	return ( port, result )

# Test one area
async def test_one_area( area ):
	# Modify the destination addresses according to the area number
	ipv4_destination = IPV4_ADDRESS.format( area=area )
	ipv6_destination = IPV6_ADDRESS.format( area=area )
	# Create a task group
	async with asyncio.TaskGroup() as task_group:
		# Do all the tests for this area
		tasks = [ task_group.create_task( test_host( address, port ) )
			for address in [ ipv4_destination, ipv6_destination ]
			for port in [ *PROTOCOLS.keys() ] ]
	# Return the results of the tasks for this area
	return [ task.result() for task in tasks ]

# Test all areas
async def test_all_areas():
	# Create a task group
	async with asyncio.TaskGroup() as task_group:
		# Test all areas
		tasks = [ task_group.create_task( test_one_area(i+1) ) for i in range( AREA_NUMBER ) ]
	# Return the results of the tasks for each area
	return [ task.result() for task in tasks ]

# Richified the test result
def output( test ):
	return Panel( f'{PROTOCOLS[test[0]]}', style=f'{'green' if test[1] else 'red dim'}', padding=(-1,0) )

# Monitoring application
async def main():
	# Get the console and clear it
	console = Console()
	console.clear()
	# Start console status
	with console.status('') as status:
		# Start monitoring
		while True:
			# Update status
			status.update( 'Updating...', spinner='earth' )
			# Run the tests
			tests = await test_all_areas()
			# Create the table for result display
			table = Table( title='\n[bold white]IUT RT Auxerre - Network Lab Monitoring[/bold white]\n', box=box.HORIZONTALS, header_style='bold', style='white', caption=' ' )
			table.add_column( 'Area', style='bold', justify='center', vertical='middle' )
			table.add_column( 'IPv4', justify='center' )
			table.add_column( 'IPv6', justify='center' )
			# Add the results to the table
			for area, results in enumerate( tests ):
				result = [ output(test) for test in results ]
				table.add_row( f'{area + 1}',
					Align( Columns( result[:PROTOCOL_NUMBER] ), align='center' ),
					Align( Columns( result[PROTOCOL_NUMBER:] ), align='center' ) )
			# Clear the screen
			console.clear()
			# Print the results
			console.print( table )
			# Update status
			status.update( f'Last updated on [bold]{time.strftime('%X')}', spinner='clock' )
			# Wait for the next update
			await asyncio.sleep( INTERVAL )

# Main application
if __name__ == '__main__':
	# Command line parameters
	parser = argparse.ArgumentParser( description='Network Lab Monitoring Application', formatter_class=argparse.ArgumentDefaultsHelpFormatter )
	parser.add_argument( '-n', '--number', type=int, default=AREA_NUMBER, help=f'Area number' )
	parser.add_argument( '-i', '--interval', type=int, default=INTERVAL, help=f'Refresh interval' )
	parser.add_argument( '-t', '--timeout', type=int, default=TIMEOUT, help=f'Network test timeout' )
	parser.add_argument( '-4', '--destination4', default=IPV4_ADDRESS, help=f'IPv4 destination address' )
	parser.add_argument( '-6', '--destination6', default=IPV6_ADDRESS, help=f'IPv6 destination address' )
	args = parser.parse_args()
	# Check if root
	if os.geteuid() != 0: print( '\n-> Run this application as root (sudo)...'); exit()
	# Get area number
	AREA_NUMBER = args.number
	# Get destination IP addresses
	IPV4_ADDRESS = args.destination4
	IPV6_ADDRESS = args.destination6
	# Get update interval parameter
	INTERVAL = args.interval
	# Get timeout parameter
	TIMEOUT = args.timeout
	# Run the monitoring application
	try: asyncio.run( main() )
	# Ctrl+C to stop the application
	except KeyboardInterrupt: Console().clear()