from abc import ABCMeta, abstractmethod

class backend():
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def clean(self):
        pass
    
    @abstractmethod
    def insert_alert(self, host, graph, field, cond):
        pass
    
    @abstractmethod
    def has_alert(self, host, graph, field, cond):
        pass
    
    @abstractmethod
    def get_stamp(self):
        pass
    
    @abstractmethod
    def close(self):
        pass