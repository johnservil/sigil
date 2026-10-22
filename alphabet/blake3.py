"""BLAKE3's hash function (unkeyed), in plain Python, from the BLAKE3
specification (github.com/BLAKE3-team/BLAKE3-specs): for checking the data
files' BLAKE3 hashes beside their SHA-256 ones without any other tool. Slow
(about 1 MB a second) and simple; test.py checks it against BLAKE3's
official test vectors.
"""

IV = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8]
CHUNK_START, CHUNK_END, PARENT, ROOT = 1, 2, 4, 8
BLOCK_LEN, CHUNK_LEN = 64, 1024
MASK = 0xFFFFFFFF


def g(s, a, b, c, d, x, y):
    s[a] = (s[a] + s[b] + x) & MASK
    s[d] = s[d] ^ s[a]
    s[d] = (s[d] >> 16 | s[d] << 16) & MASK
    s[c] = (s[c] + s[d]) & MASK
    s[b] = s[b] ^ s[c]
    s[b] = (s[b] >> 12 | s[b] << 20) & MASK
    s[a] = (s[a] + s[b] + y) & MASK
    s[d] = s[d] ^ s[a]
    s[d] = (s[d] >> 8 | s[d] << 24) & MASK
    s[c] = (s[c] + s[d]) & MASK
    s[b] = s[b] ^ s[c]
    s[b] = (s[b] >> 7 | s[b] << 25) & MASK


def compress(cv, block_words, counter, block_len, flags):
    """The compression function's 16 output words."""
    s = cv[:8] + IV[:4] + [counter & MASK, counter >> 32 & MASK, block_len, flags]
    m = list(block_words)
    for r in range(7):
        g(s, 0, 4, 8, 12, m[0], m[1])
        g(s, 1, 5, 9, 13, m[2], m[3])
        g(s, 2, 6, 10, 14, m[4], m[5])
        g(s, 3, 7, 11, 15, m[6], m[7])
        g(s, 0, 5, 10, 15, m[8], m[9])
        g(s, 1, 6, 11, 12, m[10], m[11])
        g(s, 2, 7, 8, 13, m[12], m[13])
        g(s, 3, 4, 9, 14, m[14], m[15])
        if r < 6:
            m = [m[i] for i in PERMUTATION]
    return [s[i] ^ s[i + 8] for i in range(8)] + [s[i + 8] ^ cv[i] for i in range(8)]


def words(block):
    block = block + bytes(BLOCK_LEN - len(block))
    return [int.from_bytes(block[4 * i:4 * i + 4], "little") for i in range(16)]


class Output:
    """What a chunk's last block or a parent leaves for the root to finish."""
    def __init__(self, cv, block_words, counter, block_len, flags):
        self.cv, self.block_words, self.counter, self.block_len, self.flags = cv, block_words, counter, block_len, flags

    def chaining_value(self):
        return compress(self.cv, self.block_words, self.counter, self.block_len, self.flags)[:8]

    def root_bytes(self, n):
        out = bytearray()
        i = 0
        while len(out) < n:
            w = compress(self.cv, self.block_words, i, self.block_len, self.flags | ROOT)
            out += b"".join(x.to_bytes(4, "little") for x in w)
            i += 1
        return bytes(out[:n])


def chunk_output(chunk, counter):
    """The output of one chunk (at most 1024 bytes), the `counter`th."""
    cv = IV
    blocks = [chunk[i:i + BLOCK_LEN] for i in range(0, len(chunk), BLOCK_LEN)] or [b""]
    for i, block in enumerate(blocks):
        flags = (CHUNK_START if i == 0 else 0) | (CHUNK_END if i == len(blocks) - 1 else 0)
        if i == len(blocks) - 1:
            return Output(cv, words(block), counter, len(block), flags)
        cv = compress(cv, words(block), counter, BLOCK_LEN, flags)[:8]


def parent_output(left_cv, right_cv):
    return Output(IV, left_cv + right_cv, 0, BLOCK_LEN, PARENT)


def hash(data: bytes, n: int = 32) -> bytes:
    """The first `n` bytes of BLAKE3's output for `data`."""
    chunks = [data[i:i + CHUNK_LEN] for i in range(0, len(data), CHUNK_LEN)] or [b""]
    # The tree: a stack of subtree chaining values, merged as chunks arrive
    # (the specification's left-heavy tree).
    stack = []
    for i, chunk in enumerate(chunks[:-1]):
        cv = chunk_output(chunk, i).chaining_value()
        total = i + 1
        while total & 1 == 0:
            cv = parent_output(stack.pop(), cv).chaining_value()
            total >>= 1
        stack.append(cv)
    out = chunk_output(chunks[-1], len(chunks) - 1)
    while stack:
        out = parent_output(stack.pop(), out.chaining_value())
    return out.root_bytes(n)
