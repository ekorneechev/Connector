Name: connector
Version: 1.3.14
Release: alt1

Summary: Remote desktop chooser
License: GPL
Group: Networking/Remote access

Url: https://github.com/ekorneechev/Connector
Source0: %name-%version.tar.gz
Packager: Korneechev Evgeniy <ekorneechev@altlinux.org>

BuildArch: noarch
Requires: python3 python3-module-pygobject3
Requires: libgtk+3 libgtk+3-gir remmina tigervnc

%define basedir %_datadir/%name

%description
This is an aggregator program to connnect to various servers
using all of the popular remote desktop protocols
(RDP, VNC, Citrix, VMware, etc).

%prep
%setup

%install
install -pDm755 %name %buildroot%_bindir/%name
install -pDm644 %name.desktop %buildroot%_desktopdir/%name.desktop
mkdir -p %buildroot%basedir/data/
install -p *.png *.glade %buildroot%basedir/data/
install -p *.py %buildroot%basedir/

%files
%_bindir/%name
%_desktopdir/%name.desktop
%basedir/data
%basedir/*.py

%changelog
* Thu Jun 25 2015 Evgeniy Korneechev <ekorneechev@altlinux.org> 1.3.14-alt1
- Update GUI and FreeRDP features

* Tue Jun 23 2015 Evgeniy Korneechev <ekorneechev@altlinux.org> 1.3.12-alt4
- Update SPEC

* Mon Jun 22 2015 Korneechev Evgeniy <ekorneechev@altlinux.org> 1.3.12-alt3
- Initial build by GEAR

* Tue Jun 16 2015 Michael Shigorin <mike@altlinux.org> 1.3.12-alt2
- spec cleanup

* Tue Jun 16 2015 Evgeniy Korneechev <ekorneechev@gmail.com> 1.3.12-alt1
- Initial build
