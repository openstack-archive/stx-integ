Summary: StarlingX logrotate Configuration File
Name: logrotate-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: config-files
Packager: StarlingX
URL: unknown

Source0: LICENSE
Source1: logrotate-cron.d
Source2: logrotate.conf

BuildArch: noarch
Requires: logrotate

%define debug_package %{nil}

%description
StarlingX logrotate configuration file

%install
mkdir -p %{buildroot}%{_sysconfdir}/cron.d
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/cron.d/logrotate
install -d %{buildroot}%{_datadir}/starlingx
install -m 644 %{SOURCE2} %{buildroot}%{_datadir}/starlingx/logrotate.conf

%post
if [ $1 -eq 1 ] ; then
    cp -f %{_datadir}/starlingx/logrotate.conf %{_sysconfdir}/logrotate.conf
    chmod 644 %{_sysconfdir}/logrotate.conf
    mv %{_sysconfdir}/cron.daily/logrotate %{_sysconfdir}/logrotate.cron
    chmod 700 %{_sysconfdir}/logrotate.cron
fi

%files
%defattr(-,root,root)
%license ../SOURCES/LICENSE
%{_sysconfdir}/cron.d/logrotate
%{_datadir}/starlingx/logrotate.conf
