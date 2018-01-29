from command import Command

class Interface:

	core = None

	def __init__(self, core):
		self.core = core

	def login(self):
		pass

	@staticmethod
	def parse(s):
		words = s.split()
		indices = [0] + [i for i in range(len(l)) if words[i][:2] == '--'] + [len(words)]
		groups = [l[indices[j]:indices[j + 1]] for j in range(len(indices) - 1)]
		return groups[0][0], {i[0][2:]: ' '.join(i[1:]) for i in groups[1:]}, groups[0][1]

	def run(self):
		while True:
			args = Interface.parse(input('>>> '))
			self.core.execute(Command(args[0], args[1], args[2]))
