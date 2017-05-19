_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

ВНИМАНИЕ! deb-пакет не всегда обновляется одновременно с обновлением исходников!
Ниже приведена инструкция по собственноручной сборке и установке пакета.

_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

Для успешной установки пакета необходимо разрешить зависимости, указаны в [этом файле](https://github.com/ekorneechev/Connector/blob/master/deb_package/connector/DEBIAN/control), также рекомендуется обновить в системе все пакеты до актуальных версий:

`sudo apt-get update && sudo apt-get upgrade`

Для самостоятельной сборки deb-пакета Вам потребуется выполнить несколько команд: 
* Установка необходимых для сборки пакетов:

`sudo apt-get install dpkg debconf debhelper lintian`

* Выполнение скрипта сборки DEB-пакета:

`git clone https://github.com/ekorneechev/Connector`

`cd Connector; git checkout master; cd deb_package; chmod 755 buildDeb.sh; ./buildDeb.sh`

* Установка пакета:

`sudo dpkg -i connector.deb`
