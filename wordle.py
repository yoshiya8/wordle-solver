import re
import string
from sys import stdin
from typing import Dict, Set, List, Tuple

from words import WORDS

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
        self._required = False

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
        has_letter = False
        for ix, value in enumerate(self._positions):
            has_letter = has_letter or word[ix] == self.letter
            if value is not None:
                letter_required = True
                if (value and word[ix] != self.letter) or (not value and word[ix] == self.letter):
                    return False
        return not self._required or has_letter

    def set_at_index(self, index: int, value: bool, required: bool) -> None:
        if index < 0 or index >= len(self._positions):
            raise IndexError(
                f"index ({index}) must out of range [0, {len(self._positions) - 1}]")
        self._positions[index] = value
        self._required = required

    def disqualify(self) -> None:
        for ix in range(0, len(self._positions)):
            self._positions[ix] = False
        self._required = False

    @property
    def unknown(self) -> bool:
        return all(v is None for v in self._positions)


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

    @property
    def unknown_letters(self) -> Set[str]:
        return set(l for l, f in self._letter_filters.items() if f.unknown)

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
                self._letter_filters[letter].set_at_index(ix, False, True)
            elif values[ix]:
                self._letter_filters[letter].set_at_index(ix, True, True)
            else:
                self._letter_filters[letter].disqualify()


class Solver:
    def __init__(self, word_length: int = 5):
        self._word_length = word_length
        self._filter = Filter(word_length)
        self._word_list = [w for w in WORDS if len(w) == word_length]
        self._sort_word_list()
        self._frequency = {c: 0 for c in string.ascii_lowercase}

    def _sort_word_list(self):
        multiplier = self.word_length * len(self._word_list)
        letter_values = {c: 0 for c in string.ascii_lowercase}
        for word in self._word_list:
            for letter in word:
                letter_values[letter] += 1
        for letter in self._filter.unknown_letters:
            letter_values[letter] *= multiplier
        self._word_list.sort(
            key=lambda w: -sum(letter_values[l] for l in set(w)))

    def top(self, count: int = None) -> List[str]:
        return self._word_list[0:] if count is None else self._word_list[:count]

    def update(self, word: str, values: List[bool]):
        self._filter.update(word, values)
        self._word_list = [
            w for w in self._word_list if self._filter.accept(w)]
        self._sort_word_list()

    @property
    def word_length(self):
        return self._word_length


class WordleCli:
    def __init__(self, word_length: int = 5):
        self._solver = Solver(word_length)
        self._top_size = 10

    def _handle_line(self, line: str) -> bool:
        if line == '':
            return False
        line = line.lower()
        line = line[:-1] if len(line) > 0 and line[-1] == "\n" else line
        if line in ("exit", "quit", "done", "bye"):
            return False
        tokens = line.split()
        if re.fullmatch(r'\d+', line):
            self._top_size = int(line)
            if self._top_size < 1:
                print("Top value count must be at least one (setting to one)...")
                self._top_size = 1
        elif (
            len(tokens) == 2
            and len(tokens[0]) == self._solver.word_length
            and _is_lower(tokens[0])
            and len(tokens[1]) == self._solver.word_length
            and re.fullmatch('[-ox]+', tokens[1])
        ):
            self._solver.update(tokens[0], [
                True if c == 'o' else False if c == 'x' else None for c in tokens[1]])
        else:
            self._help()
        return True

    def _help(self):
        print(f"""
You will be prompted until you either exit or there is only one word left.
1. You may exit by entering, "exit".
2. You may change the number of suggestions by entering the number you
   want (currently it is {self._top_size}).
3. You may enter a word and its corresponding evaluation. The evaluation
   is another "word" consisting of 3 characters:
      'x': letter is not in the word,
      '-': letter is in the word at another position, or
      'o': letter is in the word in the right position.
   For example, if the right answer is "FAVOR" and your guess is "VAPOR",
   then the evaluation string would be "-OXOO".
""")

    def _prompt(self):
        print(self._solver.top(self._top_size))
        print("> ", end="", flush=True)
        return stdin.readline()

    def main(self):
        self._help()
        line = self._prompt()
        while self._handle_line(line):
            line = self._prompt()

cli = WordleCli()
cli.main()