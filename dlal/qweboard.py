'I wish I could turn off key repeat...'

import tkinter
import weakref

qwe_to_note = {
    'z':  0, 's':  1, 'x':  2, 'd':  3, 'c':  4, 'v':  5,
    'g':  6, 'b':  7, 'h':  8, 'n':  9, 'j': 10, 'm': 11,
    ',': 12, 'l': 13, '.': 14, ';': 15, '/': 16,
    'q': 11,
    'w': 12, '3': 13, 'e': 14, '4': 15, 'r': 16, 't': 17,
    '6': 18, 'y': 19, '7': 20, 'u': 21, '8': 22, 'i': 23,
    'o': 24, '0': 25, 'p': 26, '-': 27, '[': 28,
}

class Qweboard:
    def __init__(self, component, show=True):
        self.component = weakref.ref(component)
        self.last = None
        self.sustaining = set()
        self.octave = 5
        self.mode = 'normal'
        if show: self.show()

    def _note(self, char, on):
        n = qwe_to_note.get(char)
        if n is None: return
        self.component().midi(
            0x90 if on else 0x80,
            12*self.octave+n,
            0x7f,
            detach=True,
        )

    def _stop(self):
        self._note(self.last, False)
        self.last = None
        for i in self.sustaining:
            self._note(i, False)
        self.sustaining.clear()

    def show(self):
        self.root = tkinter.Tk()
        self.root.title('qweboard {}'.format(self.component().name(immediate=True)))
        def regularize(keysym):
            result = keysym.lower()
            result = {
                'comma': ',',
                'less': ',',
                'period': '.',
                'greater': '.',
                'semicolon': ';',
                'colon': ';',
                'slash': '/',
                'question': '/',
            }.get(result, result)
            return result
        def key_press(event):
            # special keys
            if event.keysym == 'Escape':
                self.root.destroy()
                return
            elif event.keysym == 'Prior':  # pgup
                self.octave = min(self.octave+1, 10)
            elif event.keysym == 'Next':  # pgdn
                self.octave = max(self.octave-1, 0)
            elif event.keysym == 'Shift_L':
                self.mode = 'sustain-one'
            elif event.keysym == 'Control_L':
                self.mode = 'sustain-all'
                if self.last: self.sustaining.add(self.last)
            # regular keys
            key = regularize(event.keysym)
            if key not in qwe_to_note: return
            # mode
            if self.mode == 'normal' and self.last == key: return
            if self.mode == 'sustain-one': self._note(self.last, False)
            # key down
            self._note(key, True)
            self.last = key
            if self.mode == 'sustain-all': self.sustaining.add(key)
        def key_release(event):
            #special keys
            if event.keysym in ['Shift_L', 'Control_L']:
                self._stop()
                self.mode = 'normal'
            elif event.keysym == 'space':
                self._stop()
            # regular keys
            key = regularize(event.keysym)
            if key not in qwe_to_note: return
            # mode
            if self.mode == 'sustain-all': return
            if self.mode == 'sustain-one' and self.last == key: return
            # key up
            self._note(key, False)
        self.root.bind_all('<KeyPress>', key_press)
        self.root.bind_all('<KeyRelease>', key_release)
