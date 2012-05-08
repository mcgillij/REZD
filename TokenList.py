'''
Created on Jun 5, 2011

@author: gimpy
'''
import copy
class TokenList():
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        
        self.tokens = []
    
    def findTokenByUUID(self, uuid):
        for token in self.tokens:
           # print "card.uuid:", card.uuid + "uuid: ", uuid
            if token.uuid == uuid:
                index = self.tokens.index(token)
                return self.tokens.pop(index)
        return None    
    
    