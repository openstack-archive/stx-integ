# -*- rpm-spec -*-

# This spec file assumes you are building on a Fedora or RHEL version
# that's still supported by the vendor: that means Fedora 23 or newer,
# or RHEL 6 or newer. It may need some tweaks for other distros.
# If neither fedora nor rhel was defined, try to guess them from dist
%if (0%{?fedora} && 0%{?fedora} >= 23) || (0%{?rhel} && 0%{?rhel} >= 6)
    %define supported_platform 1
%else
    %define supported_platform 0
%endif

# Default to skipping autoreconf.  Distros can change just this one line
# (or provide a command-line override) if they backport any patches that
# touch configure.ac or Makefile.am.
# Always run autoreconf
%{!?enable_autotools:%global enable_autotools 1}

# STX: Custom build config.  Based on the R2/bitbake configure line.
%define _without_esx 1
%define _without_hyperv 1
%define _without_libxl 1
%define _without_vbox 1
%define _without_vmware 1
%define _without_xen 1
%define _without_xenapi 1
%define _without_phyp 1
%define _without_openvz 1
%define _without_numad 1
%define _without_capng 1
%define _without_polkit 1
%define _without_sasl 1
%define _without_dtrace 1
%define _without_avahi 1

# The hypervisor drivers that run in libvirtd
%define with_xen           0%{!?_without_xen:1}
%define with_qemu          0%{!?_without_qemu:1}
%define with_lxc           0%{!?_without_lxc:1}
%define with_uml           0%{!?_without_uml:1}
%define with_libxl         0%{!?_without_libxl:1}
%define with_vbox          0%{!?_without_vbox:1}

%define with_qemu_tcg      %{with_qemu}

%define qemu_kvm_arches %{ix86} x86_64

%if 0%{?fedora}
    %define qemu_kvm_arches %{ix86} x86_64 %{power64} s390x %{arm} aarch64
%endif

%if 0%{?rhel}
    %define with_qemu_tcg 0
    %define qemu_kvm_arches x86_64
    %if 0%{?rhel} >= 7
        %define qemu_kvm_arches x86_64 %{power64} aarch64
    %endif
%endif

%ifarch %{qemu_kvm_arches}
    %define with_qemu_kvm      %{with_qemu}
%else
    %define with_qemu_kvm      0
%endif

%if ! %{with_qemu_tcg} && ! %{with_qemu_kvm}
    %define with_qemu 0
%endif

# Then the hypervisor drivers that run outside libvirtd, in libvirt.so
%define with_openvz        0%{!?_without_openvz:1}
%define with_vmware        0%{!?_without_vmware:1}
%define with_phyp          0%{!?_without_phyp:1}
%define with_esx           0%{!?_without_esx:1}
%define with_hyperv        0%{!?_without_hyperv:1}

# Then the secondary host drivers, which run inside libvirtd
%if 0%{?fedora} || 0%{?rhel} >= 7
    %define with_storage_rbd      0%{!?_without_storage_rbd:1}
%else
    %define with_storage_rbd      0
%endif
%if 0%{?fedora}
    %define with_storage_sheepdog 0%{!?_without_storage_sheepdog:1}
%else
    %define with_storage_sheepdog 0
%endif
%define with_storage_gluster 0%{!?_without_storage_gluster:1}
%define with_numactl          0%{!?_without_numactl:1}

# A few optional bits off by default, we enable later
%define with_fuse          0%{!?_without_fuse:0}
%define with_cgconfig      0%{!?_without_cgconfig:0}
%define with_sanlock       0%{!?_without_sanlock:0}
%define with_systemd       0%{!?_without_systemd:0}
%define with_numad         0%{!?_without_numad:0}
%define with_firewalld     0%{!?_without_firewalld:0}
%define with_libssh2       0%{!?_without_libssh2:0}
%define with_wireshark     0%{!?_without_wireshark:0}
%define with_libssh        0%{!?_without_libssh:0}
%define with_bash_completion  0%{!?_without_bash_completion:0}
%define with_pm_utils      1

# Finally set the OS / architecture specific special cases

# Xen is available only on i386 x86_64 ia64
%ifnarch %{ix86} x86_64 ia64
    %define with_xen 0
    %define with_libxl 0
%endif

# vbox is available only on i386 x86_64
%ifnarch %{ix86} x86_64
    %define with_vbox 0
%endif

# Numactl is not available on s390[x] and ARM
%ifarch s390 s390x %{arm}
    %define with_numactl 0
%endif

# libgfapi is built only on x86_64 on rhel
%ifnarch x86_64
    %if 0%{?rhel}
        %define with_storage_gluster 0
    %endif
%endif

# librados and librbd are built only on x86_64 on rhel
%ifnarch x86_64
    %if 0%{?rhel} >= 7
        %define with_storage_rbd 0
    %endif
%endif

# RHEL doesn't ship OpenVZ, VBox, UML, PowerHypervisor,
# VMware, libxenserver (xenapi), libxenlight (Xen 4.1 and newer),
# or HyperV.
%if 0%{?rhel}
    %define with_openvz 0
    %define with_vbox 0
    %define with_uml 0
    %define with_phyp 0
    %define with_vmware 0
    %define with_xenapi 0
    %define with_libxl 0
    %define with_hyperv 0
    %define with_vz 0
%endif

# Fedora 17 / RHEL-7 are first where we use systemd. Although earlier
# Fedora has systemd, libvirt still used sysvinit there.
%if 0%{?fedora} || 0%{?rhel} >= 7
    %define with_systemd 1
    %define with_pm_utils 0
%endif

# Fedora 18 / RHEL-7 are first where firewalld support is enabled
%if 0%{?fedora} || 0%{?rhel} >= 7
    %define with_firewalld 1
%endif

# RHEL-6 stopped including Xen on all archs.
%if 0%{?rhel}
    %define with_xen 0
%endif

# fuse is used to provide virtualized /proc for LXC
%if 0%{?fedora} || 0%{?rhel} >= 7
    %define with_fuse      0%{!?_without_fuse:1}
%endif

# Enable sanlock library for lock management with QEMU
# Sanlock is available only on arches where kvm is available for RHEL
%if 0%{?fedora}
    %define with_sanlock 0%{!?_without_sanlock:1}
%endif
%if 0%{?rhel}
    %ifarch %{qemu_kvm_arches}
        %define with_sanlock 0%{!?_without_sanlock:1}
    %endif
%endif

# Enable libssh2 transport for new enough distros
%if 0%{?fedora}
    %define with_libssh2 0%{!?_without_libssh2:1}
%endif

# Enable wireshark plugins for all distros shipping libvirt 1.2.2 or newer
%if 0%{?fedora}
    %define with_wireshark 0%{!?_without_wireshark:1}
%endif

# Enable libssh transport for new enough distros
%if 0%{?fedora}
    %define with_libssh 0%{!?_without_libssh:1}
%endif

%define with_bash_completion  0%{!?_without_bash_completion:1}

%if %{with_qemu} || %{with_lxc} || %{with_uml}
# numad is used to manage the CPU and memory placement dynamically,
# it's not available on s390[x] and ARM.
    %ifnarch s390 s390x %{arm}
        %define with_numad    0%{!?_without_numad:1}
    %endif
%endif

# Pull in cgroups config system
%if %{with_qemu} || %{with_lxc}
    %define with_cgconfig 0%{!?_without_cgconfig:1}
%endif

# Force QEMU to run as non-root
%define qemu_user  qemu
%define qemu_group  qemu


%if 0%{?fedora} || 0%{?rhel} >= 7
    %define with_systemd_macros 1
%else
    %define with_systemd_macros 0
%endif


# RHEL releases provide stable tool chains and so it is safe to turn
# compiler warning into errors without being worried about frequent
# changes in reported warnings
%if 0%{?rhel}
    %define enable_werror --enable-werror
%else
    %define enable_werror --disable-werror
%endif

%if 0%{?fedora} >= 25
    %define tls_priority "@LIBVIRT,SYSTEM"
%else
    %if 0%{?fedora}
        %define tls_priority "@SYSTEM"
    %else
        %define tls_priority "NORMAL"
    %endif
%endif


Summary: Library providing a simple virtualization API
Name: libvirt
Version: 4.7.0
Release: 1%{?_tis_dist}.%{tis_patch_ver}
License: LGPLv2+
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
URL: https://libvirt.org/

%if %(echo %{version} | grep -q "\.0$"; echo $?) == 1
    %define mainturl stable_updates/
%endif
Source0: http://libvirt.org/sources/%{?mainturl}libvirt-%{version}.tar.gz
#Source1: symlinks

# STX
Source2: libvirt.logrotate
Source3: libvirt.lxc
Source4: libvirt.qemu
Source5: libvirt.uml
Source6: gnulib-ffc927e.tar.gz
Source7: keycodemapdb-16e5b07.tar.gz
Source8: qemu

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-config-network = %{version}-%{release}
Requires: libvirt-daemon-config-nwfilter = %{version}-%{release}
%if %{with_libxl}
Requires: libvirt-daemon-driver-libxl = %{version}-%{release}
%endif
%if %{with_lxc}
Requires: libvirt-daemon-driver-lxc = %{version}-%{release}
%endif
%if %{with_qemu}
Requires: libvirt-daemon-driver-qemu = %{version}-%{release}
%endif
%if %{with_uml}
Requires: libvirt-daemon-driver-uml = %{version}-%{release}
%endif
%if %{with_xen}
Requires: libvirt-daemon-driver-xen = %{version}-%{release}
%endif
%if %{with_vbox}
Requires: libvirt-daemon-driver-vbox = %{version}-%{release}
%endif
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}

Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-client = %{version}-%{release}
Requires: libvirt-libs = %{version}-%{release}

# All build-time requirements. Run-time requirements are
# listed against each sub-RPM
%if 0%{?enable_autotools}
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: gettext-devel
BuildRequires: libtool
BuildRequires: /usr/bin/pod2man
%endif
BuildRequires: git
BuildRequires: perl
BuildRequires: python
%if %{with_systemd}
BuildRequires: systemd-units
%endif
%if %{with_xen} || %{with_libxl}
BuildRequires: xen-devel
%endif
BuildRequires: libxml2-devel
BuildRequires: xhtml1-dtds
BuildRequires: libxslt
BuildRequires: readline-devel
%if %{with_bash_completion}
BuildRequires: bash-completion >= 2.0
%endif
BuildRequires: ncurses-devel
BuildRequires: gettext
BuildRequires: libtasn1-devel
%if (0%{?rhel} && 0%{?rhel} < 7)
BuildRequires: libgcrypt-devel
%endif
BuildRequires: gnutls-devel
BuildRequires: libattr-devel
# For pool-build probing for existing pools
BuildRequires: libblkid-devel >= 2.17
# for augparse, optionally used in testing
BuildRequires: augeas
%if 0%{?fedora} || 0%{?rhel} >= 7
BuildRequires: systemd-devel >= 185
%else
BuildRequires: libudev-devel >= 145
%endif
BuildRequires: libpciaccess-devel >= 0.10.9
BuildRequires: yajl-devel
%if %{with_sanlock}
BuildRequires: sanlock-devel >= 2.4
%endif
BuildRequires: libpcap-devel
%if 0%{?rhel} && 0%{?rhel} < 7
BuildRequires: libnl-devel
%else
BuildRequires: libnl3-devel
%endif
BuildRequires: avahi-devel
BuildRequires: libselinux-devel
BuildRequires: dnsmasq >= 2.41
BuildRequires: iptables
%if 0%{?rhel} && 0%{?rhel} < 7
BuildRequires: iptables-ipv6
%endif
BuildRequires: radvd
BuildRequires: ebtables
BuildRequires: module-init-tools
BuildRequires: cyrus-sasl-devel
%if 0%{?fedora} || 0%{?rhel} >= 7
# F22 polkit-devel doesn't pull in polkit anymore, which we need for pkcheck
BuildRequires: polkit >= 0.112
BuildRequires: polkit-devel >= 0.112
%else
BuildRequires: polkit-devel >= 0.93
%endif
# For mount/umount in FS driver
BuildRequires: util-linux
%if %{with_qemu}
# For managing ACLs
BuildRequires: libacl-devel
# From QEMU RPMs
BuildRequires: /usr/bin/qemu-img
%else
    %if %{with_xen}
# From Xen RPMs
BuildRequires: /usr/sbin/qcow-create
    %endif
%endif
# For LVM drivers
BuildRequires: lvm2
# For ISCSI driver
BuildRequires: iscsi-initiator-utils
# For disk driver
BuildRequires: parted-devel
# For Multipath support
BuildRequires: device-mapper-devel
%if %{with_storage_rbd}
    %if 0%{?fedora} || 0%{?rhel} >= 7
BuildRequires: librados2-devel
BuildRequires: librbd1-devel
    %else
BuildRequires: ceph-devel
    %endif
%endif
%if %{with_storage_gluster}
BuildRequires: glusterfs-api-devel >= 3.4.1
BuildRequires: glusterfs-devel >= 3.4.1
%endif
%if %{with_storage_sheepdog}
BuildRequires: sheepdog
%endif
%if %{with_numactl}
# For QEMU/LXC numa info
BuildRequires: numactl-devel
%endif
BuildRequires: libcap-ng-devel >= 0.5.0
%if %{with_fuse}
BuildRequires: fuse-devel >= 2.8.6
%endif
%if %{with_phyp} || %{with_libssh2}
BuildRequires: libssh2-devel >= 1.3.0
%endif

%if 0%{?fedora} || 0%{?rhel} >= 7
BuildRequires: netcf-devel >= 0.2.2
%else
BuildRequires: netcf-devel >= 0.1.8
%endif
%if %{with_esx}
BuildRequires: libcurl-devel
%endif
%if %{with_hyperv}
BuildRequires: libwsman-devel >= 2.2.3
%endif
BuildRequires: audit-libs-devel
# we need /usr/sbin/dtrace
BuildRequires: systemtap-sdt-devel

# For mount/umount in FS driver
BuildRequires: util-linux
# For showmount in FS driver (netfs discovery)
BuildRequires: nfs-utils

# Communication with the firewall and polkit daemons use DBus
BuildRequires: dbus-devel

# Fedora build root suckage
BuildRequires: gawk

# For storage wiping with different algorithms
BuildRequires: scrub

%if %{with_numad}
BuildRequires: numad
%endif

%if %{with_wireshark}
    %if 0%{fedora} >= 24
BuildRequires: wireshark-devel >= 2.1.0
    %else
BuildRequires: wireshark-devel >= 1.12.1
    %endif
%endif

%if %{with_libssh}
BuildRequires: libssh-devel >= 0.7.0
%endif

# STX: For generating configure
BuildRequires: gnulib
# STX: Needed by bootstrap
BuildRequires: perl-XML-XPath

Provides: bundled(gnulib)

%description
Libvirt is a C toolkit to interact with the virtualization capabilities
of recent versions of Linux (and other OSes). The main package includes
the libvirtd server exporting the virtualization support.

%package docs
Summary: API reference and website documentation
Group: Development/Libraries

%description docs
Includes the API reference for the libvirt C library, and a complete
copy of the libvirt.org website documentation.

%package daemon
Summary: Server side daemon and supporting files for libvirt library
Group: Development/Libraries

# All runtime requirements for the libvirt package (runtime requrements
# for subpackages are listed later in those subpackages)

# The client side, i.e. shared libs are in a subpackage
Requires: %{name}-libs = %{version}-%{release}

# for modprobe of pci devices
Requires: module-init-tools
# for /sbin/ip & /sbin/tc
Requires: iproute
Requires: avahi-libs
%if 0%{?fedora} || 0%{?rhel} >= 7
Requires: polkit >= 0.112
%else
Requires: polkit >= 0.93
%endif
%if %{with_cgconfig}
Requires: libcgroup
%endif
%ifarch %{ix86} x86_64 ia64
# For virConnectGetSysinfo
Requires: dmidecode
%endif
# For service management
%if %{with_systemd}
Requires(post): systemd-units
Requires(post): systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units
%endif
%if %{with_numad}
Requires: numad
%endif
# libvirtd depends on 'messagebus' service
Requires: dbus
# For uid creation during pre
Requires(pre): shadow-utils

%description daemon
Server side daemon required to manage the virtualization capabilities
of recent versions of Linux. Requires a hypervisor specific sub-RPM
for specific drivers.

%package daemon-config-network
Summary: Default configuration files for the libvirtd daemon
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}

%description daemon-config-network
Default configuration files for setting up NAT based networking

%package daemon-config-nwfilter
Summary: Network filter configuration files for the libvirtd daemon
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}

%description daemon-config-nwfilter
Network filter configuration files for cleaning guest traffic

%package daemon-driver-network
Summary: Network driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
Requires: dnsmasq >= 2.41
Requires: radvd
Requires: iptables
%if 0%{?rhel} && 0%{?rhel} < 7
Requires: iptables-ipv6
%endif

%description daemon-driver-network
The network driver plugin for the libvirtd daemon, providing
an implementation of the virtual network APIs using the Linux
bridge capabilities.


%package daemon-driver-nwfilter
Summary: Nwfilter driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
Requires: iptables
%if 0%{?rhel} && 0%{?rhel} < 7
Requires: iptables-ipv6
%endif
Requires: ebtables

%description daemon-driver-nwfilter
The nwfilter driver plugin for the libvirtd daemon, providing
an implementation of the firewall APIs using the ebtables,
iptables and ip6tables capabilities


%package daemon-driver-nodedev
Summary: Nodedev driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
# needed for device enumeration
%if 0%{?fedora} || 0%{?rhel} >= 7
Requires: systemd >= 185
%else
Requires: udev >= 145
%endif

%description daemon-driver-nodedev
The nodedev driver plugin for the libvirtd daemon, providing
an implementation of the node device APIs using the udev
capabilities.


%package daemon-driver-interface
Summary: Interface driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
%if (0%{?fedora} || 0%{?rhel} >= 7)
Requires: netcf-libs >= 0.2.2
%endif

%description daemon-driver-interface
The interface driver plugin for the libvirtd daemon, providing
an implementation of the network interface APIs using the
netcf library


%package daemon-driver-secret
Summary: Secret driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}

%description daemon-driver-secret
The secret driver plugin for the libvirtd daemon, providing
an implementation of the secret key APIs.

%package daemon-driver-storage-core
Summary: Storage driver plugin including base backends for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
Requires: nfs-utils
# For mkfs
Requires: util-linux
%if %{with_qemu}
# From QEMU RPMs
Requires: /usr/bin/qemu-img
%else
    %if %{with_xen}
# From Xen RPMs
Requires: /usr/sbin/qcow-create
    %endif
%endif

%description daemon-driver-storage-core
The storage driver plugin for the libvirtd daemon, providing
an implementation of the storage APIs using files, local disks, LVM, SCSI,
iSCSI, and multipath storage.

%package daemon-driver-storage-logical
Summary: Storage driver plugin for lvm volumes
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: lvm2

%description daemon-driver-storage-logical
The storage driver backend adding implementation of the storage APIs for block
volumes using lvm.


%package daemon-driver-storage-disk
Summary: Storage driver plugin for disk
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: parted
Requires: device-mapper

%description daemon-driver-storage-disk
The storage driver backend adding implementation of the storage APIs for block
volumes using the host disks.


%package daemon-driver-storage-scsi
Summary: Storage driver plugin for local scsi devices
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}

%description daemon-driver-storage-scsi
The storage driver backend adding implementation of the storage APIs for scsi
host devices.


%package daemon-driver-storage-iscsi
Summary: Storage driver plugin for iscsi
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: iscsi-initiator-utils

%description daemon-driver-storage-iscsi
The storage driver backend adding implementation of the storage APIs for iscsi
volumes using the host iscsi stack.


%package daemon-driver-storage-mpath
Summary: Storage driver plugin for multipath volumes
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: device-mapper

%description daemon-driver-storage-mpath
The storage driver backend adding implementation of the storage APIs for
multipath storage using device mapper.


%if %{with_storage_gluster}
%package daemon-driver-storage-gluster
Summary: Storage driver plugin for gluster
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
    %if 0%{?fedora}
Requires: glusterfs-client >= 2.0.1
    %endif
    %if (0%{?fedora} || 0%{?with_storage_gluster})
Requires: /usr/sbin/gluster
    %endif

%description daemon-driver-storage-gluster
The storage driver backend adding implementation of the storage APIs for gluster
volumes using libgfapi.
%endif


%if %{with_storage_rbd}
%package daemon-driver-storage-rbd
Summary: Storage driver plugin for rbd
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}

%description daemon-driver-storage-rbd
The storage driver backend adding implementation of the storage APIs for rbd
volumes using the ceph protocol.
%endif


%if %{with_storage_sheepdog}
%package daemon-driver-storage-sheepdog
Summary: Storage driver plugin for sheepdog
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: sheepdog

%description daemon-driver-storage-sheepdog
The storage driver backend adding implementation of the storage APIs for
sheepdog volumes using.
%endif


%package daemon-driver-storage
Summary: Storage driver plugin including all backends for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-disk = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-logical = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-scsi = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-iscsi = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-mpath = %{version}-%{release}
%if %{with_storage_gluster}
Requires: libvirt-daemon-driver-storage-gluster = %{version}-%{release}
%endif
%if %{with_storage_rbd}
Requires: libvirt-daemon-driver-storage-rbd = %{version}-%{release}
%endif
%if %{with_storage_sheepdog}
Requires: libvirt-daemon-driver-storage-sheepdog = %{version}-%{release}
%endif

%description daemon-driver-storage
The storage driver plugin for the libvirtd daemon, providing
an implementation of the storage APIs using LVM, iSCSI,
parted and more.


%if %{with_qemu}
%package daemon-driver-qemu
Summary: QEMU driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
# There really is a hard cross-driver dependency here
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-storage-core = %{version}-%{release}
Requires: /usr/bin/qemu-img
# For image compression
Requires: gzip
Requires: bzip2
Requires: lzop
Requires: xz
    %if 0%{?fedora} >= 24
Requires: systemd-container
    %endif

%description daemon-driver-qemu
The qemu driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
QEMU
%endif


%if %{with_lxc}
%package daemon-driver-lxc
Summary: LXC driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}
# There really is a hard cross-driver dependency here
Requires: libvirt-daemon-driver-network = %{version}-%{release}
    %if 0%{?fedora} >= 24
Requires: systemd-container
    %endif

%description daemon-driver-lxc
The LXC driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
the Linux kernel
%endif


%if %{with_uml}
%package daemon-driver-uml
Summary: Uml driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}

%description daemon-driver-uml
The UML driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
User Mode Linux
%endif


%if %{with_xen}
%package daemon-driver-xen
Summary: Xen driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}

%description daemon-driver-xen
The Xen driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
Xen
%endif


%if %{with_vbox}
%package daemon-driver-vbox
Summary: VirtualBox driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}

%description daemon-driver-vbox
The vbox driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
VirtualBox
%endif


%if %{with_libxl}
%package daemon-driver-libxl
Summary: Libxl driver plugin for the libvirtd daemon
Group: Development/Libraries
Requires: libvirt-daemon = %{version}-%{release}

%description daemon-driver-libxl
The Libxl driver plugin for the libvirtd daemon, providing
an implementation of the hypervisor driver APIs using
Libxl
%endif



%if %{with_qemu_tcg}
%package daemon-qemu
Summary: Server side daemon & driver required to run QEMU guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-qemu = %{version}-%{release}
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}
Requires: qemu

%description daemon-qemu
Server side daemon and driver required to manage the virtualization
capabilities of the QEMU TCG emulators
%endif


%if %{with_qemu_kvm}
%package daemon-kvm
Summary: Server side daemon & driver required to run KVM guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-qemu = %{version}-%{release}
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}
Requires: qemu-kvm

%description daemon-kvm
Server side daemon and driver required to manage the virtualization
capabilities of the KVM hypervisor
%endif


%if %{with_lxc}
%package daemon-lxc
Summary: Server side daemon & driver required to run LXC guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-lxc = %{version}-%{release}
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}

%description daemon-lxc
Server side daemon and driver required to manage the virtualization
capabilities of LXC
%endif


%if %{with_uml}
%package daemon-uml
Summary: Server side daemon & driver required to run UML guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-uml = %{version}-%{release}
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}
# There are no UML kernel RPMs in Fedora/RHEL to depend on.

%description daemon-uml
Server side daemon and driver required to manage the virtualization
capabilities of UML
%endif


%if %{with_xen} || %{with_libxl}
%package daemon-xen
Summary: Server side daemon & driver required to run XEN guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
    %if %{with_xen}
Requires: libvirt-daemon-driver-xen = %{version}-%{release}
    %endif
    %if %{with_libxl}
Requires: libvirt-daemon-driver-libxl = %{version}-%{release}
    %endif
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}
Requires: xen

%description daemon-xen
Server side daemon and driver required to manage the virtualization
capabilities of XEN
%endif

%if %{with_vbox}
%package daemon-vbox
Summary: Server side daemon & driver required to run VirtualBox guests
Group: Development/Libraries

Requires: libvirt-daemon = %{version}-%{release}
Requires: libvirt-daemon-driver-vbox = %{version}-%{release}
Requires: libvirt-daemon-driver-interface = %{version}-%{release}
Requires: libvirt-daemon-driver-network = %{version}-%{release}
Requires: libvirt-daemon-driver-nodedev = %{version}-%{release}
Requires: libvirt-daemon-driver-nwfilter = %{version}-%{release}
Requires: libvirt-daemon-driver-secret = %{version}-%{release}
Requires: libvirt-daemon-driver-storage = %{version}-%{release}

%description daemon-vbox
Server side daemon and driver required to manage the virtualization
capabilities of VirtualBox
%endif

%package client
Summary: Client side utilities of the libvirt library
Group: Development/Libraries
Requires: %{name}-libs = %{version}-%{release}
Requires: readline
Requires: ncurses
# Needed by /usr/libexec/libvirt-guests.sh script.
Requires: gettext
# Needed by virt-pki-validate script.
Requires: gnutls-utils
%if %{with_pm_utils}
# Needed for probing the power management features of the host.
Requires: pm-utils
%endif
%if %{with_bash_completion}
Requires: %{name}-bash-completion = %{version}-%{release}
%endif

%description client
The client binaries needed to access the virtualization
capabilities of recent versions of Linux (and other OSes).

%package libs
Summary: Client side libraries
Group: Development/Libraries
# So remote clients can access libvirt over SSH tunnel
# (client invokes 'nc' against the UNIX socket on the server)
Requires: nc
Requires: cyrus-sasl
# Needed by default sasl.conf - no onerous extra deps, since
# 100's of other things on a system already pull in krb5-libs
Requires: cyrus-sasl-gssapi

%description libs
Shared libraries for accessing the libvirt daemon.

%package admin
Summary: Set of tools to control libvirt daemon
Group: Development/Libraries
Requires: %{name}-libs = %{version}-%{release}
Requires: readline
%if %{with_bash_completion}
Requires: %{name}-bash-completion = %{version}-%{release}
%endif

%description admin
The client side utilities to control the libvirt daemon.

%if %{with_bash_completion}
%package bash-completion
Summary: Bash completion script

%description bash-completion
Bash completion script stub.
%endif

%if %{with_wireshark}
%package wireshark
Summary: Wireshark dissector plugin for libvirt RPC transactions
Group: Development/Libraries
Requires: wireshark >= 1.12.6-4
Requires: %{name}-libs = %{version}-%{release}

%description wireshark
Wireshark dissector plugin for better analysis of libvirt RPC traffic.
%endif

%if %{with_lxc}
%package login-shell
Summary: Login shell for connecting users to an LXC container
Group: Development/Libraries
Requires: %{name}-libs = %{version}-%{release}

%description login-shell
Provides the set-uid virt-login-shell binary that is used to
connect a user to an LXC container when they login, by switching
namespaces.
%endif

%package devel
Summary: Libraries, includes, etc. to compile with the libvirt library
Group: Development/Libraries
Requires: %{name}-libs = %{version}-%{release}
Requires: pkgconfig

%description devel
Include header files & development libraries for the libvirt C library.

%if %{with_sanlock}
%package lock-sanlock
Summary: Sanlock lock manager plugin for QEMU driver
Group: Development/Libraries
Requires: sanlock >= 2.4
#for virt-sanlock-cleanup require augeas
Requires: augeas
Requires: %{name}-daemon = %{version}-%{release}
Requires: %{name}-libs = %{version}-%{release}

%description lock-sanlock
Includes the Sanlock lock manager plugin for the QEMU
driver
%endif

%package nss
Summary: Libvirt plugin for Name Service Switch
Group: Development/Libraries
Requires: libvirt-daemon-driver-network = %{version}-%{release}

%description nss
Libvirt plugin for NSS for translating domain names into IP addresses.


%prep
%if ! %{supported_platform}
echo "This RPM requires either Fedora >= 20 or RHEL >= 6"
exit 1
%endif

%setup -q

# Patches have to be stored in a temporary file because RPM has
# a limit on the length of the result of any macro expansion;
# if the string is longer, it's silently cropped
%{lua:
    tmp = os.tmpname();
    f = io.open(tmp, "w+");
    count = 0;
    for i, p in ipairs(patches) do
        f:write(p.."\n");
        count = count + 1;
    end;
    f:close();
    print("PATCHCOUNT="..count.."\n")
    print("PATCHLIST="..tmp.."\n")
}

git init -q
git config user.name rpm-build
git config user.email rpm-build
git config gc.auto 0
git add .
git commit -q -a --author 'rpm-build <rpm-build>' \
           -m '%{name}-%{version} base'

COUNT=$(grep '\.patch$' $PATCHLIST | wc -l)
if [ $COUNT -ne $PATCHCOUNT ]; then
    echo "Found $COUNT patches in $PATCHLIST, expected $PATCHCOUNT"
    exit 1
fi
if [ $COUNT -gt 0 ]; then
    xargs git am <$PATCHLIST || exit 1
fi
echo "Applied $COUNT patches"
rm -f $PATCHLIST
rm -rf .git

%build
%if %{with_xen}
    %define arg_xen --with-xen
%else
    %define arg_xen --without-xen
%endif

%if %{with_qemu}
    %define arg_qemu --with-qemu
%else
    %define arg_qemu --without-qemu
%endif

%if %{with_openvz}
    %define arg_openvz --with-openvz
%else
    %define arg_openvz --without-openvz
%endif

%if %{with_lxc}
    %define arg_lxc --with-lxc
%else
    %define arg_lxc --without-lxc
%endif

%if %{with_vbox}
    %define arg_vbox --with-vbox
%else
    %define arg_vbox --without-vbox
%endif

%if %{with_libxl}
    %define arg_libxl --with-libxl
%else
    %define arg_libxl --without-libxl
%endif

%if %{with_phyp}
    %define arg_phyp --with-phyp
%else
    %define arg_phyp --without-phyp
%endif

%if %{with_esx}
    %define arg_esx --with-esx
%else
    %define arg_esx --without-esx
%endif

%if %{with_hyperv}
    %define arg_hyperv --with-hyperv
%else
    %define arg_hyperv --without-hyperv
%endif

%if %{with_vmware}
    %define arg_vmware --with-vmware
%else
    %define arg_vmware --without-vmware
%endif

%if %{with_uml}
    %define arg_uml --with-uml
%else
    %define arg_uml --without-uml
%endif

%if %{with_storage_rbd}
    %define arg_storage_rbd --with-storage-rbd
%else
    %define arg_storage_rbd --without-storage-rbd
%endif

%if %{with_storage_sheepdog}
    %define arg_storage_sheepdog --with-storage-sheepdog
%else
    %define arg_storage_sheepdog --without-storage-sheepdog
%endif

%if %{with_storage_gluster}
    %define arg_storage_gluster --with-storage-gluster
%else
    %define arg_storage_gluster --without-storage-gluster
%endif

%if %{with_numactl}
    %define arg_numactl --with-numactl
%else
    %define arg_numactl --without-numactl
%endif

%if %{with_numad}
    %define arg_numad --with-numad
%else
    %define arg_numad --without-numad
%endif

%if %{with_fuse}
    %define arg_fuse --with-fuse
%else
    %define arg_fuse --without-fuse
%endif

%if %{with_sanlock}
    %define arg_sanlock --with-sanlock
%else
    %define arg_sanlock --without-sanlock
%endif

%if %{with_firewalld}
    %define arg_firewalld --with-firewalld
%else
    %define arg_firewalld --without-firewalld
%endif

%if %{with_wireshark}
    %define arg_wireshark --with-wireshark-dissector
%else
    %define arg_wireshark --without-wireshark-dissector
%endif

%if %{with_pm_utils}
    %define arg_pm_utils --with-pm-utils
%else
    %define arg_pm_utils --without-pm-utils
%endif

%define when  %(date +"%%F-%%T")
%define where %(hostname)
%define who   %{?packager}%{!?packager:Unknown}
%define arg_packager --with-packager="%{who}, %{when}, %{where}"
%define arg_packager_version --with-packager-version="%{release}"

%if %{with_systemd}
    %define arg_init_script --with-init-script=systemd
%else
    %define arg_init_script --with-init-script=redhat
%endif

%if 0%{?fedora} || 0%{?rhel} >= 7
    %define arg_selinux_mount --with-selinux-mount="/sys/fs/selinux"
%else
    %define arg_selinux_mount --with-selinux-mount="/selinux"
%endif

%if 0%{?fedora}
    # Nightly firmware repo x86/OVMF
    LOADERS="/usr/share/edk2.git/ovmf-x64/OVMF_CODE-pure-efi.fd:/usr/share/edk2.git/ovmf-x64/OVMF_VARS-pure-efi.fd"
    # Nightly firmware repo aarch64/AAVMF
    LOADERS="$LOADERS:/usr/share/edk2.git/aarch64/QEMU_EFI-pflash.raw:/usr/share/edk2.git/aarch64/vars-template-pflash.raw"
    # Fedora official x86/OVMF
    LOADERS="$LOADERS:/usr/share/edk2/ovmf/OVMF_CODE.fd:/usr/share/edk2/ovmf/OVMF_VARS.fd"
    # Fedora official aarch64/AAVMF
    LOADERS="$LOADERS:/usr/share/edk2/aarch64/QEMU_EFI-pflash.raw:/usr/share/edk2/aarch64/vars-template-pflash.raw"
    %define arg_loader_nvram --with-loader-nvram="$LOADERS"
%endif

# place macros above and build commands below this comment

# STX: Generate configure script.  Default is to do a "git clone" of gnulib.
# Use the tar ball gnulib tarball instead.
tar zxf %{SOURCE6}
./bootstrap --no-git --gnulib-srcdir=gnulib-ffc927e --copy
tar zxf %{SOURCE7} -C src

%if 0%{?enable_autotools}
 autoreconf -if
%endif

rm -f po/stamp-po
%configure %{?arg_xen} \
           %{?arg_qemu} \
           %{?arg_openvz} \
           %{?arg_lxc} \
           %{?arg_vbox} \
           %{?arg_libxl} \
           --with-sasl \
           --with-avahi \
           --with-polkit \
           --with-libvirtd \
           %{?arg_uml} \
           %{?arg_phyp} \
           %{?arg_esx} \
           %{?arg_hyperv} \
           %{?arg_vmware} \
           --without-xenapi \
           --without-vz \
           --without-bhyve \
           --with-interface \
           --with-network \
           --with-storage-fs \
           --with-storage-lvm \
           --with-storage-iscsi \
           --with-storage-scsi \
           --with-storage-disk \
           --with-storage-mpath \
           %{?arg_storage_rbd} \
           %{?arg_storage_sheepdog} \
           %{?arg_storage_gluster} \
           --without-storage-zfs \
           --without-storage-vstorage \
           %{?arg_numactl} \
           %{?arg_numad} \
           --with-capng \
           %{?arg_fuse} \
           --with-netcf \
           --with-selinux \
           %{?arg_selinux_mount} \
           --without-apparmor \
           --without-hal \
           --with-udev \
           --with-yajl \
           %{?arg_sanlock} \
           --with-libpcap \
           --with-macvtap \
           --with-audit \
           --with-dtrace \
           --with-driver-modules \
           %{?arg_firewalld} \
           %{?arg_wireshark} \
           %{?arg_pm_utils} \
           --with-nss-plugin \
           %{arg_packager} \
           %{arg_packager_version} \
           --with-qemu-user=%{qemu_user} \
           --with-qemu-group=%{qemu_group} \
           --with-tls-priority=%{tls_priority} \
           %{?arg_loader_nvram} \
           %{?enable_werror} \
           --enable-expensive-tests \
           --without-audit \
           --without-dtrace \
           %{arg_init_script}

#STX: Avoid doing a 'config.status --recheck' (./configure executed twice).
touch -r config.status configure

make %{?_smp_mflags}
gzip -9 ChangeLog

%install
rm -fr %{buildroot}

# Avoid using makeinstall macro as it changes prefixes rather than setting
# DESTDIR. Newer make_install macro would be better but it's not available
# on RHEL 5, thus we need to expand it here.
make %{?_smp_mflags} install DESTDIR=%{?buildroot} SYSTEMD_UNIT_DIR=%{_unitdir}

make %{?_smp_mflags} -C examples distclean

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/lock-driver/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/lock-driver/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/connection-driver/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/connection-driver/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/storage-backend/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/storage-backend/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/storage-file/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/libvirt/storage-file/*.a
%if %{with_wireshark}
    %if 0%{fedora} >= 24
rm -f $RPM_BUILD_ROOT%{_libdir}/wireshark/plugins/libvirt.la
    %else
rm -f $RPM_BUILD_ROOT%{_libdir}/wireshark/plugins/*/libvirt.la
mv $RPM_BUILD_ROOT%{_libdir}/wireshark/plugins/*/libvirt.so \
      $RPM_BUILD_ROOT%{_libdir}/wireshark/plugins/libvirt.so
    %endif
%endif

install -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/lib/libvirt/dnsmasq/
# We don't want to install /etc/libvirt/qemu/networks in the main %files list
# because if the admin wants to delete the default network completely, we don't
# want to end up re-incarnating it on every RPM upgrade.
install -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/libvirt/networks/
cp $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/qemu/networks/default.xml \
   $RPM_BUILD_ROOT%{_datadir}/libvirt/networks/default.xml
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/qemu/networks/default.xml
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/qemu/networks/autostart/default.xml

# nwfilter files are installed in /usr/share/libvirt and copied to /etc in %post
# to avoid verification errors on changed files in /etc
install -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/libvirt/nwfilter/
cp -a $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/nwfilter/*.xml \
    $RPM_BUILD_ROOT%{_datadir}/libvirt/nwfilter/

# Strip auto-generated UUID - we need it generated per-install
sed -i -e "/<uuid>/d" $RPM_BUILD_ROOT%{_datadir}/libvirt/networks/default.xml
%if ! %{with_qemu}
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/libvirtd_qemu.aug
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/tests/test_libvirtd_qemu.aug
%endif
%find_lang %{name}

%if ! %{with_sanlock}
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/libvirt_sanlock.aug
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/tests/test_libvirt_sanlock.aug
%endif

%if ! %{with_lxc}
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/libvirtd_lxc.aug
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/tests/test_libvirtd_lxc.aug
%endif

%if ! %{with_qemu}
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/qemu.conf
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/libvirtd.qemu
%endif
%if ! %{with_lxc}
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/lxc.conf
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/libvirtd.lxc
%endif
%if ! %{with_libxl}
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/libvirt/libxl.conf
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/libvirtd.libxl
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/libvirtd_libxl.aug
rm -f $RPM_BUILD_ROOT%{_datadir}/augeas/lenses/tests/test_libvirtd_libxl.aug
%endif
%if ! %{with_uml}
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/libvirtd.uml
%endif

# Copied into libvirt-docs subpackage eventually
mv $RPM_BUILD_ROOT%{_datadir}/doc/libvirt-%{version} libvirt-docs

# STX: Disable dtrace
# %ifarch %{power64} s390x x86_64 ia64 alpha sparc64
# mv $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/libvirt_probes.stp \
#    $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/libvirt_probes-64.stp
# mv $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/libvirt_qemu_probes.stp \
#    $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/libvirt_qemu_probes-64.stp
# %endif

# STX: Begin custom install
## Enable syslog for libvirtd ( /var/log/libvirtd.log )
echo "log_outputs=\"3:syslog:libvirtd\"" >> %{buildroot}/etc/libvirt/libvirtd.conf

## Set auth_tcp to "none" for now to enable live migration.
## We'll need to set up proper authentication later.
sed -i '/#auth_tcp/a auth_tcp = "none"' %{buildroot}/etc/libvirt/libvirtd.conf

install -d -m 711 %{buildroot}/data/images
## Install logrotate files 
install -d -m 755 %{buildroot}/etc/logrotate.d
install -p -D -m 644 %{SOURCE2} %{buildroot}/etc/logrotate.d/libvirtd
install -p -D -m 644 %{SOURCE3} %{buildroot}/etc/logrotate.d/libvirtd.lxc
install -p -D -m 644 %{SOURCE4} %{buildroot}/etc/logrotate.d/libvirtd.qemu
install -p -D -m 644 %{SOURCE5} %{buildroot}/etc/logrotate.d/libvirtd.uml
## Install hooks
mkdir -p $RPM_BUILD_ROOT/etc/libvirt/hooks
install -m 0500 %{SOURCE8} $RPM_BUILD_ROOT/etc/libvirt/hooks/qemu
# STX: End custom install

%clean
rm -fr %{buildroot}

# STX: We are not maintaining the unit tests.
# %check
# cd tests
# # These tests don't current work in a mock build root
# for i in nodeinfotest seclabeltest
# do
#   rm -f $i
#   printf 'int main(void) { return 0; }' > $i.c
#   printf '#!/bin/sh\nexit 0\n' > $i
#   chmod +x $i
# done
# if ! make %{?_smp_mflags} check VIR_TEST_DEBUG=1
# then
#   cat test-suite.log || true
#   exit 1
# fi

%pre daemon
# 'libvirt' group is just to allow password-less polkit access to
# libvirtd. The uid number is irrelevant, so we use dynamic allocation
# described at the above link.
getent group libvirt >/dev/null || groupadd -r libvirt

exit 0

%post daemon

%if %{with_systemd}
    %if %{with_systemd_macros}
        %systemd_post virtlockd.socket virtlogd.socket libvirtd.service
    %else
if [ $1 -eq 1 ] ; then
    # Initial installation
    /bin/systemctl enable \
        virtlockd.socket \
        virtlogd.socket \
        libvirtd.service >/dev/null 2>&1 || :
fi
    %endif
%else
    %if %{with_cgconfig}
# Starting with Fedora 16/RHEL-7, systemd automounts all cgroups,
# and cgconfig is no longer a necessary service.
        %if 0%{?rhel} && 0%{?rhel} < 7
if [ "$1" -eq "1" ]; then
/sbin/chkconfig cgconfig on
fi
        %endif
    %endif

/sbin/chkconfig --add libvirtd
/sbin/chkconfig --add virtlogd
/sbin/chkconfig --add virtlockd
%endif

%preun daemon
%if %{with_systemd}
    %if %{with_systemd_macros}
        %systemd_preun libvirtd.service virtlogd.socket virtlogd.service virtlockd.socket virtlockd.service
    %else
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable \
        libvirtd.service \
        virtlogd.socket \
        virtlogd.service \
        virtlockd.socket \
        virtlockd.service > /dev/null 2>&1 || :
    /bin/systemctl stop \
        libvirtd.service \
        virtlogd.socket \
        virtlogd.service \
        virtlockd.socket \
        virtlockd.service > /dev/null 2>&1 || :
fi
    %endif
%else
if [ $1 = 0 ]; then
    /sbin/service libvirtd stop 1>/dev/null 2>&1
    /sbin/chkconfig --del libvirtd
    /sbin/service virtlogd stop 1>/dev/null 2>&1
    /sbin/chkconfig --del virtlogd
    /sbin/service virtlockd stop 1>/dev/null 2>&1
    /sbin/chkconfig --del virtlockd
fi
%endif

%postun daemon
%if %{with_systemd}
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl reload-or-try-restart virtlockd.service >/dev/null 2>&1 || :
    /bin/systemctl reload-or-try-restart virtlogd.service >/dev/null 2>&1 || :
    /bin/systemctl try-restart libvirtd.service >/dev/null 2>&1 || :
fi
%else
if [ $1 -ge 1 ]; then
    /sbin/service virtlockd reload > /dev/null 2>&1 || :
    /sbin/service virtlogd reload > /dev/null 2>&1 || :
    /sbin/service libvirtd condrestart > /dev/null 2>&1
fi
%endif

%if %{with_systemd}
%else
%triggerpostun daemon -- libvirt-daemon < 1.2.1
if [ "$1" -ge "1" ]; then
    /sbin/service virtlockd reload > /dev/null 2>&1 || :
    /sbin/service virtlogd reload > /dev/null 2>&1 || :
    /sbin/service libvirtd condrestart > /dev/null 2>&1
fi
%endif

# In upgrade scenario we must explicitly enable virtlockd/virtlogd
# sockets, if libvirtd is already enabled and start them if
# libvirtd is running, otherwise you'll get failures to start
# guests
%triggerpostun daemon -- libvirt-daemon < 1.3.0
if [ $1 -ge 1 ] ; then
%if %{with_systemd}
        /bin/systemctl is-enabled libvirtd.service 1>/dev/null 2>&1 &&
            /bin/systemctl enable virtlogd.socket || :
        /bin/systemctl is-active libvirtd.service 1>/dev/null 2>&1 &&
            /bin/systemctl start virtlogd.socket || :
%else
        /sbin/chkconfig libvirtd 1>/dev/null 2>&1 &&
            /sbin/chkconfig virtlogd on || :
        /sbin/service libvirtd status 1>/dev/null 2>&1 &&
            /sbin/service virtlogd start || :
%endif
fi

%post daemon-config-network
# STX: The 'with_network' flag doesn't work properly.  There are some packaging
# errors when using it.  Disable default.xml manually ...
# We don't want 'virbr0' and 'virbr0-nic' interfaces created.

# if test $1 -eq 1 && test ! -f %{_sysconfdir}/libvirt/qemu/networks/default.xml ; then
#     # see if the network used by default network creates a conflict,
#     # and try to resolve it
#     # NB: 192.168.122.0/24 is used in the default.xml template file;
#     # do not modify any of those values here without also modifying
#     # them in the template.
#     orig_sub=122
#     sub=${orig_sub}
#     nl='
# '
#     routes="${nl}$(ip route show | cut -d' ' -f1)${nl}"
#     case ${routes} in
#       *"${nl}192.168.${orig_sub}.0/24${nl}"*)
#         # there was a match, so we need to look for an unused subnet
#         for new_sub in $(seq 124 254); do
#           case ${routes} in
#           *"${nl}192.168.${new_sub}.0/24${nl}"*)
#             ;;
#           *)
#             sub=$new_sub
#             break;
#             ;;
#           esac
#         done
#         ;;
#       *)
#         ;;
#     esac
# 
#     UUID=`/usr/bin/uuidgen`
#     sed -e "s/${orig_sub}/${sub}/g" \
#         -e "s,</name>,</name>\n  <uuid>$UUID</uuid>," \
#          < %{_datadir}/libvirt/networks/default.xml \
#          > %{_sysconfdir}/libvirt/qemu/networks/default.xml
#     ln -s ../default.xml %{_sysconfdir}/libvirt/qemu/networks/autostart/default.xml
# 
#     # Make sure libvirt picks up the new network defininiton
# %if %{with_systemd}
#     /bin/systemctl try-restart libvirtd.service >/dev/null 2>&1 ||:
# %else
#     /sbin/service libvirtd condrestart > /dev/null 2>&1 || :
# %endif
# 
# fi


%post daemon-config-nwfilter
cp %{_datadir}/libvirt/nwfilter/*.xml %{_sysconfdir}/libvirt/nwfilter/
# Make sure libvirt picks up the new nwfilter defininitons
%if %{with_systemd}
    /bin/systemctl try-restart libvirtd.service >/dev/null 2>&1 ||:
%else
    /sbin/service libvirtd condrestart > /dev/null 2>&1 || :
%endif


%if %{with_systemd}
%triggerun -- libvirt < 0.9.4
%{_bindir}/systemd-sysv-convert --save libvirtd >/dev/null 2>&1 ||:

# If the package is allowed to autostart:
/bin/systemctl --no-reload enable libvirtd.service >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del libvirtd >/dev/null 2>&1 || :
/bin/systemctl try-restart libvirtd.service >/dev/null 2>&1 || :
%endif

%if %{with_qemu}
%pre daemon-driver-qemu
# We want soft static allocation of well-known ids, as disk images
# are commonly shared across NFS mounts by id rather than name; see
# https://fedoraproject.org/wiki/Packaging:UsersAndGroups
getent group kvm >/dev/null || groupadd -f -g 36 -r kvm
getent group qemu >/dev/null || groupadd -f -g 107 -r qemu
if ! getent passwd qemu >/dev/null; then
  if ! getent passwd 107 >/dev/null; then
    useradd -r -u 107 -g qemu -G kvm -d / -s /sbin/nologin -c "qemu user" qemu
  else
    useradd -r -g qemu -G kvm -d / -s /sbin/nologin -c "qemu user" qemu
  fi
fi
exit 0
%endif

%preun client

%if %{with_systemd}
    %if %{with_systemd_macros}
        %systemd_preun libvirt-guests.service
    %endif
%else
if [ $1 = 0 ]; then
    /sbin/chkconfig --del libvirt-guests
    rm -f /var/lib/libvirt/libvirt-guests
fi
%endif

%post client

/sbin/ldconfig
%if %{with_systemd}
    %if %{with_systemd_macros}
        %systemd_post libvirt-guests.service
    %endif
%else
/sbin/chkconfig --add libvirt-guests
%endif

%postun client

/sbin/ldconfig
%if %{with_systemd}
    %if %{with_systemd_macros}
        %systemd_postun libvirt-guests.service
    %endif
%triggerun client -- libvirt < 0.9.4
%{_bindir}/systemd-sysv-convert --save libvirt-guests >/dev/null 2>&1 ||:

# If the package is allowed to autostart:
/bin/systemctl --no-reload enable libvirt-guests.service >/dev/null 2>&1 ||:

# Run this because the SysV package being removed won't do them
/sbin/chkconfig --del libvirt-guests >/dev/null 2>&1 || :
%endif

%if %{with_sanlock}
%post lock-sanlock
if getent group sanlock > /dev/null ; then
    chmod 0770 %{_localstatedir}/lib/libvirt/sanlock
    chown root:sanlock %{_localstatedir}/lib/libvirt/sanlock
fi
%endif

%if %{with_lxc}
%pre login-shell
getent group virtlogin >/dev/null || groupadd -r virtlogin
exit 0
%endif

%files

# STX: Customization
%dir /data/images/

%files docs
# TODO(STX): NEWS is not present in git source repo.
%doc AUTHORS ChangeLog.gz README
%doc libvirt-docs/*

# API docs
%dir %{_datadir}/gtk-doc/html/libvirt/
%doc %{_datadir}/gtk-doc/html/libvirt/*.devhelp
%doc %{_datadir}/gtk-doc/html/libvirt/*.html
%doc %{_datadir}/gtk-doc/html/libvirt/*.png
%doc %{_datadir}/gtk-doc/html/libvirt/*.css
%doc examples/hellolibvirt
%doc examples/object-events
%doc examples/dominfo
%doc examples/domsuspend
%doc examples/dommigrate
%doc examples/openauth
%doc examples/xml
%doc examples/rename
%doc examples/systemtap
%doc examples/admin


%files daemon

%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/

%if %{with_systemd}
%{_unitdir}/libvirtd.service
%{_unitdir}/virt-guest-shutdown.target
%{_unitdir}/virtlogd.service
%{_unitdir}/virtlogd.socket
%{_unitdir}/virtlogd-admin.socket
%{_unitdir}/virtlockd.service
%{_unitdir}/virtlockd.socket
%{_unitdir}/virtlockd-admin.socket
%else
%{_sysconfdir}/rc.d/init.d/libvirtd
%{_sysconfdir}/rc.d/init.d/virtlogd
%{_sysconfdir}/rc.d/init.d/virtlockd
%endif
%doc src/remote/libvirtd.upstart
%config(noreplace) %{_sysconfdir}/sysconfig/libvirtd
%config(noreplace) %{_sysconfdir}/sysconfig/virtlogd
%config(noreplace) %{_sysconfdir}/sysconfig/virtlockd
%config(noreplace) %{_sysconfdir}/libvirt/libvirtd.conf
%config(noreplace) %{_sysconfdir}/libvirt/virtlogd.conf
%config(noreplace) %{_sysconfdir}/libvirt/virtlockd.conf
%config(noreplace) %{_prefix}/lib/sysctl.d/60-libvirtd.conf

%config(noreplace) %{_sysconfdir}/logrotate.d/libvirtd
%dir %{_datadir}/libvirt/

%ghost %dir %{_localstatedir}/run/libvirt/

%dir %attr(0711, root, root) %{_localstatedir}/lib/libvirt/images/
%dir %attr(0711, root, root) %{_localstatedir}/lib/libvirt/filesystems/
%dir %attr(0711, root, root) %{_localstatedir}/lib/libvirt/boot/
%dir %attr(0711, root, root) %{_localstatedir}/cache/libvirt/


%dir %attr(0755, root, root) %{_libdir}/libvirt/lock-driver
%attr(0755, root, root) %{_libdir}/libvirt/lock-driver/lockd.so

%{_datadir}/augeas/lenses/libvirtd.aug
%{_datadir}/augeas/lenses/tests/test_libvirtd.aug
%{_datadir}/augeas/lenses/virtlogd.aug
%{_datadir}/augeas/lenses/tests/test_virtlogd.aug
%{_datadir}/augeas/lenses/virtlockd.aug
%{_datadir}/augeas/lenses/tests/test_virtlockd.aug
%{_datadir}/augeas/lenses/libvirt_lockd.aug
%if %{with_qemu}
%{_datadir}/augeas/lenses/tests/test_libvirt_lockd.aug
%endif

%{_datadir}/polkit-1/actions/org.libvirt.unix.policy
%{_datadir}/polkit-1/actions/org.libvirt.api.policy
%{_datadir}/polkit-1/rules.d/50-libvirt.rules

%dir %attr(0700, root, root) %{_localstatedir}/log/libvirt/

%attr(0755, root, root) %{_libexecdir}/libvirt_iohelper

%attr(0755, root, root) %{_sbindir}/libvirtd
%attr(0755, root, root) %{_sbindir}/virtlogd
%attr(0755, root, root) %{_sbindir}/virtlockd

%{_mandir}/man8/libvirtd.8*
%{_mandir}/man8/virtlogd.8*
%{_mandir}/man8/virtlockd.8*
%{_mandir}/man7/virkey*.7*

%doc examples/polkit/*.rules

# STX: Customization
/etc/logrotate.d/*
/etc/libvirt/hooks/qemu

%files daemon-config-network
%dir %{_datadir}/libvirt/networks/
%{_datadir}/libvirt/networks/default.xml

%files daemon-config-nwfilter
%dir %{_datadir}/libvirt/nwfilter/
%{_datadir}/libvirt/nwfilter/*.xml
%ghost %{_sysconfdir}/libvirt/nwfilter/*.xml

%files daemon-driver-interface
%{_libdir}/%{name}/connection-driver/libvirt_driver_interface.so

%files daemon-driver-network
%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/qemu/
%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/qemu/networks/
%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/qemu/networks/autostart
%ghost %dir %{_localstatedir}/run/libvirt/network/
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/network/
%dir %attr(0755, root, root) %{_localstatedir}/lib/libvirt/dnsmasq/
%attr(0755, root, root) %{_libexecdir}/libvirt_leaseshelper
%{_libdir}/%{name}/connection-driver/libvirt_driver_network.so

%files daemon-driver-nodedev
%{_libdir}/%{name}/connection-driver/libvirt_driver_nodedev.so

%files daemon-driver-nwfilter
%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/nwfilter/
%ghost %dir %{_localstatedir}/run/libvirt/network/
%{_libdir}/%{name}/connection-driver/libvirt_driver_nwfilter.so

%files daemon-driver-secret
%{_libdir}/%{name}/connection-driver/libvirt_driver_secret.so

%files daemon-driver-storage

%files daemon-driver-storage-core
%attr(0755, root, root) %{_libexecdir}/libvirt_parthelper
%{_libdir}/%{name}/connection-driver/libvirt_driver_storage.so
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_fs.so
%{_libdir}/%{name}/storage-file/libvirt_storage_file_fs.so

%files daemon-driver-storage-disk
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_disk.so

%files daemon-driver-storage-logical
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_logical.so

%files daemon-driver-storage-scsi
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_scsi.so

%files daemon-driver-storage-iscsi
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_iscsi.so

%files daemon-driver-storage-mpath
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_mpath.so

%if %{with_storage_gluster}
%files daemon-driver-storage-gluster
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_gluster.so
%{_libdir}/%{name}/storage-file/libvirt_storage_file_gluster.so
%endif

%if %{with_storage_rbd}
%files daemon-driver-storage-rbd
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_rbd.so
%endif

%if %{with_storage_sheepdog}
%files daemon-driver-storage-sheepdog
%{_libdir}/%{name}/storage-backend/libvirt_storage_backend_sheepdog.so
%endif

%if %{with_qemu}
%files daemon-driver-qemu
%dir %attr(0700, root, root) %{_sysconfdir}/libvirt/qemu/
%dir %attr(0700, root, root) %{_localstatedir}/log/libvirt/qemu/
%config(noreplace) %{_sysconfdir}/libvirt/qemu.conf
%config(noreplace) %{_sysconfdir}/libvirt/qemu-lockd.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/libvirtd.qemu
%ghost %dir %attr(0700, root, root) %{_localstatedir}/run/libvirt/qemu/
%dir %attr(0751, %{qemu_user}, %{qemu_group}) %{_localstatedir}/lib/libvirt/qemu/
%dir %attr(0750, %{qemu_user}, %{qemu_group}) %{_localstatedir}/cache/libvirt/qemu/
%{_datadir}/augeas/lenses/libvirtd_qemu.aug
%{_datadir}/augeas/lenses/tests/test_libvirtd_qemu.aug
%{_libdir}/%{name}/connection-driver/libvirt_driver_qemu.so
%endif

%if %{with_lxc}
%files daemon-driver-lxc
%dir %attr(0700, root, root) %{_localstatedir}/log/libvirt/lxc/
%config(noreplace) %{_sysconfdir}/libvirt/lxc.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/libvirtd.lxc
%ghost %dir %{_localstatedir}/run/libvirt/lxc/
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/lxc/
%{_datadir}/augeas/lenses/libvirtd_lxc.aug
%{_datadir}/augeas/lenses/tests/test_libvirtd_lxc.aug
%attr(0755, root, root) %{_libexecdir}/libvirt_lxc
%{_libdir}/%{name}/connection-driver/libvirt_driver_lxc.so
%endif

%if %{with_uml}
%files daemon-driver-uml
%dir %attr(0700, root, root) %{_localstatedir}/log/libvirt/uml/
%config(noreplace) %{_sysconfdir}/logrotate.d/libvirtd.uml
%ghost %dir %{_localstatedir}/run/libvirt/uml/
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/uml/
%{_libdir}/%{name}/connection-driver/libvirt_driver_uml.so
%endif

%if %{with_xen}
%files daemon-driver-xen
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/xen/
%{_libdir}/%{name}/connection-driver/libvirt_driver_xen.so
%endif

%if %{with_libxl}
%files daemon-driver-libxl
%config(noreplace) %{_sysconfdir}/libvirt/libxl.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/libvirtd.libxl
%config(noreplace) %{_sysconfdir}/libvirt/libxl-lockd.conf
%{_datadir}/augeas/lenses/libvirtd_libxl.aug
%{_datadir}/augeas/lenses/tests/test_libvirtd_libxl.aug
%dir %attr(0700, root, root) %{_localstatedir}/log/libvirt/libxl/
%ghost %dir %{_localstatedir}/run/libvirt/libxl/
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/libxl/
%{_libdir}/%{name}/connection-driver/libvirt_driver_libxl.so
%endif

%if %{with_vbox}
%files daemon-driver-vbox
%{_libdir}/%{name}/connection-driver/libvirt_driver_vbox.so
%endif

%if %{with_qemu_tcg}
%files daemon-qemu
%endif

%if %{with_qemu_kvm}
%files daemon-kvm
%endif

%if %{with_lxc}
%files daemon-lxc
%endif

%if %{with_uml}
%files daemon-uml
%endif

%if %{with_xen} || %{with_libxl}
%files daemon-xen
%endif

%if %{with_vbox}
%files daemon-vbox
%endif

%if %{with_sanlock}
%files lock-sanlock
    %if %{with_qemu}
%config(noreplace) %{_sysconfdir}/libvirt/qemu-sanlock.conf
    %endif
    %if %{with_libxl}
%config(noreplace) %{_sysconfdir}/libvirt/libxl-sanlock.conf
    %endif
%attr(0755, root, root) %{_libdir}/libvirt/lock-driver/sanlock.so
%{_datadir}/augeas/lenses/libvirt_sanlock.aug
%{_datadir}/augeas/lenses/tests/test_libvirt_sanlock.aug
%dir %attr(0700, root, root) %{_localstatedir}/lib/libvirt/sanlock
%{_sbindir}/virt-sanlock-cleanup
%{_mandir}/man8/virt-sanlock-cleanup.8*
%attr(0755, root, root) %{_libexecdir}/libvirt_sanlock_helper
%endif

%files client
%{_mandir}/man1/virsh.1*
%{_mandir}/man1/virt-xml-validate.1*
%{_mandir}/man1/virt-pki-validate.1*
%{_mandir}/man1/virt-host-validate.1*
%{_bindir}/virsh
%{_bindir}/virt-xml-validate
%{_bindir}/virt-pki-validate
%{_bindir}/virt-host-validate

# STX: Disable dtrace
# %{_datadir}/systemtap/tapset/libvirt_probes*.stp
# %{_datadir}/systemtap/tapset/libvirt_qemu_probes*.stp
# %{_datadir}/systemtap/tapset/libvirt_functions.stp

%if %{with_bash_completion}
%{_datadir}/bash-completion/completions/virsh
%endif

%if %{with_systemd}
%{_unitdir}/libvirt-guests.service
%else
%{_sysconfdir}/rc.d/init.d/libvirt-guests
%endif
%config(noreplace) %{_sysconfdir}/sysconfig/libvirt-guests
%attr(0755, root, root) %{_libexecdir}/libvirt-guests.sh

%files libs -f %{name}.lang
%doc COPYING COPYING.LESSER
%config(noreplace) %{_sysconfdir}/libvirt/libvirt.conf
%config(noreplace) %{_sysconfdir}/libvirt/libvirt-admin.conf
%{_libdir}/libvirt.so.*
%{_libdir}/libvirt-qemu.so.*
%{_libdir}/libvirt-lxc.so.*
%{_libdir}/libvirt-admin.so.*
%dir %{_datadir}/libvirt/
%dir %{_datadir}/libvirt/schemas/
%dir %attr(0755, root, root) %{_localstatedir}/lib/libvirt/

%{_datadir}/libvirt/schemas/basictypes.rng
%{_datadir}/libvirt/schemas/capability.rng
%{_datadir}/libvirt/schemas/cputypes.rng
%{_datadir}/libvirt/schemas/domain.rng
%{_datadir}/libvirt/schemas/domaincaps.rng
%{_datadir}/libvirt/schemas/domaincommon.rng
%{_datadir}/libvirt/schemas/domainsnapshot.rng
%{_datadir}/libvirt/schemas/interface.rng
%{_datadir}/libvirt/schemas/network.rng
%{_datadir}/libvirt/schemas/networkcommon.rng
%{_datadir}/libvirt/schemas/nodedev.rng
%{_datadir}/libvirt/schemas/nwfilter.rng
%{_datadir}/libvirt/schemas/nwfilter_params.rng
%{_datadir}/libvirt/schemas/nwfilterbinding.rng
%{_datadir}/libvirt/schemas/secret.rng
%{_datadir}/libvirt/schemas/storagecommon.rng
%{_datadir}/libvirt/schemas/storagepool.rng
%{_datadir}/libvirt/schemas/storagevol.rng

%dir %{_datadir}/libvirt/cpu_map/
%{_datadir}/libvirt/cpu_map/*

%{_datadir}/libvirt/test-screenshot.png

%config(noreplace) %{_sysconfdir}/sasl2/libvirt.conf

%files admin
%{_mandir}/man1/virt-admin.1*
%{_bindir}/virt-admin
%if %{with_bash_completion}
%{_datadir}/bash-completion/completions/virt-admin
%endif

%if %{with_bash_completion}
%files bash-completion
%{_datadir}/bash-completion/completions/vsh
%endif

%if %{with_wireshark}
%files wireshark
%{_libdir}/wireshark/plugins/libvirt.so
%endif

%files nss
%{_libdir}/libnss_libvirt.so.2
%{_libdir}/libnss_libvirt_guest.so.2

%if %{with_lxc}
%files login-shell
%attr(4750, root, virtlogin) %{_bindir}/virt-login-shell
%config(noreplace) %{_sysconfdir}/libvirt/virt-login-shell.conf
%{_mandir}/man1/virt-login-shell.1*
%endif

%files devel
%{_libdir}/libvirt.so
%{_libdir}/libvirt-admin.so
%{_libdir}/libvirt-qemu.so
%{_libdir}/libvirt-lxc.so
%dir %{_includedir}/libvirt
%{_includedir}/libvirt/virterror.h
%{_includedir}/libvirt/libvirt.h
%{_includedir}/libvirt/libvirt-admin.h
%{_includedir}/libvirt/libvirt-common.h
%{_includedir}/libvirt/libvirt-domain.h
%{_includedir}/libvirt/libvirt-domain-snapshot.h
%{_includedir}/libvirt/libvirt-event.h
%{_includedir}/libvirt/libvirt-host.h
%{_includedir}/libvirt/libvirt-interface.h
%{_includedir}/libvirt/libvirt-network.h
%{_includedir}/libvirt/libvirt-nodedev.h
%{_includedir}/libvirt/libvirt-nwfilter.h
%{_includedir}/libvirt/libvirt-secret.h
%{_includedir}/libvirt/libvirt-storage.h
%{_includedir}/libvirt/libvirt-stream.h
%{_includedir}/libvirt/libvirt-qemu.h
%{_includedir}/libvirt/libvirt-lxc.h
%{_libdir}/pkgconfig/libvirt.pc
%{_libdir}/pkgconfig/libvirt-admin.pc
%{_libdir}/pkgconfig/libvirt-qemu.pc
%{_libdir}/pkgconfig/libvirt-lxc.pc

%dir %{_datadir}/libvirt/api/
%{_datadir}/libvirt/api/libvirt-api.xml
%{_datadir}/libvirt/api/libvirt-admin-api.xml
%{_datadir}/libvirt/api/libvirt-qemu-api.xml
%{_datadir}/libvirt/api/libvirt-lxc-api.xml

# Needed building python bindings
%doc docs/libvirt-api.xml


%changelog
