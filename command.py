class Command:
	"""Command class"""

	__cmd = None
	"""Command name"""
	__attributes = None
	"""Dictionary of attributes"""
	__target = None
	"""Target name"""

	def __init__(self, cmd, attributes, target = None):
		"""Initialize command"""
		self.__cmd = cmd
		self.__attributes = attributes
		self.__target = target

	def cmd(self):
		"""Get command name"""
		return self.__cmd

	def attributes(self):
		"""Get attributes"""
		return self.__attributes

	def target(self):
		"""Get target"""
		return self.__target
