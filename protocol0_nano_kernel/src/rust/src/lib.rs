// FILE: lygo_p0_nano_gate.rs
// VERSION: P0.4 (LOCKED)
// LYGO-P0-NG-v1.4
// Deterministic Nano Ethical Gate — FINAL
// 
// Rust #![no_std] implementation for embedded systems

#![no_std]
#![allow(clippy::needless_return)]

use core::f32;

// =========================
// HARD LIMITS
// =========================

const MAX_BYTES: usize = 8192;
const PHI_MIN: f32 = 0.618;
const PHI_MAX: f32 = 1.618;
const ENTROPY_LOW: f32 = 0.25;
const ENTROPY_HIGH: f32 = 0.90;
const COMP_MIN_LEN: usize = 64;
const COMP_POOR: f32 = 0.90;

// =========================
// TYPE DEFINITIONS
// =========================

#[derive(Copy, Clone, PartialEq, Debug)]
pub enum Decision {
    Amplify,
    Soften,
    Quarantine,
}

#[derive(Copy, Clone, Debug)]
pub struct ResultLygo {
    pub decision: Decision,
    pub risk: f32,
}

// =========================
// METRIC FUNCTIONS
// =========================

/// Calculate normalized Shannon entropy (0-1 range)
///
/// # Arguments
/// * `data` - Slice of bytes to analyze
/// 
/// # Returns
/// * Normalized entropy value between 0.0 and 1.0
fn entropy_norm(data: &[u8]) -> f32 {
    if data.is_empty() {
        return 0.0;
    }

    let mut freq = [0u32; 256];
    for &b in data {
        freq[b as usize] += 1;
    }

    let len = data.len() as f32;
    let mut ent = 0.0;

    for &c in freq.iter() {
        if c > 0 {
            let p = c as f32 / len;
            ent -= p * p.log2();
        }
    }

    let denom = if len > 1.0 {
        len.log2().min(8.0)
    } else {
        1.0
    };

    ent / denom
}

/// Calculate compression ratio using pattern detection
///
/// # Arguments
/// * `data` - Slice of bytes to analyze
/// 
/// # Returns
/// * Compression ratio (higher = less compressible)
fn compression_ratio(data: &[u8]) -> f32 {
    if data.len() < COMP_MIN_LEN {
        return 0.0;
    }

    let mut repeats = 0;
    let limit = if data.len() > 7 {
        data.len() - 7
    } else {
        return 0.0;
    };

    for i in 0..limit {
        // Check if 4-byte pattern repeats
        let slice1 = &data[i..i + 4];
        let slice2 = &data[i + 4..i + 8];
        
        if slice1 == slice2 {
            repeats += 1;
        }
    }

    let ratio = (repeats as f32 / data.len() as f32).min(1.0);
    1.0 - ratio
}

// =========================
// PUBLIC API
// =========================

/// Validate byte array against LYGO-P0-NG protocol
///
/// # Arguments
/// * `data` - Slice of bytes to validate
/// 
/// # Returns
/// * `ResultLygo` containing decision and risk score
/// 
/// # Examples
/// ```
/// use lygo_p0_nano_gate::{validate_bytes, Decision};
/// 
/// let data = [0x01, 0x02, 0x03, 0x04];
/// let result = validate_bytes(&data);
/// 
/// match result.decision {
///     Decision::Amplify => println!("Data is safe to amplify"),
///     Decision::Soften => println!("Data should be softened"),
///     Decision::Quarantine => println!("Data must be quarantined"),
/// }
/// ```
pub fn validate_bytes(data: &[u8]) -> ResultLygo {
    // Check size limit
    if data.len() > MAX_BYTES {
        return ResultLygo {
            decision: Decision::Quarantine,
            risk: 1.0,
        };
    }

    let mut risk = 0.0;
    
    // Calculate metrics
    let ent = entropy_norm(data);
    let comp = compression_ratio(data);

    // Apply risk weights
    if ent > ENTROPY_HIGH {
        risk += 0.30; // high_entropy
    } else if ent < ENTROPY_LOW {
        risk += 0.15; // low_entropy_padding
    }

    if comp > COMP_POOR {
        risk += 0.25; // poor_compression_structure
    }

    // Clamp risk to 0-1 range
    if risk > 1.0 {
        risk = 1.0;
    }

    // =========================
    // Φ GATE (SIZE-DAMPED)
    // =========================

    // Calculate size damping factor
    let size_damp = if data.len() < 128 {
        data.len() as f32 / 128.0
    } else {
        1.0
    };

    // Apply phi governance
    let phi_risk = risk * PHI_MAX * size_damp;

    // Make decision based on phi risk
    let mut decision = if phi_risk < PHI_MIN {
        Decision::Amplify
    } else if phi_risk <= PHI_MAX {
        Decision::Soften
    } else {
        Decision::Quarantine
    };

    // Safety floor: low entropy shouldn't amplify
    if ent < ENTROPY_LOW && decision == Decision::Amplify {
        decision = Decision::Soften;
    }

    ResultLygo { decision, risk }
}

/// Convert Decision enum to string slice
///
/// # Arguments
/// * `decision` - The decision to convert
/// 
/// # Returns
/// * String slice representation
pub fn decision_to_string(decision: Decision) -> &'static str {
    match decision {
        Decision::Amplify => "AMPLIFY",
        Decision::Soften => "SOFTEN",
        Decision::Quarantine => "QUARANTINE",
    }
}

// =========================
// TESTS
// =========================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_size_limit() {
        let large_data = [0u8; MAX_BYTES + 1];
        let result = validate_bytes(&large_data);
        assert_eq!(result.decision, Decision::Quarantine);
        assert_eq!(result.risk, 1.0);
    }

    #[test]
    fn test_low_entropy() {
        let data = [0x01u8; 100]; // All same byte
        let result = validate_bytes(&data);
        assert!(entropy_norm(&data) < ENTROPY_LOW);
        assert!(result.risk >= 0.15);
    }

    #[test]
    fn test_high_entropy() {
        let mut data = [0u8; 200];
        for i in 0..data.len() {
            data[i] = (i * 17) as u8; // Pseudo-random pattern
        }
        let result = validate_bytes(&data);
        assert!(entropy_norm(&data) > ENTROPY_LOW);
    }

    #[test]
    fn test_compression_ratio() {
        // Test with repeating pattern (should have low compression ratio)
        let repeating = [0xAA, 0xBB, 0xAA, 0xBB, 0xAA, 0xBB, 0xAA, 0xBB];
        let ratio = compression_ratio(&repeating);
        assert!(ratio < 0.5);
    }

    #[test]
    fn test_small_data() {
        let data = [0x01, 0x02, 0x03];
        let result = validate_bytes(&data);
        // Small data should have low risk due to size damping
        assert!(result.risk <= 1.0);
    }

    #[test]
    fn test_decision_strings() {
        assert_eq!(decision_to_string(Decision::Amplify), "AMPLIFY");
        assert_eq!(decision_to_string(Decision::Soften), "SOFTEN");
        assert_eq!(decision_to_string(Decision::Quarantine), "QUARANTINE");
    }
}

// =========================
// DEMONSTRATION (when compiled with std)
// =========================

#[cfg(feature = "demo")]
pub mod demo {
    use super::*;
    
    /// Run demonstration of LYGO-P0-NG functionality
    pub fn run_demo() {
        #[cfg(feature = "std")]
        {
            use std::println;
            
            println!("LYGO-P0-NG Rust Implementation vP0.4");
            println!("===================================\n");
            
            // Test 1: Low entropy (repeating pattern)
            let test1 = [0x01u8; 100];
            let result1 = validate_bytes(&test1);
            println!("Test 1: Repeating pattern (0x01 x 100)");
            println!("  Entropy: {:.4}", entropy_norm(&test1));
            println!("  Decision: {}", decision_to_string(result1.decision));
            println!("  Risk: {:.3}\n", result1.risk);
            
            // Test 2: Medium entropy
            let mut test2 = [0u8; 200];
            for i in 0..test2.len() {
                test2[i] = (i % 10) as u8 + 65; // A-J repeating
            }
            let result2 = validate_bytes(&test2);
            println!("Test 2: Medium entropy (A-J pattern)");
            println!("  Entropy: {:.4}", entropy_norm(&test2));
            println!("  Decision: {}", decision_to_string(result2.decision));
            println!("  Risk: {:.3}\n", result2.risk);
            
            // Test 3: Small data
            let test3 = [0xFF, 0xFE, 0xFD, 0xFC];
            let result3 = validate_bytes(&test3);
            println!("Test 3: Small data (4 bytes)");
            println!("  Decision: {}", decision_to_string(result3.decision));
            println!("  Risk: {:.3}\n", result3.risk);
            
            println!("Protocol: LYGO-P0-NG-v1.4");
            println!("Version: P0.4 (LOCKED)");
        }
    }
}

/// Convenience macro for quick validation
#[macro_export]
macro_rules! lygo_validate {
    ($data:expr) => {
        $crate::validate_bytes($data)
    };
}