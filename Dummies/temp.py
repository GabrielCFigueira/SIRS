import random

import GenericDummy

class Temp(GenericDummy.GenericDummy):
    def __init__(self):
        super(Temp, self).__init__()
        self.version = '01000000000001010000000000000000'
        self.id = 'tempankn'
        self.name = 'temp'
        self.port = 5022

    def update_state(self):
        i = random.randint(0, 100)

        if i <= 20:
            state = "LOW (0%-20%)"
        elif i >= 90:
            state = "HIGH (90%-100%)"
        else:
            state = "NORMAL (21%-89%)"

        #print("Gas: {}% | State: {}".format(i, state))
        return state



if __name__ == '__main__':
    GenericDummy.start_the_dummy(Temp)

# ADD (0%-20%) | NORMAL (21%-89%) | FULL (90%-100%)