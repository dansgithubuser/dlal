from .skeleton import *
from .qweboard import qwe_to_note

import random


class ReticulatedLiner(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'reticulated_liner', **kwargs)

    def edit(self):
        file_name = '.reticulated_liner.tmp.mid'
        self.save(file_name)
        editor = os.path.join(root, 'deps', 'dansmidieditor', 'src', 'dansmidieditor.py')
        invoke('{} --command "edit {}"'.format(editor, file_name))
        self.load(file_name)

    def random_roots(self, n=4, tonic=36):
        notes = [tonic]+[tonic+random.randint(0, 11) for i in range(n-1)]
        self.add_reticule(0x90, notes[0], 0x40)
        for i in range(len(notes)-1):
            self.add_reticule(0x80, notes[i], 0x40, 0x90, notes[i+1], 0x40)
        self.add_reticule(0x80, notes[-1], 0x40)
