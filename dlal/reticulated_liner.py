from .skeleton import *

class ReticulatedLiner(Component):
	def __init__(self, **kwargs):
		Component.__init__(self, 'reticulated_liner', **kwargs)

	def edit(self):
		file_name='.reticulated_liner.tmp.mid'
		self.save(file_name)
		editor=os.path.join(root, 'deps', 'dansmidieditor', 'src', 'dansmidieditor.py')
		invoke('{} --command "edit {}"'.format(editor, file_name))
		self.load(file_name)
