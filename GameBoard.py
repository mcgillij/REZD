import pyglet
import os
from Deck import Deck
from PodSixNet.Connection import connection, ConnectionListener
import cPickle as pickle
from pyglet.sprite import Sprite
from pyglet import window
from pyglet import clock
from pyglet import font
from Token import Token
from TokenList import TokenList
from camera import Camera
from constants import *
from vec2 import Vec2
from pyglet.gl import *
from act import Act
from MessageList import MessageList
from MovableStat import MovableStat
from MovableStatList import MovableStatList
from random import randint
import kytten
from DeckList import DeckList
from pprint import pprint


VERSION = 0.4
pyglet.options['debug_gl'] = False
class GameBoard(window.Window, ConnectionListener):
    is_event_handler = True     #: enable pyglet's events
    def __init__(self, *args, **kwargs):
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()
        template = pyglet.gl.Config(double_buffer=True)
        config = screen.get_best_config(template)
        context = config.create_context(None)
        window.Window.__init__(self, resizable=True, width=WINWIDTH, height=WINHEIGHT, caption="REZD:" + str(VERSION), context=context)
        self.camera = Camera(self)
        #host = "localhost"
        self.host = "localhost"
        #self.host = "192.168.0.101"
        #self.host = "24.138.79.5"
        self.port = 1234
        self.connected = False
        self.players = {}
        self.cards = {} #cards from the network
        self.tokens = {}
        self.acts = {}
        self.mss = {}
        self.statusLabel = "Not Connected"
        self.playersLabel = "0 players"
        self.baseDeck = Deck() # used to lookup cards basically a reference instead of using a database. Basically don't remove / add cards
        self.baseDeck.populate('assets/cardlist.xml')
        self.playerDeck = Deck() # the actual decks we can remove cards from this one
        self.localCardList = Deck()
        self.hand = Deck()
        self.opponentsHandSize = 0
        self.tokenList = TokenList()
        self.HQuuid = None
        self.RNDuuid = None
        self.ARCHIVEuuid = None
        self.movableStatList = MovableStatList()
        self.mouseposx = 0
        self.mouseposy = 0
        self.selected = None
        self.selectedToken = None
        self.selectedMS = None
        self.zoomedCard = None
        self.drawing = False
        self.nickname = None
        self.deckBrowserCard = None
        self.ML = MessageList()
        self.decoded = pyglet.text.decode_text(self.ML.getMessages())
        self.scroll_area = pyglet.text.layout.ScrollableTextLayout(self.decoded, 500, 210, multiline=True)
        self.scroll_area.x = 50
        self.scroll_area.y = 200
        
        
        # kytten stuff
        self.theme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
                                                                           "gui_color": [64, 128, 255, 255],
                                                                           "font_size": 14
                                                                           })
        
        self.theme2 = kytten.Theme(self.theme, override={
                                                    "gui_color": [61, 111, 255, 255],
                                                    "font_size": 12
                                                    })
        self.decklist = DeckList()
        self.menu_showing = False
        self.action_menu = False
        self.chat_menu = False
        self.archives = None
        
        
    #___________________________________MAIN______________________________________________________#           
    def main_loop(self):
        self.batch = pyglet.graphics.Batch()
        self.batch2 = pyglet.graphics.Batch()
        self.batch3 = pyglet.graphics.Batch()
        self.register_event_type('on_update')
        pyglet.clock.schedule(self.update_kytten)
        self.menu = self.generateMenu() #part of batch3 rendering
        self.create_network_dialog()
        self.fps = pyglet.clock.ClockDisplay()
        pyglet.font.add_file('assets/myfont.ttf')
        
        while not self.has_exit: # main loop
            self.push_handlers(self.on_mouse_release)
            if self.connected:
                self.Pump() # send stuffs to the network
                connection.Pump() # recieve stuffs from the network
            self.clear()
            clock.tick()
            self.dispatch_events()
            
            # Camera transformed stuff
            glPushMatrix()
            self.camera.transform()
            self.processNetworkedVars()
            #gameboard cards
            self.drawLocalCards()
            self.batch.draw()
            self.drawSelectedCard()
            # rectangles
            self.drawRects()
            #hand
            self.drawTokens()
            self.drawUnderlay()
            glPopMatrix()
            # End camera transformed stuff
            # Draw the Hud stuff over top
            
            self.drawHandCards()
            self.batch2.draw()
            self.drawHandRects()
            self.batch3.draw()
            self.drawZoomedCard()
            self.drawDeckBrowserCard()
            self.scroll_area.draw()
            self.fps.draw()
            self.flip() #flip to the other opengl buffer
    
    def drawDeckBrowserCard(self):
        if self.deckBrowserCard != None:
            if self.deckBrowserCard.sprite == None:
                self.deckBrowserCard.sprite = self.setupCard(self.deckBrowserCard)
            self.deckBrowserCard.scale = 2
            self.deckBrowserCard.sprite.image.anchor_x = self.deckBrowserCard.sprite.image.width/2
            self.deckBrowserCard.sprite.image.anchor_y = self.deckBrowserCard.sprite.image.height/2
            self.deckBrowserCard.sprite.position = (self.width/4, self.height/2)
            self.deckBrowserCard.sprite.draw()

    def drawZoomedCard(self):
        if self.zoomedCard:
            self.zoomedCard.scale = 2
            self.zoomedCard.image.anchor_x = self.zoomedCard.image.width/2
            self.zoomedCard.image.anchor_y = self.zoomedCard.image.height/2
            self.zoomedCard.position = (self.width/2, self.height/2)
            self.zoomedCard.draw()
       
            
    def drawSelectedCard(self):
        if self.selected != None:
            if self.selected.sprite == None or self.selected.image == None:
                self.selected.image = pyglet.image.load(self.selected.imageloc)
                self.selected.sprite = Sprite(self.selected.image) #, batch=self.batch2)
                self.selected.loadImg()
            self.selected.sprite.draw() 
    #process network actions
    def ConnectToServer(self):
        self.Connect((self.host, self.port))
        self.SetNickname(self.nickname)
        connection.Send({"action": "message", "message": pickle.dumps("Has Connected")})
        self.createHQMS()
        self.createRNDMS()
        self.createArchivesMS()
        self.connected = True
    
    def processNetworkedVars(self):
        for p in self.players:
            color = self.players[p]['color']
            #if DEBUG: print "COLOR: OMG", str(color)
            pyglet.gl.glColor4f(color[0],color[1],color[2],1.0)
            #self.drawLines(self.players[p]['lines'])
            while self.cards[p]['cards']:
                cardn = self.cards[p]['cards'].pop()
                self.MakeLocalCard(cardn)
            while self.tokens[p]['tokens']:
                tokenn = self.tokens[p]['tokens'].pop()
                self.MakeLocalToken(tokenn)
            while self.mss[p]['mss']:
                msn = self.mss[p]['mss'].pop()
                self.MakeLocalMovableStat(msn, color)
            while self.acts[p]['acts']:
                actn = self.acts[p]['acts'].pop()
                self.MakeLocalAct(actn)
        
    #gui functions
    def update_chat(self, message):
        self.ML.addMessage(message)
        self.decoded = pyglet.text.decode_text(self.ML.getMessages())
        self.decoded.set_style(0, len(self.decoded.text), dict(color=(255,255,255,255)))
        self.scroll_area._set_document(self.decoded)

    # Kytten stuff
    def on_escape(self, dialog):
        self.deckBrowserCard = None
        dialog.teardown()
    def on_escape_menu(self, dialog):
        dialog.teardown()
    def on_escape_action(self, dialog):
        dialog.teardown()
        self.action_menu = False
    def on_escape_chat(self, dialog):
        dialog.teardown()
        self.chat_menu = False
    
    def update_kytten(self,dt):
        self.dispatch_event('on_update', dt)
            
    def on_select(self, choice):
        #if choice == "Network":
         #   self.create_network_dialog()
        if choice == 'Deck Loader':
            self.create_deckloader_dialog()
        #elif choice == 'Stats':
        #    self.create_stats_dialog()
        elif choice == "Actions":
            if self.action_menu == False:
                self.create_actions_dialog()
                self.action_menu = True
        elif choice == "Runner Actions":
            self.create_runner_actions_dialog()
        elif choice == "Corp Actions":
            self.create_corp_actions_dialog()
        elif choice == "Controls":
            self.create_controls_dialog()
        elif choice == "Chat":
            self.create_chat_dialog()
        elif choice == "Quit":
            self.quitGame()
        else:
            if DEBUG: print "Unexpected menu selection: %s" % choice
    def loadDeck(self, deck):
        self.playerDeck.populate("decks/" + deck)
        self.playerDeck.shuffle()
        act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
        self.Send({"action": "addact", "act": pickle.dumps(act)})
        connection.Send({"action": "message", "message": pickle.dumps("Has loaded a deck:" + deck)})
    
    def generateMenu(self):
            dialog = kytten.Dialog(
   kytten.TitleFrame("Main Menu",
     kytten.VerticalLayout([
            kytten.Label("Select dialog to show"),
            kytten.Menu(options=["Deck Loader","Actions","Runner Actions", "Corp Actions","Controls","Chat","Quit" ],
            on_select=self.on_select),
                    ]),
                 ),
        window=self, batch=self.batch3, 
            anchor=kytten.ANCHOR_TOP_LEFT, on_escape=self.on_escape,
            theme=self.theme)
            return dialog
        
    def create_deckloader_dialog(self):
        def on_select(choice):
            if DEBUG: print "Selected: %s" % choice
            self.loadDeck(choice)
            self.on_escape(dialog)
            self.create_actions_dialog()
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.VerticalLayout([
            kytten.Label("Select a Deck:"),
            kytten.Dropdown(self.decklist.decklist,
                    on_select=on_select),
            ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape)
        return dialog

    def create_deckbrowser_dialog(self):
        def on_select(choice):
            if DEBUG: print "Selected: %s" % choice
            self.deckBrowserCard = None
            self.deckBrowserCard = self.playerDeck.findCardByName(choice)
            
        def on_submit():
            if self.deckBrowserCard != None:
                card = self.playerDeck.findCardByUUID(self.deckBrowserCard.uuid)
                mouse_STW = self.camera.screen_to_world(self.width/2, self.height/2)
                card.position = (mouse_STW[0], mouse_STW[1])
                if DEBUG: print "Dropping"
                card.dirty = True
                card.faceUp = False
                self.Send({"action": "movecard", "card": pickle.dumps(card.getCardN())})
                connection.Send({"action": "message", "message": pickle.dumps("Has picked a card from his deck")})
                act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                self.deckBrowserCard = None
                self.on_escape(dialog)
        #def on_escape(dialog):
         #   self.deckBrowserCard = None
         #   self.on_escape(dialog)
            
                
        list = []
        for card in self.playerDeck.deck:
            list.append(card.name)
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.VerticalLayout([
            kytten.Label("Select a Deck:"),
            kytten.Dropdown(list, on_select=on_select),
            kytten.Button("Place Card on Gameboard", on_click=on_submit)
            ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape)
        return dialog
    
    def create_stats_dialog(self):
        dialog = kytten.Dialog(
            kytten.Frame(
                kytten.VerticalLayout([
                       kytten.Label('FPS'),
                       kytten.Label('Connection'),
                       kytten.Label('Players'),
                       kytten.Label(str(len(self.hand.deck))),
                       kytten.Label('Cards in Play'),
                       kytten.Label('Tokens')
                       
               ])
            ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape
        )
        return dialog
    
    def create_chat_dialog(self):
        dialog = None
        def on_enter(dialog):
            if DEBUG: print "Form submitted!"
            for key, value in dialog.get_values().iteritems():
     #           if key == "name":
      #              self.nickname=value
       #             self.SetNickname(value)
                if key == "chat_text":
                    if value != "":
                        self.SendMessage(value)
                    else:
                        if DEBUG: print "not sending blank message"
                #if DEBUG: print "  %s=%s" % (key, value)
            self.on_escape_chat(dialog)
        def on_submit():
            on_enter(dialog)
        def on_cancel():
            if DEBUG: print "Form canceled."
            self.on_escape_chat(dialog)
        
        dialog = kytten.Dialog(
            kytten.Frame(
                kytten.VerticalLayout([
                kytten.Label("Text:"), kytten.Input("chat_text", "", max_length=80),
                kytten.HorizontalLayout([
                                         kytten.Button("Submit", on_click=on_submit),
                                         kytten.Button("Cancel", on_click=on_cancel)
                ])
            ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2,on_enter=on_enter, on_escape=self.on_escape)
        
        return dialog
    
    def create_network_dialog(self):
        dialog = None
        def on_enter(dialog):
            if DEBUG: print "Form submitted!"
            for key, value in dialog.get_values().iteritems():
                if key == "name":
                    if value != "":
                        self.nickname=value
                    else:
                        if DEBUG: print "no name sent"
                if key == "host":
                    if value != "":
                        self.host=value
                    else:
                        if DEBUG: print "No host specified"
                if key == "port":
                    if value != "":
                        self.port = int(value)
                    else:
                        if DEBUG: print "not sending blank message"
            
            if self.host != "" and self.port != "":
                self.ConnectToServer()
                
            self.on_escape(dialog)
            self.create_deckloader_dialog()
        def on_submit():
            on_enter(dialog)
        def on_cancel():
            if DEBUG: print "Form canceled."
            self.on_escape_chat(dialog)
        
        if self.nickname == None:
            dialog = kytten.Dialog(
                kytten.Frame(
                    kytten.VerticalLayout([
                    kytten.Label("Name: "), kytten.Input("name", "TypeYourNameHere", max_length=20),
                    kytten.Label("Host: "), kytten.Input("host", self.host, max_length=20),
                    kytten.Label("Port:"), kytten.Input("port", str(self.port), max_length=10),
                    kytten.Button("Connect", on_click=on_submit),
                    kytten.Button("Cancel", on_click=on_cancel)
                ]),
            ),
            window=self, batch=self.batch3,
            anchor=kytten.ANCHOR_CENTER,
            theme=self.theme2,on_enter=on_enter, on_escape=self.on_escape_chat)
        return dialog
    
    def create_actions_dialog(self):
        dialog = kytten.Dialog(
            kytten.Frame(
                kytten.VerticalLayout([
                kytten.Button("Draw Card", on_click=self.draw_a_card),
                kytten.Button("Put top card on the table", on_click=self.play_top_card),
                kytten.Button("Create bit", on_click=self.createBit),
                kytten.Button("Create 5 bit", on_click=self.create5Bit),
                kytten.Button("Roll D6", on_click=self.rollD6),
                kytten.Button("Shuffle Deck", on_click=self.shuffleDeck),
                kytten.Button("Browse Deck for a card", on_click=self.create_deckbrowser_dialog),
                kytten.Button("Pass Turn", on_click=self.passTurn)
               
             ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape_action)
                               
        return dialog
    
    def create_runner_actions_dialog(self):
        dialog = kytten.Dialog(
            kytten.Frame(
                kytten.VerticalLayout([
                kytten.Button("Run the Archives", on_click=self.run_archives),
                kytten.Button("Run R&D", on_click=self.run_rnd),
                kytten.Button("Run HQ", on_click=self.run_hq),
                kytten.Button("Run Aux Datafort", on_click=self.run_datafort),
                kytten.Button("Remove Tag", on_click=self.remove_tag),
                kytten.Button("Create Brain Damage", on_click=self.createBD),
                kytten.Button("Create Virus Token", on_click=self.createVirus),
                kytten.Button("Create Bad Publicity Token", on_click=self.createBadPublicity),
                
                
             ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape_action)
                               
        return dialog
    
    def create_corp_actions_dialog(self):
        dialog = kytten.Dialog(
            kytten.Frame(
                kytten.VerticalLayout([
                kytten.Button("Trace", on_click=self.trace),
                kytten.Button("Tag", on_click=self.create_tag),
                kytten.Button("Destroy Runner Resource", on_click=self.destroy_resource)
                
             ]),
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape_action)
        return dialog
    def remove_tag(self):
        connection.Send({"action": "message", "message": pickle.dumps("2Bits and an action to remove a Tag")})
    
    def destroy_resource(self):
        connection.Send({"action": "message", "message": pickle.dumps("2Bits and an action to destroy a resource of Tagged runner.")})
    
    def run_archives(self):
        connection.Send({"action": "message", "message": pickle.dumps("Starting a run on the Archives")})
    
    def run_rnd(self):
        connection.Send({"action": "message", "message": pickle.dumps("Starting a run on the R&D")})
    
    def run_hq(self):
        connection.Send({"action": "message", "message": pickle.dumps("Starting a run on the HQ")})
    
    def run_datafort(self):
        connection.Send({"action": "message", "message": pickle.dumps("Starting a run on the Aux Datafort")})
        
    def trace(self):
        connection.Send({"action": "message", "message": pickle.dumps("Is executing a Trace")})
    
        
    
    def shuffleDeck(self):
        self.playerDeck.shuffle()
        connection.Send({"action": "message", "message": pickle.dumps("Has Shuffled his deck")})
        
    def create_controls_dialog(self):
        document = pyglet.text.decode_attributed('''
{bold True}----MOUSE----{bold False}

{bold True}LEFT{bold False} click / drag to move a card\n
{bold True}RIGHT{bold False} click to Tap a card or Delete a Token\n
{bold True}MIDDLE{bold False} click to Flip a Card\n
{bold True}SCROLL{bold False} the mouse wheel to Zoom In or Out\n
{bold True}----KEYBOARD----{bold False}

{bold True}F1{bold False} Toggles Zoom in on a card\n
{bold True}ENTER{bold False} to open up the Chat window\n
{bold True}ESCAPE{bold False} will close out menu's or bring up the Main Menu\n
{bold True}L-ALT + Mouse over{bold False} will put a card back in your hand\n
{bold True}L-CTRL + mouse over{bold False} will put a card back on top of your deck\n
{bold True}SPACEBAR{bold False} will clear your drawings on the screen\n
{bold True}UP, DOWN, LEFT and RIGHT{bold False} will move the Camera\n
''')
                                                 
        dialog = kytten.Dialog(
            kytten.Frame(
               kytten.Document(document, width=500, height=500)
        ),
        window=self, batch=self.batch3,
        anchor=kytten.ANCHOR_CENTER,
        theme=self.theme2, on_escape=self.on_escape)
        return dialog   
       
    # schedule a update function to be called less often
     
    # Turn Network Data into local Data
    def MakeLocalAct(self, actn):
        tempact = pickle.loads(actn)
        if tempact.target == "ms":
            if tempact.action == "remove":
                ms = self.movableStatList.findMSByUUID(tempact.uuid)
            elif tempact.action == "update":
                ms = self.movableStatList.findMSByUUID(tempact.uuid)
                if ms:
                    ms.count = tempact.payload
                    self.movableStatList.statlist.append(ms)
        
        elif tempact.target == "token":
            if tempact.action == "remove":
                token = self.tokenList.findTokenByUUID(tempact.uuid)
        elif tempact.target == "card":
            if tempact.action == "remove":
                card = self.localCardList.findCardByUUID(tempact.uuid)
        else:
            if DEBUG: print "Could not process action"
    
    def MakeLocalCard(self, cardn):
        """Turn the networked card into a local card managed by self.localCardList """
        tempcard = pickle.loads(cardn)
        if tempcard.dirty:
            newcard = self.localCardList.findCardByUUID(tempcard.uuid)
            if newcard == None:
                newcard = self.baseDeck.findCardByCID(tempcard.cid)
            newcard.position = tempcard.position
            newcard.uuid = tempcard.uuid
            newcard.isTapped = tempcard.isTapped
            newcard.faceUp = tempcard.faceUp
            newcard.inHand = tempcard.inHand
            if DEBUG: print "Loading: ", newcard.name + "From the network"
            newcard.dirty = True
            self.localCardList.addCard(newcard)
            
    def MakeLocalToken(self, tokenn):
        temptoken = pickle.loads(tokenn)
        newtoken = self.tokenList.findTokenByUUID(temptoken.uuid)
        if newtoken == None:
            newtoken = Token(temptoken.type)
        newtoken.uuid = temptoken.uuid
        newtoken.position = temptoken.position
        self.tokenList.tokens.append(newtoken)
        
    def MakeLocalMovableStat(self, msn, color):
        tempms = pickle.loads(msn)
        if DEBUG: print "new position", str(tempms.position)
        newms = self.movableStatList.findMSByUUID(tempms.uuid)
        if newms == None:
            if DEBUG: print "NO MS FOUND, CREATING NEW ONE"
            newms = MovableStat(tempms.label, tempms.count)
            if DEBUG: print "old position: ", str(newms.position)
        else:
            if DEBUG: print "Already there, updating"
        newms.color = color
        newms.uuid = tempms.uuid
        newms.position = tempms.position
        self.movableStatList.statlist.append(newms)
    
    def drawUnderlay(self):
        for ms in self.movableStatList.statlist:
            ms.loadImg()
            pyglet.text.Label(ms.label + str(ms.count), font_name="Computerfont", font_size=78,x=ms.sprite.x+35,y=ms.sprite.y-15, color=(ms.color[0], ms.color[1], ms.color[2], ms.color[3])).draw()
            ms.sprite.draw()
        if self.selectedMS:
            self.selectedMS.sprite.draw()
        
    def drawTokens(self):
        for token in self.tokenList.tokens:
            token.loadImg()
            token.sprite.draw()
        if self.selectedToken:
            self.selectedToken.sprite.draw()
            
    def drawHandCards(self):
        for card in self.hand.deck:
            if card.sprite == None or card.image == None:
                card.image = pyglet.image.load(card.imageloc)
                card.sprite = Sprite(card.image, batch=self.batch2)
            card.loadImg()
            card.position = (100 + self.hand.deck.index(card)*170,130)
            card.set_sprite_pos()
            
    def setupCard(self, card):
        if card.sprite == None:
            card.image = pyglet.image.load(card.imageloc)
            if card.faceUp:
                card.sprite = Sprite(card.image, batch=self.batch)
            else:
                if card.playertype == "Runner":
                    card.sprite = Sprite(RUNNERBACK, batch=self.batch)
                else:
                    card.sprite = Sprite(CORPBACK, batch=self.batch)
        else: 
            if card.faceUp:
                card.sprite = Sprite(card.image, batch=self.batch)
            else:
                if card.playertype == "Runner":
                    card.sprite = Sprite(RUNNERBACK, batch=self.batch)
                else:
                    card.sprite = Sprite(CORPBACK, batch=self.batch)
        return card.sprite
          
    def drawLocalCards(self):
        if self.localCardList.deck:
            for card in self.localCardList.deck:
                card.sprite = self.setupCard(card)
                card.loadImg()
                card.set_sprite_pos()
            
    def drawRects(self):
        pyglet.gl.glColor4f(1.0,0,0,1.0)
        for card in self.localCardList.deck:
            if card.isTapped:
                ax,ay,bx,by,cx,cy,dx,dy = card.rotateRect(90)
            else:
                ax,ay,bx,by,cx,cy,dx,dy = card.rotateRect(0)
            pyglet.graphics.draw(5, pyglet.gl.GL_LINE_STRIP,('v2i', (ax,ay,bx,by,cx,cy,dx,dy,ax,ay)))
    
    def drawHandRects(self):
        pyglet.gl.glColor4f(1.0,0,1,1.0)
        
        for card in self.hand.deck:
            ax,ay,bx,by,cx,cy,dx,dy = card.rotateRect(0)
            pyglet.graphics.draw(5, pyglet.gl.GL_LINE_STRIP,('v2i', (ax,ay,bx,by,cx,cy,dx,dy,ax,ay)))
    
    def drawLines(self, linesets):
        mypointlist = []
        for lines in linesets:
            for l in lines:
                if len(l) > 1:
                    for v in l:
                        mypointlist.append(int(v))
        pyglet.graphics.draw(len(mypointlist)/2, pyglet.gl.GL_POINTS,('v2i', mypointlist ))
        
    # -------------------------------------- EVENTS ------------------------------------- #
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        scrollvalue = .05
        if scroll_y < 0:
            self.camera.zoom -= self.camera.zoom_speed * scrollvalue
        else:
            self.camera.zoom += self.camera.zoom_speed * scrollvalue
                
    def on_key_press (self, key, modifiers):
        """This function is called when a key is pressed.
        'key' is a constant indicating which key was pressed.
        'modifiers' is a bitwise or of several constants indicating which
           modifiers are active at the time of the press (ctrl, shift, capslock, etc.)
        """
        if key == pyglet.window.key.F1:
            if self.zoomedCard:
                self.zoomedCard = None
            else:
                mouse_STW = self.camera.screen_to_world(self.mouseposx, self.mouseposy)
                if DEBUG: print "Trying Zoom Card"
                self.ZoomCard(mouse_STW[0], mouse_STW[1])      
        elif key == pyglet.window.key.ENTER and self.chat_menu == False:
            self.create_chat_dialog()
            self.chat_menu = True
        elif key == pyglet.window.key.ESCAPE:
            if self.menu_showing:
                self.on_escape_menu(self.menu)
                self.menu_showing = False
            else:
                self.menu = self.generateMenu()  
               
        elif key == pyglet.window.key.LCTRL:
            mouse_STW = self.camera.screen_to_world(self.mouseposx, self.mouseposy)
            if DEBUG: print "Trying to put card back on top of the deck"
            self.CardToDeck(mouse_STW[0], mouse_STW[1])                                  
        elif key == pyglet.window.key.LALT:
            mouse_STW = self.camera.screen_to_world(self.mouseposx, self.mouseposy)
            if DEBUG: print "Trying to put card under the cursor back into your hand"
            self.CardToHand(mouse_STW[0], mouse_STW[1])
        elif key == pyglet.window.key.F2:
            if DEBUG: print "Starting Drawing"
            self.drawing = True
        elif key == pyglet.window.key.SPACE:
            if DEBUG: print "Clearing"
            self.clearLines()
            
    def on_key_release(self, key, modifiers):
        if key == pyglet.window.key.F2:
            if DEBUG: print "Stopping Drawing"
            self.drawing = False    
        
            
    def on_mouse_motion (self, x, y, dx, dy):
        """This function is called when the mouse is moved over the app.
        (x, y) are the physical coordinates of the mouse
        (dx, dy) is the distance vector covered by the mouse pointer since the
          last call.
        """
        #mouse_stw = self.camera.screen_to_world(x, y)
        #if DEBUG: print "Mouse to world: ", mouse_stw
        self.mouseposx, self.mouseposy =  x,y #director.get_virtual_coordinates (x, y)
        #self.update_mouse_text (x, y)
    
    def on_mouse_drag(self,x,y,dx,dy,buttons, modifiers):
        mouse_STW = self.camera.screen_to_world(x, y)
        if self.selected != None:
            self.CardMove(mouse_STW[0], mouse_STW[1])
        elif self.selectedToken != None:
            self.TokenMove(mouse_STW[0], mouse_STW[1])
        elif self.selectedMS != None:
            self.MSMove(mouse_STW[0], mouse_STW[1])
        
    def on_mouse_press (self, x, y, buttons, modifiers):
        """This function is called when any mouse button is pressed
        (x, y) are the physical coordinates of the mouse
        'buttons' is a bitwise or of pyglet.window.mouse constants LEFT, MIDDLE, RIGHT
        'modifiers' is a bitwise or of pyglet.window.key modifier constants
           (values like 'SHIFT', 'OPTION', 'ALT')
        """
        mouse_STW = self.camera.screen_to_world(x, y)
        
        if buttons == pyglet.window.mouse.LEFT:
           
            if self.TokenClicked(mouse_STW[0], mouse_STW[1]):
                return True
            elif self.MSClicked(mouse_STW[0], mouse_STW[1]):
                return True
            elif self.CardHandClicked(x, y):
                return True
            elif  self.CardClicked(mouse_STW[0], mouse_STW[1]):
                return True
            else:
                if DEBUG: print "No cards clicked on the board at: ", x,y
            
        elif buttons == pyglet.window.mouse.RIGHT:
            #self.MSRightClicked(mouse_STW[0], mouse_STW[1])
            self.TokenRightClicked(mouse_STW[0], mouse_STW[1])
            self.tap_card(mouse_STW[0], mouse_STW[1])
            
        elif buttons == pyglet.window.mouse.MIDDLE:
            self.flip_card(mouse_STW[0], mouse_STW[1])
    
        
    def on_mouse_release(self,x,y,button,modifiers):
        mouse_STW = self.camera.screen_to_world(x, y)
        if self.selected != None:
            self.CardDrop(mouse_STW[0], mouse_STW[1])
        elif self.selectedToken != None:
            self.TokenDrop(mouse_STW[0], mouse_STW[1])
        elif self.selectedMS != None:
            self.MSDrop(mouse_STW[0], mouse_STW[1])
       
    
    
    # -------------------------------------- Various actions triggered by the events ---------------------------- #
    
    def passTurn(self):
        connection.Send({"action": "message", "message": pickle.dumps("Go your turn now.")})
    
    def rollD6(self):
        roll = randint(1,6)
        connection.Send({"action": "message", "message": pickle.dumps("Rolling D6: " + str(roll))})
    
    def clearLines(self):
        if DEBUG: print "CLEAR FROM CLIENT"
        connection.Send({"action": "clear"})
    def quitGame(self):
        self.has_exit = True
    
    def createHQMS(self):
        ms = MovableStat('Hq: ', len(self.hand.deck))
        self.HQuuid = ms.uuid
        ms.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addms", "ms": pickle.dumps(ms.getMovableStatN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a HQ Stat token")})
        
    def createRNDMS(self):
        ms = MovableStat('RnD: ', len(self.playerDeck.deck))
        self.RNDuuid = ms.uuid
        ms.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addms", "ms": pickle.dumps(ms.getMovableStatN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a RND Stat token")})
    def createArchivesMS(self):
        ms = MovableStat('Archives', 0)
        self.ARCHIVEuuid = ms.uuid
        ms.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addms", "ms": pickle.dumps(ms.getMovableStatN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a Archives Stat token")})
        
    def createBit(self):
        token = Token("1bit")
        token.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(token.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a bit")})
    def create5Bit(self):
        token = Token("5bit")
        token.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(token.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a 5bit")})
    def createBD(self):
        bd = Token("bd")
        bd.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(bd.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a Brain Damage")})
    def createVirus(self):
        virus = Token("virus")
        virus.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(virus.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a Virus Token")})
    def create_tag(self):  
        tag = Token("tag")
        tag.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(tag.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a tag Token")})
    def createBadPublicity(self):  
        tag = Token("badpublicity")
        tag.position = self.camera.screen_to_world(self.width/2, self.height/2)
        connection.Send({"action": "addtoken", "token": pickle.dumps(tag.getTokenN())})
        connection.Send({"action": "message", "message": pickle.dumps("created a Bad Publicity Token")}) 
    
    def play_top_card(self):
        card = self.playerDeck.drawCard()
        mouse_STW = self.camera.screen_to_world(self.width/2, self.height/2)
        card.position = (mouse_STW[0], mouse_STW[1])
        if DEBUG: print "Dropping"
        card.dirty = True
        card.faceUp = False
        self.Send({"action": "movecard", "card": pickle.dumps(card.getCardN())})
        connection.Send({"action": "message", "message": pickle.dumps("Has played a card from his deck")})
        act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
        self.Send({"action": "addact", "act": pickle.dumps(act)})
                  
    def draw_a_card(self):
        #if DEBUG: print "BUTTON PRESSED OMG, adding card to hand"
        card = self.playerDeck.drawCard()
        card.inHand = True
        self.hand.addCard(card)
        act = Act(self.HQuuid, "update", "ms", payload=len(self.hand.deck))
        self.Send({"action": "addact", "act": pickle.dumps(act)})
        act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
        self.Send({"action": "addact", "act": pickle.dumps(act)})
        connection.Send({"action": "message", "message": pickle.dumps("Drawing a card")})
        
        
    def CardHandClicked(self, x,y):
        for card in self.hand.deck:
            if card.contains2(x,y):
                if DEBUG: print "Clicked from Hand:", card.name
                mouse_STW = self.camera.screen_to_world(x, y)
                card.sprite.position = (mouse_STW[0], mouse_STW[1])
                self.selected = card
                self.selected.sprite.batch = None
                self.hand.removeCard(card)
                act = Act(self.HQuuid, "update", "ms", payload=len(self.hand.deck))
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                
                return True
        return False
    
    def TokenClicked(self, x,y):
        for token in self.tokenList.tokens:
            if token.clicked(x,y):
                if DEBUG: print "Clicked token:", token.uuid
                self.selectedToken = token
                self.tokenList.tokens.remove(token)
                return True
        return False
    
    def MSClicked(self, x,y):
        for ms in self.movableStatList.statlist:
            if ms.clicked(x,y):
                if DEBUG: print "Clicked ms:", ms.uuid
                self.selectedMS = ms
                self.movableStatList.statlist.remove(ms)
                return True
        return False
    
    def TokenRightClicked(self, x,y):
        for token in self.tokenList.tokens:
            if token.clicked(x,y):
                if DEBUG: print "Right Clicked token:", token.uuid
                act = Act(token.uuid, "remove", "token")
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                return True
        return False

    #def MSRightClicked(self, x,y):
    #    for ms in self.movableStatList.statlist:
    #        if ms.clicked(x,y):
    #            if DEBUG: print "right Clicked ms:", ms.uuid
    #            act = Act(ms.uuid, "remove", "ms")
    #            self.Send({"action": "addact", "act": pickle.dumps(act)})
    #            return True
    #    return False

    def CardClicked(self, x,y):
        for card in self.localCardList.deck:
            if card.clicked(x,y):
                if DEBUG: print "card clicked: ", card.name
                self.selected = card
                self.localCardList.removeCard(card)
                return True
        return False
    
    def ZoomCard(self, x,y):
        #check cards on the board first
        for card in self.localCardList.deck:
            if card.clicked(x,y) and card.faceUp:
                if DEBUG: print "card To Zoom: ", card.name
                self.zoomedCard = Sprite(pyglet.image.load(self.baseDeck.findCardByCID(card.cid).imageloc))
                #self.zoomedCard.scale = 2
                return True
        for card in self.hand.deck:
            if card.contains2(self.mouseposx, self.mouseposy) and card.faceUp:
                if DEBUG: print "card to zoom from hand"
                self.zoomedCard = Sprite(pyglet.image.load(self.baseDeck.findCardByCID(card.cid).imageloc))
                #self.zoomedCard.scale = 4
                return True
        return False
    def CardToDeck(self, x,y):
        for card in self.localCardList.deck:
            if card.clicked(x,y):
                if DEBUG: print "card To Deck: ", card.name
                card.inHand = False
                card.isTapped = False
                card.sprite = None
                self.localCardList.findCardByUUID(card.uuid)
                self.playerDeck.putOnTop(card)
                act = Act(card.uuid, "remove", "card")
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                act = Act(self.RNDuuid, "update", "ms", payload=len(self.playerDeck.deck))
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                
                connection.Send({"action": "message", "message": pickle.dumps("has put a card on top of his deck")})
                return True
        return False
    
    def CardToHand(self, x,y):
        for card in self.localCardList.deck:
            if card.clicked(x,y):
                if DEBUG: print "card To Hand: ", card.name
                card.inHand = True
                card.isTapped = False
                card.faceUp = True
                card.sprite = None
                self.localCardList.findCardByUUID(card.uuid)
                self.hand.deck.append(card)
                act = Act(card.uuid, "remove", "card")
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                connection.Send({"action": "message", "message": pickle.dumps("has put a card in hand from the board")})
                act = Act(self.HQuuid, "update", "ms", payload=len(self.hand.deck))
                self.Send({"action": "addact", "act": pickle.dumps(act)})
                return True
        return False
    
        
    def CardMove(self, x,y):
        #if DEBUG: print "Moving"
        #mouse_STW = self.camera.screen_to_world(x, y)
        self.selected.sprite.position = (x,y)
    
    def TokenMove(self, x,y):
        self.selectedToken.sprite.position = (x,y)
        
    def MSMove(self, x,y):
        self.selectedMS.sprite.position = (x,y)
    
    def CardDrop(self, x,y):
        if DEBUG: print "Dropping"
        self.selected.position = (x,y)
        self.selected.dirty = True
        if self.selected.inHand:
            self.selected.inHand = False
            self.selected.faceUp = False
        self.Send({"action": "movecard", "card": pickle.dumps(self.selected.getCardN())})
        self.selected = None
        
    def TokenDrop(self, x,y):
        if DEBUG: print "Dropping"
        self.selectedToken.position = (x,y)
        self.Send({"action": "movetoken", "token": pickle.dumps(self.selectedToken.getTokenN())})
        self.selectedToken = None
    
    def MSDrop(self, x,y):
        if DEBUG: print "Dropping"
        self.selectedMS.position = (x,y)
        self.Send({"action": "movems", "ms": pickle.dumps(self.selectedMS.getMovableStatN())})
        self.selectedMS = None
    
    
    def tap_card(self, x,y):
        if DEBUG: print "Count of cards", str(len(self.localCardList.deck))
        for card in self.localCardList.deck:
            if card.clicked(x,y):
                if DEBUG: print "card clicked: ", card.name
                
                if card.isTapped == False:
                    card.isTapped = True
                else:
                    card.isTapped = False
                card.dirty = True
                self.localCardList.removeCard(card) 
                self.Send({"action": "movecard", "card": pickle.dumps(card.getCardN())})
                return True
        return False
    
    def flip_card(self, x,y):
        for card in self.localCardList.deck:
            if card.clicked(x,y):
                if DEBUG: print "card clicked: ", card.name
                if card.faceUp == False:
                    card.faceUp = True
                else:
                    card.faceUp = False
                    
                card.dirty = True
                self.localCardList.removeCard(card)    

                self.Send({"action": "movecard", "card": pickle.dumps(card.getCardN())})
                return True
        return False
    def SetNickname(self, input):
        connection.Send({"action": "nickname", "nickname": input})
    
    def SendMessage(self, input):
        connection.Send({"action": "message", "message": pickle.dumps(input)})
        
    # --------------------------------------- Network Callbacks ------------------------------------------- #        
    def Network_initial(self, data):
        self.players = data['colors']
    def Network_initialcards(self, data):
        self.cards = data['cards']
    def Network_initialtokens(self, data):
        self.tokens = data['tokens']
    def Network_initialacts(self, data):
        self.acts = data['acts']
    def Network_initialmss(self, data):
        self.mss = data['mss']
    def Network_addcard(self, data):
        if DEBUG: print "From network addCard"
        self.cards[data['id']]['cards'].append(data['card'])
    def Network_movecard(self, data):
        if DEBUG: print "From Network movecard"
        self.cards[data['id']]['cards'].append(data['card'])
    def Network_addact(self, data):
        if DEBUG: print "From network addact"
        self.acts[data['id']]['acts'].append(data['act'])
    def Network_addtoken(self, data):
        if DEBUG: print "From network addtoken"
        self.tokens[data['id']]['tokens'].append(data['token'])
    def Network_movetoken(self, data):
        if DEBUG: print "From Network movetoken"
        self.tokens[data['id']]['tokens'].append(data['token'])
    def Network_addms(self, data):
        if DEBUG: print "From network addms"
        self.mss[data['id']]['mss'].append(data['ms'])
    def Network_movems(self, data):
        if DEBUG: print "From Network movems"
        self.mss[data['id']]['mss'].append(data['ms'])
    
    
        
    #Chat
    def Network_message(self, data):
        self.update_chat(data['who'] + ": " + pickle.loads(data['message']))    
    def Network_players(self, data):
        self.playersLabel = str(len(data['players'])) + " players"
        mark = []
        for i in data['players']:
            if not self.players.has_key(i):
                self.players[i] = {'color': data['players'][i] }
                self.cards[i] = { 'cards': []}
                self.tokens[i] = { 'tokens': []}
                self.acts[i] = { 'acts': []}
                self.mss[i] = { 'mss': []}
                
        for i in self.players:
            if not i in data['players'].keys():
                mark.append(i)
                
        for m in mark:
            del self.players[m]

    def Network(self, data):
        pass
    
    def Network_connected(self, data):
        self.statusLabel = "connected"
    
    def Network_error(self, data):
        import traceback
        traceback.print_exc()
        self.statusLabel = data['error'][1]
        connection.Close()
    
    def Network_disconnected(self, data):
        self.statusLabel += " - disconnected"

# here's where we execute the code        
if __name__ == "__main__":
    game = GameBoard()
    game.main_loop()
