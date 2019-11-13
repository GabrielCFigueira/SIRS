import time
import threading
import os
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

'''
logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')
'''


def main():
    logging.info('Server on')
    logging.info('Enter commands...')
    while(True):
        cmd = input()

        try:
            val = int(cmd)
        except:
            val = None

        if(val):
            t = threading.Thread(target=sleeper, args=[val])
            t.start()

        else:
            fileName = cmd + '.py'
            t = threading.Thread(target=fileTrigger, args=[fileName])
            t.start()


def sleeper(seconds):
    logging.info(f'sleeping {seconds} second(s)')
    time.sleep(seconds)
    logging.info(f'Done sleeping')

def fileTrigger(fileName):
    os.system(fileName)



if __name__ == '__main__':
    main()