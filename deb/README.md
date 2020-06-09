_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Ниже приведена инструкция по собственноручной сборке и установке пакета.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

Для успешной установки пакета необходимо разрешить зависимости, указаны в [этом файле](https://github.com/MyConnector/MyConnector/blob/master/deb_package/connector/DEBIAN/control), также рекомендуется обновить в системе все пакеты до актуальных версий:

    sudo apt update && sudo apt upgrade

Для самостоятельной сборки deb-пакета Вам потребуется выполнить несколько команд:
* Установка необходимых для сборки пакетов:

      sudo apt install dpkg debconf debhelper lintian md5deep

* Выполнение скрипта сборки DEB-пакета:

      git clone https://github.com/MyConnector/MyConnector
      cd Connector/deb; chmod 755 buildDeb.sh;
      ./buildDeb.sh #для Ubuntu 18.04 и Mint 19

* Установка пакета:

      sudo dpkg -i connector*.deb
