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
		phrases = [i.strip() for i in s.split('--')]
		command, target = phrases[0].split() if len(phrases[0].split()) == 2 else (phrases[0], None)
		return command, target, {i.split()[0]: i[len(i.split()[0]):].strip() for i in phrases[1:]}

	def run(self):
		flag = False
		while not flag:
			flag = self.login()
		while True:
			cmd = input('>>> ')
			if cmd == 'exit':
				exit()
			elif cmd == 'login':
				self.login()
			else:
				command, target, attributes = Interface.parse(cmd)
				print((command, target, attributes))
				print(self.core.execute(Command(command, attributes, target)))
