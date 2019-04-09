Name:           cloud-provider-openstack
Version:        1.13.1
Release:        1%{?_tis_dist}.%{tis_patch_ver}
Summary:        For Kubernetes to work with Openstack
License:        ASL 2.0
Source0:        cloud-provider-openstack-c9abd15351c5d53b26b2cbf9a0d1023200e33238.tar.gz

ExclusiveArch:  x86_64

%description
For Kubernetes to work with Openstack. For example, Keystone authentication.

%prep
%setup -n cloud-provider-openstack

%install
install -d -p %{buildroot}%{_bindir}
install -p -m 0755 client-keystone-auth %{buildroot}%{_bindir}

%files
%doc LICENSE
%{_bindir}/client-keystone-auth
