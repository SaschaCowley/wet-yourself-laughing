"""Entry-point for Wet Yourself Laughing."""

import cmd
import wysl
import wysl.game
from wysl.setup import setup
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')


class WyslShell(cmd.Cmd):
    """Command line interface to WYSL."""

    intro = f'{wysl.__name__}\nVersion {wysl.__version__}'
    prompt = '> '

    def do_setup(self, arg):
        """Setup the game."""
        setup(config)

    def do_exit(self, args):
        """Exit the game."""
        return True


if __name__ == '__main__':
    # WyslShell().cmdloop()
    # setup(config)
    wysl.game.game_loop(config)
