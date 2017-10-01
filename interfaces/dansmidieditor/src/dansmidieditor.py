#!/usr/bin/env python

import media
from config import controls
import time

while not controls.done:
	while True:
		event=media.poll_event()
		if not event: break
		controls.input(event)
	controls.view.draw(media)
	time.sleep(0.01)
