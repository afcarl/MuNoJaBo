"""This file is part of MuNoJaBo.

MuNoJaBo is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not,
see <http://www.gnu.org/licenses/>.
"""

import time

from .backend import backend


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

        if self.cursor.fetchone() is None:
            return False
        else:
            return True

    def get_alerts(self):
        pass

    def insert_alert(self, host, graph, field, cond):
        self.cursor.execute("INSERT INTO alerts(host, graph, field, cond) VALUES (%s, %s, %s, %s)",
                            (host, graph, field, cond))

    def get_stamp(self):
        secs = self.args.notification_freq
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - secs))

    def clean(self):
        stamp = get_stamp()
        self.cursor.execute("DELETE FROM alerts WHERE stamp < %s", (stamp))

    def close(self):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()
