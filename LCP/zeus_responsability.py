from itertools import product
from random import uniform

my_name = 'Zeus'

# Should be different for Anakin and Zeus
onoff_queries = {'motor': lambda new_state: return 'ok',
                 'lock': lambda new_state: return 'ok',
                 'brake': lambda new_state: return 'ok'}


read_query = {'brake': lambda: uniform(0,1),
              'gas': lambda: uniform(1, 30),
              'direction': lambda: uniform(-360, 360)}

state = {}

def deal_with_it(query):

    if query[0] == 'read' and query[1] in read_query:
        return read_query[query[1]]()

    elif tuple(query) in product(onoff_queries.keys(), ['on', 'off']):
        return read_query[query[0]](query[1])

    else:
        return 'error'

