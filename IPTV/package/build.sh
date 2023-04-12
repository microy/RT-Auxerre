#! /bin/sh

# Remove previous packages
rm -fv iptv*.deb

# Build the package
fakeroot dpkg-deb --build iptv

# Get the version number of the package
VERSION=$(cat iptv/DEBIAN/control | grep Version | awk '{print $2}')

# Rename the package to include the version number
mv -fv iptv.deb iptv_${VERSION}.deb
