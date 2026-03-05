#! /usr/bin/env python3

#
# Service reachability test application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
# usage : $ sudo ./test-connexion.py
#

# Dependencies
import argparse
import asyncio
import ipaddress
import os
import socket
import time

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Bash colors (red, green)
COLORS = { False : '\033[41m', True : '\033[42m' }

# Destination IP addresses (coded with the area number)
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'

# Application protocols by port
PROTOCOLS = { 0 : 'ICMP', 21 : 'FTP', 22 : 'SSH', 25 : 'SMTP', 80 : 'HTTP', 443 : 'HTTPS' }

# Timeout parameter
TIMEOUT = 2

# ICMP request packets
ICMP4_PACKET = b'\x08\x00\xf7\xfe\x00\x00\x00\x01'
ICMP6_PACKET = b'\x80\x00\x7f\xfe\x00\x00\x00\x01'

# Ping destination
async def ping ( destination ) :
	# Test ping IPv4
	if ipaddress.ip_address( destination ).version == 4 : return await ping4( destination )
	# Test ping IPv6
	else : return await ping6( destination )

# Ping IPv4 destination
async def ping4 ( destination ) :
	# Create network socket
	with socket.socket( socket.AF_INET, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMP ) as icmp_socket :
		# Connect the socket to the destination
		icmp_socket.connect( ( destination, 0 ) )
		# Send ping request
		await asyncio.get_event_loop().sock_sendall( icmp_socket, ICMP4_PACKET )
		# Catch timeout exception
		try :
			# Wait for reply
			reply = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = TIMEOUT )
			# Check reply
			if reply[ 20:21 ] == b'\x00' : return True
		# Timeout
		except TimeoutError : return False

# Ping IPv6 destination
async def ping6( destination ) :
	# Create network socket
	with socket.socket( socket.AF_INET6, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMPV6 ) as icmp_socket :
		# Connect the socket to the destination
		icmp_socket.connect( ( destination, 0 ) )
		# Send ping request
		await asyncio.get_event_loop().sock_sendall( icmp_socket, ICMP6_PACKET )
		# Catch timeout exception
		try :
			# Wait for reply
			reply = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = TIMEOUT )
			# Check reply
			if reply[ :1 ] == b'\x81' : return True
		# Timeout
		except TimeoutError : return False

# Connect to a TCP service
async def connect( address, port ) :
	# Catch connection exception
	try :
		# Initiate a connection
		await asyncio.wait_for( asyncio.open_connection( host = address, port = port ), timeout = TIMEOUT )
		# Connection done
		return True
	# Connection failed
	except OSError : return False

# Test a host (TCP service or ping)
async def test_host( address, port ) :
	# Test TCP service
	if port : result = await connect( address, port )
	# Test ping IPv4
	else : result = await ping( address )
	# Return test result
	return ( port, result )

# Test one area
async def test_one_area( area_number ) :
	# Modify the destination addresses according to the area number
	ipv4_destination = IPV4_ADDRESS.format( area = area_number )
	ipv6_destination = IPV6_ADDRESS.format( area = area_number )
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Do all the tests for this area
		tasks = [ task_group.create_task( test_host( address, port ) ) for address in [ ipv4_destination, ipv6_destination ] for port in [ *PROTOCOLS.keys() ] ]
	# Return the results of the tasks for this area
	return [ task.result() for task in tasks ]

# Test all areas
async def test_all_areas( area_number ) :
	# Create a task group
	async with asyncio.TaskGroup() as task_group :
		# Test all areas
		tasks = [ task_group.create_task( test_one_area( i + 1 ) ) for i in range( area_number ) ]
	# Return the results of the tasks for each area
	return [ task.result() for task in tasks ]

#
# Main function
#

# Command line parameters
parser = argparse.ArgumentParser( description='Checks the incoming traffic of the different network areas' )
parser.add_argument( '-n', '--number', type=int, default=8,	help='Number of areas (default to 8)' )
parser.add_argument( '-i', '--interval', type=int, default=30, help='Refresh interval (default to 30 seconds)' )
parser.add_argument( '-t', '--timeout', type=int, default=TIMEOUT, help=f'Timeout for the tests (default to {TIMEOUT} seconds)' )
parser.add_argument( '-4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'IPv4 destination address (default to {IPV4_ADDRESS})' )
parser.add_argument( '-6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'IPv6 destination address (default to {IPV6_ADDRESS})' )
args = parser.parse_args()
# Register destination IP addresses
IPV4_ADDRESS = args.destination4
IPV6_ADDRESS = args.destination6
# Register timeout parameter
TIMEOUT = args.timeout
# Loop through the tests
try :
	while True :
		# Run the tests
		print( 'Updating...' )
		tests = asyncio.run( test_all_areas( args.number ) )
		# Clear screen and print results
		print( '\033[H\033[J\nRT Auxerre Lab Networks\n' )
		print( '	        ----------------- IPv4 -----------------    ----------------- IPv6 -----------------\n' )
		for area, results in enumerate( tests ) :
			# Print results for one area
			print( f'    Area {area + 1} :    '
				+ ''.join( f'{COLORS[ test[ 1 ] ]} {PROTOCOLS[ test[ 0 ] ]} \033[0m ' for test in results[ :6 ] )
				+ '   '
				+ ''.join( f'{COLORS[ test[ 1 ] ]} {PROTOCOLS[ test[ 0 ] ]} \033[0m ' for test in results[ 6: ] )
			)
		# Update time
		print( '\nLast updated on', time.strftime( '%X' ) )
		# Wait for next update
		time.sleep( args.interval )
		print( '\033[A\033[K', end='' )
# Ctrl+C to stop the application
except KeyboardInterrupt : print( '\033[A\033[KExited.' )
