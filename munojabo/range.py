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


class range():
    """A range object is a warning/critical range as configured by munin. It might have an upper
    and a lower bound or only one of each. Here are three examples of valid ranges: 10:20, 10:,
    :20.

    Note that a range may be non-existent (e.g. if no warning range is given.)
    """

    def __init__(self, text=None, lower=None, upper=None):
        self.lower = lower
        self.upper = upper

        if text:
            if text == ":":
                return

            if text.startswith(':'):  # only an upper bound
                self.upper = float(text[1:])
            elif text.endswith(':'):  # only a lower bound
                self.lower = float(text[:text.find(':')])
            else:
                lower, upper = text.split(":")
                self.lower = float(lower)
                self.upper = float(upper)

        if self.lower is not None and self.lower.is_integer():
            self.lower = int(self.lower)
        if self.upper is not None and self.upper.is_integer():
            self.upper = int(self.upper)

    def in_range(self, number):
        if self.lower is not None and number < self.lower:
            return False
        elif self.upper is not None and number > self.upper:
            return False
        else:
            return True

    def is_below(self, number):
        if self.lower is not None and number < self.lower:
            return True
        else:
            return False

    def is_above(self, number):
        if self.upper is not None and number > self.upper:
            return True
        else:
            return False

    def get_distance(self, number):
        if self.is_below(number):
            return self.lower - number
        else:
            return number - self.upper

    def get_safety_margin(self, number, boundary):
        if boundary == "lower":
            return number - self.lower
        else:
            return self.upper - number

    def __str__(self):
        if self.lower is None and self.upper is None:
            return ''
        elif self.lower is None:
            return ':%s' % self.upper
        elif self.upper is None:
            return '%s:' % self.lower
        else:
            return '%s:%s' % (self.lower, self.upper)
