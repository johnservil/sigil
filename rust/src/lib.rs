//! Sigil: bytes of a known length written as a sigil, one word of letters and
//! digits that a double-click selects whole, with no two characters alike,
//! and a check that confirms a reading or picks the right one of several.
//!
//! ```
//! let sigil = sigilcode::encode(&[0xff; 32]);
//! assert_eq!(sigil.chars().count(), 26);
//! assert_eq!(sigilcode::decode(&sigil, 32).unwrap(), [0xff; 32]);
//! ```
//!
//! The specification is the repository's README.md ("The encoding"): the data
//! is jumbled (four Feistel rounds of BLAKE3), joined by a check, and written
//! in base N = 1,353, one character more than the data needs, the check taking
//! all the room left. Decoding skips white space and default-ignorable
//! characters and reads a letter's uppercase as the letter. python/sigilcode.py
//! is the reference implementation and vectors.tsv the tests every
//! implementation passes.

use std::fmt;
use std::sync::OnceLock;

const ALPHABET_TEXT: &str = include_str!("../alphabet.txt");
/// Each letter's uppercase, in the same order; decoding reads either.
const UPPERCASE_TEXT: &str = include_str!("../uppercase.txt");
/// The code points decoding ignores, as `first..last` hex ranges.
const IGNORED_TEXT: &str = include_str!("../ignored.txt");
/// The alphabet's size.
pub const N: u32 = 1353;

struct Alphabet {
    chars: Vec<char>,
    /// Each letter's and each uppercase's digit, sorted by character.
    digits: Vec<(char, u32)>,
    ignored: Vec<(u32, u32)>,
}

fn alphabet() -> &'static Alphabet {
    static ALPHABET: OnceLock<Alphabet> = OnceLock::new();
    ALPHABET.get_or_init(|| {
        let chars: Vec<char> = ALPHABET_TEXT.chars().collect();
        let upper: Vec<char> = UPPERCASE_TEXT.chars().collect();
        assert_eq!((chars.len(), upper.len()), (N as usize, N as usize), "the alphabet has 1,353 characters");
        let mut digits: Vec<(char, u32)> =
            chars.iter().chain(&upper).enumerate().map(|(i, &c)| (c, i as u32 % N)).collect();
        digits.sort();
        digits.dedup();
        let ignored = IGNORED_TEXT
            .lines()
            .map(|l| {
                let (a, b) = l.split_once("..").expect("a range");
                (u32::from_str_radix(a, 16).unwrap(), u32::from_str_radix(b, 16).unwrap())
            })
            .collect();
        Alphabet { chars, digits, ignored }
    })
}

/// A sigil that encodes no data of the length asked for.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecodeError {
    /// The wrong number of characters.
    Length { found: usize, expected: usize },
    /// A character outside the alphabet, at a 1-based position.
    Character { position: usize, character: char },
    /// A value too large for the length: a character was misread or changed.
    Range,
    /// The check fails: a character was misread or changed.
    Check,
}

impl DecodeError {
    /// "length", "character", "range", or "check", as the specification names them.
    pub fn kind(&self) -> &'static str {
        match self {
            DecodeError::Length { .. } => "length",
            DecodeError::Character { .. } => "character",
            DecodeError::Range => "range",
            DecodeError::Check => "check",
        }
    }
}

impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            DecodeError::Length { found, expected } => write!(f, "{found} characters; the length asked for takes {expected}"),
            DecodeError::Character { position, character } => {
                write!(f, "character {position} (U+{:04X}) is not in the alphabet", *character as u32)
            }
            DecodeError::Range => write!(f, "its value is too large for the length: a character was misread or changed"),
            DecodeError::Check => write!(f, "the check fails: a character was misread or changed"),
        }
    }
}

impl std::error::Error for DecodeError {}

// BLAKE3 (github.com/BLAKE3-team/BLAKE3-specs): its derive-key mode and its
// extended output, which the jumbling and the check use.

const IV: [u32; 8] = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19];
const PERMUTATION: [usize; 16] = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8];
const CHUNK_START: u32 = 1;
const CHUNK_END: u32 = 2;
const PARENT: u32 = 4;
const ROOT: u32 = 8;
const DERIVE_KEY_CONTEXT: u32 = 32;
const DERIVE_KEY_MATERIAL: u32 = 64;

fn g(s: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize, x: u32, y: u32) {
    s[a] = s[a].wrapping_add(s[b]).wrapping_add(x);
    s[d] = (s[d] ^ s[a]).rotate_right(16);
    s[c] = s[c].wrapping_add(s[d]);
    s[b] = (s[b] ^ s[c]).rotate_right(12);
    s[a] = s[a].wrapping_add(s[b]).wrapping_add(y);
    s[d] = (s[d] ^ s[a]).rotate_right(8);
    s[c] = s[c].wrapping_add(s[d]);
    s[b] = (s[b] ^ s[c]).rotate_right(7);
}

fn compress(cv: &[u32; 8], block: &[u32; 16], counter: u64, block_len: u32, flags: u32) -> [u32; 16] {
    let mut s = [
        cv[0], cv[1], cv[2], cv[3], cv[4], cv[5], cv[6], cv[7], IV[0], IV[1], IV[2], IV[3],
        counter as u32, (counter >> 32) as u32, block_len, flags,
    ];
    let mut m = *block;
    for r in 0..7 {
        g(&mut s, 0, 4, 8, 12, m[0], m[1]);
        g(&mut s, 1, 5, 9, 13, m[2], m[3]);
        g(&mut s, 2, 6, 10, 14, m[4], m[5]);
        g(&mut s, 3, 7, 11, 15, m[6], m[7]);
        g(&mut s, 0, 5, 10, 15, m[8], m[9]);
        g(&mut s, 1, 6, 11, 12, m[10], m[11]);
        g(&mut s, 2, 7, 8, 13, m[12], m[13]);
        g(&mut s, 3, 4, 9, 14, m[14], m[15]);
        if r < 6 {
            m = PERMUTATION.map(|i| m[i]);
        }
    }
    let mut out = [0u32; 16];
    for i in 0..8 {
        out[i] = s[i] ^ s[i + 8];
        out[i + 8] = s[i + 8] ^ cv[i];
    }
    out
}

fn words(block: &[u8]) -> [u32; 16] {
    let mut b = [0u8; 64];
    b[..block.len()].copy_from_slice(block);
    std::array::from_fn(|i| u32::from_le_bytes([b[4 * i], b[4 * i + 1], b[4 * i + 2], b[4 * i + 3]]))
}

fn first8(w: [u32; 16]) -> [u32; 8] {
    std::array::from_fn(|i| w[i])
}

/// A node's inputs: chaining value, block, counter, block length, flags.
type Node = ([u32; 8], [u32; 16], u64, u32, u32);

fn blake3(data: &[u8], key: &[u32; 8], flags: u32, length: usize) -> Vec<u8> {
    let chunk = |c: &[u8], counter: u64| -> Node {
        let blocks: Vec<&[u8]> = if c.is_empty() { vec![&[][..]] } else { c.chunks(64).collect() };
        let mut cv = *key;
        for (i, block) in blocks.iter().enumerate() {
            let f = flags | if i == 0 { CHUNK_START } else { 0 } | if i == blocks.len() - 1 { CHUNK_END } else { 0 };
            if i == blocks.len() - 1 {
                return (cv, words(block), counter, block.len() as u32, f);
            }
            cv = first8(compress(&cv, &words(block), counter, 64, f));
        }
        unreachable!("a chunk has a last block")
    };
    let cv_of = |n: &Node| first8(compress(&n.0, &n.1, n.2, n.3, n.4));
    let parent = |l: [u32; 8], r: [u32; 8]| -> Node {
        let mut block = [0u32; 16];
        block[..8].copy_from_slice(&l);
        block[8..].copy_from_slice(&r);
        (*key, block, 0, 64, flags | PARENT)
    };
    let chunks: Vec<&[u8]> = if data.is_empty() { vec![&[][..]] } else { data.chunks(1024).collect() };
    let mut stack: Vec<[u32; 8]> = Vec::new();
    for (i, c) in chunks[..chunks.len() - 1].iter().enumerate() {
        let mut cv = cv_of(&chunk(c, i as u64));
        let mut total = i + 1;
        while total & 1 == 0 {
            cv = cv_of(&parent(stack.pop().unwrap(), cv));
            total >>= 1;
        }
        stack.push(cv);
    }
    let mut out = chunk(chunks[chunks.len() - 1], chunks.len() as u64 - 1);
    while let Some(l) = stack.pop() {
        out = parent(l, cv_of(&out));
    }
    let mut result = Vec::with_capacity(length + 64);
    let mut counter = 0;
    while result.len() < length {
        for w in compress(&out.0, &out.1, counter, out.3, out.4 | ROOT) {
            result.extend_from_slice(&w.to_le_bytes());
        }
        counter += 1;
    }
    result.truncate(length);
    result
}

/// BLAKE3's hash of `data`, `length` bytes of it.
pub fn blake3_hash(data: &[u8], length: usize) -> Vec<u8> {
    blake3(data, &IV, 0, length)
}

/// BLAKE3's derive-key mode: `length` bytes from key material under a context string.
pub fn blake3_derive_key(context: &str, material: &[u8], length: usize) -> Vec<u8> {
    let context_key = blake3(context.as_bytes(), &IV, DERIVE_KEY_CONTEXT, 32);
    let key: [u32; 8] = std::array::from_fn(|i| u32::from_le_bytes(context_key[4 * i..4 * i + 4].try_into().unwrap()));
    blake3(material, &key, DERIVE_KEY_MATERIAL, length)
}

// The jumbling: four Feistel rounds over the data's two halves.

fn xor_round(target: &mut [u8], i: usize, from: &[u8]) {
    let r = blake3_derive_key(&format!("Sigil 2026-10-22 jumble round {i}"), from, target.len());
    for (t, x) in target.iter_mut().zip(r) {
        *t ^= x;
    }
}

/// The jumbled data: every byte depends on every byte of `data`.
pub fn jumble(data: &[u8]) -> Vec<u8> {
    let mut out = data.to_vec();
    let (a, b) = out.split_at_mut(data.len() / 2);
    xor_round(b, 0, a);
    xor_round(a, 1, b);
    xor_round(b, 2, a);
    xor_round(a, 3, b);
    out
}

/// The data that `jumbled` is the jumbling of.
pub fn unjumble(jumbled: &[u8]) -> Vec<u8> {
    let mut out = jumbled.to_vec();
    let (a, b) = out.split_at_mut(jumbled.len() / 2);
    xor_round(a, 3, b);
    xor_round(b, 2, a);
    xor_round(a, 1, b);
    xor_round(b, 0, a);
    out
}

/// A natural number: 32-bit words, least significant first, no high zero word.
struct Nat(Vec<u32>);

impl Nat {
    fn mul_add(&mut self, m: u32, a: u32) {
        let mut carry = a as u64;
        for w in self.0.iter_mut() {
            let x = *w as u64 * m as u64 + carry;
            *w = x as u32;
            carry = x >> 32;
        }
        if carry != 0 {
            self.0.push(carry as u32);
        }
        while self.0.last() == Some(&0) {
            self.0.pop();
        }
    }
    /// Divides in place; returns the remainder.
    fn div_rem(&mut self, d: u32) -> u32 {
        let mut r = 0u64;
        for w in self.0.iter_mut().rev() {
            let x = (r << 32) | *w as u64;
            *w = (x / d as u64) as u32;
            r = x % d as u64;
        }
        while self.0.last() == Some(&0) {
            self.0.pop();
        }
        r as u32
    }
    fn bits(&self) -> usize {
        self.0.last().map_or(0, |&top| 32 * (self.0.len() - 1) + 32 - top.leading_zeros() as usize)
    }
}

/// (n, c) for data of `length` bytes (at least 1): the sigil's characters,
/// one more than the fewest that hold 8 * length bits, and the check's bits,
/// all the room left.
pub fn layout(length: usize) -> (usize, usize) {
    assert!(length >= 1, "Sigil encodes at least one byte");
    let mut power = Nat(vec![1]);
    let mut m = 0;
    while power.bits() <= 8 * length {
        power.mul_add(N, 0);
        m += 1;
    }
    // N^m >= 2^(8 * length) once N^m has more than 8 * length bits, since N is
    // not a power of two.
    power.mul_add(N, 0);
    let c = power.bits() - 1 - 8 * length;
    assert!(c < 32, "the check fits in a word");
    (m + 1, c)
}

/// The check: the first c bits of BLAKE3, in derive-key mode, over the jumbled data.
fn check(jumbled: &[u8], c: usize) -> u32 {
    let h = blake3_derive_key("Sigil 2026-10-22 check", jumbled, 8);
    (u64::from_be_bytes(h.try_into().unwrap()) >> (64 - c)) as u32
}

/// `data`'s sigil: `layout(data.len()).0` characters of the alphabet.
pub fn encode(data: &[u8]) -> String {
    let (n, c) = layout(data.len());
    let jumbled = jumble(data);
    let mut w = Nat(Vec::new());
    for &b in &jumbled {
        w.mul_add(256, b as u32);
    }
    w.mul_add(1 << c, check(&jumbled, c));
    let a = alphabet();
    let mut digits = vec![0u32; n];
    for d in digits.iter_mut().rev() {
        *d = w.div_rem(N);
    }
    digits.iter().map(|&d| a.chars[d as usize]).collect()
}

/// The `length` bytes that `sigil` encodes, or why it encodes none. White
/// space and default-ignorable characters in it are skipped, and a letter's
/// uppercase reads as the letter.
pub fn decode(sigil: &str, length: usize) -> Result<Vec<u8>, DecodeError> {
    let (n, c) = layout(length);
    let a = alphabet();
    let chars: Vec<(usize, char)> = sigil
        .chars()
        .enumerate()
        .filter(|&(_, ch)| !a.ignored.iter().any(|&(lo, hi)| lo <= ch as u32 && ch as u32 <= hi))
        .collect();
    if chars.len() != n {
        return Err(DecodeError::Length { found: chars.len(), expected: n });
    }
    let mut w = Nat(Vec::new());
    for &(i, ch) in &chars {
        let d = a
            .digits
            .binary_search_by_key(&ch, |&(x, _)| x)
            .map(|j| a.digits[j].1)
            .map_err(|_| DecodeError::Character { position: i + 1, character: ch })?;
        w.mul_add(N, d);
    }
    if w.bits() > 8 * length + c {
        return Err(DecodeError::Range);
    }
    let t = w.div_rem(1 << c);
    let mut jumbled = vec![0u8; length];
    for b in jumbled.iter_mut().rev() {
        *b = w.div_rem(256) as u8;
    }
    if t != check(&jumbled, c) {
        return Err(DecodeError::Check);
    }
    Ok(unjumble(&jumbled))
}

/// Every data of `length` bytes that some reading decodes to, for a reader
/// unsure of some characters (an OCR tool, say): `readings` gives each
/// character's possible readings, the likeliest first. One result is the
/// answer; more mean the readings leave the sigil ambiguous.
pub fn decode_readings(readings: &[&str], length: usize) -> Vec<Vec<u8>> {
    let options: Vec<Vec<char>> = readings.iter().map(|r| r.chars().collect()).collect();
    let mut found: Vec<Vec<u8>> = Vec::new();
    let mut choice = vec![0usize; options.len()];
    loop {
        let sigil: String = options.iter().zip(&choice).map(|(o, &k)| o[k]).collect();
        if let Ok(data) = decode(&sigil, length) {
            if !found.contains(&data) {
                found.push(data);
            }
        }
        // The next choice, as a counter over the positions' options.
        let mut i = options.len();
        loop {
            if i == 0 {
                return found;
            }
            i -= 1;
            choice[i] += 1;
            if choice[i] < options[i].len() {
                break;
            }
            choice[i] = 0;
        }
    }
}
