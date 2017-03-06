class Unit:
    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Test:
    def __init__(self, token, master, units):
        self.token = token
        self.master = master
        self.units = units


