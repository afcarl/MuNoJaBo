"""
This file is part of MuNoJaBo.

MuNoJaBo is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not,
see <http://www.gnu.org/licenses/>.
"""

from sleekxmpp import ClientXMPP


class MuNoJaBoConnection(ClientXMPP):
    def __init__(self, config, notifications):
        ClientXMPP.__init__(self, config.get('xmpp', 'jid'), config.get('xmpp', 'pass'))
        self.add_event_handler("session_start", self.session_start)

        self.notifications = {}
        for jid, hosts in notifications.items():
            self.notifications[jid] = {}
            for host, graphs in hosts.items():
                msg = 'One or more fields on %s are in warning or critical condition.\n\n' % host

                for graph, fields in graphs.items():
                    msg += '%s:\n' % graph

                    for field in fields:
                        msg += '* %s is ' % field.name
                        if field.is_warning():
                            msg += 'approaching critical at %s (' % field.value
                            if field.warn.is_below(field.value):
                                msg += '%s below warning' % field.warn.get_distance(field.value)
                                if field.crit and field.crit.lower is not None:
                                    msg += ', %s until critical' % (field.value - field.crit.lower)
                            elif field.warn.is_above(field.value):
                                msg += '%s above warning' % field.warn.get_distance(field.value)
                                if field.crit and field.crit.upper is not None:
                                    msg += ', %s until critical' % (field.crit.upper - field.value)
                            else:
                                print('%s.%s not warning: %s (%s:%s)' % (graph, field.name,
                                      field.crit.lower, field.crit.upper))
                            msg += ')'
                        elif field.is_critical():
                            msg += 'critical at %s (' % field.value
                            if field.crit.is_below(field.value):
                                msg += "%s below " % field.crit.get_distance(field.value)
                            elif field.crit.is_above(field.value):
                                msg += "%s above " % field.crit.get_distance(field.value)
                            else:
                                print('%s.%s not critical: %s (%s:%s)' % (
                                    graph, field.name, field.crit.lower, field.crit.upper))
                            msg += 'the threshold)'
                        else:
                            print('%s.%s not critical/warning: %s (%s:%s/%s:%s)' % (
                                graph, field.name, field.warn.lower, field.warn.upper,
                                field.crit.lower, field.crit.upper))

                    msg += '\n'

                self.notifications[jid][host] = msg.strip()

    def session_start(self, event):
        self.send_presence()

        for jid, hosts in self.notifications.items():
            for host, msg in hosts.items():
                self.send_message(mto=jid, mbody=msg, mtype='chat')

        self.disconnect(wait=True)
