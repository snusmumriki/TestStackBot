class Unit:
    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Test:
    def __init__(self, token):
        self.token = token
        self.units = []


class Draft:
    def __init__(self, token, test, num):
        self.token = token
        self.test = test
        self.num = num
