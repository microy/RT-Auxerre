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

# Bash colors
COLORS = {
	False : '\033[41m', # RED
	True : '\033[42m'   # GREEN
}

# Destination IP addresses
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'

# Application protocols by port
PROTOCOLS = {
	0 : 'ICMP',
	21 : 'FTP',
	22 : 'SSH',
	25 : 'SMTP',
	80 : 'HTTP',
	443 : 'HTTPS'
}

# ICMP request packets
ICMP4_PACKET = b'\x08\x00\xf7\xfe\x00\x00\x00\x01'
ICMP6_PACKET = b'\x80\x00\x7f\xfe\x00\x00\x00\x01'

# Timeout parameter
TIMEOUT = 2

# Test function
async def test( address, port ) :
	# Handle exceptions
	try :
		# Test TCP service
		if port :
			# Initiate a connection
			await asyncio.wait_for( asyncio.open_connection( host = address, port = port ), timeout = TIMEOUT )
			# Connection done
			return ( port, True )
		# Test IPv4 ping
		elif ipaddress.ip_address( address ).version == 4 :
			# Create network socket
			with socket.socket( socket.AF_INET, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMP ) as icmp_socket :
				# Send ping request
				await asyncio.get_event_loop().sock_sendto( icmp_socket, ICMP4_PACKET, ( address, 0 ) )
				# Wait for anwser
				async with asyncio.timeout( TIMEOUT ) :
					while True :
						# Get ping reply
						answer, remote_address = await asyncio.get_event_loop().sock_recvfrom( icmp_socket, 1024 )
						# Check reply
						if remote_address[ 0 ] == address and answer[ 20:21 ] == b'\x00' : return ( port, True )
		# Test IPv6 ping
		else :
			# Create network socket
			with socket.socket( socket.AF_INET6, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMPV6 ) as icmp_socket :
				# Send ping request
				await asyncio.get_event_loop().sock_sendto( icmp_socket, ICMP6_PACKET, ( address, 0 ) )
				# Wait for anwser
				async with asyncio.timeout( TIMEOUT ) :
					while True :
						# Get ping reply
						answer, remote_address = await asyncio.get_event_loop().sock_recvfrom( icmp_socket, 1024 )
						# Check reply
						if remote_address[ 0 ] == address and answer[ :1 ] == b'\x81' : return ( port, True )
	# Exception
	except Exception as error : print( error )
	# Failed test
	return ( port, False )

# Test one area
async def test_one_area( area_number ) :
	ipv4_destination = IPV4_ADDRESS.format( area = area_number )
	ipv6_destination = IPV6_ADDRESS.format( area = area_number )
	async with asyncio.TaskGroup() as task_group :
		tasks = [ task_group.create_task( test( ip, port ) ) for ip in [ ipv4_destination, ipv6_destination ] for port in [ *PROTOCOLS.keys() ] ]
	return [ task.result() for task in tasks ]

# Test all areas
async def test_all_areas( area_number ) :
	async with asyncio.TaskGroup() as task_group :
		tasks = [ task_group.create_task( test_one_area( i + 1 ) ) for i in range( area_number ) ]
	return [ task.result() for task in tasks ]

# Main
parser = argparse.ArgumentParser( description='Checks the incoming traffic of the different network areas' )
parser.add_argument( '-n', '--number', type=int, default=8,	help='Number of areas (default to 8)' )
parser.add_argument( '-i', '--interval', type=int, default=30, help='Refresh interval (default to 30 seconds)' )
parser.add_argument( '-4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'IPv4 destination address (default to {IPV4_ADDRESS})' )
parser.add_argument( '-6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'IPv6 destination address (default to {IPV6_ADDRESS})' )
args = parser.parse_args()
IPV4_ADDRESS = args.destination4
IPV6_ADDRESS = args.destination6
try :
	while True :
		print( 'Updating...' )
		tests = asyncio.run( test_all_areas( args.number ) )
		print( '\033[H\033[J\nRT Auxerre Lab Networks\n' )
		print( '	        ----------------- IPv4 -----------------    ----------------- IPv6 -----------------\n' )
		for area, results in enumerate( tests ) :
			print( f'    Area {area + 1} :    ' + ''.join( f'{COLORS[ test[1] ]} {PROTOCOLS[ test[0] ]} \033[0m ' for test in results[ :6 ] ) + '   ' + ''.join( f'{COLORS[ test[1] ]} {PROTOCOLS[ test[0] ]} \033[0m ' for test in results[ 6: ] ) )
		print( '\nLast updated on', time.strftime( '%X' ) )
		time.sleep( args.interval )
		print( '\033[A\033[K', end='' )
except KeyboardInterrupt :
	print( '\033[A\033[KExited.' )
