#!/usr/bin/env python

import sys
import os
import re
from rich.console import Console
from typing import NewType, Iterator
import chime  # type: ignore
from argparse import ArgumentParser
from collections import defaultdict
# from itertools import combinations

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


class LetterCount:
    def __init__(self, count: int) -> None:
        self.count: int = count
        self.max: bool = True if count == 0 else False


class SecretWordStatusLetter:
    def __init__(self, letter: str, used: bool) -> None:
        self.letter = letter
        self.used = used


class Wordle:
    def __init__(self) -> None:
        self.excludedLettersRE = ''
        self.incudedLettersRE = ''
        self.letterPositionsRE = ''
        self.letterCount: dict[str, LetterCount] = {}
        self.lineLetterCount: dict[str, LetterCount] = {}
        self.letterCountRE = ''
        self.wordleLines = WordleLines([])
        self.newWordleLine()
        self.loadWords()

    def newWordleLine(self) -> None:
        self.wordleLines.append(WordleLine([]))

    def loadWords(self) -> None:
        self.words = GuessWords([x.strip() for x in open(SOURCE_WORDS)])

    def getColumns(self) -> Iterator[list[KeyStroke]]:
        for i in range(len(self.wordleLines[0])):
            yield [cells[i] for cells in self.wordleLines]

    def addLineLetterCount(self, letter: str, increment: int) -> None:
        if letter in self.lineLetterCount:
            if increment > 0:
                self.lineLetterCount[letter].count += increment
            else:
                self.lineLetterCount[letter].max = True
        else:
            self.lineLetterCount[letter] = LetterCount(increment)

    def resetLineLetterCount(self) -> None:
        self.lineLetterCount = {}

    def mergeLineLetterCount(self) -> None:
        for letter, letterCount in self.lineLetterCount.items():
            if letter in self.letterCount: 
                if letterCount.count > self.letterCount[letter].count:
                    self.letterCount[letter].count = letterCount.count
                if letterCount.max:
                    self.letterCount[letter].max = letterCount.max
            else:
                self.letterCount[letter] = letterCount

    def makeREs(self) -> None:
        self.letterCount = {}
        self.letterCountRE = ''
        self.letterPositionsRE = ''
        # Generate positional re characters for each column
        for slot in self.getColumns():
            correct = ''
            notPostition = '[^'
            for key in slot:
                if key.keyType == RIGHT_PLACE:
                    correct = key.key
                if key.keyType == WRONG_PLACE:
                    notPostition += key.key
            if correct:
                self.letterPositionsRE += correct 
            elif len(notPostition) > 2:
                self.letterPositionsRE += notPostition + ']'
            else:
                self.letterPositionsRE += '.'
        # Go over each line and work out how many of each letter is used
        for row in self.wordleLines:
            for key in row:
                if key.keyType in [RIGHT_PLACE, WRONG_PLACE]:
                    self.addLineLetterCount(key.key, 1)
                else:
                    self.addLineLetterCount(key.key, 0)
            self.mergeLineLetterCount()
            self.resetLineLetterCount()

        for letter, count in self.letterCount.items():
            countStr = f'{count.count}' if count.max else f'{count.count},'
            self.letterCountRE += f'(?=^[^{letter}]*({letter}[^{letter}]*){{{countStr}}}$)'

    def calculateWords(self) -> GuessWords:
        words = GuessWords([])
        positionRE = self.letterPositionsRE
        letterCountRE = self.letterCountRE
        if Global.debug:
            print(f'letterCountRE: {letterCountRE}')
            print(f'positionRE: {positionRE}')
        for word in self.words:
            if re.search(letterCountRE, word) \
                    and re.search(positionRE, word):
                words.append(word)
        return words 
    
    def mkShortList(self, words: list[str]) -> GuessWords:
        lettersToTry: dict[str, int] = defaultdict(int)
        goodLetters: set[str] = set()
        shortListWords: list[str] = []
        # Get "good" letters
        for line in self.wordleLines:
            for key in line:
                if key.keyType in [RIGHT_PLACE, WRONG_PLACE]:
                    goodLetters.add(key.key)
        for word in words:
            for ch in word:
                if ch not in goodLetters:
                    lettersToTry[ch] += 1
        lettersToTryItems = sorted(lettersToTry.items(), key=lambda x: x[1], reverse=True)
        for numToTry in range(5, 0, -1):
            shortListWords = []
            wordsRE = ''
            for letter, _ in lettersToTryItems[:numToTry]:
                wordsRE += f'(?=.*{letter})'
            print('WordsRE:', wordsRE)
            for word in self.words:
                if re.search(wordsRE, word):
                    shortListWords.append(word)
            if shortListWords:
                break
        if not shortListWords:
            raise RuntimeError('Weird, no words found. Programming error?')
        print('Good letters:', goodLetters)
        return GuessWords(shortListWords)
            
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
    
    def printWords(self, antiWords:GuessWords, words: GuessWords) -> None:
        # Anti Words
        print('Up to 10 antiwords:')
        max = 10 if len(antiWords) > 10 else len(antiWords)
        for i in range(max):
            print(antiWords[i])
        # Trial Words
        max = 20 if len(words) > 20 else len(words)
        print(f'\nFound {len(words)} words', end='')
        print(f', showing the first {max}:' if len(words) > max else ':')
        for i in range(max):
            print(words[i])
    
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

    def indexSecretWordStatus(self, letter: str, 
                              secretWordStatus: list[SecretWordStatusLetter]) -> int:
        for i, c in enumerate(secretWordStatus):
            if letter == c.letter:
                if c.used is False:
                    return i
        return -1

    def makeGYB(self, guessWord: str, secretWord: str) -> WordleLine:
        secretWordStatus = [SecretWordStatusLetter(x, False) for x in secretWord]
        resultWord = WordleLine([KeyStroke('', 0) for _ in range(WORDLE_LEN)])
        # Check Green
        for col, c in enumerate(guessWord):
            if c == secretWordStatus[col].letter:
                resultWord[col] = KeyStroke(c, RIGHT_PLACE)
                secretWordStatus[col].used = True

        # Check Yellow and Black
        for col, c in enumerate(guessWord):
            if resultWord[col].key:
                continue
            else:
                i = self.indexSecretWordStatus(c, secretWordStatus)
                if i > -1:  # Check Yellow
                    secretWordStatus[i].used = True
                    resultWord[col] = KeyStroke(c, WRONG_PLACE)
                else:  # Must be black
                    resultWord[col] = KeyStroke(c, ALL_WRONG)
        return resultWord

    def event_loop(self) -> int:
        '''
        Event loop to allow checking each key as it is entered so illegal key combinations
        can be blocked
        '''
        self.console = Console()
        while True:
            key = wordle_getkey(chime.warning)
            if key is None:
                continue
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
                        print('No words found, so giving up️')
                        return 1
                    antiWords = self.mkShortList(words)
                    self.printWords(antiWords, words)
                    self.newWordleLine()
                    print('> ', end='', flush=True)
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

if __name__ == '__main__':
    sys.exit(main())

