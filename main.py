from interface import Interface
from core import Core


def main():
	core = Core()
	interface = Interface(core)
	interface.run()


if __name__ == '__main__':
	main()
