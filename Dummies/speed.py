import random

import GenericDummy

class Speed(GenericDummy.GenericDummy):
    def __init__(self):
        super(Speed, self).__init__()
        self.version = '00001010101000000000000000000000'
        self.id = 'spdsnszeus'
        self.name = 'speed'
        self.port = 5003

    def update_state(self):
        i = random.randint(0,250)
        state = "Speed {}km/h".format(i)
        #print(state)
        return state


if __name__ == '__main__':
    GenericDummy.start_the_dummy(Speed)
