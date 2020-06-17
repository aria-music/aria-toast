import logging

from aria.Aria import Aria
from aria.Config import Config

logging.basicConfig(
                level=logging.INFO,
                format='[%(asctime)s][%(module)s] %(message)s'
            )

def main():
    conf = Config()
    aria = Aria(conf)

    logging.info('start')
    try:
        aria.run()
    except Exception as E:
        logging.error(f'fucked: {E}', stack_info=True)
        aria.close()

if __name__ == "__main__":
    main()