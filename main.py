from core import Core
import sys


def main(interface_mode, database_mode):
	"""Main function"""
	core = Core(database_mode == 'mongo')
	if interface_mode == 'web':
		import interface
		interface.core = core
		interface.app.run(debug = True)
	else:
		from console import Interface
		interface = Interface(core, interface_mode == 'test')
		interface.run()


if __name__ == '__main__':
	interface_mode = False
	database_mode = False
	n = len(sys.argv)
	if n <= 3:
		if n > 1 and sys.argv[1] in ['web', 'console', 'test']:
			interface_mode = sys.argv[1]
		if n > 2 and sys.argv[2] in ['json', 'mongo']:
			database_mode = sys.argv[2]
	main(interface_mode, database_mode)
