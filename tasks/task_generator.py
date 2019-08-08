import copy
import random

import numpy as np


class BrickCollection(object):
    def __init__(self, collection_dict=dict()):
        super(BrickCollection, self).__init__()
        self.colors = range(7)

        self.collection = []
        for brick, count in collection_dict.iteritems():
            self.collection += ([brick] * count)

    def _put_brick(self, length, color):
        self.collection.append((length, color))

    def put_brick(self, brick):
        self._put_brick(len(brick), brick[0])

    def get_brick(self, length, color):
        assert color in self.colors

        to_remove = -1
        for i, (i_len, i_color) in enumerate(self.collection):
            if i_len == length and i_color == i_color:
                to_remove = i
                break

        if to_remove < 0:
            return None

        self.collection.pop(to_remove)
        return [color] * length

    def get_random_brick(self):
        brick_i = random.randint(0, len(self.collection) - 1)
        length, color = self.collection.pop(brick_i)

        return [color] * length


class TaskGenerator(object):
    def __init__(self, collection, table_width=18):
        super(TaskGenerator, self).__init__()
        self.collection = collection
        self.table_width = table_width

    @staticmethod
    def check_anchor(anchor, level, brick, table):
        width = table.shape[1]
        # first check: does brick fit in table?
        if anchor + len(brick) - 1 >= width:
            return False

        ret = False
        for i in range(anchor, anchor + len(brick)):
            # second check, does it clash with any other brick
            if table[level][i] != 0:
                return False

            # third check: are there any support points
            if table[level + 1][i] != 0:
                ret = True

        return ret

    @staticmethod
    def add_brick(table, current_level, brick):
        n_table = np.copy(table)
        width = table.shape[1]

        anchor = random.choice([i for i in range(width)
                                if
                                TaskGenerator.check_anchor(i, current_level,
                                                           brick, n_table)])

        for i in range(anchor, anchor + len(brick)):
            n_table[current_level][i] = brick[i - anchor]

        return n_table

    def generate(self, num_steps, height=8, base_width=6, base_color=6):
        assert num_steps >= 1

        base = self.collection.get_brick(base_width, base_color)
        if base is None:
            raise RuntimeError('Base not in collection.')

        steps = []
        table = np.zeros((height, self.table_width), dtype=int)

        # place base
        base_anchor = random.randint(0, self.table_width - base_width)
        for i in range(base_anchor, base_anchor + 6):
            table[height - 1][i] = base_color

        steps.append(np.copy(table))

        for i in range(num_steps - 1):
            brick = self.collection.get_random_brick()
            table = self.add_brick(table, height - 2 - i, brick)
            steps.append(np.copy(table))

            # todo remove bricks

        return steps


if __name__ == '__main__':
    brick_col = BrickCollection(collection_dict={
        (1, 6): 3,
        (2, 6): 3,
        (6, 6): 3,
    })

    gen = TaskGenerator(brick_col)
    print(gen.generate(3))