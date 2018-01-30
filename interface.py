from command import Command
import getpass
import hashlib


class Interface:

	core = None

	def __init__(self, core):
		self.core = core

	def login(self):
		alias = input('Login: ')
		password = input('Password: ')
		#password = hashlib.sha256((getpass.getpass('Password: ') + 'PwdOZ7u0hnpIWLH5R5ox').encode()).hexdigest()
		if self.core.login(alias, password):
			print('Success\n')
			return True
		else:
			print('Fail\n')
			return False

	@staticmethod
	def parse(s):
		words = s.split()
		indices = [0] + [i for i in range(len(words)) if words[i][:2] == '--'] + [len(words)]
		groups = [words[indices[j]:indices[j + 1]] for j in range(len(indices) - 1)]
		return groups[0][0], {i[0][2:]: ' '.join(i[1:]) for i in groups[1:]}, groups[0][1]

	def run(self):
		flag = False
		while not flag:
			flag = self.login()
		while True:
			cmd = input('>>> ')
			if cmd == 'exit':
				exit()
			args = Interface.parse(cmd)
			self.core.execute(Command(args[0], args[1], args[2]))
