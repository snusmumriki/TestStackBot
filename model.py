class Unit:
    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Test:
    units = []
    results = {}

    def __init__(self, token):
        self.token = token


class Draft:
    def __init__(self, token, test, num):
        self.token = token
        self.test = test
        self.num = num


class Process:
    def __init__(self, test, all, right):
        self.test = test
        self.all = all
        self.right = right
