TARGET = connector
PREFIX_BIN = /usr/local/bin
PREFIX = /usr/local/share
BASE = $(PREFIX)/$(TARGET)
MAN = $(PREFIX)/man/man1
ETC = /etc/$(TARGET)
APS = $(PREFIX)/applications
KIOSK = kiosk.access
MIME = $(PREFIX)/mime
DATESTAMP = `git log --pretty="%cd" --date=short -1 | sed s/-//g 2>/dev/null`

.PHONY: help install uninstall clean remove

help:
	@echo "Запустите make с одной из необходимых ролей:"
	@echo "... help (по умолчанию, показать данную справку)"
	@echo "... install (установка программы, требует sudo)"
	@echo "... uninstall (удаление программы, требует sudo)"
	@echo "... clean (сброс изменений в исходниках)"

install:
	apt-get remove connector -y
	sed -i s#/usr/share#$(PREFIX)#g source/*
	sed -i s#/usr/share#$(PREFIX)#g data/$(TARGET).desktop
	sed -i s#/usr/bin/$(TARGET)#$(PREFIX_BIN)/$(TARGET)#g source/*
	sed -i s#/usr/bin/$(TARGET)#$(PREFIX_BIN)/$(TARGET)#g data/$(TARGET).desktop
	sed -i s#$(PREFIX)/applications#/usr/share/applications#g source/GLOBAL.py
	@if [ -n "$(DATESTAMP)" ]; then sed -i s#git#git.$(DATESTAMP)#g source/GLOBAL.py; fi
	install -m755 source/$(TARGET) $(PREFIX_BIN)
	mkdir -p $(APS)
	install -m644 data/$(TARGET).desktop $(APS)
	mkdir -p $(BASE)/data/
	install -m644 data/*.png data/*.glade $(BASE)/data/
	install -m644 source/*.py $(BASE)
	install -m755 source/$(TARGET)-check-version $(BASE)
	mkdir -p $(MAN)
	install -m644 data/$(TARGET).man $(MAN)/$(TARGET).1
	mkdir -p $(ETC)
	install -m644 data/$(KIOSK) $(ETC)
	mkdir -p $(MIME)/packages
	install -m644 data/$(TARGET).xml $(MIME)/packages
	cp -r data/icons $(PREFIX)
	update-mime-database $(MIME)
	update-desktop-database
	make clean

uninstall:
	rm -f $(PREFIX_BIN)/$(TARGET)
	rm -rf $(BASE)
	rm -f $(MAN)/$(TARGET).1
	rm -f $(PREFIX)/applications/$(TARGET).desktop
	@if [ -f $(ETC)/$(KIOSK) ]; then mv -f $(ETC)/$(KIOSK) $(ETC)/$(KIOSK).makesave; fi
	rm -f $(MIME)/packages/$(TARGET).xml
	find $(PREFIX)/icons/hicolor -name $(TARGET).png -delete
	update-mime-database $(MIME)
	update-desktop-database

clean:
	sed -i s#$(PREFIX)#/usr/share#g source/*
	sed -i s#$(PREFIX)#/usr/share#g data/$(TARGET).desktop
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g source/*
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g data/$(TARGET).desktop
	@if [ -n "$(DATESTAMP)" ]; then sed -i s#.$(DATESTAMP)##g source/GLOBAL.py; fi

remove:
	make uninstall
