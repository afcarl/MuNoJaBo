from sleekxmpp import ClientXMPP

class MuNoJaBoConnection(ClientXMPP):
    def __init__(self, config, mto, mbody):
        ClientXMPP.__init__(self, config.get('xmpp', 'jid'), config.get('xmpp', 'pass'))
        self.mto = mto
        self.mbody = mbody
        
        self.add_event_handler("session_start", self.session_start)
        
        
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
            
        self.send_message(mto=self.mto, mbody=self.mbody, mtype='chat')
        
        self.disconnect(wait=True)