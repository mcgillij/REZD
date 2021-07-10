class Act:
    """Act class for passing various actions across to the other clients"""

    def __init__(self, uuid, action, target, payload=None):

        self.uuid = uuid
        self.action = action
        self.target = target
        self.payload = payload

    def __str__(self):
        return self.uuid, self.action, self.target, self.payload
