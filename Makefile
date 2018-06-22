TARGET = connector
PREFIX_BIN = /usr/local/bin
PREFIX = /usr/local/share
BASE = $(PREFIX)/$(TARGET)
MAN = $(PREFIX)/man/man1
ETC = /etc/$(TARGET)
APS = $(PREFIX)/applications
KIOSK = kiosk.access

.PHONY: help install uninstall clean

help:
	@echo "Запустите make с одной из необходимых ролей:"
	@echo "... help (по умолчанию, показать данную справку)"
	@echo "... install (установка программы, требует sudo)"
	@echo "... uninstall (удаление программы, требует sudo)"
	@echo "... clean (сброс изменений в исходниках)"

install:
	sed -i s#/usr/share#$(PREFIX)#g {source/*,data/$(TARGET).desktop}
	sed -i s#/usr/bin/$(TARGET)#$(PREFIX_BIN)/$(TARGET)#g {source/*,data/$(TARGET).desktop}
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

uninstall:
	rm -f $(PREFIX_BIN)/$(TARGET)
	rm -rf $(BASE)
	rm -f $(MAN)/$(TARGET).1
	rm -f $(PREFIX)/applications/$(TARGET).desktop
	mv -f $(ETC)/$(KIOSK) $(ETC)/$(KIOSK).makesave

clean:
	sed -i s#$(PREFIX)#/usr/share#g {source/*,data/$(TARGET).desktop}
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g {source/*,data/$(TARGET).desktop}
