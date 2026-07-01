#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <string.h>

/*
 * LYGO P0.4 NANO — CANONICAL + HARDENED
 * - Policy-identical to P0.4
 * - Defensive clamps added
 * - Dead macros removed
 * - ROM / firmware safe
 */

#define MAX_BYTES 8192

#define PHI_MIN 0.618f
#define PHI_MAX 1.618f

#define ENTROPY_LOW 0.25f
#define ENTROPY_HIGH 0.90f

#define COMP_MIN_LEN 64
#define COMP_POOR 0.90f

typedef enum {
    LYGO_AMPLIFY = 0,
    LYGO_SOFTEN = 1,
    LYGO_QUARANTINE = 2
} lygo_decision_t;

typedef struct {
    lygo_decision_t decision;
    float risk;
    uint8_t reasons;
} lygo_result_t;

/* reason bitmask */
#define R_HIGH_ENTROPY     (1 << 0)
#define R_LOW_ENTROPY      (1 << 1)
#define R_POOR_COMP        (1 << 2)
#define R_SIZE_EXCEEDED    (1 << 3)

/* ---------- ENTROPY ---------- */
static float entropy_norm(const uint8_t *b, size_t len) {
    if (len == 0) return 0.0f;

    uint32_t freq[256] = {0};
    for (size_t i = 0; i < len; i++) {
        freq[b[i]]++;
    }

    float ent = 0.0f;
    for (size_t i = 0; i < 256; i++) {
        if (freq[i] != 0) {
            float p = (float)freq[i] / (float)len;
            ent -= p * log2f(p);
        }
    }

    float denom;
    if (len > 1) {
        denom = log2f((float)len);
        if (denom > 8.0f) denom = 8.0f;
    } else {
        denom = 1.0f;
    }

    return ent / denom;
}

/* ---------- COMPRESSION (PATTERN HEURISTIC) ---------- */
static float compression_ratio(const uint8_t *b, size_t len) {
    if (len < COMP_MIN_LEN) return 0.0f;

    uint32_t repeats = 0;
    for (size_t i = 0; i + 8 <= len; i += 4) {
        if (memcmp(b + i, b + i + 4, 4) == 0) {
            repeats++;
        }
    }

    float c = (float)repeats / (float)len;
    if (c < 0.0f) c = 0.0f;
    if (c > 1.0f) c = 1.0f;

    return 1.0f - c;
}

/* ---------- CORE ---------- */
lygo_result_t lygo_validate_bytes(const uint8_t *data, size_t len) {
    lygo_result_t r;
    r.decision = LYGO_AMPLIFY;
    r.risk = 0.0f;
    r.reasons = 0;

    if (len > MAX_BYTES) {
        r.decision = LYGO_QUARANTINE;
        r.risk = 1.0f;
        r.reasons = R_SIZE_EXCEEDED;
        return r;
    }

    float ent = entropy_norm(data, len);
    float comp = compression_ratio(data, len);

    float risk = 0.0f;

    if (ent > ENTROPY_HIGH) {
        risk += 0.30f;
        r.reasons |= R_HIGH_ENTROPY;
    } else if (ent < ENTROPY_LOW) {
        risk += 0.15f;
        r.reasons |= R_LOW_ENTROPY;
    }

    if (comp > COMP_POOR) {
        risk += 0.25f;
        r.reasons |= R_POOR_COMP;
    }

    if (risk > 1.0f) risk = 1.0f;
    if (risk < 0.0f) risk = 0.0f;

    r.risk = risk;

    /* Φ gate with defensive size damping */
    float size_damp;
    if (len < 128) {
        size_damp = (float)len / 128.0f;
    } else {
        size_damp = 1.0f;
    }

    if (size_damp < 0.0f) size_damp = 0.0f;
    if (size_damp > 1.0f) size_damp = 1.0f;

    float phi_risk = risk * PHI_MAX * size_damp;

    if (phi_risk < PHI_MIN) {
        r.decision = LYGO_AMPLIFY;
    } else if (phi_risk <= PHI_MAX) {
        r.decision = LYGO_SOFTEN;
    } else {
        r.decision = LYGO_QUARANTINE;
    }

    /* safety floor: low entropy never amplifies */
    if ((r.reasons & R_LOW_ENTROPY) && r.decision == LYGO_AMPLIFY) {
        r.decision = LYGO_SOFTEN;
    }

    return r;
}
