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
//! The specification is the repository's README.md ("The encoding"): the data,
//! multiplied by a prime K larger than N, is written in base N = 1,353, in the
//! fewest characters that leave room for such a K. Decoding checks that the
//! value is a multiple of K, which catches every changed character and every
//! swap of neighbours.
//! The data is written in order, unjumbled; README.md's "Why Sigil writes the
//! data in order" says why. Decoding skips white space and default-ignorable
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
    /// `self / 2^shift`, rounded down, or `u64::MAX` if that does not fit.
    fn shr_saturating(&self, shift: usize) -> u64 {
        let bits = self.bits();
        if bits <= shift {
            return 0;
        }
        if bits - shift > 64 {
            return u64::MAX;
        }
        let (word, bit) = (shift / 32, shift % 32);
        let at = |i: usize| self.0.get(i).map_or(0u128, |&w| w as u128);
        let x = at(word) | at(word + 1) << 32 | at(word + 2) << 64;
        (x >> bit) as u64
    }
    fn bits(&self) -> usize {
        self.0.last().map_or(0, |&top| 32 * (self.0.len() - 1) + 32 - top.leading_zeros() as usize)
    }
}

fn is_prime(k: u32) -> bool {
    k > 1 && (2..).take_while(|p| p * p <= k).all(|p| k % p != 0)
}

/// The smallest prime larger than N: K must exceed N (README.md, "Why the
/// check catches what it does").
const LEAST_K: u32 = 1361;

/// (n, K) for data of `length` bytes (at least 1): the sigil's characters,
/// the fewest whose room R = floor(N^n / 2^(8 * length)) holds a prime larger
/// than N, and K, the largest prime at most R. Computed once for each length
/// up to 64 bytes, and on every call for longer data.
pub fn layout(length: usize) -> (usize, u32) {
    assert!(length >= 1, "Sigil encodes at least one byte");
    static LAYOUTS: [OnceLock<(usize, u32)>; 64] = [const { OnceLock::new() }; 64];
    match LAYOUTS.get(length - 1) {
        Some(cell) => *cell.get_or_init(|| compute_layout(length)),
        None => compute_layout(length),
    }
}

fn compute_layout(length: usize) -> (usize, u32) {
    let mut power = Nat(vec![1]);
    let mut n = 0;
    while power.shr_saturating(8 * length) < LEAST_K as u64 {
        power.mul_add(N, 0);
        n += 1;
    }
    // The first room at least LEAST_K is below LEAST_K * N, under 2^32.
    let mut k = power.shr_saturating(8 * length) as u32;
    while !is_prime(k) {
        k -= 1;
    }
    (n, k)
}

/// `data`'s sigil: `layout(data.len()).0` characters of the alphabet.
/// Its protection against look-alikes holds for data that looks random (a
/// secure hash's output, a key, a random identifier): jumble structured data
/// before encoding it (README.md, "Structured data: jumble it first").
pub fn encode(data: &[u8]) -> String {
    let (n, k) = layout(data.len());
    let mut w = Nat(Vec::new());
    for &b in data {
        w.mul_add(256, b as u32);
    }
    w.mul_add(k, 0);
    let a = alphabet();
    let mut digits = vec![0u32; n];
    for d in digits.iter_mut().rev() {
        *d = w.div_rem(N);
    }
    digits.iter().map(|&d| a.chars[d as usize]).collect()
}

fn is_ignored(a: &Alphabet, ch: char) -> bool {
    let p = ch as u32;
    // The last range starting at or below p, if p is in it.
    let i = a.ignored.partition_point(|&(lo, _)| lo <= p);
    i > 0 && p <= a.ignored[i - 1].1
}

fn digit(a: &Alphabet, ch: char) -> Option<u32> {
    a.digits.binary_search_by_key(&ch, |&(x, _)| x).ok().map(|j| a.digits[j].1)
}

/// The data that `n` digits encode under layout (n, k), or why they encode none.
fn decode_digits(digits: &[u32], length: usize, k: u32) -> Result<Vec<u8>, DecodeError> {
    let mut w = Nat(Vec::with_capacity(digits.len() / 3 + 2));
    for &d in digits {
        w.mul_add(N, d);
    }
    let r = w.div_rem(k);
    if w.bits() > 8 * length {
        return Err(DecodeError::Range);
    }
    if r != 0 {
        return Err(DecodeError::Check);
    }
    let mut data = vec![0u8; length];
    for b in data.iter_mut().rev() {
        *b = w.div_rem(256) as u8;
    }
    Ok(data)
}

/// The `length` bytes that `sigil` encodes, or why it encodes none. White
/// space and default-ignorable characters in it are skipped, and a letter's
/// uppercase reads as the letter.
pub fn decode(sigil: &str, length: usize) -> Result<Vec<u8>, DecodeError> {
    let (n, k) = layout(length);
    let a = alphabet();
    let mut digits = Vec::with_capacity(n);
    for (i, ch) in sigil.chars().enumerate() {
        if is_ignored(a, ch) {
            continue;
        }
        match digit(a, ch) {
            Some(d) => digits.push(d),
            // The length error comes first: count the characters to the end.
            None if digits.len() < n => {
                let rest = sigil.chars().skip(i).filter(|&x| !is_ignored(a, x)).count();
                if digits.len() + rest != n {
                    return Err(DecodeError::Length { found: digits.len() + rest, expected: n });
                }
                return Err(DecodeError::Character { position: i + 1, character: ch });
            }
            None => digits.push(u32::MAX),
        }
    }
    if digits.len() != n {
        return Err(DecodeError::Length { found: digits.len(), expected: n });
    }
    decode_digits(&digits, length, k)
}

/// Every data of `length` bytes that some reading decodes to, for a reader
/// unsure of some characters (an OCR tool, say): `readings` gives each
/// character's possible readings, the likeliest first. One result is the
/// answer; more mean the readings leave the sigil ambiguous.
pub fn decode_readings(readings: &[&str], length: usize) -> Vec<Vec<u8>> {
    let (n, k) = layout(length);
    let a = alphabet();
    // Each position's readings as digits, those outside the alphabet dropped.
    let options: Vec<Vec<u32>> = readings.iter().map(|r| r.chars().filter_map(|ch| digit(a, ch)).collect()).collect();
    let mut found: Vec<Vec<u8>> = Vec::new();
    if options.len() != n || options.iter().any(|o| o.is_empty()) {
        return found;
    }
    let mut choice = vec![0usize; n];
    let mut digits: Vec<u32> = options.iter().map(|o| o[0]).collect();
    loop {
        if let Ok(data) = decode_digits(&digits, length, k) {
            if !found.contains(&data) {
                found.push(data);
            }
        }
        let mut i = n;
        loop {
            if i == 0 {
                return found;
            }
            i -= 1;
            choice[i] += 1;
            if choice[i] < options[i].len() {
                digits[i] = options[i][choice[i]];
                break;
            }
            choice[i] = 0;
            digits[i] = options[i][0];
        }
    }
}

#[cfg(test)]
mod test {
    /// `LEAST_K` is the smallest prime larger than N.
    #[test]
    fn test_least_k() {
        assert!(super::is_prime(super::LEAST_K) && (super::N + 1..super::LEAST_K).all(|k| !super::is_prime(k)));
    }
}
