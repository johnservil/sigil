//! Sigil's speed: each operation's run mean (wall time per call, from
//! `clocks::summary::mean` over batches of about 0.1 s) and the clock its
//! thread ran at. Encoding and decoding take the same time for every value of
//! the data, so each length is timed on three: all zeros, all ones, and
//! bytes that look random.
//!
//!     cargo run --release --example bench

fn main() {
    let alphabet: Vec<char> = include_str!("../alphabet.txt").chars().collect();
    for length in [16usize, 32, 64] {
        let values: [(&str, Vec<u8>); 3] = [
            ("zeros", vec![0; length]),
            ("ones", vec![0xff; length]),
            ("random", (0..length as u32).map(|i| (i.wrapping_mul(2654435761) >> 13) as u8).collect()),
        ];
        for (name, data) in &values {
            let sigil = sigilcode::encode(data);
            report(&format!("encode {length} bytes, {name}"), &mut || {
                std::hint::black_box(sigilcode::encode(std::hint::black_box(data)));
            });
            report(&format!("decode {length} bytes, {name}"), &mut || {
                std::hint::black_box(sigilcode::decode(std::hint::black_box(&sigil), length).unwrap());
            });
        }
        // Three readings for one letter, the right one among them.
        let sigil = sigilcode::encode(&values[2].1);
        let letters: Vec<char> = sigil.chars().collect();
        let mut readings: Vec<String> = letters.iter().map(char::to_string).collect();
        readings[3] = format!("{}{}{}", alphabet[7], letters[3], alphabet[1500]);
        let readings: Vec<&str> = readings.iter().map(String::as_str).collect();
        report(&format!("decode_readings {length} bytes, 3 readings of one letter"), &mut || {
            std::hint::black_box(sigilcode::decode_readings(std::hint::black_box(&readings), length).unwrap());
        });
    }
}

fn report(name: &str, f: &mut dyn FnMut()) {
    let batches = clocks::measure(10, 100_000_000, f);
    let mean = clocks::summary::mean(batches.iter().map(|b| (b.wall_ns, b.calls)));
    let counts = batches.iter().filter_map(|b| b.counts).reduce(|a, b| a.plus(b));
    let rate = counts.filter(|c| c.p.time_ns + c.e.time_ns > 0).map_or("no cycle counts".to_owned(), |c| format!("{} MHz", c.mhz()));
    // The mean is fixed point with 64 fractional bits: tenths of a ns, rounded once.
    let tenths = (mean * 10 + (1 << 63)) >> 64;
    println!("{name:60} {:>8}.{} ns per call, {rate}", tenths / 10, tenths % 10);
}
