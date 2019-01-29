Summary: StarlingX Sudo Configuration File
Name: sudo-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: StarlingX
URL: unknown

Source0: wrs.sudo
Source1: LICENSE
Source2: sudo.conf
Source3: schema.OpenLDAP
Source4: sudoers2ldif

%define WRSROOT_P cBglipPpsKwBQ

%description
StarlingX sudo configuration file

%install
install -d %{buildroot}/%{_sysconfdir}/sudoers.d
install -m 440 %{SOURCE0}  %{buildroot}/%{_sysconfdir}/sudoers.d/wrs

install -d %{buildroot}%{_datadir}/starlingx
install -p -c -m 0640 %{SOURCE2} %{buildroot}%{_datadir}/starlingx/sudo.conf

install -d %{buildroot}/%{_sysconfdir}/openldap/schema/
install -m 644 %{SOURCE3}  %{buildroot}/%{_sysconfdir}/openldap/schema/sudo.schema

install -d %{buildroot}%{_datadir}/sudo
install -m 700 %{SOURCE4} %{buildroot}%{_datadir}/sudo/sudoers2ldif

%pre
getent group wrs >/dev/null || groupadd -r wrs
getent group wrs_protected >/dev/null || groupadd -f -g 345 wrs_protected
getent passwd wrsroot > /dev/null || \
useradd -m -g wrs -G root,wrs_protected \
    -d /home/wrsroot -p %{WRSROOT_P} \
    -s /bin/sh wrsroot 2> /dev/null || :

%post
if [ $1 -eq 1 ] ; then
cp -f %{_datadir}/starlingx/sudo.conf %{_sysconfdir}/sudo.conf
fi

%files
%license ../SOURCES/LICENSE
%config(noreplace) %{_sysconfdir}/sudoers.d/wrs
%{_datadir}/starlingx/sudo.conf
%{_sysconfdir}/openldap/schema/sudo.schema
%{_datadir}/sudo/sudoers2ldif
