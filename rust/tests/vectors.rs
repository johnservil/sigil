//! The Rust implementation against vectors.tsv.

fn bytes(hex: &str) -> Vec<u8> {
    (0..hex.len()).step_by(2).map(|i| u8::from_str_radix(&hex[i..i + 2], 16).unwrap()).collect()
}

/// A text field of vectors.tsv: \\\\, \\t, \\n and \\r stand for a backslash, tab, line feed and carriage return.
fn unescape(t: &str) -> String {
    let mut out = String::new();
    let mut chars = t.chars();
    while let Some(c) = chars.next() {
        if c == '\\' {
            match chars.next() {
                Some('t') => out.push('\t'),
                Some('n') => out.push('\n'),
                Some('r') => out.push('\r'),
                Some('\\') => out.push('\\'),
                other => panic!("an escape in vectors.tsv: {other:?}"),
            }
        } else {
            out.push(c);
        }
    }
    out
}

#[test]
fn vectors() {
    let tsv = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../vectors.tsv")).unwrap();
    let (mut good, mut spaced, mut bad) = (0, 0, 0);
    for line in tsv.lines() {
        let f: Vec<&str> = line.split('\t').collect();
        match f[0] {
            "good" => {
                let data = bytes(f[1]);
                let text = unescape(f[2]);
                assert_eq!(base1160::encode(&data), text, "encode {}", f[1]);
                assert_eq!(base1160::decode(&text, data.len()).unwrap(), data, "decode {}", f[2]);
                good += 1;
            }
            "spaced" => {
                let data = bytes(f[1]);
                assert_eq!(base1160::decode(&unescape(f[2]), data.len()).unwrap(), data, "decode spaced {}", f[2]);
                spaced += 1;
            }
            "bad" => {
                let length: usize = f[1].parse().unwrap();
                let err = base1160::decode(&unescape(f[3]), length).unwrap_err();
                assert_eq!(err.kind(), f[2], "{}", f[3]);
                bad += 1;
            }
            _ => panic!("a line of vectors.tsv: {line}"),
        }
    }
    assert_eq!((good, spaced, bad), (220, 440, 308));
    assert_eq!(base1160::layout(32), (27, 474983));
}
