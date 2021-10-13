"""Utility functions."""

from __future__ import annotations

from typing import Iterable, Optional
from ipaddress import IPv4Address, AddressValueError
from configparser import ConfigParser


def elicit_int(prompt: str = "",
               values: Optional[Iterable[int]] = None,
               err: str = "Invalid input, try again",
               default: Optional[int] = None) -> int:
    """Prompt the user for an integer."""
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
    """Prompt the user for a float."""
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
    """Prompt the user for an IP version 4 address."""
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
    """Generate a pretty string of a config object."""
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
    """Box some strings centred."""
    lines = ["+" + "-"*(width-2) + "+", "|" + " "*(width-2) + "|"]
    lines.extend(f'|  {string.center(width-6)}  |' for string in strings)
    lines.extend(lines[:2][::-1])
    return "\n".join(lines)
