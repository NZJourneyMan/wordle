#!/usr/bin/env python

import sys
import os
import re
from rich.console import Console
from typing import NewType, Iterator
import chime  # type: ignore
from argparse import ArgumentParser
from collections import defaultdict
from itertools import combinations
import requests

ROOT = os.path.dirname(__file__)

sys.path.append(os.path.join(ROOT, 'lib'))
from utils import (wordle_getkey, KeyStroke, ScriptError,
    RETURN, BACKSPACE, ALL_WRONG, WRONG_PLACE, RIGHT_PLACE)
from words import loadWords

WORDLE_LEN = 5

WordleLine = NewType('WordleLine', list[KeyStroke])
WordleLines = NewType('WordleLines', list[WordleLine])
GuessWords = NewType('GuessWords', list[str])


class Global:
    debug: bool
    includeUsed: bool


class LetterCount:
    def __init__(self, count: int) -> None:
        self.count: int = count
        self.max: bool = True if count == 0 else False


class SecretWordStatusLetter:
    def __init__(self, letter: str, used: bool) -> None:
        self.letter = letter
        self.used = used


class Wordle:
    def __init__(self, answerWords: list[str], allowedGuesses: list[str]) -> None:
        self.excludedLettersRE = ''
        self.incudedLettersRE = ''
        self.letterPositionsRE = ''
        self.letterCount: dict[str, LetterCount] = {}
        self.lineLetterCount: dict[str, LetterCount] = {}
        self.letterCountRE = ''
        self.wordleLines = WordleLines([])
        self.answerWords = answerWords
        self.allowedGuesses = allowedGuesses
        self.newWordleLine()
        if not Global.includeUsed:
            self.removeUsedWords()

    def newWordleLine(self) -> None:
        self.wordleLines.append(WordleLine([]))

    def removeUsedWords(self):
        r = requests.get('https://www.stadafa.com/2021/09/every-worlde-word-so-far-updated-daily.html')
        for line in r.content.splitlines():
            try:
                usedWord = re.search(r'^<p>[0-9]+\. (\w+?) ', line.decode())
                if usedWord:
                    del(self.answerWords[self.answerWords.index(usedWord.group(1).lower())])
            except ValueError:
                continue

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
        for word in self.answerWords:
            if re.search(letterCountRE, word) \
                    and re.search(positionRE, word):
                words.append(word)
        return words

    def mkAntiWordList(self, words: list[str]) -> GuessWords:
        '''
        Things to try:
        o Get all the letters from the possible remaining words, subtract
          all the known letters, then rank the remaining letters by frequency
        o Create a list of unique combinations of 5, 4, 3 & 2 letters from the above letter list
          and attempt to match each combination with the list of possible answers, if none
          then use the list of allowable matches. The former has a chance of being the right
          word, while the later is likely to be an "anti-word". The ideal word has 5 highly ranked
          letters from the letters list above.
        '''

        lettersToTryDict: dict[str, int] = defaultdict(int)
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
                    lettersToTryDict[ch] += 1
        lettersToTry = [x[0] for x in sorted(lettersToTryDict.items(), key=lambda x: x[1], reverse=True)]
        if Global.debug:
            print('Good letters:', goodLetters)
            print('Letters to try', lettersToTry)
        if len(lettersToTry) < 2:
            return GuessWords([])
        for numToTry in range(5, 1, -1):  # Try to find words with five letters first, then 4, ...
            for lettersCombination in combinations(lettersToTry, numToTry):
                wordsRE = ''
                for letter in lettersCombination:
                    wordsRE += f'(?=.*{letter})'
                for word in self.answerWords:  # First try words that could be the answer
                    if re.search(wordsRE, word):
                        if word not in shortListWords:
                            shortListWords.append(word)
                            if Global.debug:
                                print(f'Found "{word}" in AnswerWords with {lettersCombination}')
                if len(shortListWords) > 1:  # Offer more than one word
                    break
                for word in self.allowedGuesses:  # Try words that are unlikely to be the answer
                    if re.search(wordsRE, word):
                        if word not in shortListWords:
                            shortListWords.append(word)
                            if Global.debug:
                                print(f'Found "{word}" in AllowedGuesses with {lettersCombination}')
                if len(shortListWords) > 1:  # Offer more than one word
                    break
            if len(shortListWords) > 1:  # Offer more than one word
                break
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
                    antiWords = self.mkAntiWordList(words)
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
    parser = ArgumentParser(prog='wordle',
                            description='A Wordle solver')
    parser.add_argument('--debug', '-d', action='store_true')
    parser.add_argument('--include-used', '-i',
                        action='store_true',
                        help='Do not remove used words from consideration')
    args = parser.parse_args()
    Global.debug = args.debug
    Global.includeUsed = args.include_used
    answerWords, allowedGuesses = loadWords()
    if Global.debug:
        print(f'Loaded {len(answerWords)} answer words and {len(allowedGuesses)} allowed guess words')
    chime.theme('big-sur')
    wordle = Wordle(answerWords, allowedGuesses)
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

