#! /bin/bash
cd ..
mkdir -p deb_package/connector/usr/bin
mkdir -p deb_package/connector/usr/share/applications/data
mkdir -p deb_package/connector/usr/share/connector
cp source/*.py deb_package/connector/usr/share/connector/
cp source/connector deb_package/connector/usr/bin/
cp -r data/ deb_package/connector/usr/share/connector/
mv deb_package/connector/usr/share/connector/data/connector.desktop deb_package/connector/usr/share/applications/data
cd deb_package/
chmod 755 connector/usr/bin/connector
fakeroot dpkg-deb --build connector
rm -r connector/usr
