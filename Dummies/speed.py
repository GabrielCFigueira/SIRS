import random

import GenericDummy

class Speed(GenericDummy.GenericDummy):
    def __init__(self):
        super(Speed, self).__init__()
        self.version = 'ola01234567890132456798013245678'
        self.id = '0123465789'
        self.name = 'speed'
        self.port = 5003

    def update_state(self):
        i = random.randint(0,250)
        state = "Speed {}km/h".format(i)
        #print(state)
        return state


if __name__ == '__main__':
    g1 = Speed()
    g1.start()
    g1.join()
