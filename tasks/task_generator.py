import copy
import random

import numpy as np


class TaskGenerator(object):
    def __init__(self, collection):
        super(TaskGenerator, self).__init__()
        self.collection = collection

    @staticmethod
    def add_brick(table, current_level, brick):
        n_table = np.copy(table)
        width = n_table.shape[1]



        available_slots = [i for i, e in enumerate(n_table[current_level + 1])
                           if e != 0]

        while True:
            grows_right = random.choice((True, False))
            anchor = random.choice(available_slots)

            if grows_right:
                if (anchor + (len(brick) - 1)) >= width:
                    continue

                for i in range(len(brick)):
                    n_table[current_level][anchor + i] = brick[i]

                break
            else:
                if (anchor - (len(brick) - 1)) < 0:
                    continue

                for i in range(len(brick)):
                    n_table[current_level][anchor - i] = brick[
                        len(brick) - i - 1]

                break

        return n_table

    def generate(self, num_steps, height=8, base_color=6):
        width = 6
        base = [base_color] * width
        pieces = copy.deepcopy(self.collection)
        steps = []
        table = np.zeros((width, height), dtype=int)

        # add base


if __name__ == '__main__':
    table = np.array([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0]
    ])

    brick = [2, 2, 2]

    for i in range(200):
        print(
            TaskGenerator.add_brick(table, 1, brick)
        )
