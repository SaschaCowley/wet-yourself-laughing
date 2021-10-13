"""Entry-point for Wet Yourself Laughing."""

import cmd
import wysl
import wysl.game
from wysl.setup import setup
from configparser import ConfigParser, Error as ConfigParserError
from wysl.config import DEFAULT_CONFIG, validate_config
from wysl.utils import pprint_config

config = ConfigParser()
config.read_dict(DEFAULT_CONFIG)
config.read('config.ini')


class WyslShell(cmd.Cmd):
    """Command line interface to WYSL."""

    intro = f'{wysl.__name__}\nVersion {wysl.__version__}'
    prompt = '> '

    def do_setup(self, arg: str) -> None:
        """Set the game up."""
        setup(config)

    def do_showconfig(self, arg: str) -> None:
        """Show the current configuration."""
        print(pprint_config(config))

    def do_reloadconfig(self, args: str) -> None:
        """Reload configuration from disc."""
        config.read('config.ini')

    def do_saveconfig(self, arg: str) -> None:
        """Save the configuration to disc."""
        with open("config.ini", "w") as file:
            config.write(file)

    def do_exit(self, arg: str) -> bool:
        """Exit the game."""
        return True

    def do_play(self, arg: str) -> None:
        """Play the game."""
        try:
            validate_config(config)
        except ConfigParserError:
            print("The configuration is not valid.")
        else:
            wysl.game.game_loop(config)


if __name__ == '__main__':
    WyslShell().cmdloop()
    # setup(config)
    # wysl.game.game_loop(config)
    # print(pprint_config(config))
