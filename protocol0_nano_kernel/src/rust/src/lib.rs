//! LYGO P0.4 Nano Kernel — `#![no_std]` reference (matches `lygo_p0.py`)

#![cfg_attr(not(test), no_std)]

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum Verdict {
    Amplify,
    Soften,
    Quarantine,
}

#[derive(Copy, Clone, Debug, PartialEq)]
pub struct ResultP0 {
    pub verdict: Verdict,
    pub risk: f32,
    pub entropy: f32,
    pub compression: f32,
}

const MAX_BYTES: usize = 8192;
const PHI_MIN: f32 = 0.618;
const PHI_MAX: f32 = 1.618;
const ENTROPY_LOW: f32 = 0.25;
const ENTROPY_HIGH: f32 = 0.90;
const COMP_MIN_LEN: usize = 64;
const COMP_POOR: f32 = 0.90;

fn ln2() -> f32 {
    0.69314718056_f32
}

fn log2_f32(x: f32) -> f32 {
    if x <= 0.0 {
        return 0.0;
    }
    let mut y = x;
    let mut e: i32 = 0;
    while y >= 2.0 {
        y /= 2.0;
        e += 1;
    }
    while y < 1.0 {
        y *= 2.0;
        e -= 1;
    }
    let z = (y - 1.0) / (y + 1.0);
    let z2 = z * z;
    let mut s = z;
    let mut z_pow = z;
    for _ in 0..6 {
        z_pow *= z2;
        s += z_pow / (2 * 1 + 1) as f32;
    }
    (2.0 * s + e as f32 * ln2())
}

pub fn entropy_norm(data: &[u8]) -> f32 {
    if data.is_empty() {
        return 0.0;
    }
    let mut freq = [0u32; 256];
    for &b in data {
        freq[b as usize] += 1;
    }
    let len = data.len() as f32;
    let mut ent = 0.0_f32;
    for c in freq.iter() {
        if *c > 0 {
            let p = *c as f32 / len;
            ent -= p * log2_f32(p);
        }
    }
    let denom = if data.len() > 1 {
        log2_f32(len)
    } else {
        1.0
    };
    (ent / denom).min(1.0)
}

pub fn compression_ratio(data: &[u8]) -> f32 {
    if data.len() < COMP_MIN_LEN {
        return 0.0;
    }
    let limit = data.len() - 7;
    let mut repeats = 0u32;
    let mut i = 0usize;
    while i < limit {
        if data[i..i + 4] == data[i + 4..i + 8] {
            repeats += 1;
        }
        i += 4;
    }
    let ratio = (repeats as f32 / data.len() as f32).min(1.0);
    1.0 - ratio
}

pub fn validate_bytes(data: &[u8]) -> ResultP0 {
    if data.len() > MAX_BYTES {
        return ResultP0 {
            verdict: Verdict::Quarantine,
            risk: 1.0,
            entropy: 0.0,
            compression: 0.0,
        };
    }
    let ent = entropy_norm(data);
    let comp = compression_ratio(data);
    let mut risk = 0.0_f32;
    if ent > ENTROPY_HIGH {
        risk += 0.30;
    } else if ent < ENTROPY_LOW {
        risk += 0.15;
    }
    if comp > COMP_POOR {
        risk += 0.25;
    }
    if risk > 1.0 {
        risk = 1.0;
    }
    let size_damp = if data.len() < 128 {
        data.len() as f32 / 128.0
    } else {
        1.0
    };
    let phi_risk = risk * PHI_MAX * size_damp;
    let mut verdict = if phi_risk < PHI_MIN {
        Verdict::Amplify
    } else if phi_risk <= PHI_MAX {
        Verdict::Soften
    } else {
        Verdict::Quarantine
    };
    if ent < ENTROPY_LOW && verdict == Verdict::Amplify {
        verdict = Verdict::Soften;
    }
    ResultP0 {
        verdict,
        risk,
        entropy: ent,
        compression: comp,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_amplify() {
        let data = br#"{"a":1,"b":2}"#;
        let r = validate_bytes(data);
        assert_eq!(r.verdict, Verdict::Amplify);
    }

    #[test]
    fn oversize_quarantine() {
        let data = [0u8; 9000];
        let r = validate_bytes(&data);
        assert_eq!(r.verdict, Verdict::Quarantine);
    }
}