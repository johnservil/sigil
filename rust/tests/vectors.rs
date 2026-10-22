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
    let (mut good, mut variants, mut bad) = (0, 0, 0);
    for line in tsv.lines() {
        let f: Vec<&str> = line.split('\t').collect();
        match f[0] {
            "good" => {
                let data = bytes(f[1]);
                let text = unescape(f[2]);
                assert_eq!(sigilcode::encode(&data), text, "encode {}", f[1]);
                assert_eq!(sigilcode::decode(&text, data.len()).unwrap(), data, "decode {}", f[2]);
                good += 1;
            }
            "variant" => {
                let data = bytes(f[1]);
                assert_eq!(sigilcode::decode(&unescape(f[2]), data.len()).unwrap(), data, "decode variant {}", f[2]);
                variants += 1;
            }
            "bad" => {
                let length: usize = f[1].parse().unwrap();
                let err = sigilcode::decode(&unescape(f[3]), length).unwrap_err();
                assert_eq!(err.kind(), f[2], "{}", f[3]);
                bad += 1;
            }
            _ => panic!("a line of vectors.tsv: {line}"),
        }
    }
    assert_eq!((good, variants, bad), (220, 528, 352));
    assert_eq!(sigilcode::layout(32), (26, 14));
}

#[test]
fn readings() {
    let tsv = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../vectors.tsv")).unwrap();
    let line = tsv.lines().find(|l| l.starts_with("good\t") && l.split('\t').nth(1).unwrap().len() == 64).unwrap();
    let f: Vec<&str> = line.split('\t').collect();
    let chars: Vec<String> = f[2].chars().map(String::from).collect();
    let mut readings: Vec<String> = chars.clone();
    readings[5] = format!("0{}ab", chars[5]);
    let readings: Vec<&str> = readings.iter().map(String::as_str).collect();
    assert_eq!(sigilcode::decode_readings(&readings, 32), vec![bytes(f[1])]);
}
