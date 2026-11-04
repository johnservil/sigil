//! Sigil: bytes of a known length written as a sigil, one word that a
//! double-click selects whole, of letters with no two alike, and a check that
//! confirms a reading or picks the right one of several. A sigil has one of two
//! forms: hex-prefixed, which begins with the value's first 8 hex digits, and plain,
//! which writes those 32 bits as 3 letters; after them both forms have the
//! same letters.
//!
//! ```
//! let sigil = sigilcode::encode(&[0xab; 32]);
//! assert!(sigil.starts_with("\u{200e}abababab"));
//! assert_eq!(sigil.chars().count(), 1 + 8 + 22);
//! assert_eq!(sigilcode::decode(&sigil, 32).unwrap(), [0xab; 32]);
//! let plain = sigilcode::encode_plain(&[0xab; 32]);
//! assert_eq!(plain.chars().count(), 25);
//! // After the handle, the two forms have the same letters.
//! assert!(sigil.chars().skip(9).eq(plain.chars().skip(3)));
//! assert_eq!(sigilcode::decode(&plain, 32).unwrap(), [0xab; 32]);
//! ```
//!
//! The specification is the repository's README.md ("The encoding"). Letters
//! are base 2,048, 11 bits each; K is a prime larger than 2,048.
//!
//! The handle h is the data's first 32 bits. After it come letters writing
//! t = m * K + r: m the rest of the data with the marker bits 01 between its
//! high and low halves, r < K the number that makes h * 2048^n + t a
//! multiple of K.
//!
//! - Hex-prefixed: U+200E LEFT-TO-RIGHT MARK, h as 8 lowercase hex digits, the letters.
//! - Plain: h and the plain form's version bit (0) as 3 letters, the same letters.
//!
//! Decoding tells the forms apart by the first character, checks the plain
//! form's version bit and the multiple of K, which catches every changed character and every swap of characters
//! one or two apart, and checks that the marker is 01. It skips white space,
//! the mark and four invisible characters copying inserts (skipped.txt), reads
//! the handle's hex in either case, and refuses everything else.
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
/// room is 2^(11n - bits - 2), and n = ceil((bits + 14) / 11) keeps it in that span.
const KS: [u64; 11] = [
    4093, 8179, 16381, 32749, 65519, 131063, 262133, 524269, 1048433, 2096881, 4193633,
];
/// The mark before a handle, which keeps its digits in place beside
/// right-to-left text; decoding skips it.
const MARK: char = '\u{200e}';
/// The handle's hex digits, 32 bits.
const HANDLE: usize = 8;
/// The plain form's letters for the handle: its 32 bits, then the plain
/// form's version bit.
const PREFIX: usize = 3;
/// The plain form's version bit; a later version may write 1.
const PLAIN_VERSION: u64 = 0;

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
        assert_eq!(
            runs.iter().map(|r| r.2).sum::<i64>(),
            N as i64,
            "the alphabet has 2,048 letters"
        );
        let skipped = SKIPPED_TEXT
            .split_whitespace()
            .map(|r| {
                let (a, b) = r.split_once("..").expect("a range of skipped.txt");
                (
                    i64::from_str_radix(a, 16).unwrap(),
                    i64::from_str_radix(b, 16).unwrap(),
                )
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
    let cp = tables().runs.iter().fold(0, |cp, &(start, first, len)| {
        cp | (within(d - first, len) & (start + d - first))
    });
    char::from_u32(cp as u32).expect("a letter of the alphabet")
}

/// `ch`'s digit, and whether it is a letter of the alphabet, looked up in every run.
fn digit_of(ch: char) -> (u64, bool) {
    let c = ch as i64;
    let (digit, hit) = tables()
        .runs
        .iter()
        .fold((0, 0), |(digit, hit), &(start, first, len)| {
            let m = within(c - start, len);
            (digit | (m & (first + c - start)), hit | m)
        });
    (digit as u64, hit != 0)
}

/// `ch`'s value as a hex digit (either case), and whether it is one: no branch.
fn hex_of(ch: char) -> (u64, bool) {
    let c = ch as i64;
    let (d, l, u) = (within(c - 48, 10), within(c - 97, 6), within(c - 65, 6));
    (
        ((d & (c - 48)) | (l & (c - 87)) | (u & (c - 55))) as u64,
        (d | l | u) != 0,
    )
}

/// The lowercase hex digit of `v` (below 16): no branch.
fn hex_digit(v: u64) -> char {
    let v = v as i64;
    char::from_u32((v + 48 + (((9 - v) >> 63) & 39)) as u32).expect("a hex digit")
}

/// x mod k, for k a check prime and x below 2^63: by k's reciprocal and one
/// masked subtraction, so that no division depends on x.
fn mod_k(x: u64, k: u64) -> u64 {
    let mu = ((1u128 << 64) / k as u128) as u64; // public: k alone
    let q = ((x as u128 * mu as u128) >> 64) as u64;
    let r = x - q * k; // below 2k
    let t = r.wrapping_sub(k);
    let keep = 0u64.wrapping_sub(t >> 63); // all ones when r < k
    (r & keep) | (t & !keep)
}

fn is_skipped(ch: char) -> bool {
    let c = ch as i64;
    tables()
        .skipped
        .iter()
        .fold(0, |hit, &(a, b)| hit | within(c - a, b - a + 1))
        != 0
}

/// (n, K, bits) for data of `length` bytes (at least 8): the letters after the
/// handle, which both forms have, carry bits = 8 * length - 32 of the data;
/// n = ceil((bits + 14) / 11) letters, and K, the room 2^(11n - bits - 2)'s
/// check prime.
fn layout(length: usize) -> (usize, u64, usize) {
    assert!(length >= 8, "Sigil encodes at least 8 bytes");
    assert!(
        length <= usize::MAX / 16,
        "a length Sigil can count the bits of"
    );
    let bits = 8 * length - 4 * HANDLE;
    let n = (bits + 14).div_ceil(11);
    (n, KS[11 * n - bits - 2 - 12], bits)
}

/// 2048^n mod k: the handle's place in the check (public: n and k alone).
fn place_of_handle(n: usize, k: u64) -> u64 {
    (0..n).fold(1, |m, _| m * N as u64 % k)
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
        (0..length)
            .rev()
            .map(|i| (self.0[i / 8] >> (8 * (i % 8))) as u8)
            .collect()
    }

    /// Bits `at..at + count` (count at most 64 - at % 64 + 64), as a number.
    fn bits(&self, at: usize, count: usize) -> u64 {
        let (i, off) = (at / 64, at % 64);
        let mut v = self.0.get(i).copied().unwrap_or(0) >> off;
        if off + count > 64 && off > 0 {
            v |= self.0.get(i + 1).copied().unwrap_or(0) << (64 - off);
        }
        if count < 64 {
            v & ((1 << count) - 1)
        } else {
            v
        }
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
            out.0[i] = if 64 * (i + 1) <= s {
                limb
            } else if 64 * i >= s {
                0
            } else {
                limb & ((1 << (s % 64)) - 1)
            };
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

    /// (self + v, the final carry), over every limb.
    fn plus(&self, v: u64) -> (Nat, u64) {
        let mut carry = v;
        let out = self.0.iter().map(|&limb| {
            let (s, c) = limb.overflowing_add(carry);
            carry = c as u64;
            s
        });
        let out = Nat(out.collect());
        (out, carry)
    }

    /// (self - v, the final borrow), over every limb.
    fn minus(&self, v: u64) -> (Nat, u64) {
        let mut borrow = v;
        let out = self.0.iter().map(|&limb| {
            let (s, b) = limb.overflowing_sub(borrow);
            borrow = b as u64;
            s
        });
        let out = Nat(out.collect());
        (out, borrow)
    }

    fn is_zero(&self) -> bool {
        self.0.iter().fold(0, |a, &b| a | b) == 0
    }
}

/// `data`'s sigil in the hex-prefixed form: the mark, the data's first 8 hex
/// digits, and ceil((8 * len - 18) / 11) letters. Its protection against
/// look-alikes holds for data that looks random (a secure hash's output, a
/// key, a random identifier): hash or jumble structured data before encoding
/// it (README.md, "Data with structure"). At least 8 bytes.
pub fn encode(data: &[u8]) -> String {
    encode_form(data, true)
}

/// `data`'s sigil in the plain form: the handle's 32 bits and the version bit
/// as 3 letters, then the hex-prefixed form's letters. At least 8 bytes.
pub fn encode_plain(data: &[u8]) -> String {
    encode_form(data, false)
}

fn encode_form(data: &[u8], hex_prefixed: bool) -> String {
    let length = data.len();
    let (n, k, bits) = layout(length);
    let (width, half) = ((11 * n).max(8 * length), bits / 2);
    let d = Nat::from_be_bytes(data, width);
    let top = d.bits(bits, 64); // the handle: the data's first 32 bits
    let rest = d.low(bits, width);
    let mut marked = rest
        .shr(half, width)
        .shl(half + 2, width)
        .or(&rest.low(half, width));
    marked.or_at(half, 0b01);
    // r < K makes top * 2048^n + t a multiple of K.
    let r = mod_k(k - mod_k(top * place_of_handle(n, k), k), k);
    let (t, carry) = marked.times(k).plus(r);
    debug_assert_eq!(carry, 0, "t fits");
    let mut out = String::with_capacity(4 + HANDLE + 3 * n);
    if hex_prefixed {
        out.push(MARK);
        for i in (0..HANDLE).rev() {
            out.push(hex_digit((top >> (4 * i)) & 15));
        }
    } else {
        let head = top << 1 | PLAIN_VERSION;
        for i in (0..PREFIX).rev() {
            out.push(letter((head >> (11 * i)) & 2047));
        }
    }
    for i in (0..n).rev() {
        out.push(letter(t.bits(11 * i, 11)));
    }
    out
}

/// The `length` bytes that `sigil` encodes, in either form, or why it encodes
/// none. The characters of skipped.txt in it are skipped.
pub fn decode(sigil: &str, length: usize) -> Result<Vec<u8>, DecodeError> {
    let mut chars = sigil
        .chars()
        .enumerate()
        .filter(|&(_, ch)| !is_skipped(ch))
        .peekable();
    // The form, by the first character: hex digits are no letters.
    let hex_prefixed = chars.peek().is_some_and(|&(_, ch)| hex_of(ch).1);
    let (n, k, bits) = layout(length);
    let h = if hex_prefixed { HANDLE } else { PREFIX };
    let (width, half) = ((11 * n).max(8 * length), bits / 2);
    let (mut head, mut t) = (0u64, Nat::zero(width));
    let (mut count, mut refused) = (0, None);
    for (i, ch) in chars {
        let (value, hit) = if count < h && hex_prefixed {
            hex_of(ch)
        } else {
            digit_of(ch)
        };
        if count < h {
            head = if hex_prefixed {
                head << 4 | value
            } else {
                head << 11 | value
            };
        } else if count < h + n {
            t.or_at(11 * (h + n - 1 - count), value);
        }
        if !hit && refused.is_none() {
            refused = Some((i + 1, ch, count < h && hex_prefixed));
        }
        count += 1;
    }
    if count != h + n {
        return Err(DecodeError::Length {
            found: count,
            expected: h + n,
        });
    }
    if let Some((position, character, in_handle)) = refused {
        return Err(DecodeError::Character {
            position,
            character,
            in_handle,
        });
    }
    // Plain, the handle's letters end in the plain form's version bit.
    if !hex_prefixed && head & 1 != PLAIN_VERSION {
        return Err(DecodeError::Marker);
    }
    let top = if hex_prefixed { head } else { head >> 1 };
    // t - r, where r makes top * 2048^n + t a multiple of K: a multiple of K
    // itself exactly when the check passes, and then m * K.
    let r = mod_k(k - mod_k(top * place_of_handle(n, k), k), k);
    let (u, borrow) = t.minus(r);
    let (marked, carry) = u.exact_div(k);
    if carry != 0 || borrow != 0 {
        return Err(DecodeError::Check);
    }
    if !marked.shr(bits + 2, width).is_zero() {
        return Err(DecodeError::Range);
    }
    if marked.bits(half, 2) != 0b01 {
        return Err(DecodeError::Marker);
    }
    let mut d = marked
        .shr(half + 2, width)
        .shl(half, width)
        .or(&marked.low(half, width));
    d.or_at(bits, top);
    Ok(d.to_be_bytes(length))
}

/// The data of `length` bytes that one reading decodes to, for a reader unsure
/// of some letters (an OCR tool, say): `readings` gives each letter's possible
/// readings, the likeliest first. It fails with `Ambiguous` when several
/// readings decode to different data, and with the first reading's error when
/// none decodes. The work is the product of the readings' counts.
pub fn decode_readings(readings: &[&str], length: usize) -> Result<Vec<u8>, DecodeError> {
    let options: Vec<Vec<char>> = readings.iter().map(|r| r.chars().collect()).collect();
    if options.iter().any(|o| o.is_empty()) {
        return decode(
            &options.iter().filter_map(|o| o.first()).collect::<String>(),
            length,
        );
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
    /// The wrong number of characters.
    Length { found: usize, expected: usize },
    /// A character that is not a hex digit of the handle (`in_handle`) or not
    /// a letter of the alphabet, at `position` (counting from 1) in the text.
    Character {
        position: usize,
        character: char,
        in_handle: bool,
    },
    /// The check fails: a character was misread or changed.
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
            DecodeError::Length { found, expected } => write!(
                f,
                "{found} characters; the length asked for takes {expected}"
            ),
            DecodeError::Character {
                position,
                character,
                in_handle,
            } => write!(
                f,
                "character {position} (U+{:04X}) is not {}",
                *character as u32,
                if *in_handle {
                    "a hex digit of the handle"
                } else {
                    "a letter of the alphabet"
                }
            ),
            DecodeError::Check => write!(f, "the check fails: a character was misread or changed"),
            DecodeError::Range => write!(
                f,
                "its value is too large for the length: a letter was misread or changed"
            ),
            DecodeError::Marker => write!(
                f,
                "its marker is not Sigil's: a string of another format, or a changed letter"
            ),
            DecodeError::Ambiguous { count } => {
                write!(f, "{count} readings decode, to different data")
            }
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
        2 * (1..n)
            .filter(|&d1| {
                let r = (k - d1 * m % k) % k;
                (r > 0 && r < n) || r > k - n
            })
            .count() as u64
    }

    /// KS[i] is the check prime of the room 2^(12 + i): the largest prime at most
    /// it, above N, whose worst distance from 1 to 63 letters lets through at
    /// most twice what a random multiplier would.
    #[test]
    fn ks() {
        let n = super::N as u64;
        let passes = |k: u64| {
            let worst = (1..64u32)
                .map(|dist| escapes(k, (0..11 * dist).fold(1, |m, _| 2 * m % k)))
                .max()
                .unwrap();
            worst * k <= 2 * (2 * n - 2) * (2 * n - 2)
        };
        for (i, &k) in super::KS.iter().enumerate() {
            let room = 1u64 << (12 + i);
            assert!(is_prime(k) && k > n && k <= room && passes(k), "{k}");
            assert!(
                (k + 1..=room).all(|c| !is_prime(c) || !passes(c)),
                "{k}: a larger prime passes"
            );
        }
    }

    /// The layout of every length to 4,096 bytes: n the fewest letters whose room holds a prime above N.
    #[test]
    fn layouts() {
        assert_eq!(super::layout(32), (22, 65519, 224));
        for length in 8..=4096 {
            let (n, k, bits) = super::layout(length);
            let e = 11 * n - bits - 2;
            assert!((12..=22).contains(&e) && k <= 1 << e, "{length}");
        }
    }

    /// x mod k by the reciprocal agrees with the remainder, over each check
    /// prime's whole span of products (top below 2^32, times a place below k).
    #[test]
    fn mod_k() {
        for &k in super::KS.iter() {
            let mut x = 1u64;
            for _ in 0..20000 {
                x = x
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                let v = x >> 9; // below 2^55
                assert_eq!(super::mod_k(v, k), v % k, "{v} mod {k}");
            }
            for v in [0, 1, k - 1, k, k + 1, 2 * k - 1, 2 * k, (1 << 55) - 1] {
                assert_eq!(super::mod_k(v, k), v % k, "{v} mod {k}");
            }
        }
    }

    /// Each hex digit reads back, in either case.
    #[test]
    fn hex() {
        for v in 0..16 {
            let c = super::hex_digit(v);
            assert_eq!(c, "0123456789abcdef".chars().nth(v as usize).unwrap());
            assert_eq!(super::hex_of(c), (v, true));
            assert_eq!(super::hex_of(c.to_ascii_uppercase()), (v, true));
        }
        for c in ['g', 'G', '/', ':', '@', '`', '\u{ff10}'] {
            assert!(!super::hex_of(c).1, "{c}");
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
        assert!(
            super::is_skipped(' ')
                && super::is_skipped('\u{2060}')
                && super::is_skipped(super::MARK)
                && !super::is_skipped('\u{202e}')
        );
    }

    /// Encoding and decoding agree at every length from 8 to 300 bytes, in both forms.
    #[test]
    fn round_trips() {
        for length in 8..=300usize {
            let data: Vec<u8> = (0..length).map(|i| (i * 131 + length * 7) as u8).collect();
            assert_eq!(
                super::decode(&super::encode(&data), length).unwrap(),
                data,
                "{length}"
            );
            assert_eq!(
                super::decode(&super::encode_plain(&data), length).unwrap(),
                data,
                "{length}"
            );
        }
    }
}
