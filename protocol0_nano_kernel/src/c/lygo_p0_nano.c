#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <string.h>
#include <stdio.h>

/* LYGO P0.4 Nano Kernel — no heap, matches protocol0 python lygo_p0.py */

#define MAX_BYTES 8192
#define PHI_MIN 0.618f
#define PHI_MAX 1.618f
#define ENTROPY_LOW 0.25f
#define ENTROPY_HIGH 0.90f
#define COMP_MIN_LEN 64
#define COMP_POOR 0.90f

typedef enum { LYGO_AMPLIFY = 0, LYGO_SOFTEN = 1, LYGO_QUARANTINE = 2 } lygo_verdict_t;

typedef struct {
    lygo_verdict_t verdict;
    float risk;
    float entropy;
    float compression;
    float phi_risk;
} lygo_p0_result_t;

static float round4f(float x) {
    return roundf(x * 10000.0f) / 10000.0f;
}

float entropy_norm(const uint8_t *data, size_t len) {
    if (len == 0) return 0.0f;
    uint32_t freq[256];
    size_t i;
    float ent = 0.0f;
    float denom;
    for (i = 0; i < 256; i++) freq[i] = 0;
    for (i = 0; i < len; i++) freq[data[i]]++;
    for (i = 0; i < 256; i++) {
        if (freq[i]) {
            float p = (float)freq[i] / (float)len;
            ent -= p * log2f(p);
        }
    }
    denom = (len > 1) ? log2f((float)len) : 1.0f;
    if (ent / denom > 1.0f) return 1.0f;
    return ent / denom;
}

float compression_ratio(const uint8_t *data, size_t len) {
    size_t i;
    size_t limit;
    uint32_t repeats = 0;
    float ratio;
    if (len < (size_t)COMP_MIN_LEN) return 0.0f;
    limit = len - 7;
    for (i = 0; i < limit; i += 4) {
        if (memcmp(data + i, data + i + 4, 4) == 0) repeats++;
    }
    ratio = (float)repeats / (float)len;
    if (ratio > 1.0f) ratio = 1.0f;
    return 1.0f - ratio;
}

lygo_p0_result_t lygo_validate_bytes(const uint8_t *data, size_t len) {
    lygo_p0_result_t r;
    float ent, comp, risk, size_damp, phi_risk;
    r.verdict = LYGO_AMPLIFY;
    r.risk = 0.0f;
    r.entropy = 0.0f;
    r.compression = 0.0f;
    r.phi_risk = 0.0f;
    if (len > MAX_BYTES) {
        r.verdict = LYGO_QUARANTINE;
        r.risk = 1.0f;
        r.phi_risk = round4f(PHI_MAX);
        return r;
    }
    ent = entropy_norm(data, len);
    comp = compression_ratio(data, len);
    risk = 0.0f;
    if (ent > ENTROPY_HIGH) risk += 0.30f;
    else if (ent < ENTROPY_LOW) risk += 0.15f;
    if (comp > COMP_POOR) risk += 0.25f;
    if (risk > 1.0f) risk = 1.0f;
    size_damp = (len < 128) ? ((float)len / 128.0f) : 1.0f;
    phi_risk = risk * PHI_MAX * size_damp;
    if (phi_risk < PHI_MIN) r.verdict = LYGO_AMPLIFY;
    else if (phi_risk <= PHI_MAX) r.verdict = LYGO_SOFTEN;
    else r.verdict = LYGO_QUARANTINE;
    if (ent < ENTROPY_LOW && r.verdict == LYGO_AMPLIFY) r.verdict = LYGO_SOFTEN;
    r.risk = round4f(risk);
    r.entropy = round4f(ent);
    r.compression = round4f(comp);
    r.phi_risk = round4f(phi_risk);
    return r;
}

static const char *verdict_str(lygo_verdict_t v) {
    if (v == LYGO_AMPLIFY) return "AMPLIFY";
    if (v == LYGO_SOFTEN) return "SOFTEN";
    return "QUARANTINE";
}

#ifdef LYGO_P0_TEST_MAIN
int main(void) {
    const uint8_t sample[] = "{\"a\":1,\"b\":2}";
    lygo_p0_result_t r = lygo_validate_bytes(sample, sizeof(sample) - 1);
    printf("LYGO P0 C test\nverdict=%s risk=%.4f entropy=%.4f comp=%.4f\n",
           verdict_str(r.verdict), r.risk, r.entropy, r.compression);
    return 0;
}
#endif