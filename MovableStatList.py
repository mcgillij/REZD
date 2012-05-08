class MovableStatList():
    def __init__(self):
        self.statlist = []
    
    def findMSByUUID(self, uuid):
        for ms in self.statlist:
            if ms.uuid == uuid:
                index = self.statlist.index(ms)
                return self.statlist.pop(index)
        return None    
    
    