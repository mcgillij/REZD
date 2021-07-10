import sys
from time import sleep
from weakref import WeakKeyDictionary

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from configparser import ConfigParser
from random import randint


class ServerChannel(Channel):
    """
    This is the server representation of a single connected client.
    """

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.nickname = "anonymous"
        self.id = str(self._server.NextId())
        intid = int(self.id)
        self.color = [
            randint(0, 255),
            randint(0, 255),
            randint(0, 255),
            255,
        ]  # tuple([randint(0, 127) for r in range(3)])
        self.cards = []
        self.tokens = []
        self.acts = []
        self.mss = []

    def PassOn(self, data):
        # pass on what we received to all connected clients
        data.update({"id": self.id})
        self._server.SendToAll(data)

    def Close(self):
        self._server.DelPlayer(self)

    ##################################
    ### Network specific callbacks ###
    ##################################
    def Network_message(self, data):
        self._server.SendToAll(
            {"action": "message", "message": data["message"], "who": self.nickname}
        )

    def Network_nickname(self, data):
        self.nickname = data["nickname"]
        self._server.SendPlayers()

    def Network_addcard(self, data):
        self.cards.append(data["card"])
        self.PassOn(data)

    def Network_movecard(self, data):
        self.cards.append(data["card"])
        self.PassOn(data)

    def Network_addtoken(self, data):
        self.tokens.append(data["token"])
        self.PassOn(data)

    def Network_movetoken(self, data):
        self.tokens.append(data["token"])
        self.PassOn(data)

    def Network_addms(self, data):
        self.mss.append(data["ms"])
        self.PassOn(data)

    def Network_movems(self, data):
        self.mss.append(data["ms"])
        self.PassOn(data)

    def Network_addact(self, data):
        self.acts.append(data["act"])
        self.PassOn(data)


class GameServer(Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.players = WeakKeyDictionary()
        self.cards = WeakKeyDictionary()
        self.tokens = WeakKeyDictionary()
        self.acts = WeakKeyDictionary()
        self.mss = WeakKeyDictionary()
        print("Server launched")

    def NextId(self):
        self.id += 1
        return self.id

    def Connected(self, channel, addr):
        self.AddPlayer(channel)

    def AddPlayer(self, player):
        print("New Player" + str(player.addr))
        self.players[player] = True
        player.Send(
            {
                "action": "initial",
                "colors": dict([(p.id, {"color": p.color}) for p in self.players]),
            }
        )
        player.Send(
            {
                "action": "initialcards",
                "cards": dict([(p.id, {"cards": p.cards}) for p in self.players]),
            }
        )
        player.Send(
            {
                "action": "initialtokens",
                "tokens": dict([(p.id, {"tokens": p.tokens}) for p in self.players]),
            }
        )
        player.Send(
            {
                "action": "initialacts",
                "acts": dict([(p.id, {"acts": p.acts}) for p in self.players]),
            }
        )
        player.Send(
            {
                "action": "initialmss",
                "mss": dict([(p.id, {"mss": p.mss}) for p in self.players]),
            }
        )
        self.SendPlayers()

    def DelPlayer(self, player):
        print("Deleting Player" + str(player.addr))
        del self.players[player]
        self.SendPlayers()

    def SendPlayers(self):
        self.SendToAll(
            {
                "action": "players",
                "players": dict([(p.id, p.color) for p in self.players]),
            }
        )

    def SendToAll(self, data):
        [p.Send(data) for p in self.players]

    def Launch(self):
        while True:
            self.Pump()
            sleep(0.0001)


config = ConfigParser()
config.readfp(open("conf/game.conf"))
host = config.get("server", "host")
port = config.getint("server", "port")
s = GameServer(localaddr=(host, port))
s.Launch()
