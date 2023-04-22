#!/usr/bin/env python

import sys
import os
import re
from subprocess import run
from rich.console import Console
from typing import NewType, Iterator
import chime  # type: ignore
from argparse import ArgumentParser

ROOT = os.path.dirname(__file__)

sys.path.append(os.path.join(ROOT, 'lib'))
from utils import (wordle_getkey, KeyStroke, ScriptError,
    RETURN, BACKSPACE, ALL_WRONG, WRONG_PLACE, RIGHT_PLACE)

WORDLE_LEN = 5
SOURCE_WORDS = os.path.join(ROOT, 'wordle-sub-list-by-freq')

WordleLine = NewType('WordleLine', list[KeyStroke])
WordleLines = NewType('WordleLines', list[WordleLine])
GuessWords = NewType('GuessWords', list[str])


class Global:
    debug: bool


class Wordle:
    def __init__(self) -> None:
        self.excludedLettersRE = ''
        self.incudedLettersRE = ''
        self.letterPositionsRE = ''
        self.wordleLines = WordleLines([])
        self.newWordleLine()
        self.loadWords()

    def newWordleLine(self) -> None:
        try:
            self.wordleLines.append(WordleLine([]))
        except OSError as e:
            raise ScriptError(str(e))

    def loadWords(self) -> None:
        self.words = GuessWords([x.strip() for x in open(SOURCE_WORDS)])

    def getslots(self) -> Iterator[list[KeyStroke]]:
        for i in range(len(self.wordleLines[0])):
            yield [cells[i] for cells in self.wordleLines]

    def makeREs(self) -> None:
        self.excludedLettersRE = '(?!.*['
        self.incudedLettersRE = ''
        self.letterPositionsRE = ''
        for slot in self.getslots():
            correct = ''
            notPostition = '[^'
            included = ''
            excluded = ''
            for key in slot:
                if key.keyType == RIGHT_PLACE:
                    correct = key.key
                if key.keyType == WRONG_PLACE:
                    notPostition += key.key
                    included += f'(?=.*{key.key})'
                if key.keyType == ALL_WRONG:
                    excluded += key.key
            if correct:
                self.letterPositionsRE += correct 
            elif len(notPostition) > 2:
                self.letterPositionsRE += notPostition + ']'
            else:
                self.letterPositionsRE += '.'
            self.excludedLettersRE += excluded
            self.incudedLettersRE += included
        self.excludedLettersRE += '])'

    def calculateWords(self) -> GuessWords:
        words = GuessWords([])
        incExcRE = '^' + self.incudedLettersRE \
            + (self.excludedLettersRE if len(self.excludedLettersRE) > 9 else '')
        positionRE = self.letterPositionsRE
        if Global.debug:
            print(f'incExcRE: {incExcRE}')
            print(f'positionRE: {positionRE}')
        for word in self.words:
            if re.search(incExcRE, word) \
                    and re.search(positionRE, word):
                words.append(word)
        return words 
            
    def printLetter(self, key: KeyStroke) -> bool:
        if key.keyType == BACKSPACE:
            print('\b \b', flush=True, end='')
        elif key.keyType == RETURN:
            print()
        elif key.keyType == ALL_WRONG:
            self.console.print(f'[bold white on black]{key.key.upper()}[/]', end='')
        elif key.keyType == WRONG_PLACE:
            self.console.print(f'[bold white on yellow]{key.key.upper()}[/]', end='')
        elif key.keyType == RIGHT_PLACE:
            self.console.print(f'[bold white on green]{key.key.upper()}[/]', end='')
        else:
            return False
        return True
    
    def printWords(self, words: GuessWords) -> None:
        msg = f'Found {len(words)} words:'
        outStr = f'{msg}\n'
        for word in words:
            outStr += word + '\n'
        if len(words) > 40:
            run(['/usr/bin/less'], input=outStr, encoding='utf8')
            print(msg.rstrip(':'))
        else:
            print(outStr, end='')
    
    def checkIllegal(self, key: KeyStroke) -> bool:
        '''
        Return True if an illegal combination is found:
        o A slot having the same letter in green and another colour. With earlier double letters
          in the work, it is possible for a slot to go from Yellow to Black with the same letter.
        o A slot having two greens, but different letters
        '''
        currentSlot = len(self.wordleLines[-1])  # Len is one more than the index of the last line
        for line in self.wordleLines:
            try:
                # Same letter, One green, the other non Green
                if key.key == line[currentSlot].key\
                        and key.keyType != line[currentSlot].keyType \
                        and RIGHT_PLACE in (key.keyType, line[currentSlot].keyType):
                    return True
                # Both green, but different letters
                if key.key != line[currentSlot].key\
                        and key.keyType == line[currentSlot].keyType \
                        and key.keyType == RIGHT_PLACE:
                    return True
            except IndexError:
                break
        return False

    def allGreen(self) -> bool:
        for slot in self.wordleLines[-1]:
            if slot.keyType != RIGHT_PLACE:
                return False
        return True

    def event_loop(self) -> int:
        '''
        Event loop to allow checking each key as it is entered so illegal key combinations
        can be blocked
        '''
        self.console = Console()
        while True:
            key = wordle_getkey(chime.warning) 
            line = self.wordleLines[-1]
            if key.keyType == BACKSPACE:
                if len(line) > 0:
                    self.printLetter(key)
                    del(line[-1])
                else:
                    chime.warning()
            elif key.keyType == RETURN:
                if len(line) == WORDLE_LEN:
                    self.printLetter(key)
                    if self.allGreen():
                        chime.theme('zelda')  # Yup, cheesy
                        chime.success()
                        print("Success!")
                        break
                    '''Do stuff to create and processes REs, then print likely words'''
                    self.makeREs()
                    words = self.calculateWords()
                    if len(words) == 0:
                        chime.theme('zelda')
                        chime.error()
                        print('No words found, so giving up like a coward ☹️')
                        return 1
                    self.printWords(words)
                    self.newWordleLine()
                    print('> ', end='')
                else:
                    chime.warning()
            elif len(line) == WORDLE_LEN:
                chime.warning()
            elif self.checkIllegal(key):
                chime.warning()
            else:
                self.printLetter(key)
                line.append(key)
        return 0

def main():
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    Global.debug = parser.parse_args().debug
    chime.theme('big-sur')
    wordle = Wordle()
    print(f'''Enter the results from the Wordle screen. Press:
    - ALT+<letter> for a black tile
    - Just <letter> for a yellow tile
    - Shift+<letter> for a green tile
    - Enter once all {WORDLE_LEN} letters have been entered.
> ''', end='')
    try:
        return(wordle.event_loop())
    except KeyboardInterrupt:
        print()
    except ScriptError as e:
        print(str(e), file=sys.stderr)
        return 1
    # print('letterPositionsRE', wordle.letterPositionsRE)
    # print('incudedLettersRE', wordle.incudedLettersRE)
    # print('excludedLettersRE', wordle.excludedLettersRE)


if __name__ == '__main__':
    sys.exit(main())

