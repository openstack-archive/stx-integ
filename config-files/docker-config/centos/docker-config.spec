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
install -d %{buildroot}%{_datadir}/starlingx
install -D -m644 %{SOURCE1} %{buildroot}%{_datadir}/starlingx/docker-pmond.conf
install -D -m644 %{SOURCE2} %{buildroot}%{_datadir}/starlingx/docker-stx-override.conf
install -d -m 0755 %{buildroot}/%{_sysconfdir}/systemd/system/docker.service.d

%post
if [ $1 -eq 1 ] ; then
	ln -s %{_datadir}/starlingx/docker-stx-override.conf %{_sysconfdir}/systemd/system/docker.service.d/docker-stx-override.conf
	ln -s %{_datadir}/starlingx/docker-pmond.conf %{_sysconfdir}/pmon.d/docker.conf
fi

%preun

%postun

%files
%defattr(-,root,root)
%license ../SOURCES/LICENSE
%{_datadir}/starlingx/docker-pmond.conf
%{_datadir}/starlingx/docker-stx-override.conf
%dir %{_sysconfdir}/systemd/system/docker.service.d