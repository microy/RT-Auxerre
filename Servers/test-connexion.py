#! /usr/bin/env python3

#
# Service reachability test application
# https://github.com/microy/rt-auxerre
# Copyright (c) 2026 Michaël Roy
# usage : $ sudo ./test-connexion.py
#

# -- Source --------------------------------------------------------------------
# Checks the incoming traffic of the trainees' firewall
#
#   Release:   2024-09-02 04:30 PM
#   Author:    Valentin BELYN (valentin.belyn@stormshield.eu)
#   Copyright: Stormshield, 2024
#
# (!) Python 3.11 or later is required
# ------------------------------------------------------------------------------

# Dependencies
import argparse
import asyncio
import dataclasses
import datetime
import os
import scapy.all as scapy
import socket
import time

# Check if root
if os.geteuid() != 0 :
	print( '\n-> Run this application as root (sudo)...')
	exit()

# Destination IP addresses
IPV4_ADDRESS = '203.0.113.{area}'
IPV6_ADDRESS = 'fd00:{area}1::1'

# Bash colors
COLORS = {
	False : '\033[31m', # RED
	True : '\033[32m'   # GREEN
}

# Result data class
@dataclasses.dataclass
class Results :
	area : int
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
		writer.close()
		return True
	except OSError :
		return False

# Host reachability test funtion
async def host_is_reachable( ip_address, ipv6 = False ) :
	if ipv6 : result = scapy.sr1( scapy.IPv6( dst = ip_address ) / scapy.ICMPv6EchoRequest(), timeout = 2, verbose = False )
	else : result = scapy.sr1( scapy.IP( dst = ip_address ) / scapy.ICMP(), timeout = 2, verbose = False )
	return ( result is not None ) and ( result.type in [ 0, 129 ] )

# Test one area
async def test_environment( area ) :
	ipv4_destination = IPV4_ADDRESS.format( area = area )
	ipv6_destination = IPV6_ADDRESS.format( area = area )
	return Results(
		area = area,
		is_ipv4_host_reachable = await host_is_reachable( ipv4_destination ),
		is_ipv6_host_reachable = await host_is_reachable( ipv6_destination, True ),
		is_ipv4_http_reachable = await service_is_reachable( ipv4_destination, 80 ),
		is_ipv6_http_reachable = await service_is_reachable( ipv6_destination, 80 ),
		is_ipv4_https_reachable = await service_is_reachable( ipv4_destination, 443 ),
		is_ipv6_https_reachable = await service_is_reachable( ipv6_destination, 443 ) )

# Test all areas
async def test_environments( num_trainees ) :
	loop = asyncio.get_running_loop()
	tasks = [ loop.create_task( test_environment(i + 1) ) for i in range( num_trainees ) ]
	await asyncio.wait( tasks )
	return [ task.result() for task in tasks ]

# Main
parser = argparse.ArgumentParser( description='Checks the incoming traffic of the trainees \'router' )
parser.add_argument( '-n', '--number', type=int, default=8,	help='the number of trainees (default to 8)' )
parser.add_argument( '-i', '--interval', type=int, default=30, help='the refresh interval (default to 30 seconds)' )
parser.add_argument( '-d4', '--destination4', type=str, default=IPV4_ADDRESS, help=f'Choose the IPv4 destination address (default to {IPV4_ADDRESS})' )
parser.add_argument( '-d6', '--destination6', type=str, default=IPV6_ADDRESS, help=f'Choose the IPv6 destination address (default to {IPV6_ADDRESS})' )
args = parser.parse_args()
IPV4_ADDRESS = args.destination4
IPV6_ADDRESS = args.destination6
try :
	while True :
		print('Updating...')
		environments = asyncio.run( test_environments( args.number ) )
		print('\033[H\033[J~~ RT Auxerre Lab Networks ~~\n')
		for environment in environments:
			print(f'   Area {environment.area} :'
					f'   IPv4 ='
					f' {COLORS[environment.is_ipv4_host_reachable]}| ICMP |\033[0m'
					f' {COLORS[environment.is_ipv4_http_reachable]}| HTTP |\033[0m'
					f' {COLORS[environment.is_ipv4_https_reachable]}| HTTPS |\033[0m'
					f'   IPv6 ='
					f' {COLORS[environment.is_ipv6_host_reachable]}| ICMP |\033[0m'
					f' {COLORS[environment.is_ipv6_http_reachable]}| HTTP |\033[0m'
					f' {COLORS[environment.is_ipv6_https_reachable]}| HTTPS |\033[0m' )
		print( '\nLast updated on', datetime.datetime.today().strftime( '%H:%M:%S' ) )
		time.sleep( args.interval )
		print( '\033[A\033[K', end='' )
except KeyboardInterrupt :
	print( '\033[A\033[KExited.' )
