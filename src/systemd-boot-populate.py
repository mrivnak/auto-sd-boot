import argparse
import getpass
import jinja2
import pathlib
import re
import subprocess
import sys
import termcolor
import toml

class Paths:
    CONFIG_PATH = pathlib.PosixPath('/etc', 'systemd-boot-populate.toml').resolve()
    LOADER_TEMPLATE_PATH = pathlib.PosixPath(__file__).parent.joinpath('templates', 'loader.conf').resolve()
    ENTRY_TEMPLATE_PATH = pathlib.PosixPath(__file__).parent.joinpath('templates', 'entry.conf').resolve()

    BOOT_DIR = pathlib.PosixPath('/boot').resolve()

    LOADER_OUTPUT_PATH = pathlib.PosixPath('/efi', 'loader', 'loader.conf').resolve()
    ENTRY_OUTPUT_DIR = BOOT_DIR.joinpath('loader', 'entries').resolve()

def strip_blank_lines(text):
    return re.sub(r'\n\s*\n', '\n', text, re.MULTILINE)  # Remove extra blank lines in the output text

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
        '-n',
        '--no-delete',
        action="store_true",
        dest='no_delete',
        default=False,
        help='Do not delete existing entry files'
    )
    parser.add_argument(
        '-d',
        '--distro-name',
        action='store',
        dest='distro_name',
        help='Distribution Name to display in bootloader menu entry'
    )
    parser.add_argument(
        '-u',
        '--ucode',
        action='store',
        dest='ucode',
        help='Microcode image to load'
    )

    return parser.parse_args()

def load_config(conf):
    toml_data = toml.loads(open(Paths.CONFIG_PATH).read())

    for key in toml_data['main'].keys():
        conf[key] = toml_data['main'][key]

    return conf

def load_loader_config():
    return toml.loads(open(Paths.CONFIG_PATH).read())['loader']

def gen_loader(conf):
    t = jinja2.Template(open(Paths.LOADER_TEMPLATE_PATH).read())

    loader = t.render(
        default=conf.get('default'),
        timeout=conf.get('timeout'),
        editor='yes' if conf.get('editor') else 'no',  # Systemd-boot expects "yes" and "no" (and "1" and "0" for the following lines)
        auto_entries=1 if conf.get('auto_entries') else 0,  # rather than true or false for these fields
        auto_firmware=1 if conf.get('auto_entries') else 0,
        console_mode=conf.get('console_mode')
    )

    open(Paths.LOADER_OUTPUT_PATH, 'w').write(strip_blank_lines(loader))

def gen_entries(conf, loader_conf):
    t = jinja2.Template(open(Paths.ENTRY_TEMPLATE_PATH).read())

    kernels = load_kernels(loader_conf)

    for item in kernels:
        entry = t.render(
            title=conf['distro_name'],
            version=item['version'],
            linux=item['filename'],
            ucode=conf.get('ucode'),
            initramfs=item['initramfs'],
            options=conf['options'] if len(conf['options']) > 0 else None
        )
        open(Paths.ENTRY_OUTPUT_DIR.joinpath(f'{item.get("version")}.conf'), 'w').write(strip_blank_lines(entry))
    
def load_kernels(loader_conf):
    files = [x.name for x in pathlib.Path(Paths.BOOT_DIR).iterdir() if x.is_file()]  # Read all filenames in the boot directory
    files.sort()  # Allows searching for an initramfs to be faster since they will appear first

    kernel_re = re.compile(r'(vmlinu[x|z]-(.*))')  # Setup regex for kernel and initramfs filenames
    kernel_files = [file for file in files if kernel_re.match(file)]  # Find all kernel filenames

    # Check if the default kernel selection exists and issue a warning if not
    found_default = False
    for file in kernel_files:
        match = kernel_re.search(file)
        if match.group(2) == loader_conf.get('default'):
            found_default = True
    if not found_default:
        print(termcolor.colored('WARNING', 'yellow'), f': Cannot find default kernel selection \"{loader_conf["default"]}\"', sep='', file=sys.stderr)


    kernels = []
    for file in kernel_files:
        match = kernel_re.search(file)
        
        initramfs_re = re.compile(f'(initramfs-{match.group(2)})')

        kernels.append({
            'filename': match.group(1),
            'version': match.group(2) if not 'arch' in open(pathlib.PosixPath('/etc', 'os-release').resolve()).readline().lower() else f'{match.group(2)}-' + subprocess.run([f"pacman -Qi {match.group(2)} | grep -Po \'^Version\s*: \K.+\'"], shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8').strip('\n'),
            'initramfs': initramfs_match.group(1) if any((initramfs_match := initramfs_re.match(x)) for x in files) else None
        })

    return kernels
        

if __name__ == "__main__":
    # Confirm that script is running as root
    if getpass.getuser() != 'root':
        print(termcolor.colored('ERROR', 'red'), ': systemd-boot-populate must be run as root', sep='', file=sys.stderr)
        sys.exit(1)

    conf = {
        'verbose': True,
        'no_delete': False,
        'distro_name': 'Linux',
        'ucode': None,
        'options': []
    }

    conf = load_config(conf)
    loader_conf = load_loader_config()

    args = parse_args()

    conf['verbose'] = conf['verbose'] or args.verbose
    conf['no_delete'] = conf['no_delete'] or args.no_delete
    conf['distro_name'] = args.distro_name if args.distro_name else conf['distro_name']
    conf['ucode'] = args.ucode if args.ucode else conf['ucode']

    if not conf['no_delete']:
        files = [x for x in pathlib.Path(Paths.ENTRY_OUTPUT_DIR).iterdir() if x.is_file()]
        for file in files:
            try:
                file.unlink()
            except OSError as e:
                print(termcolor.colored("ERROR", 'red'), ':', e, sep='', file=sys.stderr)

    gen_loader(loader_conf)
    gen_entries(conf, loader_conf)
