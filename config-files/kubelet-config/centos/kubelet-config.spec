Summary: StarlingX kubelet Configuration File
Name: kubelet-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: config-files
Packager: StarlingX
URL: unknown

Source0: LICENSE
Source1: kubelet-pmond.conf
Source2: kubelet-stx-override.conf

BuildArch: noarch
Requires: kubernetes

%define debug_package %{nil}

%description
StarlingX kubelet configuration file

%install
install -d %{buildroot}%{_datadir}/starlingx
install -D -m644 %{SOURCE1} %{buildroot}%{_datadir}/starlingx/kubelet-pmond.conf
install -D -m644 %{SOURCE2} %{buildroot}%{_datadir}/starlingx/kubelet-stx-override.conf

%post

%preun

%postun

%files
%defattr(-,root,root)
%license ../SOURCES/LICENSE
%{_datadir}/starlingx/kubelet-pmond.conf
%{_datadir}/starlingx/kubelet-stx-override.conf
