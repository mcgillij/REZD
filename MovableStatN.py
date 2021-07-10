class MovableStatN:
    def __init__(self, label, count, uuid, position):
        self.label = label
        self.count = count
        self.uuid = uuid
        self.position = position

    def __str__(self):
        return self.label + "," + self.count + "," + self.uuid + "," + self.position
