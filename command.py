class Command:

	__cmd = None
	__attributes = None
	__target = None

	def __init__(self, cmd, attributes, target = None):
		self.__cmd = cmd
		self.__attributes = attributes
		self.__target = target

	def cmd(self):
		return self.__cmd

	def attribute(self):
		return self.__attributes

	def target(self):
		return self.__target
