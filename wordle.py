import re
import string
from sys import stdin
from typing import Dict, Set, List, Tuple

_LOWERS = {c: True for c in string.ascii_lowercase}


def _is_lower(word: str):
    for c in word:
        if not _LOWERS.get(c):
            return False
    return True


class LetterFilter:
    def __init__(self, letter: str, word_length: int):
        if letter is None or len(letter) != 1:
            raise ValueError(f'letter ("{letter}") is not a single character')
        if word_length <= 0:
            raise ValueError(
                f"word_length ({word_length}) is not greater than zero")
        self._letter = letter
        self._positions = [None] * word_length

    @property
    def disqualified(self) -> bool:
        for value in self._positions:
            if value != False:
                return False
        return True

    @property
    def letter(self) -> str:
        return self._letter

    def accept(self, word: str) -> bool:
        if word is None or len(word) != len(self._positions):
            return False
        for ix, filter_letter in enumerate(self._positions):
            if filter_letter is not None and ((filter_letter and word[ix] != self.letter) or (not filter_letter and word[ix] == self.letter)):
                return False
        return True

    def set_at_index(self, index: int, value: bool = True) -> None:
        if index < 0 or index >= len(self._positions):
            raise IndexError(
                f"index ({index}) must out of range [0, {len(self._positions) - 1}]")
        self._positions[index] = value

    def disqualify(self) -> None:
        for ix in range(0, len(self._positions)):
            self._positions[ix] = False


class Filter:
    def __init__(self, word_length: int = 5):
        self._word_length = word_length
        self._letter_filters = {l: LetterFilter(
            l, word_length) for l in string.ascii_lowercase}

    @property
    def length(self):
        return self._word_length

    def accept(self, word: str):
        for letter_filter in self._letter_filters.values():
            if not letter_filter.accept(word):
                return False
        return True

    def update(self, word: str, values: List[bool]):
        """
        values maps to the letters in the word - True means letter is in correct
        location, False means letter is not in word, None means the letter is in
        the word, but not in that position.
        """
        if len(word) != self._word_length:
            raise ValueError(
                f'word ("{word}") is not the right length ({self._word_length})')
        if len(values) != self._word_length:
            raise ValueError(
                f'values length ({len(values)} does not match that of word ("{word}")')
        word = word.lower()
        if not _is_lower(word):
            raise ValueError(
                f'word ("{word}") contains non-alphabetic characters')
        for ix, letter in enumerate(word):
            if values[ix] is None:
                self._letter_filters[letter].set_at_index(ix, False)
            elif values[ix]:
                self._letter_filters[letter].set_at_index(ix, True)
            else:
                self._letter_filters[letter].disqualify()


class Solver:
    def __init__(self, word_length: int = 5):
        words: Set[str] = set()
        frequency: Dict[str, int] = {c: 0 for c in string.ascii_lowercase}
        with open("/usr/share/dict/words", "r") as fh:
            while True:
                line = fh.readline()
                if line == '':
                    break
                word = line[:-
                            1] if len(line) > 0 and line[-1] == "\n" else line
                if len(word) != word_length or not _is_lower(word):
                    continue
                words.add(word)
                for c in word:
                    frequency[c] += 1

        self._word_length = word_length
        self._word_list = sorted(
            words, key=lambda w: -sum(frequency[c] for c in {c for c in w}))
        self._filter = Filter(word_length)
        self._frequency = {c: 0 for c in string.ascii_lowercase}

    def top(self, count: int = None) -> List[str]:
        return self._word_list[0:] if count is None else self._word_list[:count]

    def update(self, word: str, values: List[bool]):
        self._filter.update(word, values)
        for c in word:
            self._frequency[c] += 1
        self._word_list = sorted(
            (w for w in self._word_list if self._filter.accept(w)),
            key=lambda w: -sum(self._frequency[c] for c in w))

    @property
    def word_length(self):
        return self._word_length


solver = Solver()
while True:
    print(solver.top(10))
    print("> ", end="")
    line = stdin.readline()
    if line == '':
        print()
        exit(0)
    line = line[:-1] if len(line) > 0 and line[-1] == "\n" else line
    tokens = line.split()
    if len(tokens) != 2 or len(tokens[0]) != solver.word_length or not _is_lower(tokens[0]) or not re.fullmatch('[-ox]' * solver.word_length, tokens[1]):
        print('Enter word and evaluation (i.e. "shoot x-oo-")')
        continue
    solver.update(tokens[0], [
                  True if c == 'o' else False if c == 'x' else None for c in tokens[1]])
