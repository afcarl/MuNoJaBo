from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import JID

class MuNoJaBoConnection(ClientXMPP):
    def __init__(self, config, notifications):
        ClientXMPP.__init__(self, config.get('xmpp', 'jid'), config.get('xmpp', 'pass'))
        self.add_event_handler("session_start", self.session_start)
        
        self.notifications = {}
        for jid_str, hosts in notifications.items():
            jid = JID(jid_str)
            self.notifications[jid] = {}
            for host, graphs in hosts.items():
                msg = 'One or more fields on %s are in warning or critical condition.\n\n'%host
                for graph, fields in graphs.items():
                    lines = []
                    for field in fields:
                        lines.append(str(field))
                    
                    msg += '%s:\n%s\n\n'%(graph, '\n'.join(lines))
                
                self.notifications[jid][host] = msg.strip()
        
    def session_start(self, event):
        self.send_presence()
        
        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        try:
            self.get_roster()
        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()
            
        for jid, hosts in self.notifications.items():
            for host, msg in hosts.items():
                self.send_message(mto=jid, mbody=msg.strip(), mtype='chat')
        
        self.disconnect(wait=True)