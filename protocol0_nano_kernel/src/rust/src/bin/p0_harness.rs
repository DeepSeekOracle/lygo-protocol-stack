use lygo_p0_nano_kernel::{validate_bytes, ResultP0, Verdict};
use std::fs::File;
use std::io::{BufRead, BufReader};

fn hex_byte(pair: &[u8]) -> Option<u8> {
    if pair.len() != 2 {
        return None;
    }
    fn nib(b: u8) -> Option<u8> {
        match b {
            b'0'..=b'9' => Some(b - b'0'),
            b'a'..=b'f' => Some(b - b'a' + 10),
            b'A'..=b'F' => Some(b - b'A' + 10),
            _ => None,
        }
    }
    let hi = nib(pair[0])?;
    let lo = nib(pair[1])?;
    Some((hi << 4) | lo)
}

fn decode_hex(s: &str) -> Option<Vec<u8>> {
    let bytes = s.as_bytes();
    if bytes.len() % 2 != 0 {
        return None;
    }
    let mut out = Vec::with_capacity(bytes.len() / 2);
    for chunk in bytes.chunks(2) {
        out.push(hex_byte(chunk)?);
    }
    Some(out)
}

fn verdict_name(v: Verdict) -> &'static str {
    match v {
        Verdict::Amplify => "AMPLIFY",
        Verdict::Soften => "SOFTEN",
        Verdict::Quarantine => "QUARANTINE",
    }
}

fn canonical_line(id: &str, r: &ResultP0) -> String {
    format!(
        "{}|{}|{:.4}|{:.4}|{:.4}|{:.4}",
        id,
        verdict_name(r.verdict),
        r.risk,
        r.entropy,
        r.compression,
        r.phi_risk
    )
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: p0_harness <vectors.tsv>");
    let file = File::open(path).expect("open vectors");
    let reader = BufReader::new(file);
    for line in reader.lines() {
        let line = line.expect("read line");
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let mut parts = line.splitn(2, '\t');
        let id = parts.next().expect("id");
        let hex = parts.next().expect("hex");
        let data = decode_hex(hex).expect("hex decode");
        let r = validate_bytes(&data);
        println!("{}", canonical_line(id, &r));
    }
}