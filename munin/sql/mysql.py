import time

from backend import backend

class mysqldb(backend):
    def __init__(self, args, config):
        import MySQLdb
        
        self.args = args
        self.config = config
        self.conn = MySQLdb.connect(
            host=config.get('sql', 'host'),
            user=config.get('sql', 'user'),
            passwd=config.get('sql', 'pass'),
            db=config.get('sql', 'db')
            )
        self.cursor = self.conn.cursor()
        
    def has_alert(self, host, graph, field, cond):
        stamp = self.get_stamp()
        self.cursor.execute(
            """SELECT * FROM alerts
                WHERE stamp > %s AND host=%s AND graph=%s AND field=%s AND cond=%s""",
            (stamp, host, graph, field, cond)
        )
        
        if self.cursor.fetchone() == None:
            return False
        else:
            return True
        
    def get_alerts(self):
        pass
        
    def insert_alert(self, host, graph, field, cond):
        self.cursor.execute("INSERT INTO alerts(host, graph, field, cond) VALUES (%s, %s, %s, %s)",
            (host, graph, field, cond)
        )
        
    def get_stamp(self):
        secs = self.args.notification_freq
        return time.strftime( '%Y-%m-%d %H:%M:%S', time.gmtime( time.time() - secs ) )
        
    def clean(self):
        stamp = get_stamp()
        self.cursor.execute( "DELETE FROM alerts WHERE stamp < %s", (stamp) )
        
    def close(self):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()