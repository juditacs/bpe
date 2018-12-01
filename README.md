# bpe

Byte pair encoding

## Usage

Learn BPE units:

    cat input.txt | python learn_bpe.py -u 10000 > bpe_units

Apply BPE:

    cat input.txt | python apply_bpe.py bpe_units > input.bpe

`apply_bpe` has two matchings strategies: longest and shortest. Long finds the
longest possible match, while shortest does the opposite. The separator can
also be redefined with the `-s` switch.

