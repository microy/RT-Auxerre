#! /usr/bin/env python3

#
# Script pour générer les configurations des materiels des TP réseaux
#

# https://florian-dahlitz.de/articles/generate-file-reports-using-pythons-template-class

# Modules externes
import string
import sys

# Teste les arguments de la ligne de commmande
if len( sys.argv ) != 3 :
	print( 'Usage: {} fichier_template numéro_zone'.format( sys.argv[0] ) )
	sys.exit()

# Lit le fichier template
with open( sys.argv[1], 'r' ) as fichier :
	template = fichier.read()

# Change le numéro de zone
result = string.Template( template ).substitute( zone = sys.argv[2] )

# Affiche le résultat
print( result )
