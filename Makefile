TARGET = connector
PREFIX_BIN = /usr/local/bin
PREFIX = /usr/local/share
BASE = $(PREFIX)/$(TARGET)
MAN = $(PREFIX)/man/man1
ETC = /etc/$(TARGET)
APS = $(PREFIX)/applications
KIOSK = kiosk.access
MIME = $(PREFIX)/mime
ICON = $(PREFIX)/icons/hicolor/64x64/apps

.PHONY: help install uninstall clean

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
	install -m755 source/$(TARGET) $(PREFIX_BIN)
	mkdir -p $(APS)
	install -m644 data/$(TARGET).desktop $(APS)
	mkdir -p $(BASE)/data/
	install -m644 data/*.png data/*.glade $(BASE)/data/
	install -m644 source/*.py $(BASE)
	mkdir -p $(MAN)
	install -m644 data/$(TARGET).man $(MAN)/$(TARGET).1
	mkdir -p $(ETC)
	install -m644 data/$(KIOSK) $(ETC)
	mkdir -p $(MIME)/packages
	install -m644 data/$(TARGET).xml $(MIME)/packages
	mkdir -p $(ICON)
	install -m644 data/emblem $(ICON)/$(TARGET).png
	update-mime-database $(MIME)
	make clean

uninstall:
	rm -f $(PREFIX_BIN)/$(TARGET)
	rm -rf $(BASE)
	rm -f $(MAN)/$(TARGET).1
	rm -f $(PREFIX)/applications/$(TARGET).desktop
	mv -f $(ETC)/$(KIOSK) $(ETC)/$(KIOSK).makesave
	rm -f $(MIME)/packages/$(TARGET).xml
	rm -f $(ICON)/$(TARGET).png
	update-mime-database $(MIME)

clean:
	sed -i s#$(PREFIX)#/usr/share#g source/*
	sed -i s#$(PREFIX)#/usr/share#g data/$(TARGET).desktop
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g source/*
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g data/$(TARGET).desktop
