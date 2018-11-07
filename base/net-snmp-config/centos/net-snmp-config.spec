Summary: net-snmp-config
Name: net-snmp-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: StarlingX
URL: unknown
BuildArch: noarch
Source: %name-%version.tar.gz

Requires: net-snmp
Summary: package StarlingX configuration files of net-snmp to system folder.

%description
package StarlingX configuration files of net-snmp to system folder.

%prep
%setup

%build

%install
%{__install} -d %{buildroot}%{_datadir}/starlingx
%{__install} -d %{buildroot}%{_datadir}/snmp
%{__install} -d %{buildroot}%{_initrddir}
%{__install} -d  %{buildroot}%{_sysconfdir}/systemd/system

%{__install} -m 644 snmpd.conf.cgcs   %{buildroot}%{_datadir}/starlingx/snmpd.conf.cgcs
%{__install} -m 755 snmpd.cgcs        %{buildroot}%{_initrddir}/snmpd
%{__install} -m 660 snmp.conf.cgcs    %{buildroot}%{_datadir}/snmp/snmp.conf
%{__install} -m 644 snmpd.service     %{buildroot}%{_sysconfdir}/systemd/system

%post
if [ $1 -eq 1 ] ; then
        # Initial installation
        cp -f %{_datadir}/starlingx/snmpd.conf.cgcs %{_sysconfdir}/snmp/snmpd.conf
        chmod 640 %{_sysconfdir}/snmp/snmpd.conf
        chmod 640 %{_sysconfdir}/snmp/snmptrapd.conf
fi
/bin/systemctl disable haproxy.service

%files
%{_datadir}/starlingx/snmpd.conf.cgcs
%{_initrddir}/snmpd
%config(noreplace) %attr(0660,snmpd,snmpd) %{_datadir}/snmp/snmp.conf
%{_sysconfdir}/systemd/system/snmpd.service

