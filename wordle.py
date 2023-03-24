#!/usr/bin/env python

import sys
import os
import re
from rich.console import Console
from typing import NewType

ROOT = os.path.dirname(__file__)

sys.path.append(os.path.join(ROOT, 'lib'))
from utils import (wordle_getkey, KeyStroke,
    RETURN, BACKSPACE, ALL_WRONG, WRONG_PLACE, RIGHT_PLACE)

WORDLE_LEN = 5
SOURCE_WORDS = os.path.join(ROOT, 'wordle-sub-list-by-freq')

WordleWord = NewType('WordleWord', list[KeyStroke])
class WordleSlot:
    def __init__(self, 
                 RightLetter: str| None, 
                 WrongPlaceLetter: list[str]) -> None:
        self.RightLetter = RightLetter
        self.WrongPlaceLetter = WrongPlaceLetter
WordleSlots = NewType('WordleSlots', list[WordleSlot])


class Wordle:
    def __init__(self) -> None:
        # 5 Slot structure with correct letter, and incorrect letters list
        self.slots = []
        self.incudedLettersRE: str = ''
        self.excludedLettersRE: str = ''
        self.letterPositionsRE: str = ''
        self.words: list[str] = []
        self.loadWords()
        self.wordleSlots = WordleSlots([])
        for _ in range(WORDLE_LEN):
            self.wordleSlots.append(
                WordleSlot(
                    RightLetter = None,
                    WrongPlaceLetter = []
                )
            )

    def loadWords(self) -> None:
        with open(SOURCE_WORDS) as fd:
            for line in fd:
                self.words.append(line)

    def makeREs(self, word: WordleWord) -> None:
        pass

    def processWord(self, word: WordleWord) -> None:
        for i, c in enumerate(word):
            if c.keyType == ALL_WRONG:
                    self.excludedLettersRE += c.key
            elif c.keyType == WRONG_PLACE:
                    self.incudedLettersRE += c.key
                    self.wordleSlots[i].WrongPlaceLetter.append(c.key) 
            elif c.keyType == RIGHT_PLACE:
                    # self.excludedLettersRE += (c.key)
                    self.wordleSlots[i].RightLetter = c.key


    def get_wordle_word(self) -> WordleWord:
        console = Console()
        wordle_keys: WordleWord = WordleWord([])
        while True:
            k = wordle_getkey()
            if k.keyType == BACKSPACE:
                print('\b \b', flush=True, end='')
                if len(wordle_keys) > 0:
                    del(wordle_keys[-1])
                continue
            elif k.keyType == RETURN and len(wordle_keys) == WORDLE_LEN:
                print()
                break
            elif len(wordle_keys) == WORDLE_LEN:
                continue

            if k.keyType == ALL_WRONG:
                console.print(f'[bold white on black]{k.key}[/]', end='')
            elif k.keyType == WRONG_PLACE:
                console.print(f'[bold white on yellow]{k.key}[/]', end='')
            elif k.keyType == RIGHT_PLACE:
                console.print(f'[bold white on green]{k.key}[/]', end='')
            else:
                continue
            wordle_keys.append(k)
        return wordle_keys

def main():
    wordle = Wordle()
    word = wordle.get_wordle_word()
    wordle.processWord(word)
    # Vars to build the REs
    # wordle_slots = []  # 5 Slot structure with correct letter, and incorrect letters list

    # Structure with a letter key, that has a count of how many letters
    # where known. For example:
    #     - A max of zero if a letter is to be excluded
    #     - A found count if 1 or more letters are found
    #     - A max of n when a max number of letters is known, for example 
    #       a Green A and a Black A would mean max = 1
    # letter_count: dict[str, int] = {}  

    print([x.key for x in word])

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt):
        print()

