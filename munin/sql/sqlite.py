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

import os
import sqlite3
import time

from .backend import backend
from .. import field


class sqlite(backend):
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.conn = sqlite3.connect(os.path.expanduser(self.config.get('sql', 'db')))
        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            stamp INTEGER, host TEXT, graph TEXT, field TEXT, cond TEXT,
            value FLOAT, warn_lower FLOAT, warn_upper FLOAT, crit_lower FLOAT, crit_upper FLOAT,
            notified INTEGER DEFAULT 0)''')
        self.conn.commit()

    def get_alerts(self):
        """
        * Fetch alerts within the last 5 minutes
            * see if notifications were already sent out.
            * if yes, quit
            * else:
                * send notifications
                * set notified=1
        """
        alerts = []
        now = time.time()
        last_run = time.time() - self.args.run_freq
        oldest_stamp = now - self.args.notification_freq

        # fetch all alerts added since the last run
        self.cursor.execute("SELECT * FROM alerts WHERE stamp > ? AND notified=0", (last_run,))

        for row in self.cursor.fetchall():
            id, stamp, host, graph, fieldname, cond = row[0:6]

            if self.args.force_send:  # we force sending notifications
                alerts.append(row)
                continue

            # see if this alert was already sent out:
            self.cursor.execute("""SELECT * FROM alerts
                WHERE stamp > ? AND host=? AND graph=? AND field=? AND cond=? AND notified=1""",
                                (oldest_stamp, host, graph, fieldname, cond))

            if not self.cursor.fetchone():
                self.cursor.execute("UPDATE alerts SET notified=1 WHERE id=?", (id,))
                alerts.append(row)

        # group alerts by host/graphs:
        alerts_by_host = {}
        for id, stamp, host, graph, fieldname, cond, value, warn_lower, warn_upper, \
                crit_lower, crit_upper, notified in alerts:

            if host not in alerts_by_host:
                alerts_by_host[host] = {}
            if graph not in alerts_by_host[host]:
                alerts_by_host[host][graph] = []

            alerts_by_host[host][graph].append(field.field(
                name=fieldname, value=value, warn=(warn_lower, warn_upper),
                crit=(crit_lower, crit_upper)
            ))

        return alerts_by_host

    def insert_alert(self, host, graph, cond, field):
        """
        Insert an alert into the database
        """
        self.cursor.execute(
            """INSERT INTO alerts(stamp, host, graph, field, cond, value, warn_lower, warn_upper,
                           crit_lower, crit_upper)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), host, graph, field.name, cond, field.value, field.warn_lower(),
             field.warn_upper(), field.crit_lower(), field.crit_upper())
        )

    def get_stamp(self):
        return time.time() - self.args.notification_freq

    def clean(self):
        """
        Clean old alerts.
        """
        self.cursor.execute("DELETE FROM alerts WHERE stamp < ?", (self.get_stamp(),))

    def close(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
