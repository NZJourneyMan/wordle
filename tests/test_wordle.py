
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from wordle import Wordle

def test_makeGYB():
    w = Wordle()
    correct = ['a: RIGHT_PLACE', 'b: ALL_WRONG', 'b: RIGHT_PLACE', 
               'c: WRONG_PLACE', 'e: ALL_WRONG']
    ans = [str(x) for x in w.makeGYB('abbce', 'aabac')]
    assert ans == correct