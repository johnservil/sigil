//! base345: bytes of a known length as a codeword: one word of digits and
//! lowercase Latin, Greek and Cyrillic letters, which a double-click selects
//! whole and either case decodes; every one-character error and every swap of
//! neighbours is caught.
//!
//! ```
//! let codeword = base345::encode(&[0xff; 32]);
//! assert_eq!(codeword.chars().count(), 32);
//! assert_eq!(base345::decode(&codeword, 32).unwrap(), [0xff; 32]);
//! ```
//!
//! Decoding skips white space and default-ignorable characters, which copying
//! and line breaking insert. The specification is the repository's README.md
//! ("The encoding"): L bytes are a number v below 2^(8L); the codeword is v * K in base N = 345,
//! exactly n digits, most significant first, digit d the alphabet's d-th
//! character (alphabet.txt, ascending), where n is the fewest digits that leave
//! room for a prime K larger than N and K is the largest prime at most
//! N^n / 2^(8L).
//! python/base345.py is the reference implementation and vectors.tsv the
//! tests every implementation passes.

use std::fmt;
use std::sync::OnceLock;

const ALPHABET_TEXT: &str = include_str!("../alphabet.txt");
/// Each letter's uppercase, in the same order; decoding reads either.
const UPPERCASE_TEXT: &str = include_str!("../uppercase.txt");
/// The code points decoding ignores, as `first..last` hex ranges: white
/// space and the default-ignorable characters, which copying and line
/// breaking insert.
const IGNORED_TEXT: &str = include_str!("../ignored.txt");
/// The alphabet's size.
pub const N: u32 = 345;

/// The alphabet's characters, the digit of each letter and of its
/// uppercase (sorted by code point), and the ignored ranges, built once.
struct Alphabet {
    chars: Vec<char>,
    digits: Vec<(char, u32)>,
    ignored: Vec<(u32, u32)>,
}

fn alphabet() -> &'static Alphabet {
    static ALPHABET: OnceLock<Alphabet> = OnceLock::new();
    ALPHABET.get_or_init(|| {
        let chars: Vec<char> = ALPHABET_TEXT.chars().collect();
        let upper: Vec<char> = UPPERCASE_TEXT.chars().collect();
        assert_eq!((chars.len(), upper.len()), (N as usize, N as usize), "the alphabet has 345 characters");
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

/// A codeword that encodes no data of the length asked for.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecodeError {
    /// The wrong number of characters.
    Length { found: usize, expected: usize },
    /// A character outside the alphabet, at a 1-based position.
    Character { position: usize, character: char },
    /// The check fails: the text was changed.
    Corrupt,
}

impl DecodeError {
    /// "length", "character", or "corrupt", as the specification names them.
    pub fn kind(&self) -> &'static str {
        match self {
            DecodeError::Length { .. } => "length",
            DecodeError::Character { .. } => "character",
            DecodeError::Corrupt => "corrupt",
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
            DecodeError::Corrupt => write!(f, "the check fails: the codeword was changed"),
        }
    }
}

impl std::error::Error for DecodeError {}

/// A natural number: 32-bit words, least significant first, no high zero word.
#[derive(Clone)]
struct Nat(Vec<u32>);

impl Nat {
    fn small(x: u32) -> Nat {
        let mut n = Nat(vec![x]);
        n.trim();
        n
    }
    fn trim(&mut self) {
        while self.0.last() == Some(&0) {
            self.0.pop();
        }
    }
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
        self.trim();
    }
    /// Divides in place; returns the remainder.
    fn div_rem(&mut self, d: u32) -> u32 {
        let mut r = 0u64;
        for w in self.0.iter_mut().rev() {
            let x = (r << 32) | *w as u64;
            *w = (x / d as u64) as u32;
            r = x % d as u64;
        }
        self.trim();
        r as u32
    }
    fn bits(&self) -> u64 {
        match self.0.last() {
            None => 0,
            Some(&top) => 32 * (self.0.len() as u64 - 1) + (32 - top.leading_zeros() as u64),
        }
    }
    /// The number shifted right by `s` bits, if it fits in 64 bits; else none.
    fn shr_u64(&self, s: u64) -> Option<u64> {
        let total = self.bits();
        if total <= s {
            return Some(0);
        }
        if total - s > 64 {
            return None;
        }
        let mut out = 0u64;
        for bit in (s..total).rev() {
            let word = self.0[(bit / 32) as usize];
            out = (out << 1) | ((word >> (bit % 32)) & 1) as u64;
        }
        Some(out)
    }
}

fn is_prime(k: u64) -> bool {
    if k < 2 {
        return false;
    }
    let mut d = 2;
    while d * d <= k {
        if k % d == 0 {
            return false;
        }
        d += 1;
    }
    true
}

/// (n, K) for data of `length` bytes (at least 1): the text's length, and
/// the prime the value is multiplied by.
pub fn layout(length: usize) -> (usize, u32) {
    assert!(length >= 1, "base345 encodes at least one byte");
    let bits = 8 * length as u64;
    let mut power = Nat::small(1);
    let mut n = 0;
    let k = loop {
        power.mul_add(N, 0);
        n += 1;
        // N^n >> 8L, while it is at most N (it fits in 64 bits until then).
        match power.shr_u64(bits) {
            Some(x) if x <= N as u64 => continue,
            Some(x) => break x,
            None => unreachable!("N^n >> 8L passes N before it passes 64 bits"),
        }
    };
    let mut k = k;
    while !is_prime(k) {
        k -= 1;
    }
    (n, u32::try_from(k).expect("K is below N^2 + N"))
}

/// `data`'s codeword: `layout(data.len()).0` characters of the alphabet.
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
    assert!(w.0.is_empty(), "v * K is below N^n");
    digits.iter().map(|&d| a.chars[d as usize]).collect()
}

/// The `length` bytes that `codeword` encodes, or why it encodes none.
/// White space and default-ignorable characters in it are skipped.
pub fn decode(codeword: &str, length: usize) -> Result<Vec<u8>, DecodeError> {
    let (n, k) = layout(length);
    let a = alphabet();
    let chars: Vec<(usize, char)> = codeword
        .chars()
        .enumerate()
        .filter(|&(_, c)| !a.ignored.iter().any(|&(lo, hi)| lo <= c as u32 && c as u32 <= hi))
        .collect();
    if chars.len() != n {
        return Err(DecodeError::Length { found: chars.len(), expected: n });
    }
    let mut w = Nat(Vec::new());
    for &(i, c) in &chars {
        let d = a
            .digits
            .binary_search_by_key(&c, |&(x, _)| x)
            .map(|j| a.digits[j].1)
            .map_err(|_| DecodeError::Character { position: i + 1, character: c })?;
        w.mul_add(N, d);
    }
    if w.div_rem(k) != 0 || w.bits() > 8 * length as u64 {
        return Err(DecodeError::Corrupt);
    }
    let mut out = vec![0u8; length];
    for b in out.iter_mut().rev() {
        *b = w.div_rem(256) as u8;
    }
    Ok(out)
}
