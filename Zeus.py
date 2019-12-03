import multiprocessing
import subprocess
from LCP import lcp_provider

my_dummies = {5001: ['python3', 'Dummies/oil.py'],
             5002: ['python3', 'Dummies/gas.py'],
             5003: ['python3', 'Dummies/speed.py'],
             5011: ['python3', 'Dummies/brakes.py']}

#my_dummies = {0: ['python3', 'Dummies/GenericDummy.py']}


if __name__ == '__main__':

    dummies = {}

    # Launch Dummies
    for port, cmd in my_dummies.items():
        dummies[port] = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)
        print(dummies[port].pid)

    # RCP
    rcp = multiprocessing.Process(name='rcp', target=lcp_provider.run,
                                  args=[], daemon=True)
    rcp.start()

    print("Press enter to kill them all")
    input()

    for dummy in dummies.values():
        dummy.terminate()
        print(dummy.wait())
