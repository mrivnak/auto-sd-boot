install:
	install -d -m 755 $(DESTDIR)/usr/share/systemd-boot-populate
	install -d -m 755 $(DESTDIR)/usr/share/systemd-boot-populate/templates
	install -m 644 src/systemd-boot-populate.py $(DESTDIR)/usr/share/systemd-boot-populate/
	install -m 644 src/templates/entry.conf $(DESTDIR)/usr/share/systemd-boot-populate/templates/
	install -m 644 src/templates/loader.conf $(DESTDIR)/usr/share/systemd-boot-populate/templates/
	install -m 644 systemd-boot-populate.toml $(DESTDIR)/etc/
	echo "#!/bin/sh" > $(DESTDIR)/usr/bin/systemd-boot-populate
	echo "python3 /usr/share/systemd-boot-populate/systemd-boot-populate.py" >> $(DESTDIR)/usr/bin/systemd-boot-populate
	chmod 700 $(DESTDIR)/usr/bin/systemd-boot-populate
