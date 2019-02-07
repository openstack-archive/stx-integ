Summary: StarlingX Docker Configuration File
Name: docker-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: config-files
Packager: StarlingX
URL: unknown

Source0: LICENSE
Source1: docker-pmond.conf
Source2: docker-stx-override.conf

BuildArch: noarch
Requires: docker-ce

%define debug_package %{nil}

%description
StarlingX docker configuration file

%install
install -d -m 0755 %{buildroot}/%{_sysconfdir}/pmon.d
install -D -m644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pmon.d/docker.conf
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/system/docker.service.d
install -D -m644 %{SOURCE2} %{buildroot}%{_sysconfdir}/systemd/system/docker.service.d/docker-stx-override.conf

%files
%defattr(-,root,root)
%license ../SOURCES/LICENSE
%dir %{_sysconfdir}/systemd/system/docker.service.d
%dir %{_sysconfdir}/pmon.d
%{_sysconfdir}/pmon.d/docker.conf
%{_sysconfdir}/systemd/system/docker.service.d/docker-stx-override.conf

