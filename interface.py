from command import Command
import getpass
import hashlib


class Interface:
	"""Inteface class"""

	core = None
	"""Core object"""
	command_line_mode = False
	"""Command line mode"""

	def __init__(self, core, mode):
		"""Initialize interface"""
		self.core = core
		self.command_line_mode = mode

	def set_command_line_mode(self, mode):
		"""Set command line mode"""
		self.command_line_mode = mode

	def input(self, s):
		return input('' if self.command_line_mode else s)

	def login(self):
		"""Change current user"""
		alias = self.input('Login: ')
		password = self.input('Password: ')
		#password = hashlib.sha256((getpass.getpass('Password: ') + 'PwdOZ7u0hnpIWLH5R5ox').encode()).hexdigest()
		if self.core.login(alias, password):
			print('Success\n')
			return True
		else:
			print('Fail\n')
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
