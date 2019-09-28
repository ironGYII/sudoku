# -*- coding: utf-8 -*-
data = '800000000003600000070090200050007000000045700000100030001000068008500010090000400'
# data = '060012870050460309908003020024500760300100004579080000890076201007090653001240080'


class SudokuGame(object):

    def __init__(self, data):
        self.data = list(data)
        self.avaliable_value = {i: 9 - self.data.count(i) for i in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] if 9 - self.data.count(i) > 0}

    def get_question_possibility(self):
        if '0' not in self.data:
            return None

        index = self.data.index('0')
        return index, self.get_index_question_possibility(index)

    def get_index_question_possibility(self, index):
        x = index % 9
        y = int(index / 9)

        intersections = self.get_x_set(x) + self.get_y_set(y) + self.get_o_set(x, y)
        possiable_set = {'1', '2', '3', '4', '5', '6', '7', '8', '9'} - set([str(self.data[i]) for i in intersections])
        return possiable_set

    def assignment(self, index, value):
        if self.avaliable_value.get(value, 0) < 0:
            return False
        self.data[index] = str(value)
        return True

    def get_x_set(self, x):
        return [x + y * 9 for y in range(9)]

    def get_y_set(self, y):
        return [x + y * 9 for x in range(9)]

    def get_o_set(self, x, y):
        return [_x + _y * 9 for _x in range(x - x % 3, x - x % 3 + 3) for _y in range(y - int(y % 3), y - int(y % 3) + 3)]

    def vertify(self, index, value):

        x = index % 9
        y = int(index / 9)
        # vertify_x_line
        x_set = self.get_x_set(x)
        # vertify_y_line
        y_set = self.get_y_set(y)
        # vertify_o
        o_set = self.get_o_set(x, y)

        for position in x_set + y_set + o_set:
            if self.data[position] == value:
                return False
        return True


def calc(game_obj):

    data = game_obj.get_question_possibility()

    if data is None:
        return ''.join(game_obj.data)

    index, values = data
    values = sorted(values)

    for value in values:
        if game_obj.assignment(index, value) is False:
            continue
        child = SudokuGame(game_obj.data)
        data = calc(child)
        if data is not None:
            return data
    return None


if __name__ == '__main__':
    import time

    for _ in range(100):
        l = time.time()
        obj = SudokuGame(data)
        print(calc(obj), time.time() - l)
