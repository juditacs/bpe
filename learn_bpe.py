#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 Judit Acs <judit@sch.bme.hu>
#
# Distributed under terms of the MIT license.

from argparse import ArgumentParser
from collections import Counter, defaultdict
from sys import stdin
import re


class Alphabet:
    def __init__(self, words):
        self.alphabet = set()
        for word in words:
            self.alphabet |= set(word)
        self.char_codes = set(ord(c) for c in self.alphabet)
        self.new_code = 100

    def get_new_char(self):
        while self.new_code in self.char_codes:
            self.new_code += 1
        self.char_codes.add(self.new_code)
        return chr(self.new_code)

    def get_end_char(self):
        self.end_char = self.get_new_char()
        return self.end_char


def compute_bigram_freqs(word_freqs):
    bigram_freqs = defaultdict(int)
    rev_mapping = defaultdict(set)
    for word, freq in word_freqs.items():
        for i in range(len(word)-1):
            bigram_freqs[word[i:i+2]] += freq
            rev_mapping[word[i:i+2]].add(word)
    return bigram_freqs, rev_mapping


def learn_bpe(stream, units):
    orig_freqs = Counter(stream.read().split())
    alphabet = Alphabet(orig_freqs.keys())
    end_char = alphabet.get_end_char()
    word_freqs = {"{}{}".format(word, end_char): fr
                  for word, fr in orig_freqs.items()}
    bigram_freqs, rev_mapping = compute_bigram_freqs(word_freqs)
    replacements = []
    for u in range(units):
        most_frequent = max(bigram_freqs.keys(),
                            key=lambda w: bigram_freqs[w])
        repl_char = alphabet.get_new_char()
        replacements.append((most_frequent, repl_char,
                             bigram_freqs[most_frequent]))
        repl_re = re.compile(r'{}'.format(re.escape(most_frequent)),
                             re.UNICODE)
        repl_words = list(rev_mapping[most_frequent])
        for word in repl_words:
            new_word = repl_re.sub(repl_char, word)
            fr = word_freqs[word]
            for i in range(len(word)-1):
                rev_mapping[word[i:i+2]].discard(word)
                bigram_freqs[word[i:i+2]] -= fr
            for i in range(len(new_word)-1):
                rev_mapping[new_word[i:i+2]].add(new_word)
                bigram_freqs[new_word[i:i+2]] += fr
            word_freqs[new_word] = fr
            del word_freqs[word]
    return replacements, alphabet


def decode_bp(code, inv_dict, end_char):
    if code not in inv_dict:
        if end_char in code:
            code = code.replace(end_char, '</w>')
        return code
    return decode_bp(inv_dict[code][0], inv_dict, end_char) + \
        decode_bp(inv_dict[code][1], inv_dict, end_char)


def parse_args():
    p = ArgumentParser()
    p.add_argument('-u', '--units', type=int, default=10000)
    return p.parse_args()


def main():
    args = parse_args()
    patterns, alphabet = learn_bpe(stdin, args.units)
    inv_dict = {tgt: src for src, tgt, _ in patterns}
    for src, tgt, freq in patterns:
        print("{}\t{}".format(decode_bp(tgt, inv_dict, alphabet.end_char),
                              freq))

if __name__ == '__main__':
    main()
