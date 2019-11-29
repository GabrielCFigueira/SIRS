import random
import time

import GenericDummy

class Oil(GenericDummy.GenericDummy):
    def __init__(self):
        super(Oil, self).__init__()
        self.version = 'ola01234567890132456798013245678'
        self.id = '0123465789'
        self.name = 'oil'
        self.state = self.update_state()
        self.port = 5001

    def update_state(self):
        i = random.randint(0, 100)

        if i <= 20:
            state = "ADD (0%-20%)"
        elif i >= 90:
            state = "FULL (90%-100%)"
        else:
            state = "NORMAL (21%-89%)"

        print("Oil: {}% | State: {}".format(i, state))
        return state



if __name__ == '__main__':
    g1 = Oil()
    g1.start()
    g1.join()
