import os, time, sqlite3

from backend import backend

class sqlite(backend):
    def __init__(self, config):
        self.config = config
        self.conn = sqlite3.connect(os.path.expanduser(self.config.get('sql', 'db')))
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            stamp INTEGER, host TEXT, graph TEXT, field TEXT, cond TEXT)'''
        )
        self.conn.commit()
        
    def has_alert(self, host, graph, field, cond):
        stamp = self.get_stamp()
        self.cursor.execute(
            """SELECT * FROM alerts
                WHERE stamp > ? AND host=? AND graph=? AND field=? AND cond=?""",
            (stamp, host, graph, field, cond)
        )
        
        if len(self.cursor.fetchall()) == 0:
            return False
        else:
            return True
        
    def insert_alert(self, host, graph, field, cond):
        self.cursor.execute("""INSERT INTO alerts(stamp, host, graph, field, cond)
                VALUES (?, ?, ?, ?, ?)""",
            (time.time(), host, graph, field, cond)
        )
        
    def get_stamp(self):
        secs = 21600
        return time.time()-secs
        
    def clean(self):
        stamp = get_stamp()
        self.cursor.execute( "DELETE FROM alerts WHERE stamp < %s", (stamp) )
        
    def close(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()