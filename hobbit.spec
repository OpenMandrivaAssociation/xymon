#define beta %{nil}
%define release %mkrel 11
%define _localstatedir %{_var}/lib
%{?!_logdir:%global _logdir /var/log}
%{?!mkrel:%define mkrel(c:) %{-c:0.%{-c*}.}%{!?_with_unstable:%(perl -e '$_="%{1}";m/(.\*\\D\+)?(\\d+)$/;$rel=${2}-1;re;print "$1$rel";').%{?subrel:%subrel}%{!?subrel:1}.%{?distversion:%distversion}%{?!distversion:%(echo $[%{mdkversion}/10])}}%{?_with_unstable:%{1}}%{?distsuffix:%distsuffix}%{?!distsuffix:mdk}}

%{?!mdkversion: %define notmdk 1}

Name: hobbit
Version: 4.2.0
Release: %release
Group: Networking/Other
URL: http://%{name}mon.sourceforge.net/
License: GPL
Source: %{name}-%{version}%{?beta:-RC-%beta}.tar.bz2
Patch:	hobbit-4.1.2-ignore-cdrom.patch
Patch1:	hobbit-4.1.2-fix-apache-alias.patch
Patch2:	hobbit-4.1.2p1-client-send-msgs.patch
Patch3:	http://www.hswn.dk/hobbitsw/patches/allinone.patch
Patch4: empty-dirinclude.patch
Patch5: http://bbwin.sourceforge.net/download/bbwin_4.2.patch
# From devmon 0.3.0rc1 extras/
Patch6: hobbit-4.2.0-devmon.patch
Patch7: hobbit-4.2.0-fix-critical-confreport.patch
Patch8: hobbit-4.2.0-increase-nk-priorities.patch
Source1: do_devmon.c
Summary: Hobbit network monitor
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires(pre): %{!?notmdk:apache}%{?notmdk:httpd}
Requires: %{name}-client = %{version} rrdtool
Conflicts: %{name}-client < 4.2.0-%mkrel 2
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
%patch3 -p0
%patch4 -p0
%patch5 -p0
%patch6 -p1 -b .devmon
cp %{SOURCE1} hobbitd/rrd/
%patch7 -p1
%patch8 -p1
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
install -m755 rpm/%{name}-client.init %{buildroot}/%{_initrddir}/%{name}-client
mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig
install rpm/%{name}-client.default %{buildroot}/%{_sysconfdir}/sysconfig/%{name}-client
mkdir -p %{buildroot}/%{_bindir}
ln -s %{_libdir}/%{name}/server/bin/bb{,cmd} %{buildroot}/%{_bindir}
rmdir %{buildroot}/%{_libdir}/%{name}/client/tmp
mkdir -p %{buildroot}/%{_localstatedir}/%{name}-client
ln -s %{_localstatedir}/%{name}-client %{buildroot}/%{_libdir}/%{name}/client/tmp
ln -s %{_localstatedir}/%{name}/tmp %{buildroot}/%{_libdir}/%{name}/tmp
rmdir %{buildroot}/%{_libdir}/%{name}/client/logs
perl -pi -e 's!^BBDISP=.*!include /var/run/%{name}client-runtime.cfg!;s/^BBDISPLAYS=.*$//g' %{buildroot}/%{_libdir}/%{name}/client%{_sysconfdir}/%{name}client.cfg

echo "directory %{_sysconfdir}/%{name}/hobbitlaunch.d" >> %{buildroot}/%{_sysconfdir}/%{name}/hobbitlaunch.cfg
echo "directory %{_sysconfdir}/%{name}/hobbitgraph.d" >> %{buildroot}/%{_sysconfdir}/%{name}/hobbitgraph.cfg
mkdir -p %{buildroot}/%{_sysconfdir}/%{name}/{hobbitlaunch,hobbitgraph,clientlaunch}.d

# server-only stuff
%if %{?!_without_server:1}%{?_without_server:0}
install -m755 rpm/%{name}-init.d %{buildroot}/%{_initrddir}/%{name}
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d
mv %{buildroot}/%{_sysconfdir}/%{name}/%{name}-apache.conf %{buildroot}/%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}/%{_sysconfdir}/logrotate.d
install -m644 rpm/%{name}.logrotate %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

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
perl -pi -e 's,/etc/default/,%{_sysconfdir}/sysconfig/,g;s,su (-c .+) (- hobbit),su $2 $1,g;s,/usr/lib,%{_libdir},g' %{buildroot}/%{_initrddir}/hobbit*

chmod u+w %{buildroot}/%{_libdir}/%{name}/client/bin/*

%clean
rm -rf %{buildroot}/

%pre client
if getent passwd %{name} 1>/dev/null 2>&1
then
echo "%{name} user present"
else
%_pre_useradd %{name} %{_libdir}/%{name} /bin/sh
fi
gpasswd -a hobbit adm

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
%exclude %{_sysconfdir}/%{name}/*client*.cfg
%exclude %{_sysconfdir}/%{name}/*client*.cfg
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/bb-*
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/*.csv
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}-apache.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/web
%{_initrddir}/%{name}
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/server
%attr(4710,root,hobbit) %{_libdir}/%{name}/server/bin/hobbitping
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


