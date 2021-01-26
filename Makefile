#
# Global Settings
#

INSTALL = install
DST_DIR = $(HOME)/.config/casper

#
# Targets
#

all:
	@echo "Nothing to do"

install:
	$(INSTALL) -m0644 -D casper.py $(DST_DIR)/casper.py
	$(INSTALL) -m0644 -D default.config $(DST_DIR)/default.config
	$(INSTALL) -m0644 -D layout.json $(DST_DIR)/layout.json
	$(INSTALL) -m0755 -D launch.sh $(DST_DIR)/launch.sh

uninstall:
	rm $(DST_DIR)/casper.py
	rm $(DST_DIR)/default.config
	rm $(DST_DIR)/layout.json
	rm $(DST_DIR)/launch.sh

.PHONY: all install uninstall
