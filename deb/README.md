_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
Ниже приведена инструкция по собственноручной сборке и установке пакета.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

Для успешной установки пакета необходимо разрешить зависимости, указаны в [этом файле](https://github.com/ekorneechev/Connector/blob/master/deb_package/connector/DEBIAN/control), также рекомендуется обновить в системе все пакеты до актуальных версий:

    sudo apt-get update && sudo apt-get upgrade

Для самостоятельной сборки deb-пакета Вам потребуется выполнить несколько команд: 
* Установка необходимых для сборки пакетов:

      sudo apt-get install dpkg debconf debhelper lintian md5deep

* Выполнение скрипта сборки DEB-пакета:

      git clone https://github.com/ekorneechev/Connector
      cd Connector/deb; chmod 755 buildDeb.sh;
      ./buildDeb.sh #для Ubuntu 18.04 и Mint 19
      ./buildDeb.sh mint17/ubuntu14 #для Ubuntu 14.04 и Mint 17

* Установка пакета:
    
      sudo dpkg -i connector*.deb
