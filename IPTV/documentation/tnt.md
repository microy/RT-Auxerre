
# Streaming de la télévision TNT


## Configuration de la carte WinTV USB sous Linux

Documentation :

	https://www.linuxtv.org/wiki/index.php/Hauppauge_WinTV-dualHD

Téléchargement et installation du firmware :

	wget http://palosaari.fi/linux/v4l-dvb/firmware/Si2168/Si2168-B40/4.0.25/dvb-demod-si2168-b40-01.fw
	cp dvb-demod-si2168-b40-01.fw /lib/firmware/


## Recherche des chaines

Installation des logiciels nécessaires :

	apt install w-scan dvb-apps dtv-scan-tables dvb-tools

Recherche des chaînes :

	scan /usr/share/dvb/dvb-legacy/dvb-t/fr-All > channels-scan.conf
	w_scan > channels-wscan.conf


## Diffusion de la TNT

Installation de dvblast :

	apt install dvblast

Fichier de configuration `/etc/dvblast/tnt.conf` :

	230.0.0.1:5005 1 1045 # France 5
	230.0.0.1:5006 1 1025 # M6
	230.0.0.1:5007 1 1031 # Arte
	230.0.0.1:5009 1 1026 # W9
	230.0.0.1:5022 1 1046 # 6ter

Activation du stream vidéo :

	dvblast --quiet --frequency 554000000 --config-file /etc/dvblast/tnt.conf

	# dvblast -a 0 -f 554000000 -c conf-5 -m QAM_64 -b 8 -e
	# dvblast -f 554000000 -c conf-5

Lecture du stream vidéo :

	vlc rtp://230.0.0.1:5005
	vlc rtp://230.0.0.1:5007

## Service de diffusion automatique

Fichier de configuration `/etc/systemd/system/tnt.service` :

	[Unit]
	Description=DVB-T streaming server
	Wants=network-online.target
	After=network-online.target

	[Service]
	ExecStart=/usr/bin/dvblast --quiet --frequency 554000000 --config-file /etc/dvblast/tnt.conf
	Restart=on-failure

	[Install]
	WantedBy=multi-user.target

Activation du service :

	systemctl enable tnt
	systemctl start tnt

Désactivation du service :

	systemctl stop tnt
	systemctl disable tnt

Diagnostic du service :

	systemctl status tnt
	systemctl restart tnt
