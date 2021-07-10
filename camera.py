from vec2 import Vec2
import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *
import os
from collections import defaultdict


class Camera(object):
    """The editor 2D camera."""

    def __init__(self, window):
        """Create a camera for the given window."""
        self.window = window
        self.pos = Vec2(0, 0)
        self.speed = 2000.0
        self._zoom = 1.0
        self.zoom_speed = 1.2

        ## KeyState for camera movement
        self.key_state = key.KeyStateHandler()
        window.push_handlers(self.key_state)

        pyglet.clock.schedule(self.check_input)

    def _set_zoom(self, value):
        self._zoom = value
        if self._zoom < 0.01:
            self._zoom = 0.01

    def _get_zoom(self):
        return self._zoom

    zoom = property(_get_zoom, _set_zoom)

    def transform(self):
        """Apply the camera transformation."""
        half_win = Vec2(self.window.width / 2, self.window.height / 2)
        t = self.pos + half_win

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(half_win.x, half_win.y, 0.0)
        glScalef(self.zoom, self.zoom, 1.0)
        glTranslatef(-t.x, -t.y, 0.0)

    def screen_to_world(self, x, y):
        """Converts from screen to world coordinates."""
        half_win = Vec2(self.window.width / 2, self.window.height / 2)
        spos = Vec2(x, y)

        return ((spos - half_win) / self.zoom) + (self.pos + half_win)

    def check_input(self, dt):
        """Update method called at each frame."""
        dx, dy = 0, 0
        if self.key_state[key.UP]:
            dy = 1
        elif self.key_state[key.DOWN]:
            dy = -1

        if self.key_state[key.RIGHT]:
            dx = 1
        elif self.key_state[key.LEFT]:
            dx = -1

        if dx != 0 or dy != 0:
            vel = Vec2(dx, dy).normalize() * self.speed * dt
            self.pos = self.pos + vel
            # print str(dt)
        # if self.key_state[key.DOWN]:
        #    self.zoom -= self.zoom_speed * dt
        # elif self.key_state[key.UP]:
        #   self.zoom += self.zoom_speed * dt
