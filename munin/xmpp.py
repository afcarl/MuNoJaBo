"""
This file is part of munojabo.

munojabo is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
                msg = 'One or more fields on %s are in warning or critical condition.\n\n'%host
                
                for graph, fields in graphs.items():
                    msg += '%s:\n' % graph
                    
                    for field in fields:
                        msg += '* %s is ' % field.name
                        if field.is_warning():
                            msg += 'approaching critical at %s (' % field.value
                            if field.warn.is_below(field.value):
                                msg += '%s below warning' % field.warn.get_distance(field.value)
                                if field.crit and field.crit.lower != None:
                                    msg += ', %s until critical' % (field.value - field.crit.lower)
                            else:
                                msg += '%s above warning' % field.warn.get_distance(field.value)
                                if field.crit and field.crit.upper != None:
                                    msg += ', %s until critical' % (field.crit.upper - field.value)
                            msg +=')'
                        else:
                            msg += 'critical at %s (' % field.value
                            if field.crit.is_below(field.value):
                                msg += "%s below " % field.crit.get_distance(field.value)
                            else:
                                msg += "%s above " % field.crit.get_distance(field.value)
                            msg += 'the threshold)'
                    msg += '\n'
                
                self.notifications[jid][host] = msg.strip()
        
    def session_start(self, event):
        self.send_presence()
            
        for jid, hosts in self.notifications.items():
            for host, msg in hosts.items():
                self.send_message(mto=jid, mbody=msg, mtype='chat')
        
        self.disconnect(wait=True)