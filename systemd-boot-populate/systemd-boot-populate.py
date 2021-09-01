import argparse
import jinja2
import semver
import toml

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-v',
        '--verbose',
        action="store_true",
        dest='verbose',
        default=False,
        help='Displays additional information'
    )
    parser.add_argument(
        'Distro Name',
        '-n',
        '--distro-name',
        action='store',
        dest='distro_name',
        help='Distribution Name to display in bootloader menu entry'
        )
    parser.add_argument(
        'Microcode',
        '-u',
        '--ucode',
        action='store',
        dest='ucode',
        help='Microcode image to load'
        )

    return parser.parse_args()

def load_config(settings):
    return settings

if __name__ == "__main__":
    settings = {
        'verbose': True,
        'distro_name': 'Linux',
        'ucode': None
    }

    args = parse_args()
