TARGET = connector
PREFIX_BIN = /usr/local/bin
PREFIX = /usr/local/share
BASE = $(PREFIX)/$(TARGET)
MAN = $(PREFIX)/man/man1

.PHONY: help install uninstall clean

help:
	@echo "Запустите make с одной из необходимых ролей:"
	@echo "... help (по умолчанию, показать данную справку)"
	@echo "... install (установка программы, требует sudo)"
	@echo "... uninstall (удаление программы, требует sudo)"
	@echo "... clean (сброс изменений в исходниках)"

install:
	sed -i s#/usr/share#$(PREFIX)#g source/*
	sed -i s#/usr/bin/$(TARGET)#$(PREFIX_BIN)/$(TARGET)#g source/*
	install source/$(TARGET) $(PREFIX_BIN)
	install data/$(TARGET).desktop $(PREFIX)/applications
	mkdir -p $(BASE)/data/
	install data/*.png data/*.glade $(BASE)/data/
	install source/*.py $(BASE)
	mkdir -p $(MAN)
	install data/$(TARGET).man $(MAN)/$(TARGET).1

uninstall:
	rm -f $(PREFIX_BIN)/$(TARGET)
	rm -rf $(BASE)
	rm -f $(MAN)/$(TARGET).1
	rm -f $(PREFIX)/applications/$(TARGET).desktop

clean:
	sed -i s#$(PREFIX)#/usr/share#g source/*
	sed -i s#$(PREFIX_BIN)/$(TARGET)#/usr/bin/$(TARGET)#g source/*
