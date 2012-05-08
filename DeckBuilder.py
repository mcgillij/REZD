import pyglet
import os
from Deck import Deck
from PodSixNet.Connection import connection, ConnectionListener
from pyglet.sprite import Sprite
from pyglet import window
from pyglet import clock
from pyglet import font
from constants import *
from pyglet.gl import *
from random import randint
import kytten
from DeckList import DeckList

VERSION = 0.4
pyglet.options['debug_gl'] = False
class DeckBuilder(window.Window):
    is_event_handler = True     #: enable pyglet's events
    def __init__(self, *args, **kwargs):
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()
        template = pyglet.gl.Config(double_buffer=True)
        config = screen.get_best_config(template)
        context = config.create_context(None)
        window.Window.__init__(self, resizable=True, width=WINWIDTH, height=WINHEIGHT, caption="REZD:" + str(VERSION), context=context)
        self.baseDeck = Deck() # used to lookup cards basically a reference instead of using a database. Basically don't remove / add cards
        self.baseDeck.populate('assets/cardlist.xml')
        self.newdeck = Deck()
        self.selectedCard = None
        self.runnerbaselist = []
        self.corpbaselist = []
    
        for card in self.baseDeck.deck:
            if card.playertype == "Runner":
                self.runnerbaselist.append(card.name)
            else:
                self.corpbaselist.append(card.name)
        
        self.runnerbaselist.sort()
        self.corpbaselist.sort()
        # kytten stuff
        self.theme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
                                                                           "gui_color": [64, 128, 255, 255],
                                                                           "font_size": 14
                                                                           })
        
        self.theme2 = kytten.Theme(self.theme, override={
                                                    "gui_color": [61, 111, 255, 255],
                                                    "font_size": 12
                                                    })
        
    def main_loop(self):
        self.batch = pyglet.graphics.Batch()
        self.register_event_type('on_update')
        pyglet.clock.schedule(self.update_kytten)
        self.fps = pyglet.clock.ClockDisplay()
        self.generateMenu()
        while not self.has_exit: # main loop
            #self.push_handlers(self.on_mouse_release)
            self.clear()
            clock.tick()
            self.dispatch_events()
            self.batch.draw()
            self.drawSelectedCard()
            self.drawNewDeckList()
            self.fps.draw()
            self.flip() #flip to the other opengl buffer
    
    def drawNewDeckList(self):
        count = 0
        iter = 0
        offsetx = self.width/2+200
        offsety = self.height - 50
            
        for card in self.newdeck.deck:
            if count < 35:
                pyglet.text.Label(card.name, font_name="Arial", font_size=14,x=offsetx,y=offsety-(count*25), color=(255,255,255,255)).draw()
            else:
                pyglet.text.Label(card.name, font_name="Arial", font_size=14,x=offsetx+250,y=offsety-(iter*25), color=(255,255,255,255)).draw()
                iter = iter + 1
            count = count + 1
        total = len(self.newdeck.deck)
        pyglet.text.Label("Total: " + str(total), font_name="Arial", font_size=16,x=self.width/2+100,y=self.height-50, color=(255,255,255,255)).draw()
            
    
    def drawSelectedCard(self):
        if self.selectedCard != None:
            if self.selectedCard.sprite == None or self.selectedCard.image == None:
                self.selectedCard.image = pyglet.image.load(self.selectedCard.imageloc)
                self.selectedCard.sprite = Sprite(self.selectedCard.image) #, batch=self.batch2)
                self.selectedCard.loadImg()
                self.selectedCard.sprite.position = (self.width/4, self.height/2)
            self.selectedCard.sprite.draw() 
    
    def update_kytten(self,dt):
        self.dispatch_event('on_update', dt)
    
    def on_select(self, choice):
        if choice == "New Runner Deck":
            self.create_new_runner_deck_dialog()
        elif choice == "New Corporation Deck":
            self.create_new_corp_deck_dialog()
        elif choice == "Save":
            self.create_save_dialog()
        elif choice == "Load":
            self.create_load_dialog()
        elif choice == "Clear Deck":
            self.newdeck.deck = []
            self.selectedCard = None
        elif choice == "Quit":
            self.quitGame()
        else:
            if DEBUG: print "Unexpected menu selection: %s" % choice
    
    def create_save_dialog(self):
        dialog = None
    
        def on_select(filename):
            print "File save: %s" % filename
            if self.newdeck.deck:
                f = open(filename, 'w')
                f.write("<cards>\n")
                for card in self.newdeck.deck:
                    f.write(card.to_xml())
                f.write("</cards>\n")
                f.close()
            self.on_escape(dialog)
    
        dialog = kytten.FileSaveDialog(  # by default, path is current working dir
        extensions=['.xml'],
        window=self, batch=self.batch,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape, on_select=on_select)
        return dialog
    
    def create_load_dialog(self):
        dialog = None
    
        def on_select(filename):
            print "File load: %s" % filename
            self.newdeck.populate(filename)
            self.on_escape(dialog)
    
        dialog = kytten.FileLoadDialog(  # by default, path is current working dir
        extensions=['.xml'],
        window=self, batch=self.batch, 
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape, on_select=on_select)

        
            
    def create_new_runner_deck_dialog(self):
        
        def on_select_base(choice):
            if DEBUG: print "Selected: %s" % choice
            self.selectedCard = None
            self.selectedCard = self.baseDeck.findCardByName(choice)
        
        def on_add():
            if self.selectedCard != None:
                #print "Adding getting called?"
                card = self.baseDeck.findCardByCID(self.selectedCard.cid)
                self.newdeck.deck.append(card)
                #self.selectedCard = None
        
        def on_remove():
            if self.selectedCard != None:
                card = self.newdeck.findCardByCID(self.selectedCard.cid)
                #print "Removing", card.name
                self.newdeck.removeCardByCid(card.cid)
                self.selectedCard = None
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.VerticalLayout([
            kytten.Label("Select a Card:"),
            kytten.Dropdown(self.runnerbaselist, on_select=on_select_base),
            kytten.Button("Add Selected Card to Deck", on_click=on_add),
            kytten.Button("Remove Selected From the Deck", on_click=on_remove)
            ]),
        ),
        window=self, batch=self.batch,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape)
        return dialog
    
    def create_new_corp_deck_dialog(self):
        
        def on_select_base(choice):
            if DEBUG: print "Selected: %s" % choice
            self.selectedCard = None
            self.selectedCard = self.baseDeck.findCardByName(choice)
        
        def on_add():
            if self.selectedCard != None:
                #print "Adding getting called?"
                card = self.baseDeck.findCardByCID(self.selectedCard.cid)
                self.newdeck.deck.append(card)
                #self.selectedCard = None
        
        def on_remove():
            if self.selectedCard != None:
                card = self.newdeck.findCardByCID(self.selectedCard.cid)
                #print "Removing", card.name
                self.newdeck.removeCardByCid(card.cid)
                self.selectedCard = None
        
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.VerticalLayout([
            kytten.Label("Select a Deck:"),
            kytten.Dropdown(self.corpbaselist, on_select=on_select_base),
            kytten.Button("Add Selected Card to Deck", on_click=on_add),
            kytten.Button("Remove Selected From the Deck", on_click=on_remove)
            ]),
        ),
        window=self, batch=self.batch,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape)
        return dialog
    
    def quitGame(self):
        self.has_exit = True
    
    def on_escape(self, dialog):
        dialog.teardown()
        
    def generateMenu(self):
            dialog = kytten.Dialog(
   kytten.TitleFrame("Deck Builder",
     kytten.VerticalLayout([
            kytten.Label("Select dialog to show"),
            kytten.Menu(options=["New Runner Deck", "New Corporation Deck", "Save", "Load", "Clear Deck", "Quit" ],
            on_select=self.on_select),
                    ]),
                 ),
        window=self, batch=self.batch, 
            anchor=kytten.ANCHOR_TOP_LEFT, on_escape=self.on_escape,
            theme=self.theme)
            return dialog
   
# here's where we execute the code        
if __name__ == "__main__":
    deckbuilder = DeckBuilder()
    deckbuilder.main_loop()
    
