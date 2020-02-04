Name: connector-kiosk
Version: 0.1
Release: alt1

Summary: Mode "KIOSK" for connector
License: GPL
Group: Networking/Remote access

BuildArch: noarch
Requires: connector >= 1.8.9
Requires: chromium

%define basedir %_datadir/connector/kiosk

%description
Files for connector mode "KIOSK"

%prep

%install
mkdir -p %buildroot%basedir
install -pm755 %name %buildroot%basedir/
install -pm644 %name.desktop %buildroot%basedir/


%files
%dir %basedir
%basedir/*

%changelog
* Tue Feb 4 2020 Evgeniy Korneechev <ekorneechev@altlinux.org> 0.1-alt1
- initial release
