import GenericDummy

class Brakes(GenericDummy.GenericDummy):
    def __init__(self):
        self.state = 'on' #hack, do not do try this at home
        super(Brakes, self).__init__()
        self.version = 'ola01234567890132456798013245678'
        self.id = '0123465789'
        self.name = 'brakes'
        self.port = 5011

    def update_state(self):
        return self.state

    def set_state(self, new_state):
        # straightforward set, we're trusting the sender here
        return new_state


if __name__ == '__main__':
    g1 = Brakes()
    g1.start()
    g1.join()
