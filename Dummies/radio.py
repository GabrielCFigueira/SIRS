import GenericDummy

class Radio(GenericDummy.GenericDummy):
    def __init__(self):
        self.state = 'on' #hack, do not do try this at home
        super(Brakes, self).__init__()
        self.version = '00100000000000000000000000000000'
        self.id = 'radioankin'
        self.name = 'radio'
        self.port = 5021

    def update_state(self):
        return self.state

    def set_state(self, new_state):
        # straightforward set, we're trusting the sender here
        return new_state


if __name__ == '__main__':
    GenericDummy.start_the_dummy(Radio)