# answerWords and allowedGuesses are sorted by frequency as found in the Google Corpus

from os.path import join as pjoin, dirname, abspath


ROOT_DIR = pjoin(abspath(dirname(__file__)), '..')
ANSWER_WORDS_FILE = pjoin(ROOT_DIR, 'wordle-words', 'answer-words.manual.sorted.by.freq.txt')
ALLOWED_GUESSES_FILE = pjoin(ROOT_DIR, 'wordle-words', 'allowed-guesses.wordle-code.sorted.by.freq.txt')

def loadWords():
    with open(ANSWER_WORDS_FILE) as inFD:
        answerWords = inFD.read().splitlines()
    with open(ALLOWED_GUESSES_FILE) as inFD:
        allowedGuesses = inFD.read().splitlines()
    return answerWords, allowedGuesses
