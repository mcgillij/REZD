import os
class DeckList():
    def __init__(self):
        self.decklist = os.listdir('decks/')
        
    def print_list(self):
        for entry in self.decklist:
            print entry
            
            
            
if __name__ == "__main__":
    decklist = DeckList()
    decklist.print_list
    