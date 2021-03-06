TARGET = connector
PREFIX_BIN = /usr/local/bin
PREFIX = /usr/local/share
BASE = $(PREFIX)/$(TARGET)
MAN = $(PREFIX)/man/man1
APS = $(PREFIX)/applications
MIME = $(PREFIX)/mime
ETC = /etc/$(TARGET)
KIOSK = kiosk.conf
DATESTAMP = `git log --pretty="%cd" --date=short -1 | sed s/-//g 2>/dev/null`

.PHONY: help install uninstall clean remove

help:
	@echo "Запустите make с одной из необходимых ролей:"
	@echo "... help (по умолчанию, показать данную справку)"
	@echo "... install (установка программы, требует sudo)"
	@echo "... uninstall (удаление программы, требует sudo)"
	@echo "... clean (сброс изменений в исходниках)"

install:
	apt-get remove connector -y || /bin/true
	sed -i s#/usr/share#$(PREFIX)#g source/* data/$(TARGET).desktop kiosk/*
	sed -i s#/usr/bin/$(TARGET)#$(PREFIX_BIN)/$(TARGET)#g source/* data/$(TARGET).desktop kiosk/*
	sed -i s#$(PREFIX)/applications#/usr/share/applications#g source/GLOBAL.py
	@if [ -n "$(DATESTAMP)" ]; then sed -i s#git#git.$(DATESTAMP)#g source/GLOBAL.py; fi
	install -m755 source/$(TARGET) $(PREFIX_BIN)
	mkdir -p $(APS)
	install -m644 data/$(TARGET).desktop $(APS)
	mkdir -p $(BASE)/data/
	install -m644 data/*.png data/*.ui $(BASE)/data/
	install -m644 source/*.py $(BASE)
	install -m755 source/$(TARGET)-check-* $(BASE)
	mkdir -p $(MAN)
	install -m644 data/$(TARGET).man $(MAN)/$(TARGET).1
	install -m644 kiosk/$(TARGET)-kiosk.man $(MAN)/$(TARGET)-kiosk.1
	mkdir -p $(MIME)/packages
	install -m644 data/$(TARGET).xml $(MIME)/packages
	cp -r data/icons $(PREFIX)
	cp -r kiosk $(BASE)
	mkdir -p $(ETC)
	@if [ ! -f $(ETC)/$(KIOSK) ]; then install -m600 kiosk/$(KIOSK) $(ETC); fi
	update-mime-database $(MIME)
	update-desktop-database
	make clean

uninstall:
	rm -f $(PREFIX_BIN)/$(TARGET)
	rm -rf $(BASE)
	rm -f $(MAN)/$(TARGET).1
	rm -f $(MAN)/$(TARGET)-kiosk.1
	rm -f $(PREFIX)/applications/$(TARGET).desktop
	rm -f $(MIME)/packages/$(TARGET).xml
	@if [ -f $(ETC)/$(KIOSK) ]; then mv -f $(ETC)/$(KIOSK) $(ETC)/$(KIOSK).makesave; fi
	find $(PREFIX)/icons/hicolor -name $(TARGET).png -delete
	update-mime-database $(MIME)
	update-desktop-database

clean:
	sed -i s#$(PREFIX)#/usr/share#g source/* data/$(TARGET).desktop kiosk/*
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g source/* data/$(TARGET).desktop kiosk/*
	@if [ -n "$(DATESTAMP)" ]; then sed -i s#.$(DATESTAMP)##g source/GLOBAL.py; fi

remove:
	make uninstall
