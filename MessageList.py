class MessageList:
    def __init__(self):
        self.list = []

    def addMessage(self, message):
        if len(self.list) > 6:
            self.list.pop(0)

        self.list.append(message)

    def getMessages(self):
        return_string = ""
        for item in self.list:
            return_string += item + "\n"
        if return_string == "":
            return "1"
        return return_string
