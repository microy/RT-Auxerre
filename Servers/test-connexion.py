#! /usr/bin/env python3

#
# Service reachability test application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
# usage : $ sudo ./test-connexion.py
#

#
# Reference :
#   Valentin BELYN (https://github.com/ValentinBELYN)
#

# Dependencies
import asyncio, os, socket
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from time import sleep

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Destination IP addresses
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'

# Bash colors
COLORS = {
	False : '\033[41m', # RED
	True : '\033[42m'   # GREEN
}

# ICMP request packets
ICMP4_PACKET = b'\x08\x00\xf7\xfe\x00\x00\x00\x01'
ICMP6_PACKET = b'\x80\x00\x7f\xfe\x00\x00\x00\x01'

# Result data class
@dataclass
class Results :
	number : int
	is_ipv4_host_reachable : bool = False
	is_ipv6_host_reachable : bool = False
	is_ipv4_http_reachable : bool = False
	is_ipv6_http_reachable : bool = False
	is_ipv4_https_reachable : bool = False
	is_ipv6_https_reachable : bool = False

# Service reachability test funtion
async def service_is_reachable( ip_address, port ) :
	try :
		_, writer = await asyncio.wait_for( asyncio.open_connection( host = ip_address, port = port ), timeout = 2 )
		return True
	except : pass
	return False

# Ping IPv4
async def ping4( destination_address ) :
	try :
		icmp_socket = socket.socket( socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP )
		icmp_socket.setblocking( False )
		icmp_socket.sendto( ICMP4_PACKET, ( destination_address, 0 ) )
		response = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = 2 )
		if response[20:21] == b'\x00' : return True
	except : pass
	return False

# Ping IPv6
async def ping6( destination_address ) :
	try :
		icmp_socket = socket.socket( socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6 )
		icmp_socket.setblocking( False )
		icmp_socket.sendto( ICMP6_PACKET, ( destination_address, 0 ) )
		response = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = 2 )
		if response[:1] == b'\x81' : return True
	except : pass
	return False

# Test one area
async def test_area( area ) :
	ipv4_destination = IPV4_ADDRESS.format( area = area )
	ipv6_destination = IPV6_ADDRESS.format( area = area )
	return Results(
		number = area,
		is_ipv4_host_reachable = await ping4( ipv4_destination ),
		is_ipv6_host_reachable = await ping6( ipv6_destination ),
		is_ipv4_http_reachable = await service_is_reachable( ipv4_destination, 80 ),
		is_ipv6_http_reachable = await service_is_reachable( ipv6_destination, 80 ),
		is_ipv4_https_reachable = await service_is_reachable( ipv4_destination, 443 ),
		is_ipv6_https_reachable = await service_is_reachable( ipv6_destination, 443 ) )

# Test all areas
async def test_areas( area_number ) :
	async with asyncio.TaskGroup() as task_group :
		tasks = [ task_group.create_task( test_area( i + 1 ) ) for i in range( area_number ) ]
	return [ task.result() for task in tasks ]

# Main
parser = ArgumentParser( description='Checks the incoming traffic of the different network areas' )
parser.add_argument( '-n', '--number', type=int, default=8,	help='Number of areas (default to 8)' )
parser.add_argument( '-i', '--interval', type=int, default=30, help='Refresh interval (default to 30 seconds)' )
parser.add_argument( '-d4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'IPv4 destination address (default to {IPV4_ADDRESS})' )
parser.add_argument( '-d6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'IPv6 destination address (default to {IPV6_ADDRESS})' )
args = parser.parse_args()
IPV4_ADDRESS = args.destination4
IPV6_ADDRESS = args.destination6
try :
	while True :
		print('Updating...')
		areas = asyncio.run( test_areas( args.number ) )
		print('\033[H\033[J~~ RT Auxerre Lab Networks ~~\n')
		for area in areas:
			print( f'   Area {area.number} :'
				   f'   IPv4 '
				   f'{COLORS[area.is_ipv4_host_reachable]} ICMP \033[0m '
				   f'{COLORS[area.is_ipv4_http_reachable]} HTTP \033[0m '
				   f'{COLORS[area.is_ipv4_https_reachable]} HTTPS \033[0m'
				   f'   IPv6 '
				   f'{COLORS[area.is_ipv6_host_reachable]} ICMP \033[0m '
				   f'{COLORS[area.is_ipv6_http_reachable]} HTTP \033[0m '
				   f'{COLORS[area.is_ipv6_https_reachable]} HTTPS \033[0m' )
		print( '\nLast updated on', datetime.today().strftime( '%H:%M:%S' ) )
		sleep( args.interval )
		print( '\033[A\033[K', end='' )
except KeyboardInterrupt :
	print( '\033[A\033[KExited.' )
