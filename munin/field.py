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

from . import range

class field():
    """A field object represents a field in a munin graph. It contains its
    name, current value plus warning and critical ranges. The warning and
    critical ranges may be an empty string, if no range is configured by
    munin. Current value and warn/crit ranges are coma-seperated, here are a
    few examples:
    * "Core 1=21.0,18:23,12:28"
    * "/dev/sda=34,32:38,"
    * "foo=12,,12:38
    """

    def __init__(self, text=None, name=None, value=None, warn=None, crit=None):
        if text:
            self.warn = None
            self.crit = None
            self.value = None
    
            self.name, data = text.split("=")
            value, warn, crit = data.split(",")
            if value != "unknown":
                self.value = float(value)
    
            if warn != '' and warn != ":" and value:
                self.warn = range.range(warn)
                if self.warn.in_range(self.value):
                    raise ValueError("This is not a warning or critical value")
    
            if crit != '' and crit != ":" and value:
                self.crit = range.range(crit)
                if not self.warn and self.crit.in_range(self.value):
                    raise ValueError("This is not a warning or critical value")
        else:
            self.name = name
            self.value = value
            self.warn = range.range(lower=warn[0], upper=warn[1])
            self.crit = range.range(lower=crit[0], upper=crit[1])
            
        if self.value and self.value.is_integer():
            self.value = int(self.value)
                
    def warn_lower(self):
        if self.warn:
            return self.warn.lower
        return None
    
    def warn_upper(self):
        if self.warn:
            return self.warn.upper
        return None
    
    def crit_lower(self):
        if self.crit:
            return self.crit.lower
        return None
    
    def crit_upper(self):
        if self.crit:
            return self.crit.upper

    def is_critical(self):
        if not self.crit or self.crit.in_range(self.value):
            return False

        return True

    def is_warning(self):
        if not self.warn or self.warn.in_range(self.value):
            return False

        if self.crit:
            if self.crit.in_range(self.value):
                return True
            else:
                return False

        return True
    
    def __str__(self):
        return '%s=%s,%s,%s' % (self.name, self.value, self.warn, self.crit)
    
    def old_str(self):
        retVal = "* %s is at %s (" %(self.name, self.value)

        if self.is_warning():
            if self.warn.is_below(self.value):
                retVal += '%s below warning, %s above critical)' % \
                    (self.warn.get_distance(self.value),
                     self.crit.get_safety_margin(self.value, "lower"))
            else:
                retVal += '%s above warning, %s below critical)' % \
                    (self.warn.get_distance(self.value),
                     self.crit.get_safety_margin(self.value, "upper"))
        elif self.is_critical():
            if self.crit.is_below(self.value):
                retVal += "%s below critical)" % self.crit.get_distance(self.value)
            else:
                retVal += "%s above critical)" % self.crit.get_distance(self.value)
        else:
            retVal +="Unknown"

        return retVal
