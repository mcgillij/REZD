class TokenN:
    """Network version of the Token that gets passed
    to the server, so we don't spam it with all the card information"""

    def __init__(self, type, uuid, position):
        self.type = type
        self.uuid = uuid
        self.position = position

    def __str__(self):
        return self.type + "," + self.uuid + "," + self.position
