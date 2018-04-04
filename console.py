from command import Command


class Interface:
	"""Interface class"""

	core = None
	"""Core object"""
	test_mode = False
	"""Command line mode"""

	def __init__(self, core, mode):
		"""Initialize interface"""
		self.core = core
		self.test_mode = mode

	def set_test_mode(self, mode):
		"""Set command line mode"""
		self.test_mode = mode

	def input(self, s):
		return input('' if self.test_mode else s).strip()

	def login(self):
		"""Change current user"""
		alias = self.input('Login: ').strip()
		password = self.input('Password: ')
		if self.core.login(alias, password):
			print('Success' + ('' if self.test_mode else '\n'))
			return True
		else:
			print('Fail' + ('' if self.test_mode else '\n'))
			return False

	@staticmethod
	def parse(s):
		"""Parse command and arguments"""
		phrases = [i.strip() for i in s.split('--')]
		command, target = phrases[0].split() if len(phrases[0].split()) == 2 else (phrases[0], '')
		return command, target, {i.split()[0]: i[len(i.split()[0]):].strip() for i in phrases[1:]}

	def run(self):
		"""Run interface"""
		flag = False
		while not flag:
			flag = self.login()
		while True:
			cmd = self.input('>>> ')
			if cmd == 'exit':
				exit()
			elif cmd == 'login':
				self.login()
			else:
				command, target, attributes = Interface.parse(cmd)
				print(self.core.execute(Command(command, attributes, target)))
