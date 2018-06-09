#! /bin/bash
rm -rf connector*
mkdir -p connector/usr/bin
mkdir -p connector/usr/share/applications/data
mkdir -p connector/usr/share/connector
mkdir -p connector/usr/share/man/man1
mkdir -p connector/etc/connector
cp ../source/*.py connector/usr/share/connector/
cp ../source/connector connector/usr/bin/
cp -r ../data/ connector/usr/share/connector/
mv connector/usr/share/connector/data/connector.desktop connector/usr/share/applications/data
mv connector/usr/share/connector/data/connector.man connector/usr/share/man/man1/connector.1
mv connector/usr/share/connector/data/kiosk.access connector/etc/connector
chmod 755 connector/usr/bin/connector
mkdir -p connector/DEBIAN
cd connector
md5deep -rl usr > DEBIAN/md5sums
md5deep -rl etc >> DEBIAN/md5sums
cd ..
cp control conffiles connector/DEBIAN/
fakeroot dpkg-deb --build connector
mv connector.deb connector_`grep Version control | sed s/Version:\ //g`_all.deb
rm -r connector/
