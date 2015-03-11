Для сборки deb-пакета Вам потребуется установить следующие пакеты:

`sudo apt-get install dpkg debconf debhelper lintian`

Настройка исполняемых файлов:

`chmod 755 connector/usr/bin/connector && chmod 755 connector/DEBIAN/postrm`

После команда для сборки:

`fakeroot dpkg-deb --build connector`
