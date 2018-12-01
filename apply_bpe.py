#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 Judit Acs <judit@sch.bme.hu>
#
# Distributed under terms of the MIT license.

from argparse import ArgumentParser
from sys import stdin
import re


def parse_args():
    p = ArgumentParser()
    p.add_argument('patterns', type=str)
    p.add_argument('-m', '--mode',
                   choices=['longest', 'shortest'],
                   default='longest')
    p.add_argument('-s', '--separator', default='@@', type=str)
    return p.parse_args()


def load_patterns(fn):
    with open(fn) as f:
        patterns = [line.strip().split("\t")[0] for line in f]
    return patterns


def create_regex(patterns, mode):
    if mode == 'shortest':
        merged_pat = '|'.join(re.escape(p) for p in sorted(patterns, key=len))
    elif mode == 'longest':
        merged_pat = '|'.join(re.escape(p)
                              for p in sorted(patterns, key=len, reverse=True))

    merged_pat += '|.'
    r = re.compile(r'{}'.format(merged_pat), re.UNICODE)
    return r


def apply_bpe(stream, pattern_re, sep):
    whitespace_re = re.compile(r'\s+', re.UNICODE)
    for line in stream:
        out_words = []
        for word in whitespace_re.split(line):
            if not word:
                continue
            parts = pattern_re.findall(word+"</w>")
            if ''.join(parts[-4:]) == "</w>":
                parts = parts[:-4]
            out_words.extend("{}{}".format(p, sep) for p in parts[:-1])
            out_words.append(parts[-1].rstrip("</w>"))
        print(" ".join(out_words))


def main():
    args = parse_args()
    patterns = load_patterns(args.patterns)
    pattern_re = create_regex(patterns, args.mode)
    apply_bpe(stdin, pattern_re, args.separator)

if __name__ == '__main__':
    main()
