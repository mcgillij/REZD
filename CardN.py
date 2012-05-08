class CardN():
    """Network version of the card that gets passed
     to the server, so we don't spam it with all the card information"""
    def __init__(self, cid, position, uuid, isTapped, faceUp, inHand, dirty):
        
        self.cid = cid
        self.position = position
        self.uuid = uuid
        self.isTapped = isTapped
        self.faceUp = faceUp
        self.inHand = inHand
        self.dirty = dirty
        #print "uuid from cardn: ", self.uuid
    def __str__(self):
        return self.cid, self.position, self.uuid, self.isTapped, self.faceUp, self.inHand, self.dirty
