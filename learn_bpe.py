#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 Judit Acs <judit@sch.bme.hu>
#
# Distributed under terms of the MIT license.

from argparse import ArgumentParser
from collections import defaultdict
from sys import stdin
import re
import logging


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


def count_input_words(stream):
    freqs = defaultdict(int)
    for line in stream:
        for word in line.rstrip("\n").split(" "):
            if word.strip():
                freqs[word.strip()] += 1
    return freqs


def remove_rare(freqs, threshold):
    zero_keys = list(k for k in freqs if freqs[k] < threshold)
    for key in zero_keys:
        del freqs[key]


def learn_bpe(stream, units, rare_threshold):
    orig_freqs = count_input_words(stream)
    logging.info("Input loaded")
    alphabet = Alphabet(orig_freqs.keys())
    end_char = alphabet.get_end_char()
    word_freqs = {"{}{}".format(word, end_char): fr
                  for word, fr in orig_freqs.items()}
    bigram_freqs, rev_mapping = compute_bigram_freqs(word_freqs)
    remove_rare(bigram_freqs, rare_threshold)
    replacements = []
    log_step = int(units // 10)
    for u in range(units):
        if (u+1) % log_step == 0:
            logging.info("Extracting {}%".format(int((u+1) * 10 // log_step)))
        if not bigram_freqs:
            logging.info("No more frequent bigrams left, exiting early")
            break
        most_frequent = max(bigram_freqs.keys(),
                            key=lambda w: bigram_freqs[w])
        repl_char = alphabet.get_new_char()
        replacements.append((most_frequent, repl_char,
                             bigram_freqs[most_frequent]))
        repl_re = re.compile(r'{}'.format(re.escape(most_frequent)),
                             re.UNICODE)
        repl_words = list(rev_mapping[most_frequent])
        for word in repl_words:
            fr = word_freqs[word]
            new_word = repl_re.sub(repl_char, word)
            for i in range(len(word)-1):
                rev_mapping[word[i:i+2]].discard(word)
                bigram_freqs[word[i:i+2]] -= fr
            for i in range(len(new_word)-1):
                rev_mapping[new_word[i:i+2]].add(new_word)
                bigram_freqs[new_word[i:i+2]] += fr
            word_freqs[new_word] = fr
            del word_freqs[word]
        if u % 100 == 99:
            remove_rare(bigram_freqs, rare_threshold)
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
    p.add_argument('-r', '--rare-threshold', type=int, default=2,
                   help="Discard bigrams appearing less than T times")
    return p.parse_args()


def main():
    args = parse_args()
    patterns, alphabet = learn_bpe(stdin, args.units, args.rare_threshold)
    inv_dict = {tgt: src for src, tgt, _ in patterns}
    for src, tgt, freq in patterns:
        print("{}\t{}".format(decode_bp(tgt, inv_dict, alphabet.end_char),
                              freq))

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()
    #import cProfile
    #cProfile.run('main()', '/tmp/judit/bpe.stats')
