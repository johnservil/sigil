//! Sigil: bytes of a known length written as a sigil, one word of letters that
//! a double-click selects whole, with no two letters alike, and a check that
//! confirms a reading or picks the right one of several.
//!
//! ```
//! let sigil = sigilcode::encode(&[0xff; 32]);
//! assert_eq!(sigil.chars().count(), 25);
//! assert_eq!(sigilcode::decode(&sigil, 32).unwrap(), [0xff; 32]);
//! ```
//!
//! The specification is the repository's README.md ("The encoding"): the data,
//! with the marker bits 01 between its high and low halves, is multiplied by a
//! prime K larger than the alphabet's 2,048 letters and written in base 2,048,
//! 11 bits a letter. Decoding checks that the value is a multiple of K, which
//! catches every changed letter and every swap of neighbours, and that the
//! marker is 01. It skips white space and four invisible characters copying
//! inserts (skipped.txt), and nothing else outside the alphabet.
//! python/sigilcode.py is the reference implementation and vectors.tsv the
//! tests every implementation passes.
//!
//! **Time.** `encode` and `decode` take time linear in the data's length, and
//! run in constant time: what they do depends on the data's length alone, never
//! on its value (no branch, table index or division depends on it). A sigil
//! whose letters are all three bytes of UTF-8 has a length in bytes that the
//! data's length alone decides. `decode` returns early on an error, and so
//! reveals the kind of error; a well-formed sigil takes the same path for every
//! value. `decode_readings` searches readings, and its time depends on them.
#![forbid(unsafe_code)]

use std::fmt;
use std::sync::OnceLock;

const ALPHABET_TEXT: &str = include_str!("../alphabet.txt");
/// The code points decoding skips, as `first..last` hex ranges.
const SKIPPED_TEXT: &str = include_str!("../skipped.txt");
/// The alphabet's size: 2^11.
const N: usize = 2048;
/// K for each room 2^12 to 2^22, by README.md's rule (`check_prime` in
/// python/sigilcode.py, and the test `ks` below): the largest prime at most the
/// room whose worst letter distance lets few two-letter changes through. The
/// room is 2^(11n - 8L - 2), and n = ceil((8L + 14) / 11) keeps it in that span.
const KS: [u64; 11] = [4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633];

struct Tables {
    /// The alphabet as runs of consecutive code points: (first code point, its digit, length).
    runs: Vec<(i64, i64, i64)>,
    skipped: Vec<(i64, i64)>,
}

fn tables() -> &'static Tables {
    static TABLES: OnceLock<Tables> = OnceLock::new();
    TABLES.get_or_init(|| {
        let mut runs: Vec<(i64, i64, i64)> = Vec::new();
        for (digit, ch) in ALPHABET_TEXT.chars().enumerate() {
            let c = ch as i64;
            assert!(ch.len_utf8() == 3, "every letter is three bytes of UTF-8");
            match runs.last_mut() {
                Some((start, _, len)) if *start + *len == c => *len += 1,
                _ => runs.push((c, digit as i64, 1)),
            }
        }
        assert_eq!(runs.iter().map(|r| r.2).sum::<i64>(), N as i64, "the alphabet has 2,048 letters");
        let skipped = SKIPPED_TEXT
            .split_whitespace()
            .map(|r| {
                let (a, b) = r.split_once("..").expect("a range of skipped.txt");
                (i64::from_str_radix(a, 16).unwrap(), i64::from_str_radix(b, 16).unwrap())
            })
            .collect();
        Tables { runs, skipped }
    })
}

/// All ones when 0 <= off < len, else zero: no branch.
fn within(off: i64, len: i64) -> i64 {
    (!off >> 63) & ((off - len) >> 63)
}

/// The letter for `digit` (below 2,048), looked up in every run.
fn letter(digit: u64) -> char {
    let d = digit as i64;
    let cp = tables().runs.iter().fold(0, |cp, &(start, first, len)| cp | (within(d - first, len) & (start + d - first)));
    char::from_u32(cp as u32).expect("a letter of the alphabet")
}

/// `ch`'s digit, and whether it is a letter of the alphabet, looked up in every run.
fn digit_of(ch: char) -> (u64, bool) {
    let c = ch as i64;
    let (digit, hit) = tables().runs.iter().fold((0, 0), |(digit, hit), &(start, first, len)| {
        let m = within(c - start, len);
        (digit | (m & (first + c - start)), hit | m)
    });
    (digit as u64, hit != 0)
}

fn is_skipped(ch: char) -> bool {
    let c = ch as i64;
    tables().skipped.iter().fold(0, |hit, &(a, b)| hit | within(c - a, b - a + 1)) != 0
}

/// (n, K) for data of `length` bytes: n = ceil((8 * length + 14) / 11) letters,
/// and K, the room 2^(11n - 8 * length - 2)'s check prime.
fn layout(length: usize) -> (usize, u64) {
    assert!(length >= 1, "Sigil encodes at least one byte");
    assert!(length <= usize::MAX / 16, "a length Sigil can count the bits of");
    let n = (8 * length + 14).div_ceil(11);
    (n, KS[11 * n - 8 * length - 2 - 12])
}

/// A number of `bits` bits as little-endian 64-bit limbs; every operation
/// below runs over all of its limbs, whatever their values.
#[derive(Clone)]
struct Nat(Vec<u64>);

impl Nat {
    fn zero(bits: usize) -> Nat {
        Nat(vec![0; bits.div_ceil(64)])
    }

    fn from_be_bytes(data: &[u8], bits: usize) -> Nat {
        let mut n = Nat::zero(bits);
        for (i, &b) in data.iter().rev().enumerate() {
            n.0[i / 8] |= (b as u64) << (8 * (i % 8));
        }
        n
    }

    fn to_be_bytes(&self, length: usize) -> Vec<u8> {
        (0..length).rev().map(|i| (self.0[i / 8] >> (8 * (i % 8))) as u8).collect()
    }

    /// Bits `at..at + count` (count at most 64 - at % 64 + 64), as a number.
    fn bits(&self, at: usize, count: usize) -> u64 {
        let (i, off) = (at / 64, at % 64);
        let mut v = self.0.get(i).copied().unwrap_or(0) >> off;
        if off + count > 64 && off > 0 {
            v |= self.0.get(i + 1).copied().unwrap_or(0) << (64 - off);
        }
        if count < 64 { v & ((1 << count) - 1) } else { v }
    }

    /// `v` (below 2^(64 - at % 64), or spanning into the next limb) put into bits from `at`.
    fn or_at(&mut self, at: usize, v: u64) {
        let (i, off) = (at / 64, at % 64);
        self.0[i] |= v << off;
        if off > 0 && i + 1 < self.0.len() {
            self.0[i + 1] |= v >> (64 - off);
        }
    }

    /// self >> s, in `bits` bits.
    fn shr(&self, s: usize, bits: usize) -> Nat {
        let mut out = Nat::zero(bits);
        for i in 0..out.0.len() {
            out.0[i] = self.bits(64 * i + s, 64);
        }
        out
    }

    /// self << s, in `bits` bits.
    fn shl(&self, s: usize, bits: usize) -> Nat {
        let mut out = Nat::zero(bits);
        for (i, &limb) in self.0.iter().enumerate() {
            if 64 * i + s < bits {
                out.or_at(64 * i + s, limb);
            }
        }
        out
    }

    /// The low `s` bits, in `bits` bits.
    fn low(&self, s: usize, bits: usize) -> Nat {
        let mut out = Nat::zero(bits);
        for i in 0..out.0.len() {
            let limb = self.0.get(i).copied().unwrap_or(0);
            out.0[i] = if 64 * (i + 1) <= s { limb } else if 64 * i >= s { 0 } else { limb & ((1 << (s % 64)) - 1) };
        }
        out
    }

    fn or(mut self, other: &Nat) -> Nat {
        for (a, b) in self.0.iter_mut().zip(&other.0) {
            *a |= b;
        }
        self
    }

    /// self * k, in self's limbs (the caller knows the product fits).
    fn times(&self, k: u64) -> Nat {
        let mut carry = 0u128;
        let out = self.0.iter().map(|&limb| {
            let t = limb as u128 * k as u128 + carry;
            carry = t >> 64;
            t as u64
        });
        let out = Nat(out.collect());
        debug_assert_eq!(carry, 0, "the product fits");
        out
    }

    /// (self / k, the final carry) by exact division with k's inverse modulo
    /// 2^64, low limb first: self = quotient * k - carry * 2^(64 limbs), so the
    /// carry is zero exactly when k divides self.
    fn exact_div(&self, k: u64) -> (Nat, u64) {
        let mut inv = k; // Newton's iteration: each step doubles the bits of k * inv = 1 that hold.
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(k.wrapping_mul(inv)));
        }
        debug_assert_eq!(k.wrapping_mul(inv), 1);
        let mut carry = 0u64;
        let q = self.0.iter().map(|&limb| {
            let (x, borrow) = limb.overflowing_sub(carry);
            let q = x.wrapping_mul(inv);
            carry = ((q as u128 * k as u128) >> 64) as u64 + borrow as u64;
            q
        });
        let q = Nat(q.collect());
        (q, carry)
    }

    fn is_zero(&self) -> bool {
        self.0.iter().fold(0, |a, &b| a | b) == 0
    }
}

/// `data`'s sigil, of ceil((8 * len + 14) / 11) letters. Its protection
/// against look-alikes holds for data that looks random (a secure hash's
/// output, a key, a random identifier): hash or jumble structured data before
/// encoding it (README.md, "Data with structure").
pub fn encode(data: &[u8]) -> String {
    let length = data.len();
    let (n, k) = layout(length);
    let (bits, half) = (11 * n, 4 * length);
    let d = Nat::from_be_bytes(data, bits);
    let mut marked = d.shr(half, bits).shl(half + 2, bits).or(&d.low(half, bits));
    marked.or_at(half, 0b01);
    let w = marked.times(k);
    let mut out = String::with_capacity(3 * n);
    for i in (0..n).rev() {
        out.push(letter(w.bits(11 * i, 11)));
    }
    out
}

/// The `length` bytes that `sigil` encodes, or why it encodes none. The
/// characters of skipped.txt in it are skipped.
pub fn decode(sigil: &str, length: usize) -> Result<Vec<u8>, DecodeError> {
    let (n, k) = layout(length);
    let (bits, half) = (11 * n, 4 * length);
    let mut w = Nat::zero(bits);
    let (mut count, mut refused) = (0, None);
    for (i, ch) in sigil.chars().enumerate() {
        if is_skipped(ch) {
            continue;
        }
        let (digit, letter) = digit_of(ch);
        if count < n {
            w.or_at(11 * (n - 1 - count), digit);
        }
        if !letter && refused.is_none() {
            refused = Some((i + 1, ch));
        }
        count += 1;
    }
    if count != n {
        return Err(DecodeError::Length { found: count, expected: n });
    }
    if let Some((position, character)) = refused {
        return Err(DecodeError::Character { position, character });
    }
    let (marked, carry) = w.exact_div(k);
    if carry != 0 {
        return Err(DecodeError::Check);
    }
    if !marked.shr(8 * length + 2, bits).is_zero() {
        return Err(DecodeError::Range);
    }
    if marked.bits(half, 2) != 0b01 {
        return Err(DecodeError::Marker);
    }
    Ok(marked.shr(half + 2, bits).shl(half, bits).or(&marked.low(half, bits)).to_be_bytes(length))
}

/// The data of `length` bytes that one reading decodes to, for a reader unsure
/// of some letters (an OCR tool, say): `readings` gives each letter's possible
/// readings, the likeliest first. It fails with `Ambiguous` when several
/// readings decode to different data, and with the first reading's error when
/// none decodes. The work is the product of the readings' counts.
pub fn decode_readings(readings: &[&str], length: usize) -> Result<Vec<u8>, DecodeError> {
    let options: Vec<Vec<char>> = readings.iter().map(|r| r.chars().collect()).collect();
    if options.iter().any(|o| o.is_empty()) {
        return decode(&options.iter().filter_map(|o| o.first()).collect::<String>(), length);
    }
    let mut choice = vec![0usize; options.len()];
    let (mut found, mut first_error): (Vec<Vec<u8>>, Option<DecodeError>) = (Vec::new(), None);
    loop {
        let text: String = choice.iter().zip(&options).map(|(&c, o)| o[c]).collect();
        match decode(&text, length) {
            Ok(data) if !found.contains(&data) => found.push(data),
            Ok(_) => {}
            Err(e) => first_error = first_error.or(Some(e)),
        }
        let mut i = options.len();
        loop {
            if i == 0 {
                return match found.len() {
                    0 => Err(first_error.expect("a reading was tried")),
                    1 => Ok(found.pop().unwrap()),
                    count => Err(DecodeError::Ambiguous { count }),
                };
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

/// Why a text encodes no data of the length asked for.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DecodeError {
    /// The wrong number of letters.
    Length { found: usize, expected: usize },
    /// A character outside the alphabet, at `position` (counting from 1) in the text.
    Character { position: usize, character: char },
    /// The check fails: a letter was misread or changed.
    Check,
    /// A value too large for the length: a letter was misread or changed.
    Range,
    /// A marker other than Sigil's: a string of another format, or a changed letter.
    Marker,
    /// Several readings decode, to different data.
    Ambiguous { count: usize },
}

impl DecodeError {
    /// The error's kind, as vectors.tsv names it: "length", "character",
    /// "check", "range", "marker" or "ambiguous".
    pub fn kind(&self) -> &'static str {
        match self {
            DecodeError::Length { .. } => "length",
            DecodeError::Character { .. } => "character",
            DecodeError::Check => "check",
            DecodeError::Range => "range",
            DecodeError::Marker => "marker",
            DecodeError::Ambiguous { .. } => "ambiguous",
        }
    }
}

impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            DecodeError::Length { found, expected } => write!(f, "{found} letters; the length asked for takes {expected}"),
            DecodeError::Character { position, character } => {
                write!(f, "character {position} (U+{:04X}) is not a letter of the alphabet", *character as u32)
            }
            DecodeError::Check => write!(f, "the check fails: a letter was misread or changed"),
            DecodeError::Range => write!(f, "its value is too large for the length: a letter was misread or changed"),
            DecodeError::Marker => write!(f, "its marker is not Sigil's: a string of another format, or a changed letter"),
            DecodeError::Ambiguous { count } => write!(f, "{count} readings decode, to different data"),
        }
    }
}

impl std::error::Error for DecodeError {}

#[cfg(test)]
mod test {
    fn is_prime(k: u64) -> bool {
        k > 1 && (2..).take_while(|p| p * p <= k).all(|p| k % p != 0)
    }

    /// The two-letter changes, each by less than N, that a check by k misses when
    /// one letter's place is m times the other's: d1 * m + d2 = 0 (mod k).
    fn escapes(k: u64, m: u64) -> u64 {
        let n = super::N as u64;
        2 * (1..n).filter(|&d1| { let r = (k - d1 * m % k) % k; (r > 0 && r < n) || r > k - n }).count() as u64
    }

    /// KS[i] is the check prime of the room 2^(12 + i): the largest prime at most
    /// it, above N, whose worst distance from 1 to 63 letters lets through at
    /// most twice what a random multiplier would.
    #[test]
    fn ks() {
        let n = super::N as u64;
        let passes = |k: u64| {
            let worst = (1..64u32).map(|dist| escapes(k, (0..11 * dist).fold(1, |m, _| 2 * m % k))).max().unwrap();
            worst * k <= 2 * (2 * n - 2) * (2 * n - 2)
        };
        for (i, &k) in super::KS.iter().enumerate() {
            let room = 1u64 << (12 + i);
            assert!(is_prime(k) && k > n && k <= room && passes(k), "{k}");
            assert!((k + 1..=room).all(|c| !is_prime(c) || !passes(c)), "{k}: a larger prime passes");
        }
    }

    /// The layout of every length to 4,096 bytes: n the fewest letters whose room holds a prime above N.
    #[test]
    fn layouts() {
        assert_eq!(super::layout(32), (25, 131063));
        for length in 1..=4096 {
            let (n, k) = super::layout(length);
            let e = 11 * n - 8 * length - 2;
            assert!((12..=22).contains(&e) && k <= 1 << e, "{length}");
        }
    }

    /// Every digit's letter reads back as the digit, and no letter is skipped.
    #[test]
    fn letters() {
        for d in 0..super::N as u64 {
            let c = super::letter(d);
            assert_eq!(super::digit_of(c), (d, true));
            assert!(!super::is_skipped(c));
        }
        assert!(super::is_skipped(' ') && super::is_skipped('\u{2060}') && !super::is_skipped('\u{202e}'));
    }

    /// Encoding and decoding agree at every length to 300 bytes.
    #[test]
    fn round_trips() {
        for length in 1..=300usize {
            let data: Vec<u8> = (0..length).map(|i| (i * 131 + length * 7) as u8).collect();
            assert_eq!(super::decode(&super::encode(&data), length).unwrap(), data, "{length}");
        }
    }
}
