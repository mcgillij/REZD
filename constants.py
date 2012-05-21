import pyglet
import ConfigParser
gameconfig = ConfigParser.ConfigParser()
gameconfig.readfp(open("conf/game.conf"))
WINHEIGHT = gameconfig.getint('resolution', 'height')
WINWIDTH = gameconfig.getint('resolution', 'width')
DEBUG = gameconfig.getboolean('debug', 'debug')
RUNNERBACK = pyglet.image.load("assets/images/runner_back.jpg")
CORPBACK = pyglet.image.load("assets/images/corp_back.jpg")
FIVEBITTOKEN = pyglet.image.load("assets/images/5bit.png")
ONEBITTOKEN = pyglet.image.load("assets/images/bit.png")
#RND = pyglet.image.load("assets/images/rnd.png")
ARCHIVES = pyglet.image.load("assets/images/archives.png")
DRAGGER = pyglet.image.load("assets/images/dragger.png")
TAG = pyglet.image.load("assets/images/tag.png")
BADPUBLICITY = pyglet.image.load("assets/images/badpublicity.png")
#BG = pyglet.image.load("assets/images/bg.gif")
BRAINDAMAGE = pyglet.image.load("assets/images/braindamage.png")
VIRUS = pyglet.image.load("assets/images/virus.png")