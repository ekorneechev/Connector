#! /bin/bash
mkdir -p connector/usr/bin
mkdir -p connector/usr/share/applications/data
mkdir -p connector/usr/share/connector
mkdir -p connector/usr/share/man/man1
cp ../source/*.py connector/usr/share/connector/
cp ../source/connector connector/usr/bin/
cp -r ../data/ connector/usr/share/connector/
mv connector/usr/share/connector/data/connector.desktop connector/usr/share/applications/data
mv connector/usr/share/connector/data/connector.man connector/usr/share/man/man1/connector.1
chmod 755 connector/usr/bin/connector
mkdir -p connector/DEBIAN
cp control connector/DEBIAN/
fakeroot dpkg-deb --build connector
rm -r connector/
