%if "%{?_tis_build_type}" == "rt"
%define bt_ext -rt
%else
%undefine bt_ext
%endif

# Define the kmod package name here.
%define kmod_name e1000e

Name:    %{kmod_name}-kmod%{?bt_ext}
Version: 3.4.2.1
Release: 0%{?_tis_dist}.%{tis_patch_ver}
Group:   System Environment/Kernel
License: GPLv2
Summary: %{kmod_name}%{?bt_ext} kernel module(s)
URL:     http://www.intel.com/

BuildRequires: kernel%{?bt_ext}-devel, redhat-rpm-config, perl, openssl
ExclusiveArch: x86_64

# Sources.
Source0:  %{kmod_name}-%{version}.tar.gz
Source5:  GPL-v2.0.txt
Source11: modules-load.conf

%define kversion %(rpm -q kernel%{?bt_ext}-devel | sort --version-sort | tail -1 | sed 's/kernel%{?bt_ext}-devel-//')

%package       -n kmod-e1000e%{?bt_ext}
Summary:          e1000e kernel module(s)
Group:            System Environment/Kernel
%global _use_internal_dependency_generator 0
Provides:         kernel-modules >= %{kversion}
Provides:         e1000e-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires(post):   /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod

%description   -n kmod-e1000e%{?bt_ext}
This package provides the e1000e kernel module(s) built
for the Linux kernel using the %{_target_cpu} family of processors.

%post          -n kmod-e1000e%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find /lib/modules/%{kversion}/extra/e1000e | grep '\.ko$') )
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --add-modules
fi
echo "Done."

%preun         -n kmod-e1000e%{?bt_ext}
rpm -ql kmod-e1000e%{?bt_ext}-%{version}-%{release}.x86_64 | grep '\.ko$' > /var/run/rpm-kmod-e1000e%{?bt_ext}-modules

%postun        -n kmod-e1000e%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat /var/run/rpm-kmod-e1000e%{?bt_ext}-modules) )
rm /var/run/rpm-kmod-e1000e%{?bt_ext}-modules
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --remove-modules
fi
echo "Done."

%files         -n kmod-e1000e%{?bt_ext}
%defattr(644,root,root,755)
/lib/modules/%{kversion}/
%config(noreplace)/etc/depmod.d/kmod-e1000e.conf
%doc /usr/share/doc/kmod-e1000e-%{version}/
%doc /usr/share/man/man7/
%{_sysconfdir}/modules-load.d/e1000e.conf

# Disable the building of the debug package(s).
%define debug_package %{nil}

%description
This package provides the %{kmod_name} kernel module(s).
It is built to depend upon the specific ABI provided by a range of releases
of the same variant of the Linux kernel and not on any one specific build.

%prep
%autosetup -p 1 -n %{kmod_name}-%{version}
%{__gzip} %{kmod_name}.7
echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

%build
pushd src >/dev/null
%{__make} KSRC=%{_usrsrc}/kernels/%{kversion}
popd >/dev/null

%install
%{__install} -d %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} src/%{kmod_name}.ko %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} -d %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} -d %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} %{SOURCE5} %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} pci.updates %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} README %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} -d %{buildroot}%{_mandir}/man7/
%{__install} %{kmod_name}.7.gz %{buildroot}%{_mandir}/man7/
%{__install} -d %{buildroot}%{_sysconfdir}/modules-load.d
%{__install} -m 644 %{SOURCE11} %{buildroot}%{_sysconfdir}/modules-load.d/e1000e.conf

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
%{__rm} -rf %{buildroot}

%changelog
* Fri Feb 24 2017 Matt Peters <matt.peters@windriver.com> 3.3.5.3
- Initial RPM package

