#! /bin/bash

echo "--------------------------------------"
echo "-                                    -"
echo "- Configuration du réseau sur enp2s0 -"
echo "-                                    -"
echo "--------------------------------------"
echo ""

echo "Adresse IPv4 : "
read adresse_ipv4

echo ""
echo "Passerelle IPv4 : "
read gateway_ipv4

echo ""
echo "DNS IPv4: "
read dns_ipv4

echo ""
echo "Adresse IPv6 : "
read adresse_ipv6

echo ""
echo "Passerelle IPv6 : "
read gateway_ipv6

echo ""
echo "DNS IPv6: "
read dns_ipv6
echo ""


# Désactive l’interface eno1
nmcli connection down eno1

# Désactive l’interface enp2s0
nmcli connection down enp2s0

# Configure IPv4 de l’interface enp2s0
nmcli connection modify enp2s0 ipv4.method manual ipv4.addresses $adresse_ipv4 ipv4.gateway $gateway_ipv4 ipv4.dns $dns_ipv4

# Configure IPv6 de l’interface enp2s0
nmcli connection modify enp2s0 ipv6.method manual ipv6.addresses $adresse_ipv6 ipv6.gateway $gateway_ipv6 ipv6.dns $dns_ipv6

# Active l’interface enp2s0
nmcli connection up enp2s0

echo ""
nmcli --terse

