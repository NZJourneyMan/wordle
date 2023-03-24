import os
import sys
import tty
import termios
from string import ascii_lowercase, ascii_uppercase

ESC = chr(27)
RETURN = chr(10)
BACKSPACE = chr(127)
ALL_WRONG = -1
WRONG_PLACE = -2
RIGHT_PLACE = -3

class KeyStroke:

    def __init__(self, key: str, keyType: int| str) -> None:
        self.key: str = key
        self.keyType = keyType
        

def getkey() -> str:
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)
    try:
        return os.read(sys.stdin.fileno(), 10).decode()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def wordle_getkey() -> KeyStroke:
    while True:
        k = getkey()
        # print([ord(x) for x in k])
        if len(k) == 1:
            if k == ESC:
                raise KeyboardInterrupt
            elif k == RETURN:
                return KeyStroke(k, k)
            elif k == BACKSPACE:
                return KeyStroke(k, k)
            elif k in ascii_lowercase:
                return KeyStroke(k.upper(), WRONG_PLACE)
            elif k in ascii_uppercase:
                return KeyStroke(k.upper(), RIGHT_PLACE)
                print(f'Upper {k}')
        elif len(k) == 2 and k[0] == ESC and k[1] in ascii_lowercase:
            return KeyStroke(k[1].upper(), ALL_WRONG)
