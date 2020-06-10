#! /bin/bash
TARGET=myconnector
USR=$TARGET/usr
BIN=$USR/bin
MAN=$USR/share/man/man1
PYTHON=$USR/lib/python3/dist-packages/$TARGET #TODO fix for Alt

rm -rf $TARGET
mkdir -p $USR $PYTHON
cp -r ../bin/ $USR/
cp -r ../share/ $USR/
chmod 755 $BIN/*
ln -s $TARGET $BIN/connector
mv $BIN/$TARGET-check-* $USR/share/$TARGET
cp ../lib/* $PYTHON/
mkdir -p $MAN
cp ../$TARGET.man $MAN/$TARGET.1
INST_SIZE=`du -s myconnector | cut -f 1`
mkdir -p $TARGET/DEBIAN
cd $TARGET
md5deep -rl usr > DEBIAN/md5sums
cd ..
cp control $TARGET/DEBIAN/
sed -i "s\Installed-Size:\Installed-Size: $INST_SIZE\g" $TARGET/DEBIAN/control
fakeroot dpkg-deb --build $TARGET
mv $TARGET.deb ${TARGET}_`grep Version $TARGET/DEBIAN/control | sed s/Version:\ //g`_all.deb
rm -r $TARGET/
