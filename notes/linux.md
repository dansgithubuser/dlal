If portaudio says it can't find card 0 and panics, there's probably an underlying problem. Confirm with `arecord -l`. If this also fails, there's an underlying problem.

One possibility is that the user is not in the audio group. Check for success with the root user:
`sudo arecord -l`

Add user to the group with:
`sudo adduser dan audio`

And start a new session for that change to take effect.

If it doesn't work, we can put it back to how it was:
`sudo deluser dan audio`
