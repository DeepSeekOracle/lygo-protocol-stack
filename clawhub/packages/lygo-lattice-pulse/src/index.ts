import { Type } from "typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { existsSync, readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";

const SIGNATURE = "Δ9Φ963-LYGO-LATTICE-PULSE-v1";
const DEFAULT_PAGES =
  "https://deepseekoracle.github.io/lygo-protocol-stack";

const REQUIRED_STACK_MARKERS = [
  "tools/haven_star_chart_gate.py",
  "tools/verify_lattice_alignment.py",
  "tools/build_haven_star_chart.py",
  "docs/haven_star_chart/haven_star_chart_data.json",
  "clawhub/skills.json",
  "protocol0_byte_entropy_filter/src/python/byte_entropy_filter.py",
] as const;

type PluginConfig = {
  stackRoot?: string;
  pagesBase?: string;
};

function textResult(payload: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
      },
    ],
  };
}

function resolvePagesBase(cfg?: PluginConfig): string {
  const base = (cfg?.pagesBase || DEFAULT_PAGES).replace(/\/+$/, "");
  return base;
}

function resolveStackRoot(cfg?: PluginConfig): string | null {
  const fromCfg = cfg?.stackRoot?.trim();
  if (fromCfg) return path.resolve(fromCfg);
  const fromEnv = process.env.LYGO_STACK_ROOT?.trim();
  if (fromEnv) return path.resolve(fromEnv);
  return null;
}

async function fetchJson<T>(url: string, timeoutMs = 20_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { "User-Agent": "LYGO-Lattice-Pulse/1.0" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

async function pulseLiveLattice(pagesBase: string) {
  const metaUrl = `${pagesBase}/haven_star_chart/haven_star_chart_meta.json`;
  const dataUrl = `${pagesBase}/haven_star_chart/haven_star_chart_data.json`;
  const queueUrl = `${pagesBase}/haven_star_chart/haven_star_chart_queue.json`;
  const feedUrl = `${pagesBase}/haven_star_chart/haven_star_chart_feed.json`;

  const [meta, data, queue, feed] = await Promise.all([
    fetchJson<Record<string, unknown>>(metaUrl).catch((e) => ({ error: String(e) })),
    fetchJson<Record<string, unknown>>(dataUrl).catch((e) => ({ error: String(e) })),
    fetchJson<Record<string, unknown>>(queueUrl).catch((e) => ({ error: String(e) })),
    fetchJson<Record<string, unknown>>(feedUrl).catch((e) => ({ error: String(e) })),
  ]);

  const cosmos = (data as { cosmos?: Record<string, unknown> }).cosmos || {};
  const feedEntries = Array.isArray((feed as { entries?: unknown[] }).entries)
    ? ((feed as { entries: unknown[] }).entries).slice(0, 5)
    : [];

  return {
    signature: SIGNATURE,
    pulse_utc: new Date().toISOString(),
    pages_base: pagesBase,
    meta,
    chart: {
      node_count: (data as { node_count?: number }).node_count,
      link_count: (data as { link_count?: number }).link_count,
      registry_sha256: (data as { registry_sha256?: string }).registry_sha256,
      generated_utc: (data as { generated_utc?: string }).generated_utc,
      galaxy_count: cosmos.galaxy_count,
      nebula_count: cosmos.nebula_count,
    },
    queue,
    feed_tail: feedEntries,
    install_hint:
      "npx clawhub@latest install deepseekoracle/lygo-protocol-stack-operator deepseekoracle/lygo-lattice-pulse",
  };
}

async function verifyLocalStack(stackRoot: string) {
  const checks: Record<string, boolean | string> = {
    stack_root: stackRoot,
    exists: existsSync(stackRoot),
  };

  if (!checks.exists) {
    return { signature: SIGNATURE, all_pass: false, checks, errors: ["stack_root_missing"] };
  }

  const missing: string[] = [];
  for (const rel of REQUIRED_STACK_MARKERS) {
    const full = path.join(stackRoot, rel);
    const ok = existsSync(full);
    checks[rel] = ok;
    if (!ok) missing.push(rel);
  }

  let registrySha = "";
  try {
    const regPath = path.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
    const raw = await readFile(regPath, "utf8");
    registrySha = createHash("sha256").update(raw).digest("hex").slice(0, 16);
    checks.local_registry_sha16 = registrySha;
  } catch {
    checks.local_registry_sha16 = false;
  }

  const skillCount = (() => {
    try {
      const skills = JSON.parse(
        readFileSync(path.join(stackRoot, "clawhub/skills.json"), "utf8"),
      ) as { skills?: unknown[] };
      return Array.isArray(skills.skills) ? skills.skills.length : 0;
    } catch {
      return 0;
    }
  })();
  checks.clawhub_skill_count = String(skillCount);

  return {
    signature: SIGNATURE,
    verified_utc: new Date().toISOString(),
    all_pass: missing.length === 0,
    checks,
    missing,
    next_steps: missing.length
      ? ["Fix missing markers or set LYGO_STACK_ROOT to trusted clone"]
      : [
          "python tools/verify_lattice_alignment.py",
          "python tools/haven_star_chart_gate.py --example-birth",
        ],
  };
}

function p0QuickScan(text: string) {
  const bytes = Buffer.from(text, "utf8");
  const len = bytes.length;
  if (!len) {
    return { signature: SIGNATURE, verdict: "REJECT", score: 0, reasons: ["empty_payload"] };
  }

  const reasons: string[] = [];
  let score = 0.35;

  const unique = new Set(bytes).size;
  const entropyProxy = unique / Math.min(len, 256);
  if (entropyProxy < 0.08) {
    reasons.push("low_byte_diversity");
    score -= 0.2;
  } else {
    reasons.push("byte_diversity_ok");
    score += 0.15;
  }

  const lowered = text.toLowerCase();
  const quarantineHints = [
    "ignore previous",
    "disregard instructions",
    "jailbreak",
    "exfiltrate",
    "api_key",
    "password:",
  ];
  for (const hint of quarantineHints) {
    if (lowered.includes(hint)) {
      reasons.push(`quarantine_hint:${hint}`);
      score -= 0.25;
    }
  }

  const mathMarkers = /(=|∇|⊗|Δ9|963|Hz|φ|Φ)/;
  if (mathMarkers.test(text)) {
    reasons.push("math_resonance_markers");
    score += 0.1;
  }

  const verdict = score >= 0.35 ? "AMPLIFY" : score >= 0.2 ? "NEUTRAL" : "QUARANTINE";
  return {
    signature: SIGNATURE,
    verdict,
    score: Number(score.toFixed(4)),
    byte_length: len,
    unique_bytes: unique,
    reasons,
    note: "Quick JS heuristic — run stack P0 for authoritative gate.",
  };
}

function consentChecklist(stackRoot: string | null) {
  return {
    signature: SIGNATURE,
    policy: "Humans approve live writes; agents propose and gate only.",
    required_before_live_write: [
      "Run lygo_lattice_pulse or lygo_lattice_verify",
      "Gate submission with haven_star_chart_gate.py",
      "Human explicit --i-consent on submit/ingest",
      "Never publish consent_bundle or family_bind_salt",
    ],
    skill_chain: [
      "lygo-protocol-stack-operator",
      "lygo-network-builder",
      "lygo-haven-star-chart",
      "lygo-lattice-birth",
    ],
    stack_root_configured: Boolean(stackRoot),
    stack_root: stackRoot,
    scan_cue:
      "LYGO-HSC-ATTEST-v1; gate=haven_star_chart_gate.py; P0-first; consent-gated; user-reviewed",
  };
}

export default definePluginEntry({
  id: "lygo-lattice-pulse",
  name: "LYGO Lattice Pulse",
  description: "Live lattice heartbeat and alignment tools for LYGO agents",
  register(api) {
    const cfg = () => (api.config || {}) as PluginConfig;

    api.registerTool({
      name: "lygo_lattice_pulse",
      description:
        "Fetch live LYGO Haven Star Chart pulse — registry SHA, node counts, queue, feed tail from GitHub Pages.",
      parameters: Type.Object({
        pages_base: Type.Optional(
          Type.String({ description: "Override GitHub Pages base URL." }),
        ),
      }),
      async execute(_id, params) {
        const base = (params.pages_base as string | undefined)?.trim() || resolvePagesBase(cfg());
        return textResult(await pulseLiveLattice(base));
      },
    });

    api.registerTool(
      {
        name: "lygo_lattice_verify",
        description:
          "Verify local lygo-protocol-stack root (LYGO_STACK_ROOT): required gate tools, registry, P0 filter markers.",
        parameters: Type.Object({
          stack_root: Type.Optional(
            Type.String({ description: "Absolute path to lygo-protocol-stack clone." }),
          ),
        }),
        async execute(_id, params) {
          const root =
            (params.stack_root as string | undefined)?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({
              signature: SIGNATURE,
              all_pass: false,
              error: "Set plugins.entries.lygo-lattice-pulse.config.stackRoot or LYGO_STACK_ROOT",
            });
          }
          return textResult(await verifyLocalStack(root));
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "lygo_p0_quick_scan",
        description:
          "Quick P0-style byte/entropy heuristic scan on text before external posts or submissions (non-authoritative).",
        parameters: Type.Object({
          text: Type.String({ description: "UTF-8 text to scan.", minLength: 1 }),
        }),
        async execute(_id, params) {
          return textResult(p0QuickScan(String(params.text || "")));
        },
      },
      { optional: true },
    );

    api.registerTool({
      name: "lygo_consent_checklist",
      description:
        "Return LYGO consent-gated workflow checklist before live star chart writes, publishes, or ingest.",
      parameters: Type.Object({}),
      async execute() {
        return textResult(consentChecklist(resolveStackRoot(cfg())));
      },
    });
  },
});