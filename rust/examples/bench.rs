//! Sigil's speed: each operation's run mean (wall time per call, from
//! `clocks::summary::mean` over batches of about 0.1 s) and the clock its
//! thread ran at, at three lengths.
//!
//!     cargo run --release --example bench

fn main() {
    let lengths = [16usize, 32, 64];
    for &length in &lengths {
        let data: Vec<u8> = (0..length as u8).map(|i| i.wrapping_mul(97).wrapping_add(13)).collect();
        let sigil = sigilcode::encode(&data);
        // Three readings for one character, the right one among them.
        let chars: Vec<String> = sigil.chars().map(String::from).collect();
        let mut readings = chars.clone();
        readings[3] = format!("0{}ab", chars[3]);
        let readings: Vec<&str> = readings.iter().map(String::as_str).collect();
        report(&format!("encode {length} bytes"), &mut || {
            std::hint::black_box(sigilcode::encode(std::hint::black_box(&data)));
        });
        report(&format!("decode {length} bytes"), &mut || {
            std::hint::black_box(sigilcode::decode(std::hint::black_box(&sigil), length).unwrap());
        });
        report(&format!("decode_readings {length} bytes, 3 readings of one character"), &mut || {
            std::hint::black_box(sigilcode::decode_readings(std::hint::black_box(&readings), length));
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
