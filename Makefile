#SERIAL 201411242120

# Base the name of the software on the spec file
PACKAGE := $(shell basename *.spec .spec)
# Override this arch if the software is arch specific
ARCH = noarch

# Variables for clean build directory tree under repository
BUILDDIR = ./build
ARTIFACTDIR = ./artifacts
SDISTDIR = ${ARTIFACTDIR}/sdist
RPMBUILDDIR = ${BUILDDIR}/rpm-build
RPMDIR = ${ARTIFACTDIR}/rpms
DEBBUILDDIR = ${BUILDDIR}/deb-build
DEBDIR = ${ARTIFACTDIR}/debs

# base rpmbuild command that utilizes the local buildroot
# not using the above variables on purpose.
# if you can make it work, PRs are welcome!
BASE_RPMBUILD = rpmbuild --define "_topdir %(pwd)/build" \
	--define "_sourcedir  %(pwd)/artifacts/sdist" \
	--define "_builddir %{_topdir}/rpm-build" \
	--define "_srcrpmdir %{_rpmdir}" \
	--define "_rpmdir %(pwd)/artifacts/rpms"

ifdef MILESTONE
RPMBUILD = ${BASE_RPMBUILD} --define "milestone ${MILESTONE}"
else
RPMBUILD = ${BASE_RPMBUILD}
endif

# Allow which python to be overridden at the environment level
PYTHON := $(shell which python)

ifneq ("$(wildcard setup.py)","")
GET_SDIST = ${PYTHON} setup.py sdist -d "${SDISTDIR}"
else
  ifdef MILESTONE
GET_SDIST = spectool -g -C ${SDISTDIR} --define "milestone ${MILESTONE}" ${PACKAGE}.spec
  else
GET_SDIST = spectool -g -C ${SDISTDIR} ${PACKAGE}.spec
  endif
endif

all: rpms

clean:
	rm -rf ${BUILDDIR}/ *~
	rm -rf *.egg-info
	find . -name '*.pyc' -exec rm -f {} \;

clean_all: clean
	rm -rf ${ARTIFACTDIR}/

build: clean
	${PYTHON} setup.py build -f

install: build
	${PYTHON} setup.py install -f --root ${DESTDIR}

install_rpms: rpms
	yum install ${RPMDIR}/${ARCH}/${PACKAGE}*.${ARCH}.rpm

reinstall: uninstall install

uninstall: clean
	rm -f /usr/bin/${PACKAGE}
	rm -rf /usr/lib/python*/site-packages/${PACKAGE}

uninstall_rpms: clean
	rpm -e ${PACKAGE}

sdist:
	mkdir -p ${SDISTDIR}
	${GET_SDIST}

prep_rpmbuild: prep_build
	mkdir -p ${RPMBUILDDIR}
	mkdir -p ${RPMDIR}
	cp ${SDISTDIR}/*gz ${RPMBUILDDIR}/

rpms: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec

prep_build: sdist
	mkdir -p ${BUILDDIR}

prep_debbuild: prep_build
	mkdir -p ${DEBBUILDDIR}
	mkdir -p ${DEBDIR}
	SDISTPACKAGE=`ls ${SDISTDIR}`; \
	BASE=`basename $$SDISTPACKAGE .tar.gz`; \
	DEBBASE=`echo $$BASE | sed 's/-/_/'`; \
	TARGET=${DEBBUILDDIR}/$$DEBBASE.orig.tar.gz; \
	ln -f -s ../../${SDISTDIR}/$$SDISTPACKAGE $$TARGET; \
	tar -xz -f $$TARGET -C ${DEBBUILDDIR}; \
	rm -rf ${DEBBUILDDIR}/$$BASE/debian; \
	cp -pr debian/ ${DEBBUILDDIR}/$$BASE

debs: prep_debbuild
	SDISTPACKAGE=`ls ${SDISTDIR}`; \
	BASE=`basename $$SDISTPACKAGE .tar.gz`; \
	cd ${DEBBUILDDIR}/$$BASE; \
	debuild -uc -us
	mv ${DEBBUILDDIR}/*.deb ${DEBDIR}/

