#define beta %{nil}
%define release %mkrel 3
%define oldname hobbit
%define _localstatedir %{_var}/lib
%{?!_logdir:%global _logdir /var/log}
%{?!mkrel:%define mkrel(c:) %{-c:0.%{-c*}.}%{!?_with_unstable:%(perl -e '$_="%{1}";m/(.\*\\D\+)?(\\d+)$/;$rel=${2}-1;re;print "$1$rel";').%{?subrel:%subrel}%{!?subrel:1}.%{?distversion:%distversion}%{?!distversion:%(echo $[%{mdkversion}/10])}}%{?_with_unstable:%{1}}%{?distsuffix:%distsuffix}%{?!distsuffix:mdk}}

%{?!mdkversion: %define notmdk 1}

Name: xymon
Version: 4.2.3
Release: %release
Group: Networking/Other
URL: http://hobbitmon.sourceforge.net/
License: GPL
Source: http://downloads.sourceforge.net/hobbitmon/%{name}-%{version}%{?beta:-RC-%beta}.tar.gz
Patch:	hobbit-4.1.2-ignore-cdrom.patch
Patch1:	hobbit-4.1.2-fix-apache-alias.patch
Patch2:	hobbit-4.1.2p1-client-send-msgs.patch
Patch3: xymon-4.2.3-devmon-multi-DS.patch
Patch8: hobbit-4.2.0-increase-nk-priorities.patch
Patch9: xymon-4.2-fix-graph-zoom-konq-firefox35.path
#Source1: do_devmon.c
# From devmon extras/devmon-graph.cfg
Source2: devmon-graph.cfg
Summary: Hobbit network monitor
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires(pre): %{!?notmdk:apache}%{?notmdk:httpd}
Requires: %{name}-client = %{version} rrdtool
Conflicts: %{name}-client < 4.2.0-%mkrel 2
Obsoletes: %{oldname} < 4.2.2
Provides: %{oldname} = %{version}-%{release}
%{!?notmdk:Requires(pre): rpm-helper}
%if %{?!_without_server:1}%{?_without_server:0}
BuildRequires: fping
BuildRequires: openssl-devel
BuildRequires: pcre-devel
BuildRequires: rrdtool-devel
BuildRequires: openldap-devel
%endif

%description
Hobbit is a system for monitoring your network servers and
applications. It is heavily inspired by the Big Brother
tool, but is a complete re-implementation with a lot of added
functionality and performance improvements.

%package client
Summary: Hobbit client reporting data to the Hobbit server
Group: Networking/Other
Obsoletes: %{oldname}-client < 4.2.2
Provides: %{oldname}-client = %{version}-%{release}
%{!?notmdk:Requires(pre): rpm-helper}

%description client
This package contains a client for the Hobbit monitor. Clients
report data about the local system to the monitor, allowing it
to check on the status of the system load, filesystem utilisation,
processes that must be running etc.

%prep
%setup -q %{?beta: -n %{name}-%{version}-RC-%{beta}}
%patch -p1
%patch1 -p1
#cp %{SOURCE1} hobbitd/rrd/
%patch3 -p1 -b .devmon
%patch8 -p1
%patch9 -p0 -b .fixgraphzoom
#%patch2 -p1
# test should really check for RC -ne 127 (file not found), 1 is also acceptable
perl -pi -e 's/-eq 0/-ne 127/g' build/fping.sh

%build
export ENABLESSL=y \
ENABLELDAP=y \
ENABLELDAPSSL=y \
BBUSER=%{name} \
BBTOPDIR=%{_libdir}/%{name} \
BBVAR=%{_localstatedir}/%{name} \
BBHOSTURL=/%{name} \
CGIDIR=%{_libdir}/%{name}/cgi-bin \
BBCGIURL=/%{name}-cgi \
SECURECGIDIR=%{_libdir}/%{name}/cgi-secure \
SECUREBBCGIURL=/%{name}-seccgi \
HTTPDGID=apache \
BBLOGDIR=%{_logdir}/%{name} \
BBHOSTNAME=localhost \
BBHOSTIP=127.0.0.1 \
MANROOT=%{_mandir} \
BARS=all \
USENEWHIST=y \
PIXELCOUNT=960 \
INSTALLBINDIR=%{_libdir}/%{name}/server/bin \
INSTALLETCDIR=%{_sysconfdir}/%{name} \
INSTALLWEBDIR=%{_sysconfdir}/%{name}/web \
INSTALLEXTDIR=%{_libdir}/%{name}/server/ext \
INSTALLTMPDIR=%{_localstatedir}/%{name}/tmp \
INSTALLWWWDIR=%{_localstatedir}/%{name}/www \
CONFTYPE=server \
USEHOBBITPING=n
%if %{?!_without_server:1}%{?_without_server:0}
./configure
%else
./configure --client
%endif
#%configure --server

perl -pi -e 's/ch(own|grp)/echo chown/g' web/Makefile
PKGBUILD=1 make

%install
rm -Rf %{buildroot}
INSTALLROOT=%{buildroot}/ PKGBUILD=1 make install
mkdir -p %{buildroot}/%{_initrddir}
which install
install -m755 rpm/%{oldname}-client.init %{buildroot}/%{_initrddir}/%{name}-client
mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig
install rpm/%{oldname}-client.default %{buildroot}/%{_sysconfdir}/sysconfig/%{name}-client
mkdir -p %{buildroot}/%{_bindir}
ln -s %{_libdir}/%{name}/server/bin/bb{,cmd} %{buildroot}/%{_bindir}
rmdir %{buildroot}/%{_libdir}/%{name}/client/tmp
mkdir -p %{buildroot}/%{_localstatedir}/%{name}-client
ln -s %{_localstatedir}/%{name}-client %{buildroot}/%{_libdir}/%{name}/client/tmp
ln -s %{_localstatedir}/%{name}/tmp %{buildroot}/%{_libdir}/%{name}/tmp
rmdir %{buildroot}/%{_libdir}/%{name}/client/logs
perl -pi -e 's!^BBDISP=.*!include /var/run/%{name}client-runtime.cfg!;s/^BBDISPLAYS=.*$//g' %{buildroot}/%{_libdir}/%{name}/client%{_sysconfdir}/%{oldname}client.cfg

echo "directory %{_sysconfdir}/%{name}/hobbitlaunch.d" >> %{buildroot}/%{_sysconfdir}/%{name}/hobbitlaunch.cfg
echo "directory %{_sysconfdir}/%{name}/hobbitgraph.d" >> %{buildroot}/%{_sysconfdir}/%{name}/hobbitgraph.cfg
mkdir -p %{buildroot}/%{_sysconfdir}/%{name}/{hobbitlaunch,hobbitgraph,clientlaunch}.d
install -m 644 %{SOURCE2} %{buildroot}/%{_sysconfdir}/%{name}/hobbitgraph.d/devmon.cfg

# server-only stuff
%if %{?!_without_server:1}%{?_without_server:0}
install -m755 rpm/%{oldname}-init.d %{buildroot}/%{_initrddir}/%{name}
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d
mv %{buildroot}/%{_sysconfdir}/%{name}/%{oldname}-apache.conf %{buildroot}/%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}/%{_sysconfdir}/logrotate.d
install -m644 rpm/%{oldname}.logrotate %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}
perl -pi -e 's/%{oldname}/%{name}/g' %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

install -d %{buildroot}/%{_datadir}/%{name}/www
mv %{buildroot}%{_localstatedir}/%{name}/www/{gifs,help} %{buildroot}/%{_datadir}/%{name}/www
ln -s %{_datadir}/%{name}/www/{gifs,help} %{buildroot}%{_localstatedir}/%{name}/www/
export DONT_CLEANUP=1
touch %{buildroot}/%{_sysconfdir}/%{name}/%{name}-nkview.cfg.bak
# end of server-only stuff
%else
# extra stuff to do in client-only build
install -d %{buildroot}/%{_sysconfdir}/%{name}
install -d %{buildroot}/%{_logdir}/%{name}
rm -f %{buildroot}/%{_bindir}/bb*
rm -f %{buildroot}/%{_libdir}/%{name}/tmp
# end of client-only build
%endif

ln -s %{_logdir}/%{name} %{buildroot}/%{_libdir}/%{name}/client/logs
mv %{buildroot}/%{_libdir}/%{name}/client/etc/*.cfg %{buildroot}/%{_sysconfdir}/%{name}/
rmdir %{buildroot}/%{_libdir}/%{name}/client/etc
ln -sf %{_sysconfdir}/%{name} %{buildroot}/%{_libdir}/%{name}/client/etc
echo "directory %{_sysconfdir}/%{name}/hobbitlaunch.d" >> %{buildroot}/%{_sysconfdir}/%{name}/clientlaunch.cfg

perl -pi -e 's,\$HOBBITCLIENTHOME,\$HOME/client,g' %{buildroot}/%{_sysconfdir}/%{name}/hobbitclient.cfg
perl -pi -e 's,/etc/default/,%{_sysconfdir}/sysconfig/,g;s,su (-c .+) (- %{oldname}),su - %{name} $1,g;s,/usr/lib/%{oldname},%{_libdir}/%{name},g;s/%{oldname}$/%{name}/g;s/ %{oldname}/ %{name}/g;s/%{oldname} /%{name} /g;s/%{oldname}(-?client)/%{name}${1}/g' %{buildroot}/%{_initrddir}/%{name}*

chmod u+w %{buildroot}/%{_libdir}/%{name}/client/bin/*

%clean
rm -rf %{buildroot}/

%pre client
# Upgrade from hobbit to xymon:
if getent passwd %{oldname} 1>/dev/null 2>&1
then
  echo "Migrating from %{oldname} to %{name}"
  if [ -x %{_initrddir}/%{oldname} ]
    then %{_initrddir}/%{oldname} stop
  elif [ -x %{_initrddir}/%{oldname}-client ]
    then %{_initrddir}/%{oldname}-client stop
  fi
  retval=$?
  /usr/sbin/groupmod -n %{name} %{oldname}||echo "groupmod failed: $?"
  /usr/sbin/usermod -l %{name} %{oldname}||echo "usermod -l failed: $?"
  /usr/sbin/usermod -d %{_libdir}/%{name} -m %{name}||echo "usermod -d failed: $?"
  # Copy config files before upgrade to get .rpmnew files instead of
  # clobbering
  echo "Copying init script settings"
  if [ -e %{_sysconfdir}/sysconfig/%{oldname} ]
  then %__cp -a %{_sysconfdir}/sysconfig/%{oldname} %{_sysconfdir}/sysconfig/%{name}
  fi
  if [ -e %{_sysconfdir}/sysconfig/%{oldname}-client ]
  then %__cp -a %{_sysconfdir}/sysconfig/%{oldname}-client %{_sysconfdir}/sysconfig/%{name}-client
  fi
  echo "Copying existing configuration from %{_sysconfdir}/%{oldname} to %{_sysconfdir}/%{name}"
  %__cp -a %{_sysconfdir}/%{oldname} %{_sysconfdir}/%{name}
  echo "Replacing %{oldname} with %{name} where relevant in config"
  %__perl -p -i.hobbit-to-xymon -e 's,%{_libdir}/%{oldname},%{_libdir}/%{name},g;s,%{_sysconfdir}/%{oldname},%{_sysconfdir}/%{name},g' `find %{_sysconfdir}/%{name} -type f`
  echo "Moving data files from %{_localstatedir}/%{oldname} to %{_localstatedir}/%{name}"
  %__mv %{_localstatedir}/%{oldname} %{_localstatedir}/%{name}
  echo "Moving log files from %{_logdir}/%{oldname} to %{_logdir}/%{name}"
  %__mv %{_logdir}/%{oldname} %{_logdir}/%{name}
  echo "Migration complete"
  echo -e '\n\nBeware, any files reported below as .rpmsave should probably be restored before starting xymon!\n\n'
fi

if getent passwd %{name} 1>/dev/null 2>&1
then
echo "%{name} user present"
else
%_pre_useradd %{name} %{_libdir}/%{name} /bin/sh
fi
gpasswd -a %{name} adm

%post
if [ $1 == 1 ]
then /etc/init.d/httpd reload
fi
%_post_service %{name}
/sbin/chkconfig --list %{name}-client |grep -q on && /sbin/chkconfig %{name}-client off ||:

%post client
# if no server is installed, start the client via init script
if [ -f /etc/init.d/%{name} ]
then
echo "server package installed, not starting client at boot"
else
%_post_service %{name}-client
fi

%preun
%_preun_service %{name}

%preun client
%_preun_service %{name}-client

%if %{?!_without_server:1}%{?_without_server:0}
%files
%defattr(-,root,root) 
%doc README README.CLIENT Changes* COPYING CREDITS
%attr(644,root,root) %doc %{_mandir}/man*/*
%exclude %{_mandir}/man1/bb.*
%exclude %{_mandir}/man1/bbcmd.*
%exclude %{_mandir}/man1/bbdigest.*
%exclude %{_mandir}/man1/clientupdate.*
%exclude %{_mandir}/man1/logfetch.*
%exclude %{_mandir}/man1/orcahobbit.*
%exclude %{_mandir}/man5/hobbitlaunch.cfg*
%exclude %{_mandir}/man8/hobbitlaunch.*
%exclude %{_mandir}/man8/msgcache.*
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/*.cfg*
%attr(664,root,apache) %config(noreplace) %{_sysconfdir}/%{name}/%{name}-nkview.cfg*
%dir %{_sysconfdir}/%{name}/hobbitgraph.d
%{_sysconfdir}/%{name}/hobbitgraph.d/*.cfg
%exclude %{_sysconfdir}/%{name}/*client*.cfg
%exclude %{_sysconfdir}/%{name}/*client*.cfg
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/bb-*
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/*.csv
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf.d/%{oldname}-apache.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/web
%{_initrddir}/%{name}
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/server
%attr(4710,root,%{name}) %{_libdir}/%{name}/server/bin/hobbitping
%{_libdir}/%{name}/cgi-bin
%{_libdir}/%{name}/cgi-secure
%{_libdir}/%{name}/tmp
%{_bindir}/*
%attr(775,%{name},%{name}) %dir %{_localstatedir}/%{name}/www
%attr(775,%{name},apache) %dir %{_localstatedir}/%{name}/www/rep
%attr(775,%{name},apache) %dir %{_localstatedir}/%{name}/www/snap
%attr(644,root,root) %config(noreplace) %{_localstatedir}/%{name}/www/menu/*
%{_localstatedir}/%{name}/www/gifs
%{_localstatedir}/%{name}/www/help
%{_datadir}/%{name}
%defattr(-,%{name},%{name})
%dir %{_localstatedir}/%{name}
%dir %{_localstatedir}/%{name}/histlogs
%dir %{_localstatedir}/%{name}/tmp
%dir %{_localstatedir}/%{name}/hist
%dir %{_localstatedir}/%{name}/rrd
%dir %{_localstatedir}/%{name}/acks
%dir %{_localstatedir}/%{name}/www/notes
%endif

%files client
%defattr(-, root, root) 
%doc README README.CLIENT Changes* COPYING CREDITS
%attr(644,root,root) %doc %{_mandir}/man1/bb.*
%attr(644,root,root) %doc %{_mandir}/man1/bbcmd.*
%attr(644,root,root) %doc %{_mandir}/man1/bbdigest.*
%attr(644,root,root) %doc %{_mandir}/man1/clientupdate.*
%attr(644,root,root) %doc %{_mandir}/man1/logfetch.*
%attr(644,root,root) %doc %{_mandir}/man1/orcahobbit.*
%attr(644,root,root) %doc %{_mandir}/man5/hobbitlaunch.cfg*
%attr(644,root,root) %doc %{_mandir}/man8/hobbitlaunch.*
%attr(644,root,root) %doc %{_mandir}/man8/msgcache.*
%{_libdir}/%{name}/client
%dir %{_sysconfdir}/%{name} 
%config(noreplace) %{_sysconfdir}/%{name}/*client*.cfg
%dir %{_sysconfdir}/%{name}/hobbitlaunch.d
%attr(755,root,root) %{_initrddir}/%{name}-client
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}-client
%attr(755,%{name},%{name}) %dir %{_logdir}/%{name}
%attr(755,%{name},%{name}) %dir %{_libdir}/%{name}/client/ext
%attr(755,%{name},%{name}) %dir %{_localstatedir}/%{name}-client


