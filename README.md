**MuNoJaBo** stands for "munin jabber notification bot". MuNoJaBo is a script
that is designed to be called by munin when the values monitored by munin
are at "warning" or "critical". As of version 2.0 this script also uses a simple
mysql-database to store notificatons that where already send and does not send
notifications again for six hours.

Installation
============

This script is written for Python3 and requires SleekXMPP and dnspython3. If
you want to run it in a virtualenv, just initialize the virtualenv and install
the required dependencies:

```
virtualenv -p /usr/bin/python3 .
source bin/activate
pip install -r requirements.txt
```

Under Debian/Ubuntu, you can also install the required dependencies:

```
apt-get install python3-sleekxmpp python3-dnspython
```

**NOTE:** The below examples assume that you symlinked both
``munojabo-save.py`` and ``munojabo-notify.py`` inside our PATH (e.g.
``/usr/local/bin/`` and dependencies were installed globally. If you want to
keep everything inside a virtualenv, use e.g. ``/root/MuNoJaBo/bin/python
/root/MuNoJaBo/munojabo-notify.py`` instead (this assumes you cloned the
git-repository to ``/root`` and initialized the virtualenv diretly inside of
it).

Munin configuration
===================

With **MuNoJaBo**, the script itself takes care on deciding what message should
be sent when to which user. So you only configure one contact to call the
script itself, and configure the contacts for each host in the
MuNoJaBo-specific configuration file (see below).

To configure munin to use this script, add a contact line like this to your
munin.conf and add it as contact address for your hosts:

```
[host.example.com]
    contacts munojabo

contact.munojabo.command munojabo-save.py 
    --host=${var:host} \
	"--graph=${var:graph_title}" \
	"--warning=${loop<;>:wfields \
		${var:label}=${var:value},${var:wrange},${var:crange}}" \
	"--critical=${loop<;>:cfields \
		${var:label}=${var:value},${var:wrange},${var:crange}}" \
	"--unknown=${loop<;>:ufields \
		${var:label}=${var:value},${var:wrange},${var:crange}}"
```

Please also see the 
[How To Contact](http://munin.projects.linpro.no/wiki/HowToContact)
in the Munin documentation.

MuNoJaBo configuration
======================

This script requires a config-file located at ``/etc/munojabo.conf``. An example
configuration file can be found in this directory. Just fill in the appropriate
details.

The only thing missing is that ```munojabo-notify.py``` must be called by cron
to actually send the notifications. Here is an example line you could add to
e.g. ``/etc/cron.d/munojabo/``:

```
*/5 *   * * *   munin   munojabo-notify.py
```

Test configuration
==================

You can save a fake alert:

```
munojabo-save.py --host=host.example.com --graph=test --warning="warn-field=30,:20,:35" --critical= --unknown=
munojabo-notify.py
```

If everything is configured correctly, you should receive a message via jabber:

```
One or more fields on host.example.com are in warning or critical condition.

test:
* warn-field is approaching critical at 30 (10 above warning, 5 until critical)
```
