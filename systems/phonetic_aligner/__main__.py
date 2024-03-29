import argparse
import datetime
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('dataset_path')
args = parser.parse_args()

DIR = os.path.dirname(os.path.realpath(__file__))

def blue(text):
    return '\x1b[34m' + text + '\x1b[0m'

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

def invoke(
    *args,
    out=False,
    **kwargs,
):
    if len(args) == 1:
        args = args[0].split()
    print(blue('-'*40))
    print(timestamp())
    print(os.getcwd()+'$', end=' ')
    print(' '.join(args))
    if kwargs: print(kwargs)
    print()
    if 'check' not in kwargs:
        kwargs['check'] = True
    if out:
        kwargs['capture_output'] = True
    result = subprocess.run(args, **kwargs)
    if out:
        result = result.stdout.decode('utf-8').strip()
    return result

if invoke('docker image inspect mfa-english', check=False).returncode:
    invoke('docker pull mmcauliffe/montreal-forced-aligner')
    with open(os.path.join(DIR, 'missing_words.dict')) as f:
        missing_words = f.read()
    invoke(
        'docker', 'run',
        '--name', 'mfa-english',
        'mmcauliffe/montreal-forced-aligner',
        'bash', '-c', ';'.join([
            'mfa model download acoustic english_us_arpa',
            'mfa model download dictionary english_us_arpa',
            f'echo "{missing_words}" > /mfa/pretrained_models/dictionary/missing_words.dict',
            'mfa model add_words /mfa/pretrained_models/dictionary/english_us_arpa.dict /mfa/pretrained_models/dictionary/missing_words.dict',
        ])
    )
    invoke('docker commit mfa-english mfa-english')
    invoke('docker rm mfa-english')
invoke('docker run -dt --name mfa-english mfa-english bash')
invoke(f'docker cp {args.dataset_path} mfa-english:/home/mfauser/dataset')
invoke(f'docker exec -it mfa-english mfa align /home/mfauser/dataset english_us_arpa english_us_arpa /home/mfauser/aligned')
invoke('docker cp mfa-english:/home/mfauser/aligned .')
invoke('docker rm -f mfa-english')
print('Done! Results are in `./aligned`.')
print('Note: you may want to fix up the alignment, specifically stops between words. Praat can be used for this.')
