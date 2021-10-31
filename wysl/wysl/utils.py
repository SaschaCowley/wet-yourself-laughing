"""Utility functions."""

from __future__ import annotations

from configparser import ConfigParser
from ipaddress import AddressValueError, IPv4Address
from typing import Iterable, Optional


def elicit_int(prompt: str = "",
               values: Optional[Iterable[int]] = None,
               err: str = "Invalid input, try again",
               default: Optional[int] = None) -> int:
    """Prompt the user for an integer.

    Args:
        prompt (str, optional): String with which to prompt the user.
            Defaults to "".
        values (Optional[Iterable[int]], optional): Iterable of allowable
            values. If None, any integer is accepted. Defaults to None.
        err (str, optional): Error message to show on invalid input.
            Defaults to "Invalid input, try again".
        default (Optional[int], optional): Default value, which will be
            returned if no input is given. If None, there is no default, and
            the user must enter an integer. Defaults to None.

    Returns:
        int: An integer, as entered by the user. If default is not None and the
            user doesn't enter anything, default is returned. If values is
            given, the return will be one of the items in values (or default,
            if given).
    """
    while True:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                return default
            n = int(i)
            if values is not None and n not in values:
                raise ValueError
            return n
        except ValueError:
            print(err)


def elicit_float(prompt: str = "",
                 err: str = "Invalid input, try again",
                 default: Optional[float] = None) -> float:
    """Prompt the user for a float.

    Args:
        prompt (str, optional): String with which to prompt the user. Should
            not contain trailing space or colon, as these will be added.
            Defaults to "".
        err (str, optional): Message to show on invalid input.
            Defaults to "Invalid input, try again".
        default (Optional[float], optional): Default value to use if the user
            enters nothing. If None, the user must enter a float.
            Defaults to None.

    Returns:
        float: A float, as entered by the user, or, if given, default.
    """
    if default is not None:
        prompt += f'(default {default})'
    prompt += ": "
    while True:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                return default
            n = float(i)
            return n
        except ValueError:
            print(err)


def elicit_ipv4_address(prompt: str = "",
                        err: str = "Invalid IPv4 address, try again",
                        default: Optional[str] = None) -> str:
    """Prompt the user for an IP version 4 address.

    Args:
        prompt (str, optional): String with which to prompt the user.
            Defaults to "".
        err (str, optional): Message to show on invalid input.
            Defaults to "Invalid IPv4 address, try again".
        default (Optional[str], optional): Default value, to be used if the
            user enters nothing. Defaults to None.

    Returns:
        str: An IPv4 address (string of the format "xxx.xxx.xxx.xxx") as
            entered by the user, or, if given, default.
    """
    if default is not None:
        prompt += f'(default {default})'
    prompt += ": "
    while True:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                return default
            addr = IPv4Address(i)
            return str(addr)
        except AddressValueError:
            print(err)


def pprint_config(config: ConfigParser) -> str:
    """Generate a pretty-formatted string from a config object.

    Note: This does not return a string suitable for machine reading.

    Args:
        config (ConfigParser): ConfigParser object to prettyprint.

    Returns:
        str: Prettyprinted string of the ConfigParser object.
    """
    lines: list[str] = []
    sections = config.sections()
    max_sect_len = max(len(section) for section in sections)
    max_opt_len = max(len(option)
                      for section in sections
                      for option in config.options(section))

    for section in sections:
        for i, option in enumerate(config.options(section)):
            lines.append(
                f'{(f"[{section}]" if i == 0 else "").ljust(max_sect_len+2)}  '
                f'{f"{option}:".ljust(max_opt_len)}  '
                f'{config.get(section, option)}')

    return "\n".join(lines)


def box_strings(*strings: str, width: int = 80) -> str:
    """Centre-align and visually box some strings.

    Args:
        *strings (str): Strings to box. Each string will be printed on its own
            line. You need to ensure the strings are short enough to fit in the
            box (width-6) or the results will not be as intended.
        width (int, optional): Width of the box. Defaults to 80.

    Returns:
        str: The strings, centred and surrounded by a border box.
    """
    lines = ["+" + "-"*(width-2) + "+", "|" + " "*(width-2) + "|"]
    lines.extend(f'|  {string.center(width-6)}  |' for string in strings)
    lines.extend(lines[:2][::-1])
    return "\n".join(lines)
