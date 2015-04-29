!!!!!!!!!!!!!!!!!!!!!!!!!

ВНИМАНИЕ! deb-пакет не всегда обновляется одновременно с обновление исходников!
Инструкция по обновлению установленной версии будет немного позже.
Пока можно использовать инструкцию по собственноручной сборке и установке пакета.

!!!!!!!!!!!!!!!!!!!!!!!!!

Для успешной установки пакета необходимо разрешить зависимости, указаны в [этом файле](https://github.com/ekorneechev/Connector/blob/master/deb_package/connector/DEBIAN/control), также рекомендуется обновить в системе все пакеты до актуальных версий:

`sudo apt-get update && sudo apt-get upgrade`


Для самостоятельной сборки deb-пакета Вам потребуется выполнить несколько команд: 
* Установка необходимых для сборки пакетов:

`sudo apt-get install dpkg debconf debhelper lintian`

* Обновление файлов для сборки:

`cp source/*.py deb_package/connector/usr/share/connector/ && \`

`cp source/connector deb_package/connector/usr/bin/ && \`

`cp -r data/ deb_package/connector/usr/share/connector/ && \`

`mv deb_package/connector/usr/share/connector/data/connector.desktop deb_package/connector/usr/share/applications/data`

* Настройка исполняемого файла:

`cd deb_package/ && chmod 755 connector/usr/bin/connector`

* Сборка пакета:

`fakeroot dpkg-deb --build connector`

* Установка пакета:

`sudo dpkg -i connector.deb`
