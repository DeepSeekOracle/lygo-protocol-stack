/* LYGO P0 vector harness — reads fixtures manifest, prints canonical lines for SHA parity */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "lygo_p0_nano.c"

static int hex_nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static size_t hex_decode(const char *hex, uint8_t *out, size_t max_out) {
    size_t len = strlen(hex);
    size_t i, o = 0;
    if (len % 2 != 0) return 0;
    for (i = 0; i < len; i += 2) {
        int hi = hex_nibble(hex[i]);
        int lo = hex_nibble(hex[i + 1]);
        if (hi < 0 || lo < 0 || o >= max_out) return 0;
        out[o++] = (uint8_t)((hi << 4) | lo);
    }
    return o;
}

int main(int argc, char **argv) {
    FILE *fp;
    char line[65536];
    char id[128];
    char hex[60000];
    uint8_t buf[9000];
    size_t n;

    if (argc < 2) {
        fprintf(stderr, "usage: %s <vectors.tsv>\n", argv[0]);
        return 2;
    }
    fp = fopen(argv[1], "r");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    while (fgets(line, sizeof(line), fp)) {
        if (line[0] == '#' || line[0] == '\n') continue;
        if (sscanf(line, "%127s\t%65535s", id, hex) != 2) continue;
        n = hex_decode(hex, buf, sizeof(buf));
        if (n == 0) continue;
        {
            lygo_p0_result_t r = lygo_validate_bytes(buf, n);
            printf("%s|%s|%.4f|%.4f|%.4f|%.4f\n",
                   id,
                   verdict_str(r.verdict),
                   r.risk,
                   r.entropy,
                   r.compression,
                   r.phi_risk);
        }
    }
    fclose(fp);
    return 0;
}