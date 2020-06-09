#! /bin/bash
TARGET=connector
BIN=$TARGET/usr/bin
SHARE=$TARGET/usr/share
PREFIX=$SHARE/$TARGET
DATA=$PREFIX/data
APPS=$SHARE/applications
MAN=$SHARE/man/man1
MIME=$SHARE/mime/packages

rm -rf $TARGET
mkdir -p $BIN $APPS $PREFIX $MAN $MIME
cp ../source/*.py $PREFIX/
cp ../source/$TARGET-check-* $PREFIX/
cp ../source/$TARGET $BIN/
cp -r ../data/ $PREFIX/
mv $DATA/$TARGET.desktop $APPS
mv $DATA/$TARGET.man $MAN/$TARGET.1
mv $DATA/icons $SHARE
mv $DATA/$TARGET.xml $MIME
chmod 755 $BIN/$TARGET $PREFIX/$TARGET-check-*
INST_SIZE=`du -s connector | cut -f 1`
mkdir -p $TARGET/DEBIAN
cd $TARGET
md5deep -rl usr > DEBIAN/md5sums
cd ..
cp control $TARGET/DEBIAN/
sed -i "s\Installed-Size:\Installed-Size: $INST_SIZE\g" $TARGET/DEBIAN/control
fakeroot dpkg-deb --build $TARGET
mv $TARGET.deb ${TARGET}_`grep Version $TARGET/DEBIAN/control | sed s/Version:\ //g`_all.deb
rm -r $TARGET/
