#!/usr/bin/env python3

import sys, os
from os.path import join as pJoin

sys.path.append(pJoin(os.getcwd(), '../lib'))

import csv

with open('wordle-words/answer-words.manual.txt') as inFD:
    answerWords = inFD.read().splitlines()

with open('wordle-words/allowed-guesses.wordle-code.txt') as inFD:
    allowedGuesses = inFD.read().splitlines()

wordFreq = {}

for word, count in csv.reader(open('google-words/unigram_freq.csv')):
    wordFreq[word] = count

# Process the Answer Words
newAnswerWordsByFreq = {}
with open('wordle-words/answer-words.manual.sorted.by.freq.txt', 'wt') as outFD:
    missingWords = 0
    print(f'Missing words in Answer Words: ', end='')
    for word in answerWords:
        try:
            newAnswerWordsByFreq[word] = wordFreq[word]
        except KeyError:
            newAnswerWordsByFreq[word] = 0
            print(f'{word}, ', end='')
            missingWords += 1

    print(f"\nCount: {missingWords}")
    for word, freq in sorted(newAnswerWordsByFreq.items(), key=lambda x: int(x[1]), reverse=True):
        print(word, file=outFD)

# Process the Allowed Guesses Words
with open('wordle-words/allowed-guesses.wordle-code.sorted.by.freq.txt', 'wt') as outFD:
    missingWords = 0
    print(f'Missing words in Allowed Guesses: ', end='')
    for word in allowedGuesses:
        try:
            newAnswerWordsByFreq[word] = wordFreq[word]
        except KeyError:
            newAnswerWordsByFreq[word] = 0
            print(f'{word}, ', end='')
            missingWords += 1

    print(f"\nCount: {missingWords}")
    for word, freq in sorted(newAnswerWordsByFreq.items(), key=lambda x: int(x[1]), reverse=True):
        print(word, file=outFD)




