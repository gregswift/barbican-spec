%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2:        %global __python2 /usr/bin/python2}
%{!?python2_sitelib:  %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global release_name juno
%global release_version 2014.2
#global release_number 2

# We optionally support both release_number and milestone
# as definiable build paramters.  This is useful for non-stable
# building.
# release_number: used for primary milestone release candidates
#   If populated will auto populate the milestone macro and
# milestone: Used for primary milestone release candidates and
#   for incremental development builds.
%{?release_number: %define milestone 0b%{release_number}}
%{?milestone: %define version_milestone .%{milestone}}

# Using the above we generate the macro for the Source URL
%{?release_number: %define release_version %{release_name}-%{release_number}}
%{!?release_version: %define release_version %{release_name}}

Name:    openstack-barbican
Version: 2014.2
Release: 5%{?version_milestone}%{?dist}
Summary: OpenStack Barbican Key Manager

Group:   Applications/System
License: ASL 2.0
Url:     https://github.com/openstack/barbican
Source0: https://launchpad.net/barbican/%{release_name}/%{release_version}/+download/barbican-%{version}%{?version_milestone}.tar.gz

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service
%if %{release_name} != juno
Source3: openstack-barbican-keystone-listener.service
%endif

BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-oslo-config
BuildRequires: python-oslo-messaging
BuildRequires: python-pbr

Requires(pre): shadow-utils
Requires: uwsgi
Requires: uwsgi-plugin-python
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
Summary: All python modules of Barbican
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


%package -n openstack-barbican-api
Summary: Barbican Key Manager API daemon
Requires: python-barbican

%description -n openstack-barbican-api
This package contains scripts to start a barbican api instance.


%package -n openstack-barbican-worker
Summary: Barbican Key Manager worker daemon
Requires: python-barbican
# Todo for now we rely on the -api package because of a shared config file
Requires: openstack-barbican-api

%description -n openstack-barbican-worker
This package contains scripts to start a barbican worker
on a worker node.


%if "%{release_name}" != "juno"
%package -n openstack-barbican-keystone-listener
Summary: Barbican Keystone Listener daemon
Requires: python-barbican

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.
%endif

%prep
%setup -q -n barbican-%{version}%{?version_milestone}

rm -rf barbican.egg-info

# make doc build compatible with python-oslo-sphinx RPM
sed -i 's/oslosphinx/oslo.sphinx/' doc/source/conf.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requiers_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

%build
%{__python2} setup.py build

%install
PBR_VERSION=%{version}%{?version_milestone} %{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_sysconfdir}/barbican/vassals
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}

install -m 644 etc/barbican/policy.json %{buildroot}%{_sysconfdir}/barbican/
install -m 644 etc/barbican/barbican* %{buildroot}%{_sysconfdir}/barbican/
install -m 644 etc/barbican/vassals/* %{buildroot}%{_sysconfdir}/barbican/vassals/
# Generally its not very clean to put scripts with their language extension into
# the bin directories. Upstream has a bug to fix this, we are doing it manually for now
# https://bugs.launchpad.net/barbican/+bug/1454587
install -m 755 bin/barbican-worker.py %{buildroot}%{_bindir}/barbican-worker
install -m 755 bin/barbican-db-manage.py %{buildroot}%{_bindir}/barbican-db-manage
%if "%{release_name}" != "juno"
install -m 755 bin/barbican-keystone-listener.py %{buildroot}%{_bindir}/baribcan-keystone-listener
%endif

# Remove the bash script since its more dev focused
rm -f %{buildroot}%{_bindir}/barbican.sh

%if 0%{?el6}
# upstart services
mkdir -p %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-api.conf %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-worker.conf %{buildroot}%{_sysconfdir}/init
%if "%{release_name}" != "juno"
install -m 644 etc/init/barbican-keystone-listener.conf %{buildroot}%{_sysconfdir}/init
%endif
%else
# systemd services
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-barbican-api.service
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-barbican-worker.service
%if "%{release_name}" != "juno"
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_unitdir}/openstack-barbican-keystone-listener.service
%endif
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


%files -n openstack-barbican
%doc LICENSE
%dir %{_sysconfdir}/barbican
%dir %{_localstatedir}/log/barbican
%attr(0755,root,root) %{_bindir}/barbican-db-manage

%files -n python-barbican
%doc LICENSE
%defattr(-,barbican,barbican)
%{python2_sitelib}/barbican
%{python2_sitelib}/barbican-%{version}-py?.?.egg-info
%dir %{_localstatedir}/lib/barbican

%files -n openstack-barbican-api
%config(noreplace) %{_sysconfdir}/logrotate.d/barbican-api
%config(noreplace) %{_sysconfdir}/barbican/barbican-admin-paste.ini
%config(noreplace) %{_sysconfdir}/barbican/barbican-api-paste.ini
%config(noreplace) %{_sysconfdir}/barbican/barbican-api.conf
%config(noreplace) %{_sysconfdir}/barbican/policy.json
%config(noreplace) %{_sysconfdir}/barbican/vassals/barbican-api.ini
%config(noreplace) %{_sysconfdir}/barbican/vassals/barbican-admin.ini
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-api.conf
%else
%{_unitdir}/openstack-barbican-api.service
%endif

%files -n openstack-barbican-worker
%doc LICENSE
%defattr(-,root,root)
%dir %{_sysconfdir}/barbican
%dir %{_localstatedir}/log/barbican
%attr(0755,root,root) %{_bindir}/barbican-worker
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-worker.conf
%else
%{_unitdir}/openstack-barbican-worker.service
%endif

%if "%{release_name}" != "juno"
%files -n openstack-barbican-keystone-listener
%doc LICENSE
%attr(0755,root,root) %{_bindir}/barbican-keystone-listener
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-keystone-listener.conf
%else
%{_unitdir}/openstack-barbican-keystone-listener.service
%endif
%endif

%post -n openstack-barbican-api
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

%if "%{release_name}" != "juno"
%post -n openstack-barbican-keystone-listener
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-keystone-listener.service
/bin/systemctl daemon-reload
%endif
%endif

%preun -n openstack-barbican-api
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

%if "%{release_name}" != "juno"
%preun -n openstack-barbican-keystone-listener
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-keystone-listener >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-keystone-listener.service
%endif
%endif

%postun -n openstack-barbican-api
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-api.service
%endif

%postun -n openstack-barbican-worker
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-worker.service
%endif

%if "%{release_name}" != "juno"
%postun -n openstack-barbican-keystone-listener
%if 0%{?rhel} != 6
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-keystone-listender.service
%endif
%endif

%changelog
* Mon Jul 06 2015 Greg Swift <greg.swift@rackspace.net> - 2014.2-5
- Update to remove .py extension from bins, and ensure the service files match

* Tue Jun 30 2015 Michael McCune <msm@redhat.com> - 2014.2-4
- removing pbr runtime replacement patch
- removing patch for barbican.sh as this file is not used for runtime
- adding vassals to installed files
- changing python file inclusion to specifically mention barbican files

* Tue Apr 07 2015 Greg Swift <greg.swift@rackspace.com> - 2014.2-3
- Created -api subpackage
- Made worker require -api rather than conflict with it due to shared config
- Other small cleanup for review request

* Wed Apr 01 2015 Greg Swift <greg.swift@rackspace.com> - 2014.2-2
- use versioned python macros
- wrap patches in a juno specific conditional to deprecate them
- drop %clean and %defattr
- change URL to openstack github rather than cloudkeep github

* Mon Feb 09 2015 Greg Swift <greg.swift@rackspace.com> - 2014.2-1
- Revamped for fedora packaging request

* Thu Nov 13 2014 Abhishek Koneru <akoneru@redhat.com>
- Initial spec file for building openstack-barbican packages -
  openstack-barbican, python-barbican, openstack-barbican-worker.
