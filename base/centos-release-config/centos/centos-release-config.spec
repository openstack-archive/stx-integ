Summary: centos-release-config
Name: centos-release-config
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: StarlingX
URL: unknown
BuildArch: noarch
Source: %name-%version.tar.gz

Requires: centos-release
Summary: package StarlingX configuration files of centos-release to system folder.

%description
package StarlingX configuration files of centos-release to system folder.

%prep
%setup

%build

%install
# Overwrite default issue files with cgcs related files.
install -d %{buildroot}/usr/share/starlingx
install -m 0644 issue %{buildroot}/usr/share/starlingx/stx.issue
install -m 0644 issue.net %{buildroot}/usr/share/starlingx/stx.issue.net
sed -i -e "s/xxxPLATFORM_RELEASExxx/%{platform_release}/g" \
    %{buildroot}/usr/share/starlingx/stx.issue \
    %{buildroot}/usr/share/starlingx/stx.issue.net

%post
if [ $1 -eq 1 ] ; then
        # Initial installation
        cp -f /usr/share/starlingx/stx.issue /etc/issue
        cp -f /usr/share/starlingx/stx.issue.net /etc/issue.net
        chmod 644 /etc/issue
        chmod 644 /etc/issue.net
fi
%files
%defattr(-,root,root,-)
/usr/share/starlingx/stx.issue
/usr/share/starlingx/stx.issue.net
