%{!?_licensedir:%global license %%doc}
%global pypi_name python-cephclient

Name:      python-cephclient
Version:   0.1.0.5
Release:   0%{?_tis_dist}.%{tis_patch_ver}
Summary:   python-cephclient

License:   Apache-2.0
URL:       https://github.com/dmsimard/python-cephclient
Group:     devel/python
Packager:  Wind River <info@windriver.com>

Source0:   %{pypi_name}-v%{version}.tar.gz

Patch0: 0001-comment-code-is-for-ceph-mgr-RESTful-plugin.patch
Patch1: 0002-give-service-endpoint-to-access-to-RESTful-plugin.patch
Patch2: 0003-refactor-client.py-to-use-RESTful-plugin-service.patch
Patch3: 0004-construct-response-data-for-ok-status_code-reason.patch
Patch4: 0005-df-refactor-implementation.patch
Patch5: 0006-mon-dump-refactor-implementation.patch
Patch6: 0007-fsid-refactor-implementation.patch
Patch7: 0008-health-refactor-implementation.patch
Patch8: 0009-quorum_status-refactor-implementation.patch
Patch9: 0010-status-refactor-implementation.patch
Patch10: 0011-auth_del-refactor-implementation.patch
Patch11: 0012-auth_get_or_create-refactor-implementation.patch
Patch12: 0013-osd_crush_rule_dump-refactor-implementation.patch
Patch13: 0014-osd_crush_rule_ls-refactor-implementation.patch
Patch14: 0015-osd_crush_tree-implementation.patch
Patch15: 0016-osd_pool_get-implementation.patch
Patch16: 0017-osd_pool_get_quota-implementation.patch
Patch17: 0018-osd_pool_ls-implementation.patch
Patch18: 0019-osd_stat-refactor-implementation.patch
Patch19: 0020-osd_tree-refactor-implementation.patch
Patch20: 0021-osd_create-refactor-implementation.patch
Patch21: 0022-osd_crush_add_bucket-refactor-implementation.patch
Patch22: 0023-osd_crush_move-refactor-implementation.patch
Patch23: 0024-osd_crush_remove-refactor-implementation.patch
Patch24: 0025-osd_crush_rule_rm-refactor-implementation.patch
Patch25: 0026-osd_down-refactor-implementation.patch
Patch26: 0027-osd_pool_create-refactor-implementation.patch
Patch27: 0028-osd_pool_delete-refactor-implementation.patch
Patch28: 0029-osd_set_pool_param-refactor-implementation.patch
Patch29: 0030-osd_set_pool_quota-refactor-implementation.patch
Patch30: 0031-osd_set_key-refactor-implementation.patch
Patch31: 0032-osd_get_pool_quota-implementation.patch
Patch32: 0033-osd_get_pool_param-implementation.patch
Patch33: 0034-osd_df-implementation.patch
Patch34: 0035-pg_dump_stuck-refactor-implementation.patch
Patch35: 0036-compability-use-ruleset-as-parameter-for-osd_pool_cr.patch
Patch36: 0037-special-deal-with-osd_crush_tree-function.patch
Patch37: 0038-default-raise-exception-for-unused-API.patch

BuildArch: noarch

BuildRequires: python
BuildRequires: ceph
BuildRequires: python2-pip
BuildRequires: python2-wheel

Requires: python

Provides: python-cephclient

%description
Client library for the Ceph REST API

%prep
%autosetup -p 1 -n %{pypi_name}-%{version}

# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

# Let RPM handle the dependencies
rm -f requirements.txt

%build
%{__python2} setup.py build
%py2_build_wheel

%install
%{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p $RPM_BUILD_ROOT/wheels
install -m 644 dist/*.whl $RPM_BUILD_ROOT/wheels/

%files
%doc README.rst
%license LICENSE
%{python2_sitelib}/cephclient
%{python2_sitelib}/*.egg-info

%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
