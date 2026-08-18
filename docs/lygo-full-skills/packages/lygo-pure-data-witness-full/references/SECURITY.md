# Security — lygo-pure-data-witness

- HTTPS-only fetch; SSRF / private IP / metadata host block
- Content heuristics reject malware bait / extreme script density
- Snapshots size-capped; secret pattern redaction
- No subprocess shell
- Star Chart writes are consent-gated pending submissions (not anonymous)
- Register portal never fetches or writes the chart from the browser
- Do not archive credentials, private dashboards, or illegal content
- Portal playbook: `PORTAL_TRAINING.md`
