#! /usr/bin/env python3

#
# Network Service Monitoring Application
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

# Format the test result for display
def output( test ) :
	if test[1] : return f'\033[42m {PROTOCOLS[test[0]]} \033[0m'
	else : return f'\033[41m {PROTOCOLS[test[0]]} \033[0m'

# Monitoring application
async def main() :
	# Start monitoring
	while True :
		# Run the tests
		print( '\nUpdating...\n' )
		tests = await test_all_areas()
		# Clear screen and print results
		print( '\033[H\033[J\nIUT RT Auxerre - Network Lab Monitoring\n' )
		print( '	        -------------------- IPv4 --------------------    -------------------- IPv6 --------------------\n' )
		for area, results in enumerate( tests ) :
			# Print results for one area
			print( f'    Area {area + 1} :    '
				+ ' '.join( output(test) for test in results[:PROTOCOL_NUMBER] )
				+ '    '
				+ ' '.join( output(test) for test in results[PROTOCOL_NUMBER:] )
			)
		# Update time
		print( f'\nLast updated on {time.strftime('%X')}' )
		# Wait for next update
		await asyncio.sleep( INTERVAL )

# Main application
if __name__ == '__main__' :
	# Command line parameters
	parser = argparse.ArgumentParser( description='Monitor lab network services' )
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
	# Run the monitoring application
	try : asyncio.run( main() )
	# Ctrl+C to stop the application
	except KeyboardInterrupt : print( '\n' )