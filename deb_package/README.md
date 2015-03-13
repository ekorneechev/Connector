Для успешной установки пакета необходимо разрешить зависимости, указаны в [этом файле](https://github.com/ekorneechev/Connector/blob/master/deb_package/connector/DEBIAN/control), также рекомендуется обновить в системе все пакеты до актуальных версий:

`sudo apt-get update && sudo apt-get upgrade`

Для самостоятельной сборки deb-пакета Вам потребуется выполнить несколько команд: 
* Установка необходимых для сборки пакетов:

`sudo apt-get install dpkg debconf debhelper lintian`

* Настройка исполняемых файлов:

`chmod 755 connector/usr/bin/connector && chmod 755 connector/DEBIAN/postrm`

* Сборка пакета:

`fakeroot dpkg-deb --build connector`
