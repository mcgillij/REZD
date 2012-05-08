'''
Created on Jun 5, 2011

@author: gimpy
'''
import copy
from random import shuffle
from xml.etree import ElementTree as ET
from Card import Card
class Deck():
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.type = "type"
        self.deck = []
    def __str__(self):
        return self.type    
    def addCard(self, card):
      #  print "adding card"
        self.deck.append(card)
        
    def drawCard(self):
        #print "drawing a card"
        self.deck[0].fromDeck = False
        return self.deck.pop(0)
    
    def putOnTop(self, card):
        #print "Putting card on top"
        self.deck.insert(0, card)
        
    def shuffle(self):
        #print "Shuffling"
        shuffle(self.deck)
    
    def removeCard(self, card):
        self.deck.remove(card)
    def removeCardByCid(self, cid):
        for card in self.deck:
            if card.cid == cid:
                index = self.deck.index(card)
                return self.deck.pop(index)
        return None
        
    def findCard(self, card):
        i = self.deck.index(card)
        return self.deck.pop(i)
    def findCardByName(self, name):
        for card in self.deck:
            if (card.name == name):
                return copy.copy(card)
        return None
    
    def findCardByCID(self, cid):
        for card in self.deck:
            if card.cid == cid:
                return copy.copy(card)
        return None
    
    def findCardByUUID(self, uuid):
        for card in self.deck:
            #print "card.uuid:", card.uuid + "uuid: ", uuid
            if card.uuid == uuid:
                index = self.deck.index(card)
                return self.deck.pop(index)
        return None    
    
    def getTop(self, num, remove=False):
        cards = []
        if num > len(self.deck):
            cards = self.deck
            if remove == True:
                self.deck = []
            return cards
        
        cards = self.deck[0:num-1]
        if remove == True:
            del self.deck[0:num-1]
        return cards
    
    def populate(self, cardlist):
        xml = ET.parse(cardlist)
        iter = xml.getiterator('card')
        self.deck = [] # reset the deck when loading a new one.
        for element in iter:
            card = Card()
            for child in element:
                if (child.tag == "cid"): 
                    card.cid = child.text
                if (child.tag == "name"):
                    card.name = child.text
                if (child.tag == "type"):
                    card.type = child.text
                if (child.tag == "subtype1"):
                    card.subtype1 = child.text
                if (child.tag == "subtype2"):
                    card.subtype2 = child.text
                if (child.tag == "cost"):
                    card.cost = child.text
                if (child.tag == "installCost"):
                    card.installCost = child.text
                if (child.tag == "rezCost"):
                    card.rezCost = child.text
                if (child.tag == "trashCost"):
                    card.trashCost = child.text
                if (child.tag == "strength"):
                    card.strength = child.text
                if (child.tag == "mu"):
                    card.mu = child.text
                if (child.tag == "rarity"):
                    card.rarity = child.text
                if (child.tag == "artist"):
                    card.artist = child.text
                if (child.tag == "text"):
                    card.text = child.text
                if (child.tag == "quote"):
                    card.quote = child.text
                if (child.tag == "release"):
                    card.release = child.text
                if (child.tag == "difficulty"):
                    card.difficulty = child.text
                if (child.tag == "agendaPoints"):
                    card.agendaPoints = child.text
                if (child.tag == "image"):
                    card.imageloc = child.text
                if (child.tag == "playertype"):
                    card.playertype = child.text
                #print child.tag, child.text
            #print "name: ", card.name
            #print "uuid: ", card.uuid
            self.addCard(card)  
    #    self.deck = tempDeck     
#        return deck
            
            
        
    
if __name__ == "__main__":
    testdeck = Deck()
    testdeck.populate('runner.xml')
    print "#cards: ", str(len(testdeck.deck))
        