import uuid
from CardN import CardN
from pyglet.sprite import Sprite
from pyglet.gl import *
import math
from constants import *


class Card:
    def __init__(self):
        # various card states
        self.faceUp = True
        self.isTapped = False
        self.inHand = False
        self.dirty = True  # like on the screen :P
        # self.fromDeck = True

        # vars for xml

        self.uuid = str(uuid.uuid4())

        self.cid = ""
        self.name = ""
        self.type = ""
        self.subtype1 = ""
        self.subtype2 = ""
        self.cost = ""
        self.installCost = ""
        self.rezCost = ""
        self.trashCost = ""
        self.strength = ""
        self.mu = ""
        self.rarity = ""
        self.artist = ""
        self.text = ""
        self.quote = ""
        self.release = ""
        self.difficulty = ""
        self.agendaPoints = ""
        self.playertype = ""
        self.imageloc = ""

        self.sprite = None
        self.position = (0, 0)

    # def draw(self):
    #     self.image.blit(self.sprite.position[0], self.sprite.position[1])

    def set_sprite_pos(self):
        self.sprite.position = self.position
        # self.image.anchor_x = self.image.width/2
        # self.image.anchor_y = self.image.height/2

    def loadImg(self):
        self.sprite.image.height = 440
        self.sprite.image.width = 312
        self.sprite.image.anchor_x = self.sprite.image.width / 2
        self.sprite.image.anchor_y = self.sprite.image.height / 2

        if self.inHand:
            self.sprite.scale = 0.5
            self.sprite.image.anchor_x = self.sprite.image.width / 2
            self.sprite.image.anchor_y = self.sprite.image.height / 2
            return

        if self.isTapped:
            self.sprite.image.anchor_x = self.sprite.image.width / 2
            self.sprite.image.anchor_y = self.sprite.image.height / 2
            self.sprite.rotation = 90
        else:
            self.sprite.rotation = 0

            # self.sprite.image.anchor_x = self.sprite.image.width/2
            # self.sprite.image.anchor_x = self.sprite.image.height/2

    def clicked(self, x, y):
        return self.contains(x, y)
        # return self.contains(x,y)

    # def clickedHand(self,x,y):
    #    return self.containsHand(x,y)

    def rotateRect(self, deg):
        x1 = -self.sprite.image.anchor_x * self.sprite.scale
        y1 = -self.sprite.image.anchor_y * self.sprite.scale
        x2 = x1 + self.sprite.image.width * self.sprite.scale
        y2 = y1 + self.sprite.image.height * self.sprite.scale

        # x1 = -self.sprite.image.anchor_x
        # y1 = -self.sprite.image.anchor_y
        # x2 = x1 + self.sprite.image.width
        # y2 = y1 + self.sprite.image.height
        x, y = self.sprite.position

        r = -math.radians(deg)
        cr = math.cos(r)
        sr = math.sin(r)
        ax = int(x1 * cr - y1 * sr + x)
        ay = int(x1 * sr + y1 * cr + y)
        bx = int(x2 * cr - y1 * sr + x)
        by = int(x2 * sr + y1 * cr + y)
        cx = int(x2 * cr - y2 * sr + x)
        cy = int(x2 * sr + y2 * cr + y)
        dx = int(x1 * cr - y2 * sr + x)
        dy = int(x1 * sr + y2 * cr + y)

        return ax, ay, bx, by, cx, cy, dx, dy

    # def containsHand(self, x, y):
    #   ax,ay = self.sprite.position
    #    ax -= self.sprite.image.anchor_x
    #  ay -= self.sprite.image.anchor_y
    #    print "SCALE: ", str(self.sprite.scale)
    #   if x < ax or x > ax + self.sprite.image.width * self.sprite.scale: return False
    #   if y < ay or y > ay + self.sprite.image.height * self.sprite.scale: return False
    #    return True

    def contains2(self, x, y):
        """Return True if the point (x, y) is contained on the node
        bounds.
        """
        ax, ay, bx, by, cx, cy, dx, dy = self.rotateRect(0)
        if x < ax or x > ax + self.sprite.width:
            return False
        if y < ay or y > ay + self.sprite.height:
            return False
        return True
        # Put point on the node local coord system
        # p = p - self.sprite.position
        # p = p.rotate(-self.sprite.rotation)

        # return abs(p.x) < (self.sprite.width/2) and abs(p.y) < (self.sprite.height/2)

    def contains(self, x, y):
        ax, ay = self.sprite.position
        if self.isTapped:
            ax -= self.sprite.image.anchor_y
            ay -= self.sprite.image.anchor_x
            if x < ax or x > ax + self.sprite.height:
                return False
            if y < ay or y > ay + self.sprite.width:
                return False
        else:
            ax -= self.sprite.image.anchor_x
            ay -= self.sprite.image.anchor_y
            # if x < ax or x > ax + self.sprite.image.width: return False
            # if y < ay or y > ay + self.sprite.image.height: return False
            if x < ax or x > ax + self.sprite.width:
                return False
            if y < ay or y > ay + self.sprite.height:
                return False
        return True

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def to_xml(self):
        xml = "<card>\n"
        if self.cid:
            xml += "\t<cid>" + self.cid + "</cid>\n"
        if self.name:
            xml += "\t<name>" + self.name + "</name>\n"
        if self.type:
            xml += "\t<type>" + self.type + "</type>\n"
        if self.subtype1:
            xml += "\t<subtype1>" + self.subtype1 + "</subtype1>\n"
        if self.subtype2:
            xml += "\t<subtype2>" + self.subtype2 + "</subtype2>\n"
        if self.cost:
            xml += "\t<cost>" + self.cost + "</cost>\n"
        if self.installCost:
            xml += "\t<install_cost>" + self.installCost + "</install_cost>\n"
        if self.rezCost:
            xml += "\t<rez_cost>" + self.rezCost + "</rez_cost>\n"
        if self.trashCost:
            xml += "\t<trash_cost>" + self.trashCost + "</trash_cost>\n"
        if self.strength:
            xml += "\t<strength>" + self.strength + "</strength>\n"
        if self.mu:
            xml += "\t<mu>" + self.mu + "</mu>\n"
        if self.rarity:
            xml += "\t<rarity>" + self.rarity + "</rarity>\n"
        if self.artist:
            xml += "\t<artist>" + self.artist + "</artist>\n"
        if self.text:
            xml += "\t<text>" + self.text + "</text>\n"
        if self.quote:
            xml += "\t<quote>" + self.quote + "</quote>\n"
        if self.release:
            xml += "\t<release>" + self.release + "</release>\n"
        if self.difficulty:
            xml += "\t<difficulty>" + self.difficulty + "</difficulty>\n"
        if self.agendaPoints:
            xml += "\t<agenda_points>" + self.agendaPoints + "</agenda_points>\n"
        if self.playertype:
            xml += "\t<playertype>" + self.playertype + "</playertype>\n"
        if self.imageloc:
            xml += "\t<image>" + self.imageloc + "</image>\n"
        xml += "</card>\n"
        return xml

    def getCardN(self):
        return CardN(
            self.cid,
            self.position,
            self.uuid,
            self.isTapped,
            self.faceUp,
            self.inHand,
            self.dirty,
        )
