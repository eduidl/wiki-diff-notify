from argparse import ArgumentParser
from pathlib import Path
from time import sleep

from libs import WikiDiffNotifier


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument('--config', default='config.ini')
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    notifier = WikiDiffNotifier(config_path)
    while True:
        notifier.notify()
        sleep(5 * 60)


if __name__ == '__main__':
    main()
