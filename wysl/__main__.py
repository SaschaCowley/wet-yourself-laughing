import cmd
import wysl
from wysl.setup import setup

config = {}


class WyslShell(cmd.Cmd):
    intro = f'{wysl.__name__}\nVersion {wysl.__version__}'
    prompt = '> '

    def do_setup(self, arg):
        """ Setup the game """
        setup(config)

    def do_exit(self, args):
        """Exit the game. """
        return True


if __name__ == '__main__':
    #WyslShell().cmdloop()
    setup(config)
