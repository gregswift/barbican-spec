%global release_name juno

%{!?__initrddir: %define __initrddir /etc/rc.d/init.d}
%{!?_unitdir: %define _unitdir /usr/lib/systemd/system}

define version 2015.1
%{?milestone: %define version_milestone .%{milestone}}
%{?milestone: %define release_milestone -%{milestone}}

Name:    openstack-barbican
Version: %{version}%{?version_milestone}
Release: 1%{?dist}
Summary: OpenStack Barbican Key Manager

Group:   Python WSGI Application
License: ASL 2.0
Url:     http://github.com/cloudkeep/barbican
Source0: https://launchpad.net/barbican/%{release_name}/%{release_name}%{release_milestone}/+download/barbican-%{version}.tar.gz

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service

# TODO: Submit PR to add these to upstream
# patches_base=2014.2
#
Patch0001: 0001-Remove-runtime-dependency-on-pbr.patch
Patch0002: 0002-Removed-pyenv-references-in-barbican.sh.patch

BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-setuptools

Requires(pre): shadow-utils
Requires: python-barbican
%if 0%{?el6}
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
%else
Requires(post): systemd
Requires(preun): systemd
Requires(preun): systemd
BuildRequires: systemd
%endif

%description -n openstack-barbican
Openstack Barbican provides a ReST API for securely storing,
provisioning and managing secrets. It is aimed at being
useful for all environments, including large ephemeral Clouds.
Clients can generate various types of secrets like symmetric
and asymmetric keys, passphrases and binary data.


%package -n python-barbican
Summary: All python modules of Barbican.
Requires: python-alembic
Requires: python-babel
Requires: python-crypto
Requires: python-cryptography
Requires: python-eventlet
Requires: python-iso8601
Requires: python-jsonschema
Requires: python-kombu
Requires: python-netaddr
Requires: python-oslo-config
Requires: python-oslo-messaging
Requires: python-paste
Requires: python-paste-deploy
Requires: python-pbr
Requires: python-pecan
Requires: python-six
Requires: python-sqlalchemy
Requires: python-stevedore
Requires: python-webob

%description -n python-barbican
This package contains the barbican python library.
It is required by both the API(openstack-barbican) and
worker(openstack-barbican-worker) packages.


%package -n openstack-barbican-worker
Summary: Barbican Key Manager worker daemon
Requires: python-barbican

%description -n openstack-barbican-worker
This package contains scripts to start a barbican worker
on a worker node. It currently conflicts with the main package.


%package -n openstack-barbican-keystone-listener
Summary: Barbican Keystone Listener daemon
Requires: python-barbican

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.


%prep
%setup -q -n barbican-%{version}

%patch0001 -p1
%patch0002 -p1

rm -rf barbican.egg-info

echo %{version} > barbican/versioninfo
sed -i '/setuptools_git/d; /setup_requires/d; /install_requires/d; /dependency_links/d' setup.py
sed -i s/REDHATBARBICANVERSION/%{version}/ barbican/version.py
sed -i s/REDHATBARBICANRELEASE/%{release}/ barbican/version.py

# make doc build compatible with python-oslo-sphinx RPM
sed -i 's/oslosphinx/oslo.sphinx/' doc/source/conf.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requiers_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

%build
%{__python} setup.py build

%install
PBR_VERSION=%{version}%{version_milestone} %{__python} setup.py install -O1 --root %{buildroot}
mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}
install -m 644 etc/barbican/policy.json %{buildroot}%{_sysconfdir}/barbican/
install -m 644 etc/barbican/barbican* %{buildroot}%{_sysconfdir}/barbican/

%if 0%{?el6}
# upstart services
mkdir -p %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-api.conf %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-worker.conf %{buildroot}%{_sysconfdir}/init
%else
# systemd services
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-barbican-api.service
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-barbican-worker.service
%endif

# install log rotation
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m644 etc/logrotate.d/barbican-api %{buildroot}%{_sysconfdir}/logrotate.d/barbican-api


%pre
# Add the 'barbican' user
getent group barbican >/dev/null || groupadd -r barbican
getent passwd barbican >/dev/null || \
    useradd -r -g barbican -d %{_localstatedir}/lib/barbican -s /sbin/nologin \
    -c "Barbican Key Manager user account." barbican
exit 0


%clean
rm -rf %{buildroot}


%files -n openstack-barbican
%defattr(-,root,root)
%dir %{_localstatedir}/log/barbican
%{_sysconfdir}/logrotate.d/barbican-api
%attr(0755,root,root) %{_bindir}/barbican.sh
%attr(0755,root,root) %{_bindir}/barbican-db-manage.py
%config(noreplace) %{_sysconfdir}/barbican/*
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-api.conf
%else
%{_unitdir}/openstack-barbican-api.service
%endif

%files -n python-barbican
%defattr(-,barbican,barbican)
%{python_sitelib}/*
%dir %{_localstatedir}/lib/barbican

%files -n openstack-barbican-worker
%defattr(-,root,root)
%dir %{_localstatedir}/log/barbican
#%{_sysconfdir}/logrotate.d/barbican-worker
%attr(0755,root,root) %{_bindir}/barbican-worker.py
%config(noreplace) %{_sysconfdir}/barbican/barbican-api.conf
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-worker.conf
%else
%{_unitdir}/openstack-barbican-worker.service
%endif

%files -n openstack-barbican-keystone-listener
%attr(0755,root,root) %{_bindir}/barbican-keystone-listener.py
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-keystone-listener.conf
%else
%endif

%post -n openstack-barbican
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-api.service
/bin/systemctl daemon-reload
%endif

%post -n openstack-barbican-worker
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-worker.service
/bin/systemctl daemon-reload
%endif

%post -n openstack-barbican-keystone-listener
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
#%systemd_post openstack-barbican-keystone-listener.service
/bin/systemctl daemon-reload
%endif


%preun -n openstack-barbican
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-api >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-api.service
%endif

%preun -n openstack-barbican-worker
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-worker >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-worker.service
%endif

%preun -n openstack-barbican-keystone-listener
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-keystone-listener >/dev/null 2>&1 || :
fi
%else
#%systemd_preun openstack-barbican-keystone-listener.service
%endif


%postun -n openstack-barbican
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-api.service
%endif

%postun -n openstack-barbican-worker
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-worker.service
%endif

%postun -n openstack-barbican-keystone-listener
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
#%systemd_postun_with_restart openstack-barbican-keystone-listender.service
%endif


%changelog

* Thu Nov 13 2014 Abhishek Koneru <akoneru@redhat.com>
- Initial spec file for building openstack-barbican packages -
  openstack-barbican, python-barbican, openstack-barbican-worker.
