#! /usr/bin/env python3

#
# Network and service reachability test application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
# usage : $ sudo ./test-connexion.py
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
	is_ipv4_http_reachable : bool = False
	is_ipv4_https_reachable : bool = False
	is_ipv6_host_reachable : bool = False
	is_ipv6_http_reachable : bool = False
	is_ipv6_https_reachable : bool = False

# Service reachability test funtion
async def test_service( ip_address, port ) :
	try :
		await asyncio.wait_for( asyncio.open_connection( host = ip_address, port = port ), timeout = 2 )
		return True
	except : return False

# Ping IPv4
async def test_ping4( destination_address ) :
	try :
		with socket.socket( socket.AF_INET, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMP ) as icmp_socket :
			icmp_socket.sendto( ICMP4_PACKET, ( destination_address, 0 ) )
			answer = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = 2 )
			return True if answer[ 20:21 ] == b'\x00' else False
	except : return False

# Ping IPv6
async def test_ping6( destination_address ) :
	try :
		with socket.socket( socket.AF_INET6, socket.SOCK_RAW | socket.SOCK_NONBLOCK, socket.IPPROTO_ICMPV6 ) as icmp_socket :
			icmp_socket.sendto( ICMP6_PACKET, ( destination_address, 0 ) )
			answer = await asyncio.wait_for( asyncio.get_event_loop().sock_recv( icmp_socket, 1024 ), timeout = 2 )
			return True if answer[ :1 ] == b'\x81' else False
	except : return False

# Test one area
async def test_one_area( area_number ) :
	ipv4_destination = IPV4_ADDRESS.format( area = area_number )
	ipv6_destination = IPV6_ADDRESS.format( area = area_number )
	async with asyncio.TaskGroup() as task_group :
		task_ipv4_host_reachable = task_group.create_task( test_ping4( ipv4_destination ) )
		task_ipv4_http_reachable = task_group.create_task( test_service( ipv4_destination, 80 ) )
		task_ipv4_https_reachable = task_group.create_task( test_service( ipv4_destination, 443 ) )
		task_ipv6_host_reachable = task_group.create_task( test_ping6( ipv6_destination ) )
		task_ipv6_http_reachable = task_group.create_task( test_service( ipv6_destination, 80 ) )
		task_ipv6_https_reachable = task_group.create_task( test_service( ipv6_destination, 443 ) )
	return Results(
		number = area_number,
		is_ipv4_host_reachable = task_ipv4_host_reachable.result(),
		is_ipv4_http_reachable = task_ipv4_http_reachable.result(),
		is_ipv4_https_reachable = task_ipv4_https_reachable.result(),
		is_ipv6_host_reachable = task_ipv6_host_reachable.result(),
		is_ipv6_http_reachable = task_ipv6_http_reachable.result(),
		is_ipv6_https_reachable = task_ipv6_https_reachable.result() )

# Test all areas
async def test_all_areas( area_number ) :
	async with asyncio.TaskGroup() as task_group :
		tasks = [ task_group.create_task( test_one_area( i + 1 ) ) for i in range( area_number ) ]
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
		areas = asyncio.run( test_all_areas( args.number ) )
		print( '\033[H\033[J\nRT Auxerre Lab Networks\n' )
		print( '	     ------- IPv4 --------   ------- IPv6 --------\n' )
		for area in areas:
			print( f'   Area {area.number} :  '
				   f'{COLORS[area.is_ipv4_host_reachable]} ICMP \033[0m '
				   f'{COLORS[area.is_ipv4_http_reachable]} HTTP \033[0m '
				   f'{COLORS[area.is_ipv4_https_reachable]} HTTPS \033[0m   '
				   f'{COLORS[area.is_ipv6_host_reachable]} ICMP \033[0m '
				   f'{COLORS[area.is_ipv6_http_reachable]} HTTP \033[0m '
				   f'{COLORS[area.is_ipv6_https_reachable]} HTTPS \033[0m' )
		print( '\nLast updated on', datetime.today().strftime( '%H:%M:%S' ) )
		sleep( args.interval )
		print( '\033[A\033[K', end='' )
except KeyboardInterrupt :
	print( '\033[A\033[KExited.' )