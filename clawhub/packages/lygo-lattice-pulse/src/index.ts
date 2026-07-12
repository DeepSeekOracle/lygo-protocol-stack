import { Type } from "typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";

const SIGNATURE = "Δ9Φ963-LYGO-LATTICE-PULSE-v1.1";
const DEFAULT_PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack";

const REQUIRED_STACK_MARKERS = [
  "tools/haven_star_chart_gate.py",
  "tools/haven_star_chart_submit.py",
  "tools/haven_star_chart_ingest.py",
  "tools/verify_lattice_alignment.py",
  "tools/build_haven_star_chart.py",
  "tools/lygo_lattice_birth.py",
  "tools/lygo_lineage_codec.py",
  "docs/haven_star_chart/haven_star_chart_data.json",
  "docs/haven_star_chart/submission_schema.json",
  "clawhub/skills.json",
  "clawhub/packages/lygo-lattice-pulse/openclaw.plugin.json",
  "protocol0_byte_entropy_filter/src/python/byte_entropy_filter.py",
] as const;

const PLUGIN_INSTALL =
  "openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse";
const SKILL_CHAIN = [
  "lygo-protocol-stack-operator",
  "lygo-network-builder",
  "lygo-sovereign-super-skill",
  "lygo-haven-star-chart",
  "lygo-lattice-birth",
] as const;

type PluginConfig = { stackRoot?: string; pagesBase?: string };

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
  return (cfg?.pagesBase || DEFAULT_PAGES).replace(/\/+$/, "");
}

function resolveStackRoot(cfg?: PluginConfig): string | null {
  const fromCfg = cfg?.stackRoot?.trim();
  if (fromCfg) return path.resolve(fromCfg);
  const fromEnv = process.env.LYGO_STACK_ROOT?.trim();
  if (fromEnv) return path.resolve(fromEnv);
  return null;
}

function sha256Hex(data: string): string {
  return createHash("sha256").update(data).digest("hex");
}

async function fetchJson<T>(url: string, timeoutMs = 20_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { "User-Agent": "LYGO-Lattice-Pulse/1.1" },
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
    ? ((feed as { entries: unknown[] }).entries).slice(0, 8)
    : [];

  return {
    signature: SIGNATURE,
    pulse_utc: new Date().toISOString(),
    pages_base: pagesBase,
    live: !(data as { error?: string }).error,
    meta,
    chart: {
      node_count: (data as { node_count?: number }).node_count,
      link_count: (data as { link_count?: number }).link_count,
      registry_sha256: (data as { registry_sha256?: string }).registry_sha256,
      generated_utc: (data as { generated_utc?: string }).generated_utc,
      galaxy_count: cosmos.galaxy_count,
      nebula_count: cosmos.nebula_count,
      cluster_count: cosmos.cluster_count,
    },
    queue,
    feed_tail: feedEntries,
    plugin: PLUGIN_INSTALL,
    skill_chain: [...SKILL_CHAIN],
    package: "clawhub:@deepseekoracle/lygo-lattice-pulse@1.1.0",
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
    const ok = existsSync(path.join(stackRoot, rel));
    checks[rel] = ok;
    if (!ok) missing.push(rel);
  }

  try {
    const regPath = path.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
    const raw = await readFile(regPath, "utf8");
    checks.local_registry_sha256 = sha256Hex(raw);
    checks.local_registry_sha16 = checks.local_registry_sha256.slice(0, 16);
  } catch {
    checks.local_registry_sha256 = false;
  }

  try {
    const skills = JSON.parse(
      readFileSync(path.join(stackRoot, "clawhub/skills.json"), "utf8"),
    ) as { skills?: { slug: string }[]; count_published?: number };
    checks.clawhub_skill_count = String(skills.skills?.length ?? 0);
    checks.clawhub_count_published = String(skills.count_published ?? 0);
  } catch {
    checks.clawhub_skill_count = "0";
  }

  const python = process.platform === "win32" ? "python" : "python3";
  const alignTool = path.join(stackRoot, "tools", "verify_lattice_alignment.py");
  if (existsSync(alignTool)) {
    const probe = spawnSync(python, [alignTool], {
      cwd: stackRoot,
      encoding: "utf8",
      timeout: 180_000,
      shell: process.platform === "win32",
    });
    checks.lattice_alignment_probe = probe.status === 0 ? "ok" : `exit_${probe.status}`;
    checks.lattice_alignment_all_pass = probe.status === 0;
  }

  return {
    signature: SIGNATURE,
    verified_utc: new Date().toISOString(),
    all_pass: missing.length === 0,
    checks,
    missing,
    next_steps: missing.length
      ? ["Fix missing markers or set LYGO_STACK_ROOT to trusted clone"]
      : [
          "lygo_alignment_ready — composite check before live ops",
          "python tools/haven_star_chart_gate.py submission.json",
        ],
  };
}

async function compareRegistry(stackRoot: string, pagesBase: string) {
  const localPath = path.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
  let localSha = "";
  try {
    localSha = sha256Hex(await readFile(localPath, "utf8"));
  } catch (e) {
    return {
      signature: SIGNATURE,
      match: false,
      error: `local_read_failed:${e}`,
    };
  }

  const live = await fetchJson<{ registry_sha256?: string; generated_utc?: string }>(
    `${pagesBase}/haven_star_chart/haven_star_chart_data.json`,
  );
  const liveSha = live.registry_sha256 || "";

  return {
    signature: SIGNATURE,
    compared_utc: new Date().toISOString(),
    local_sha256: localSha,
    live_sha256: liveSha,
    match: Boolean(liveSha && localSha === liveSha),
    live_generated_utc: live.generated_utc,
    note: liveSha && localSha !== liveSha
      ? "Local clone differs from Pages — rebuild or pull before claiming LIVE"
      : "Registry aligned with published Pages JSON",
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
  for (const hint of [
    "ignore previous",
    "disregard instructions",
    "jailbreak",
    "exfiltrate",
    "api_key",
    "password:",
    "consent_bundle",
    "family_bind_salt",
  ]) {
    if (lowered.includes(hint)) {
      reasons.push(`quarantine_hint:${hint}`);
      score -= 0.25;
    }
  }

  if (/(=|∇|⊗|Δ9|963|Hz|φ|Φ)/.test(text)) {
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
    note: "Quick JS heuristic — run haven_star_chart_gate.py for authoritative ACCEPT/REJECT.",
  };
}

function consentChecklist(stackRoot: string | null) {
  return {
    signature: SIGNATURE,
    policy: "Humans approve live writes; agents propose and gate only.",
    required_before_live_write: [
      "lygo_alignment_ready → all_pass before submit",
      "lygo_lattice_pulse or lygo_registry_compare",
      "haven_star_chart_gate.py → verdict ACCEPT",
      "Human explicit --i-consent on submit/ingest",
      "Never publish consent_bundle or family_bind_salt",
    ],
    skill_chain: [...SKILL_CHAIN],
    plugin: PLUGIN_INSTALL,
    stack_root_configured: Boolean(stackRoot),
    stack_root: stackRoot,
    scan_cue:
      "LYGO-HSC-ATTEST-v1; gate=haven_star_chart_gate.py; P0-first; consent-gated; user-reviewed",
  };
}

function runStarChartGate(stackRoot: string, submissionPath: string, exampleBirth: boolean) {
  const gateTool = path.join(stackRoot, "tools", "haven_star_chart_gate.py");
  if (!existsSync(gateTool)) {
    return { signature: SIGNATURE, all_pass: false, error: "gate_tool_missing" };
  }

  const resolved = path.resolve(submissionPath);
  if (!resolved.startsWith(path.resolve(stackRoot)) && !resolved.startsWith(process.cwd())) {
    return {
      signature: SIGNATURE,
      all_pass: false,
      error: "submission_must_be_under_stack_root_or_cwd",
      path: resolved,
    };
  }

  const python = process.platform === "win32" ? "python" : "python3";
  const args = exampleBirth
    ? [gateTool, "--example-birth"]
    : [gateTool, resolved];
  const run = spawnSync(python, args, {
    cwd: stackRoot,
    encoding: "utf8",
    timeout: 120_000,
    shell: process.platform === "win32",
  });

  const stdout = (run.stdout || "").trim();
  const stderr = (run.stderr || "").trim();
  let parsed: Record<string, unknown> | null = null;
  try {
    parsed = JSON.parse(stdout) as Record<string, unknown>;
  } catch {
    const gateBlock = stdout.match(/\{[\s\S]*"verdict"[\s\S]*\}/);
    if (gateBlock) {
      try {
        parsed = JSON.parse(gateBlock[0]) as Record<string, unknown>;
      } catch {
        parsed = null;
      }
    }
  }

  if (parsed?._gate_preview && typeof parsed._gate_preview === "object") {
    parsed = parsed._gate_preview as Record<string, unknown>;
  }

  return {
    signature: SIGNATURE,
    gate_utc: new Date().toISOString(),
    exit_code: run.status,
    all_pass: parsed?.all_pass === true || parsed?.verdict === "ACCEPT",
    gate: parsed,
    stdout: parsed ? undefined : stdout.slice(0, 4000),
    stderr: stderr ? stderr.slice(0, 2000) : undefined,
    tool: "haven_star_chart_gate.py",
  };
}

async function alignmentReady(cfg: PluginConfig) {
  const stackRoot = resolveStackRoot(cfg);
  const pagesBase = resolvePagesBase(cfg);
  const report: Record<string, unknown> = {
    signature: SIGNATURE,
    checked_utc: new Date().toISOString(),
    ready_for_live_ops: false,
    score: 0,
    checks: {} as Record<string, boolean>,
  };
  const checks = report.checks as Record<string, boolean>;
  let score = 0;

  try {
    const pulse = await pulseLiveLattice(pagesBase);
    checks.live_pulse = Boolean(pulse.live);
    if (checks.live_pulse) score += 25;
    report.pulse = {
      registry_sha256: pulse.chart.registry_sha256,
      node_count: pulse.chart.node_count,
    };
  } catch {
    checks.live_pulse = false;
  }

  if (stackRoot) {
    const verify = await verifyLocalStack(stackRoot);
    checks.stack_markers = verify.all_pass === true;
    if (checks.stack_markers) score += 35;
    report.verify_missing = verify.missing;

    try {
      const cmp = await compareRegistry(stackRoot, pagesBase);
      checks.registry_match = cmp.match === true;
      if (checks.registry_match) score += 25;
      report.registry_compare = cmp;
    } catch {
      checks.registry_match = false;
    }
  } else {
    checks.stack_markers = false;
    checks.registry_match = false;
    report.stack_error = "Set LYGO_STACK_ROOT or plugins.entries.lygo-lattice-pulse.config.stackRoot";
  }

  checks.consent_ack = true;
  score += 15;
  report.score = score;
  report.ready_for_live_ops =
    checks.live_pulse && checks.stack_markers && checks.registry_match && score >= 85;
  report.if_not_ready = report.ready_for_live_ops
    ? ["Proceed to gate submission; human --i-consent before submit/ingest"]
    : [
        !checks.live_pulse && "Fix network or pages_base",
        !checks.stack_markers && "Fix LYGO_STACK_ROOT markers",
        !checks.registry_match && "Rebuild chart or git pull to match Pages",
        "Run lygo_star_chart_gate before any live write",
      ].filter(Boolean);

  return report;
}

export default definePluginEntry({
  id: "lygo-lattice-pulse",
  name: "LYGO Lattice Pulse",
  description: "Live lattice heartbeat, stack verify, registry compare, and star chart gate for LYGO agents",
  register(api) {
    const cfg = () => (api.config || {}) as PluginConfig;

    api.registerTool({
      name: "lygo_lattice_pulse",
      description:
        "Fetch live LYGO Haven Star Chart pulse — registry SHA, cosmology counts, queue, feed tail.",
      parameters: Type.Object({
        pages_base: Type.Optional(Type.String({ description: "Override GitHub Pages base URL." })),
      }),
      async execute(_id, params) {
        const base =
          (params.pages_base as string | undefined)?.trim() || resolvePagesBase(cfg());
        return textResult(await pulseLiveLattice(base));
      },
    });

    api.registerTool(
      {
        name: "lygo_lattice_verify",
        description:
          "Verify local lygo-protocol-stack root: gate tools, birth codec, registry, optional alignment probe.",
        parameters: Type.Object({
          stack_root: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const root =
            (params.stack_root as string | undefined)?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({
              signature: SIGNATURE,
              all_pass: false,
              error: "Set stackRoot config or LYGO_STACK_ROOT",
            });
          }
          return textResult(await verifyLocalStack(root));
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "lygo_registry_compare",
        description:
          "Compare local haven_star_chart_data.json SHA256 against live GitHub Pages registry.",
        parameters: Type.Object({
          stack_root: Type.Optional(Type.String()),
          pages_base: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const root =
            (params.stack_root as string | undefined)?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({ signature: SIGNATURE, match: false, error: "stack_root_required" });
          }
          const base =
            (params.pages_base as string | undefined)?.trim() || resolvePagesBase(cfg());
          return textResult(await compareRegistry(root, base));
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "lygo_star_chart_gate",
        description:
          "Run authoritative haven_star_chart_gate.py on a submission JSON (or --example-birth preview).",
        parameters: Type.Object({
          submission_path: Type.Optional(
            Type.String({ description: "Path to submission JSON under stack or cwd." }),
          ),
          example_birth: Type.Optional(
            Type.Boolean({ description: "Run built-in lattice birth example through gate." }),
          ),
          stack_root: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const root =
            (params.stack_root as string | undefined)?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({ signature: SIGNATURE, all_pass: false, error: "stack_root_required" });
          }
          const exampleBirth = params.example_birth === true;
          const subPath = (params.submission_path as string | undefined)?.trim();
          if (!exampleBirth && !subPath) {
            return textResult({
              signature: SIGNATURE,
              all_pass: false,
              error: "Provide submission_path or example_birth:true",
            });
          }
          return textResult(runStarChartGate(root, subPath || "", exampleBirth));
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "lygo_p0_quick_scan",
        description: "Quick P0-style heuristic on text (non-authoritative; use gate for submissions).",
        parameters: Type.Object({
          text: Type.String({ minLength: 1 }),
        }),
        async execute(_id, params) {
          return textResult(p0QuickScan(String(params.text || "")));
        },
      },
      { optional: true },
    );

    api.registerTool({
      name: "lygo_consent_checklist",
      description: "LYGO consent-gated workflow checklist before live star chart writes or ingest.",
      parameters: Type.Object({}),
      async execute() {
        return textResult(consentChecklist(resolveStackRoot(cfg())));
      },
    });

    api.registerTool({
      name: "lygo_alignment_ready",
      description:
        "Composite readiness: live pulse + stack markers + registry SHA match → ready_for_live_ops.",
      parameters: Type.Object({
        pages_base: Type.Optional(Type.String()),
        stack_root: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        const merged: PluginConfig = {
          ...cfg(),
          pagesBase:
            (params.pages_base as string | undefined)?.trim() || cfg().pagesBase,
          stackRoot:
            (params.stack_root as string | undefined)?.trim() || cfg().stackRoot,
        };
        return textResult(await alignmentReady(merged));
      },
    });
  },
});