import random

import GenericDummy

class Oil(GenericDummy.GenericDummy):
    def __init__(self):
        super(Oil, self).__init__()
        self.version = '00000000000000000000000000000001'
        self.id = 'oilsnszeus'
        self.name = 'oil'
        self.port = 5001

    def update_state(self):
        i = random.randint(0, 100)

        if i <= 20:
            state = "ADD (0%-20%)"
        elif i >= 90:
            state = "FULL (90%-100%)"
        else:
            state = "NORMAL (21%-89%)"

        #print("Oil: {}% | State: {}".format(i, state))
        return state



if __name__ == '__main__':
    GenericDummy.start_the_dummy(Oil)
