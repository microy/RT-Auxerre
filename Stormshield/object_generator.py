#! /usr/bin/env python3

#
# Script pour générer les objets Stormshield pour les Labs SNS
#

# Module string pour les templates
import string

# Variables globales
ENTREPRISE = [ None,'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X' ]
ENTREPRISE_MAX = 17
ADDRESS_OUT = '192.36.253'
ADDRESS_IN = '192.168'
ADDRESS_DMZ = '172.16'

# Template objets entreprise
TEMPLATE_ENTREPRISE = '''
### ENTREPRISE ${entreprise} ###
#type,#name,#ip,#ipv6,#resolve,#mac,#comment
host,FW_${entreprise},${address_out}.${numero}0,,static,,\"FIREWALL ENTREPRISE ${entreprise}\"
host,SRV_FTP_PUB_${entreprise},${address_out}.${numero}2,,static,,\"SERVEUR FTP PUBLIC ENTREPISE ${entreprise}\"
host,SRV_MAIL_PUB_${entreprise},${address_out}.${numero}3,,static,,\"SERVEUR MAIL PUBLIC ENTREPRISE ${entreprise}\"
host,SRV_DNS_PRIV_${entreprise},${address_dmz}.${numero}.10,,static,,\"SERVEUR DNS PRIVÉ ENTREPRISE ${entreprise}\"
host,SRV_WEB_PRIV_${entreprise},${address_dmz}.${numero}.11,,static,,\"SERVEUR WEB PRIVÉ ENTREPRISE ${entreprise}\"
host,SRV_FTP_PRIV_${entreprise},${address_dmz}.${numero}.12,,static,,\"SERVEUR FTP PRIVÉ ENTREPRISE ${entreprise}\"
host,SRV_MAIL_PRIV_${entreprise},${address_dmz}.${numero}.13,,static,,\"SERVEUR MAIL PRIVÉ ENTREPRISE ${entreprise}\"
host,PC_ADMIN_${entreprise},${address_in}.${numero}.2,,static,,\"PC ADMIN ENTREPRISE ${entreprise}\"
#type,#name,#ip,#mask,#prefixlen,#ipv6,#prefixlenv6,#comment
network,LAN_${entreprise},${address_in}.${numero}.0,255.255.255.0,24,,,\"LAN ENTREPRISE ${entreprise}\"
network,DMZ_${entreprise},${address_dmz}.${numero}.0,255.255.255.0,24,,,\"DMZ ENTREPRISE ${entreprise}\"
#type,#name,#elements,#comment
group,SRV_PUB_${entreprise},\"SRV_FTP_PUB_${entreprise},SRV_MAIL_PUB_${entreprise}\",\"GROUPE SERVEURS PUBLICS ENTREPRISE ${entreprise}\"
group,SRV_PRIV_${entreprise},\"SRV_DNS_PRIV_${entreprise},SRV_WEB_PRIV_${entreprise},SRV_FTP_PRIV_${entreprise},SRV_MAIL_PRIV_${entreprise}\",\"GROUPE SERVEURS PRIVÉS ENTREPRISE ${entreprise}\"
group,NET_${entreprise},\"LAN_${entreprise},DMZ_${entreprise}\",\"GROUPE RÉSEAUX ENTREPRISE ${entreprise}\"
'''

# Définition du groupe des firewalls
GROUPE_FIREWALLS = '''
### GROUPE FIREWALLS ###
#type,#name,#elements,#comment
group,FW_ALL,\"{}\",\"GROUPE FIREWALLS\"
'''.format( ','.join( [ 'FW_{}'.format( ENTREPRISE[i] ) for i in range( 1, ENTREPRISE_MAX ) ] ) )

# Définition du groupe des serveurs publics
GROUPE_SRV_PUB = '''
### GROUPE SERVEURS PUBLICS ###
#type,#name,#elements,#comment
group,SRV_PUB_ALL,\"{}\",\"GROUPE SERVEURS PUBLICS\"
'''.format( ','.join( [ 'SRV_PUB_{}'.format( ENTREPRISE[i] ) for i in range( 1, ENTREPRISE_MAX ) ] ) )

# Définition du service webmail
SERVICE_WEBMAIL = '''
### SERVICE WEBMAIL ###
#type,#name,#proto,#port,#toport,#comment
service,PORT_WEBMAIL,tcp,808,,\"PORT WEBMAIL\"
'''

# Définition des pools pour le DCHP
POOL_DHCP = '''
#type,#name,#begin,#end,#beginv6,#endv6,#beginmac,#endmac,#comment
{}
'''.format( '\n'.join( [ 'range,POOL_DHCP_LAN_{0},192.168.{1}.20,192.168.{1}.50,,,,,\"POOL DHCP LAN {0}\"'.format(ENTREPRISE[i],i) for i in range( 1, ENTREPRISE_MAX ) ] ) )


# Écrit le fichier CSV
with open( 'test-objects.csv', 'w' ) as csvfile :
	for i in range( 1, ENTREPRISE_MAX ) :
		csvfile.write( string.Template( TEMPLATE_ENTREPRISE ).substitute( entreprise = ENTREPRISE[i], numero = i, address_out = ADDRESS_OUT, address_in = ADDRESS_IN, address_dmz = ADDRESS_DMZ ) )
	csvfile.write( GROUPE_FIREWALLS )
	csvfile.write( GROUPE_SRV_PUB )
	csvfile.write( SERVICE_WEBMAIL )
	csvfile.write( POOL_DHCP )
