#! /usr/bin/env python3

#
# Script pour générer les objets Stormshield pour les Labs SNS
#

# Module string pour les templates
import string

# Variables globales
ENTREPRISE_MAX = 17

ADRESSES_IUT = '''
### ADRESSES IUT ###
#type,#name,#ip,#ipv6,#resolve,#mac,#comment
host,GATEWAY_IUT_TPR1,10.129.58.1,,static,,\"GATEWAY IUT TP RÉSEAUX 1\"
host,GATEWAY_IUT_TPR2,10.129.58.129,,static,,\"GATEWAY IUT TP RÉSEAUX 2\"
host,DNS1_UB,193.50.50.2,,static,,\"DNS1 UB\"
host,DNS2_UB,193.50.50.6,,static,,\"DNS1 UB\"
host,ntp.u-bourgogne.fr,193.50.50.6,,dynamic,,"SERVEUR DE TEMPS NTP UB"
host,pool.ntp.org,162.159.200.1,,dynamic,,"SERVEURS DE TEMPS NTP.ORG"
host,0.pool.ntp.org,213.209.109.45,,dynamic,,"SERVEURS DE TEMPS NTP.ORG 0"
host,1.pool.ntp.org,5.45.111.220,,dynamic,,"SERVEURS DE TEMPS NTP.ORG 1"
host,2.pool.ntp.org,78.47.249.55,,dynamic,,"SERVEURS DE TEMPS NTP.ORG 2"
host,3.pool.ntp.org,185.120.22.14,,dynamic,,"SERVEURS DE TEMPS NTP.ORG 3"
#type,#name,#elements,#comment
group,NTP_ORG,"0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org","SERVEURS DE TEMPS NTP"
#type,#name,#begin,#end,#beginv6,#endv6,#beginmac,#endmac,#comment
range,POOL_DHCP_MANAGEMENT,100.64.11.1,100.64.11.99,,,,,"POOL DHCP MANAGEMENT"
'''

# Définition du groupe des firewalls
GROUPE_NAT_STORMSHIELD = '''
### GROUPE NAT STORMSHIELD ###
#type,#name,#elements,#comment
group,NAT_STORMSHIELD,\"FW_ALL,SRV_PUB_ALL\",\"GROUPE NAT STORMSHIELD\"
'''

ADRESSES_NAT_IUT_TPR1 = '''
### ADRESSES NAT IUT TP RÉSEAUX 1###
#type,#name,#ip,#ipv6,#resolve,#mac,#comment
{}
'''.format( '\n'.join( [ 'host,NAT_IUT_TPR1_{0},10.129.58.{0},,static,,\"ADRESSE NAT IUT TPR1 {0}\"'.format(i) for i in range( 31, (ENTREPRISE_MAX-1)*3+31 ) ] ) )

GROUPE_NAT_IUT_TPR1 = '''
### GROUPE ADRESSES NAT IUT TP RÉSEAUX 1 ###
#type,#name,#elements,#comment
group,NAT_IUT_TPR1,\"{}\",\"GROUPE NAT IUT TP RÉSEAUX 1\"
'''.format( ','.join( [ 'NAT_IUT_TPR1_{}'.format( i ) for i in range( 31, (ENTREPRISE_MAX-1)*3+31 ) ] ) )

ADRESSES_NAT_IUT_TPR2 = '''
### ADRESSES NAT IUT TP RÉSEAUX 2###
#type,#name,#ip,#ipv6,#resolve,#mac,#comment
{}
'''.format( '\n'.join( [ 'host,NAT_IUT_TPR2_{0},10.129.58.{0},,static,,\"ADRESSE NAT IUT TPR2 {0}\"'.format(i) for i in range( 151, (ENTREPRISE_MAX-1)*3+151 ) ] ) )

GROUPE_NAT_IUT_TPR2 = '''
### GROUPE ADRESSES NAT IUT TP RÉSEAUX 2 ###
#type,#name,#elements,#comment
group,NAT_IUT_TPR2,\"{}\",\"GROUPE NAT IUT TP RÉSEAUX 2\"
'''.format( ','.join( [ 'NAT_IUT_TPR2_{}'.format( i ) for i in range( 151, (ENTREPRISE_MAX-1)*3+151 ) ] ) )


# Écrit le fichier CSV pour l'IUT (Trainer)
with open( 'test-objects-iut.csv', 'w' ) as csvfile :
	csvfile.write( ADRESSES_IUT )
	csvfile.write( GROUPE_NAT_STORMSHIELD )
	csvfile.write( ADRESSES_NAT_IUT_TPR1 )
	csvfile.write( GROUPE_NAT_IUT_TPR1 )
	csvfile.write( ADRESSES_NAT_IUT_TPR2 )
	csvfile.write( GROUPE_NAT_IUT_TPR2 )
