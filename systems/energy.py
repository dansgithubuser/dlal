import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('subject')
parser.add_argument('--command')
parser.add_argument('--runs', type=int, default=100)
args = parser.parse_args()

audio = dlal.Audio()
dlal.driver_set(audio)
subject = eval(args.subject)
if args.command: exec('subject.'+args.command)
tape = dlal.Tape()

subject.connect(tape)

energy = 0
for i in range(args.runs):
    audio.run()
    x = tape.read()
    energy += sum(i*i for i in x)
print(energy)
