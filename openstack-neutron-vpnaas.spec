%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_vpnaas
%global servicename neutron-vpnaas
%global type VPNaaS

%global neutron_version 11.0.0

%define major_neutron_version %(echo %{neutron_version} | awk 'BEGIN { FS=\".\"}; {print $1}')
%define next_neutron_version %(echo $((%{major_neutron_version} + 1)))

Name:           openstack-%{servicename}
Version:        XXX
Release:        XXX%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz
Source1:        neutron-vpn-agent.service
Source2:        neutron-vyatta-agent.service

Obsoletes:      openstack-neutron-vpn-agent < %{version}
Provides:       openstack-neutron-vpn-agent = %{epoch}:%{version}-%{release}

BuildArch:      noarch
BuildRequires:  gawk
BuildRequires:  openstack-macros
BuildRequires:  python2-devel
BuildRequires:  python-neutron >= 1:%{major_neutron_version}
BuildConflicts: python-neutron >= 1:%{next_neutron_version}
BuildRequires:  python-pbr
BuildRequires:  python-setuptools
BuildRequires:  systemd-units
BuildRequires:	git

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= 1:%{major_neutron_version}
Conflicts:      openstack-neutron >= 1:%{next_neutron_version}

%description
This is a %{type} service plugin for Openstack Neutron (Networking) service.


%package -n python-%{servicename}
Summary:        Neutron %{type} Python libraries

Requires:       python-neutron >= 1:%{major_neutron_version}
Conflicts:      python-neutron >= 1:%{next_neutron_version}
Requires:       python-alembic >= 0.8.4
Requires:       python-jinja2
Requires:       python-netaddr >= 0.7.12
Requires:       python-neutron-lib >= 0.4.0
Requires:       python-oslo-concurrency >= 3.8.0
Requires:       python-oslo-config >= 2:3.14.0
Requires:       python-oslo-db >= 1.14.0
Requires:       python-oslo-log >= 1.14.0
Requires:       python-oslo-messaging >= 5.2.0
Requires:       python-oslo-reports >= 0.6.0
Requires:       python-oslo-serialization >= 1.10.0
Requires:       python-oslo-service >= 1.10.0
Requires:       python-oslo-utils >= 3.16.0
Requires:       python-pbr
Requires:       python-requests
Requires:       python-six >= 1.9.0
Requires:       python-sqlalchemy >= 1.0.10


%description -n python-%{servicename}
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains the Neutron %{type} Python library.


%package -n python-%{servicename}-tests
Summary:        Neutron %{type} tests

Requires:       python-neutron-tests
Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}


%description -n python-%{servicename}-tests
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains Neutron %{type} test files.


%package -n openstack-neutron-vyatta-agent
Summary:        Neutron VPNaaS Vyatta agent

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}
# TODO(ihrachys): this agent also requires networking-brocade package but we
# don't have it in RDO so far. Users may install it from PyPI until someone
# contributes the package to RDO.


%description -n openstack-neutron-vyatta-agent
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains Neutron VPNaaS Vyatta agent.


%prep
%autosetup -n %{servicename}-%{upstream_version} -S git

# Let's handle dependencies ourselves
rm -f requirements.txt

# Kill egg-info in order to generate new SOURCES.txt
rm -rf neutron_vpnaas.egg-info

%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py build

# Generate configuration files
PYTHONPATH=. tools/generate_config_file_samples.sh
find etc -name *.sample | while read filename
do
    filedir=$(dirname $filename)
    file=$(basename $filename .sample)
    mv ${filename} ${filedir}/${file}
done


%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

# Create fake egg-info for the tempest plugin
%py2_entrypoint %{modulename} %{servicename}

# Move rootwrap files to proper location
install -d -m 755 %{buildroot}%{_datarootdir}/neutron/rootwrap
mv %{buildroot}/usr/etc/neutron/rootwrap.d/*.filters %{buildroot}%{_datarootdir}/neutron/rootwrap

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/neutron
mv etc/*.ini etc/*.conf %{buildroot}%{_sysconfdir}/neutron

# Install systemd units
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/neutron-vpn-agent.service
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/neutron-vyatta-agent.service

# Create and populate distribution configuration directory for VPN agent
# (the same as for L3 agent)
mkdir -p %{buildroot}%{_datadir}/neutron/l3_agent
ln -s %{_sysconfdir}/neutron/vpn_agent.ini %{buildroot}%{_datadir}/neutron/l3_agent/vpn_agent.conf

# Create configuration directory that can be populated by users with custom *.conf files
for agent in vpn vyatta; do
    mkdir -p %{buildroot}/%{_sysconfdir}/neutron/conf.d/neutron-$agent-agent
done

# Make sure neutron-server loads new configuration file
mkdir -p %{buildroot}/%{_datadir}/neutron/server
ln -s %{_sysconfdir}/neutron/%{modulename}.conf %{buildroot}%{_datadir}/neutron/server/%{modulename}.conf


%post
%systemd_post neutron-vpn-agent.service


%preun
%systemd_preun neutron-vpn-agent.service


%postun
%systemd_postun_with_restart neutron-vpn-agent.service


%post -n openstack-neutron-vyatta-agent
%systemd_post neutron-vyatta-agent.service


%preun -n openstack-neutron-vyatta-agent
%systemd_preun neutron-vyatta-agent.service


%postun -n openstack-neutron-vyatta-agent
%systemd_postun_with_restart neutron-vyatta-agent.service


%files
%license LICENSE
%doc AUTHORS CONTRIBUTING.rst README.rst
%{_bindir}/neutron-vpn-agent
%{_bindir}/neutron-vpn-netns-wrapper
%{_unitdir}/neutron-vpn-agent.service
%{_datarootdir}/neutron/rootwrap/vpnaas.filters
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/vpn_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/neutron_vpnaas.conf
%dir %{_sysconfdir}/neutron/conf.d
%dir %{_sysconfdir}/neutron/conf.d/neutron-vpn-agent
%{_datadir}/neutron/l3_agent/*.conf
%{_datadir}/neutron/server/%{modulename}.conf


%files -n openstack-neutron-vyatta-agent
%license LICENSE
%{_bindir}/neutron-vyatta-agent
%{_unitdir}/neutron-vyatta-agent.service
%dir %{_sysconfdir}/neutron/conf.d
%dir %{_sysconfdir}/neutron/conf.d/neutron-vyatta-agent


%files -n python-%{servicename}
%{python2_sitelib}/%{modulename}
%{python2_sitelib}/%{modulename}-%{version}-py%{python2_version}.egg-info
%exclude %{python2_sitelib}/%{modulename}/tests


%files -n python-%{servicename}-tests
%{python2_sitelib}/%{modulename}/tests
%{python2_sitelib}/%{modulename}_tests.egg-info

%changelog
