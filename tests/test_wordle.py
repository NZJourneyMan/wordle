
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from wordle import Wordle
from words import allowedGuesses, answerWords

def test_makeGYB():
    w = Wordle(answerWords, allowedGuesses)
    correct = ['a: RIGHT_PLACE', 'b: ALL_WRONG', 'b: RIGHT_PLACE', 
               'c: WRONG_PLACE', 'e: ALL_WRONG']
    ans = [str(x) for x in w.makeGYB('abbce', 'aabac')]
    assert ans == correct