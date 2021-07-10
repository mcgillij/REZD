import uuid
from pyglet.sprite import Sprite
from pyglet.gl import *
import math
from constants import *
from MovableStatN import MovableStatN


class MovableStat:
    def __init__(self, label, count):
        self.label = label
        self.count = count
        self.uuid = str(uuid.uuid4())
        self.sprite = None
        self.position = (500, 500)
        self.color = None

    def loadImg(self):
        if self.sprite == None:
            self.sprite = Sprite(DRAGGER)
            self.sprite.image.anchor_x = self.sprite.image.height / 2
            self.sprite.image.anchor_y = self.sprite.image.width / 2
        self.sprite.position = self.position

    def clicked(self, x, y):
        return self.contains(x, y)

    def rotateRect(self, deg):
        x1 = -self.sprite.image.anchor_x * self.sprite.scale
        y1 = -self.sprite.image.anchor_y * self.sprite.scale
        x2 = x1 + self.sprite.image.width * self.sprite.scale
        y2 = y1 + self.sprite.image.height * self.sprite.scale
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

    def contains(self, x, y):
        ax, ay = self.sprite.position
        ax -= self.sprite.image.anchor_x
        ay -= self.sprite.image.anchor_y
        if x < ax or x > ax + self.sprite.image.width * self.sprite.scale:
            return False
        if y < ay or y > ay + self.sprite.image.height * self.sprite.scale:
            return False
        return True

    def __str__(self):
        return self.name

    def getMovableStatN(self):
        return MovableStatN(self.label, self.count, self.uuid, self.position)
