from interface import Interface
from core import Core
import sys


def main(mode):
	"""Main function"""
	core = Core()
	interface = Interface(core, mode)
	interface.run()


if __name__ == '__main__':
	if len(sys.argv) == 2:
		mode = sys.argv[1] == 'command_line_mode_on'
	else:
		mode = False
	main(mode)
