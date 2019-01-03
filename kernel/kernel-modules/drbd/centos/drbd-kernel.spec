%if "%{?_tis_build_type}" == "rt"
%define bt_ext -rt
%else
%undefine bt_ext
%endif

# Define the kmod package name here.
%define kmod_name drbd

Name: drbd-kernel%{?bt_ext}
Summary: Kernel driver for DRBD
Version: 9.0.16
%define upstream_release 1
Release: %{upstream_release}%{?_tis_dist}.%{tis_patch_ver}

# always require a suitable userland
Requires: drbd-utils >= 9.2.0

%global tarball_version %(echo "%{version}-%{?upstream_release}" | sed -e "s,%{?dist}$,,")
Source: http://oss.linbit.com/drbd/drbd-%{tarball_version}.tar.gz
License: GPLv2+
Group: System Environment/Kernel
URL: http://www.drbd.org/
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: kernel%{?bt_ext}-devel, redhat-rpm-config, perl, openssl
ExclusiveArch: x86_64


%define kversion %(rpm -q kernel%{?bt_ext}-devel | sort --version-sort | tail -1 | sed 's/kernel%{?bt_ext}-devel-//')


%global _use_internal_dependency_generator 0
Provides:         kernel-modules >= %{kversion}
Provides:         drbd-kernel = %{?epoch:%{epoch}:}%{version}-%{release}
Requires(post):   /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod
BuildRequires: kernel%{?bt_ext}-devel

%description
This module is the kernel-dependent driver for DRBD.  This is split out so
that multiple kernel driver versions can be installed, one for each
installed kernel.

%package       -n kmod-drbd%{?bt_ext}
Summary:          drbd kernel module(s)
%description -n kmod-drbd%{?bt_ext}
This module is the kernel-dependent driver for DRBD.  This is split out so
that multiple kernel driver versions can be installed, one for each
installed kernel.

%post          -n kmod-drbd%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find /lib/modules/%{kversion}/extra/drbd | grep '\.ko$') )
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --add-modules
fi
echo "Done."
%preun         -n kmod-drbd%{?bt_ext}
rpm -ql kmod-drbd%{?bt_ext}-%{version}-%{release}.x86_64 | grep '\.ko$' > /var/run/rpm-kmod-drbd%{?bt_ext}-modules
%postun        -n kmod-drbd%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat /var/run/rpm-kmod-drbd%{?bt_ext}-modules) )
rm /var/run/rpm-kmod-drbd%{?bt_ext}-modules
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --remove-modules
fi
echo "Done."
%files         -n kmod-drbd%{?bt_ext}
%defattr(644,root,root,755)
/lib/modules/%{kversion}/
%config(noreplace)/etc/depmod.d/drbd.conf
%doc /usr/share/doc/kmod-drbd-%{version}/


# Disable the building of the debug package(s).
%define debug_package %{nil}

%prep
%setup -q -n drbd-%{tarball_version}

%build
rm -rf obj
mkdir obj
ln -s ../drbd-headers obj/
cp -r drbd obj/default
make -C obj/default %{_smp_mflags} all KDIR=/usr/src/kernels/%{kversion}

%install
pwd
%{__install} -d %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} obj/default/%{kmod_name}.ko %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} -d %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} -d %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} ChangeLog %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} COPYING %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
mv obj/default/.kernel.config.gz obj/k-config-$kernelrelease.gz
%{__install} obj/k-config-$kernelrelease.gz %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/

echo "override drbd * weak-updates" > %{buildroot}%{_sysconfdir}/depmod.d/drbd.conf 

# Strip the modules(s).
find %{buildroot} -type f -name \*.ko -exec %{__strip} --strip-debug \{\} \;

# Always Sign the modules(s).
# If the module signing keys are not defined, define them here.
%{!?privkey: %define privkey /usr/src/kernels/%{kversion}/signing_key.priv}
%{!?pubkey: %define pubkey /usr/src/kernels/%{kversion}/signing_key.x509}
for module in $(find %{buildroot} -type f -name \*.ko);
do %{__perl} /usr/src/kernels/%{kversion}/scripts/sign-file \
    sha256 %{privkey} %{pubkey} $module;
done

%clean
rm -rf %{buildroot}

%changelog
* Thu Oct 25 2018 Philipp Reisner <phil@linbit.com> - 9.0.16-1
- New upstream release.

* Tue Aug 14 2018 Philipp Reisner <phil@linbit.com> - 9.0.15-1
- New upstream release.

* Tue May 01 2018 Lars Ellenberg <lars@linbit.com> - 9.0.14-1
- New upstream release.

* Tue Apr 17 2018 Philipp Reisner <phil@linbit.com> - 9.0.13-1
- New upstream release.

* Mon Jan 22 2018 Philipp Reisner <phil@linbit.com> - 9.0.12-1
- New upstream release.

* Tue Jan 09 2018 Roland Kammerer <roland.kammerer@linbit.com> - 9.0.11-1
- New upstream release.

* Fri Dec 22 2017 Roland Kammerer <roland.kammerer@linbit.com> - 9.0.10-1
- New upstream release.

* Thu Aug 31 2017 Philipp Reisner <phil@linbit.com> - 9.0.9-1
- New upstream release.

* Mon Jun 19 2017 Philipp Reisner <phil@linbit.com> - 9.0.8-1
- New upstream release.

* Fri Mar 31 2017 Philipp Reisner <phil@linbit.com> - 9.0.7-1
- New upstream release.

* Fri Dec 23 2016 Philipp Reisner <phil@linbit.com> - 9.0.6-1
- New upstream release.

* Thu Oct 20 2016 Philipp Reisner <phil@linbit.com> - 9.0.5-1
- New upstream release.

* Tue Sep 06 2016 Philipp Reisner <phil@linbit.com> - 9.0.4-1
- New upstream release.

* Thu Jul 14 2016 Philipp Reisner <phil@linbit.com> - 9.0.3-1
- New upstream release.

* Tue Apr 19 2016 Philipp Reisner <phil@linbit.com> - 9.0.2-1
- New upstream release.

* Tue Feb 02 2016 Philipp Reisner <phil@linbit.com> - 9.0.1-1
- New upstream release.

* Tue Jul 28 2015 Lars Ellenberg <lars@linbit.com> - 9.0.0-3
- Fixes for the RDMA transport
- Fixes for 8.4 compatibility
- Rebuild after compat and build system fixes

* Tue Jun 16 2015 Philipp Reisner <phil@linbit.com> - 9.0.0-1
- New upstream release.

* Mon Jul 18 2011 Philipp Reisner <phil@linbit.com> - 8.4.0-1
- New upstream release.

* Fri Jan 28 2011 Philipp Reisner <phil@linbit.com> - 8.3.10-1
- New upstream release.

* Thu Nov 25 2010 Andreas Gruenbacher <agruen@linbit.com> - 8.3.9-1
- Convert to a Kernel Module Package.
