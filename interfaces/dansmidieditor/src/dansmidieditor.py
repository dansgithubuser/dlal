#!/usr/bin/env python

import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--command', '-c', action='append', default=[])
args=parser.parse_args()

import media
from config import controls
import time

for i in args.command: controls.command(i)

while not controls.done:
	while True:
		event=media.poll_event()
		if not event: break
		controls.input(event)
	controls.view.draw(media)
	time.sleep(0.01)
