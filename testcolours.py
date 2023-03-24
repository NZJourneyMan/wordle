#!/usr/bin/env python

from colorama import init, Back, Style, Fore

# initialize colorama
# init()

# print a message with a colored background
print(Back.LIGHTWHITE_EX + Fore.BLACK + "W" + Style.RESET_ALL, end='')
print(Back.LIGHTYELLOW_EX + Fore.BLACK + "O" + Style.RESET_ALL, end='')
print(Style.BRIGHT + Back.LIGHTGREEN_EX + Fore.BLACK + "R" + Style.RESET_ALL, end='')
print()

import rich
rich.print('[bold white on black]W[/]', end='')
rich.print('[bold white on yellow]O[/]', end='')
rich.print('[bold white on green]R[/]', end='')
rich.print('[bold white on green]R[/]', end='')
print(chr(8) + ' ', end='')
print()
rich.print(':warning-emoji: [bold red ] DANGER![/]')
rich.console.Console().print("Danger, Will Robinson!", style="blink bold red underline on white")