import random

import GenericDummy

class Gas(GenericDummy.GenericDummy):
    def __init__(self):
        super(Gas, self).__init__()
        self.version = '01000000000001010000000000000000'
        self.id = 'gassnszeus'
        self.name = 'gas'
        self.port = 5002

    def update_state(self):
        i = random.randint(0, 100)

        if i <= 20:
            state = "ADD (0%-20%)"
        elif i >= 90:
            state = "FULL (90%-100%)"
        else:
            state = "NORMAL (21%-89%)"

        #print("Gas: {}% | State: {}".format(i, state))
        return state



if __name__ == '__main__':
    g1 = Gas()
    g1.start()
    g1.join()

# ADD (0%-20%) | NORMAL (21%-89%) | FULL (90%-100%)
