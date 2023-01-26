#!/usr/bin/python3.10

import sys, os

def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

letters = {}
words = {}
for c in char_range('a', 'z'):
    letters[c] = 0

with open('/home/mark/wordle-sub-list-by-freq') as fd:
    for word in fd:
        word = word.strip()
        words[word] = 0
        for c in word:
            letters[c] += 1
for word in list(words):
    for c in word:
        words[word] += letters[c]

# for k, v in sorted(letters.items(), key= lambda x:x[1], reverse=True):
#     print(k, v)

with open('/home/mark/wordle-by-letter-freq', mode='w') as fd:
    for k, v in sorted(words.items(), key=lambda x:x[1], reverse=True):
        print(k, v)
        fd.write(k + '\n')