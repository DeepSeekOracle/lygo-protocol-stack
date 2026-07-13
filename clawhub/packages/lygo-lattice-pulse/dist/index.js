// src/index.ts
import { Type } from "typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { existsSync, readFileSync as readFileSync2 } from "node:fs";
import { readFile } from "node:fs/promises";
import path2 from "node:path";
import { createHash as createHash2 } from "node:crypto";

// src/gate_preview.ts
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
var GATE_VERSION = "1.2.0-preview";
var SCAN_CUE_MARKERS = ["LYGO-HSC-ATTEST-v1", "HAVEN-STAR-CHART-GATE", "Aligned to LYGO"];
var VALID_KINDS = /* @__PURE__ */ new Set([
  "seal",
  "champion",
  "lattice",
  "portal",
  "champion_egg",
  "joy_loop_egg",
  "node"
]);
var ID_RE = /^(SEAL_\d{3,}|GAB_SEAL_\d{3}|CHAMPION_[A-Z0-9_]+|LATTICE_[A-Z0-9_]+|PORTAL_[A-Z0-9_]+|CHAMPION_EGG_[A-Z0-9_]+|JOY_[A-Z0-9_]+|NODE_LYGO_[A-F0-9]{8}|NODE_[A-Z0-9_]+)$/;
var MATH_MARKERS = /(=|×|·|∇|⊗|∣|\||\+|−|-|φ|Φ|Δ|Ω|∞|√|∑|Hz|hz|963|528|432|1111|1440|741|8787|BPM|bpm|∅|⟩|⟨)/;
var HARMONIC_NUMBERS = [963, 528, 432, 1111, 1440, 741, 8787, 122, 0];
var FORBIDDEN_SUBMITTER = /* @__PURE__ */ new Set(["human_direct", "human", "browser_form", "anonymous"]);
function loadRegistryIds(stackRoot) {
  const ids = /* @__PURE__ */ new Set(["SEAL_000", "GAB_SEAL_000"]);
  const dataPath = path.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
  try {
    const doc = JSON.parse(readFileSync(dataPath, "utf8"));
    for (const n of doc.nodes || []) {
      if (n.id) ids.add(String(n.id).toUpperCase());
    }
  } catch {
  }
  const accepted = path.join(stackRoot, "data/haven_star_chart/submissions/accepted");
  try {
    for (const name of readdirSync(accepted)) {
      if (!name.endsWith(".json")) continue;
      try {
        const row = JSON.parse(readFileSync(path.join(accepted, name), "utf8"));
        const nid = (row.node || row).id;
        if (nid) ids.add(String(nid).toUpperCase());
      } catch {
      }
    }
  } catch {
  }
  return ids;
}
function canonicalNodeBody(node) {
  const tags = Array.isArray(node.tags) ? [...node.tags].map((t) => String(t).toUpperCase()).sort() : [];
  const conns = Array.isArray(node.connections) ? [...node.connections].map((c) => String(c)).sort() : [];
  const core = {
    id: node.id,
    kind: node.kind,
    name: node.name,
    equation: node.equation,
    glyph: node.glyph,
    tone: node.tone,
    tags,
    connections: conns,
    urls: node.urls || {},
    layer: node.layer
  };
  if (node.lineage && typeof node.lineage === "object") {
    core.lineage = node.lineage;
  }
  return JSON.stringify(core, Object.keys(core).sort());
}
function contentSha256(node) {
  return createHash("sha256").update(canonicalNodeBody(node)).digest("hex");
}
function mathResonanceScore(equation, tone) {
  const reasons = [];
  const eq = (equation || "").trim();
  const tn = (tone || "").trim();
  if (!eq) return { score: 0, reasons: ["equation_empty"] };
  if (eq.length < 3) return { score: 0, reasons: ["equation_too_short"] };
  if (!MATH_MARKERS.test(eq)) return { score: 0, reasons: ["equation_no_math_markers"] };
  let score = 0.45;
  reasons.push("math_markers_ok");
  for (const n of HARMONIC_NUMBERS) {
    if (eq.includes(String(n)) || tn.includes(String(n))) {
      score += 0.08;
      reasons.push(`harmonic_${n}`);
    }
  }
  if (/\d+\s*Hz/i.test(eq + tn)) {
    score += 0.1;
    reasons.push("hz_present");
  }
  if (eq.includes("\u03949") || tn.includes("\u03949") || eq.includes("963")) {
    score += 0.1;
    reasons.push("delta9_resonance");
  }
  return { score: Math.min(score, 1), reasons };
}
function checkAgentAttestation(sub) {
  const errors = [];
  if (FORBIDDEN_SUBMITTER.has(String(sub.submitter_type || ""))) {
    errors.push("human_direct_forbidden_use_aligned_agent");
  }
  const att = sub.agent_attestation || {};
  if (!att || !Object.keys(att).length) {
    errors.push("missing_agent_attestation");
    return errors;
  }
  if (!att.agent_id) errors.push("missing_agent_id");
  if (!att.skill_slug) errors.push("missing_skill_slug");
  const cue = String(att.scan_cue || "");
  if (!SCAN_CUE_MARKERS.some((m) => cue.toLowerCase().includes(m.toLowerCase()))) {
    errors.push("invalid_scan_cue");
  }
  if (att.local_gate_pass !== true) errors.push("local_gate_pass_not_true");
  if (att.gate_tool !== "haven_star_chart_gate.py") errors.push("wrong_gate_tool");
  return errors;
}
function validateSubmissionPreview(sub, registryIds) {
  const errors = [];
  const warnings = [];
  const node = sub.node || sub;
  if (!node || typeof node !== "object") {
    return { verdict: "REJECT", errors: ["missing_node_object"], authoritative: false };
  }
  const nid = String(node.id || "").trim().toUpperCase();
  const kind = String(node.kind || "seal").trim().toLowerCase();
  const name = String(node.name || "").trim();
  if (!nid) errors.push("missing_id");
  else if (!ID_RE.test(nid)) errors.push(`invalid_id_format:${nid}`);
  if (!VALID_KINDS.has(kind)) errors.push(`invalid_kind:${kind}`);
  if (!name || name.length < 2) errors.push("name_too_short");
  if (name.length > 120) errors.push("name_too_long");
  errors.push(...checkAgentAttestation(sub));
  const { score: mscore } = mathResonanceScore(
    String(node.equation || ""),
    String(node.tone || "")
  );
  if ((kind === "seal" || kind === "champion") && mscore < 0.35) {
    errors.push(`math_resonance_fail:score=${mscore.toFixed(2)}`);
  } else if (mscore < 0.25) {
    errors.push(`math_resonance_fail:score=${mscore.toFixed(2)}`);
  }
  const conns = node.connections || [];
  if (!conns.length) errors.push("connections_empty_must_anchor_to_lattice");
  for (const c of conns) {
    const cs = String(c).trim().toUpperCase();
    if (!registryIds.has(cs) && cs !== "SEAL_000" && cs !== "GAB_SEAL_000") {
      errors.push(`unknown_connection:${cs}`);
    }
  }
  if (registryIds.has(nid) && !sub.supersedes) errors.push(`duplicate_id:${nid}`);
  const expected = sub.content_sha256 || sub.agent_attestation?.content_sha256;
  const actual = contentSha256(node);
  if (expected && expected !== actual) errors.push("content_sha256_mismatch");
  const verdict = errors.length ? "REJECT" : "ACCEPT";
  return {
    verdict,
    all_pass: verdict === "ACCEPT",
    errors,
    warnings,
    math_resonance_score: mscore,
    content_sha256_computed: actual,
    gate_version: GATE_VERSION,
    gate_tool: "lygo-lattice-pulse-gate-preview",
    authoritative: false,
    note: "JS preview only \u2014 run scripts/gate_submission.py for authoritative P0 + lineage gate."
  };
}

// src/index.ts
var SIGNATURE = "\u03949\u03A6963-LYGO-LATTICE-PULSE-v1.2";
var DEFAULT_PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack";
var REQUIRED_STACK_MARKERS = [
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
  "protocol0_byte_entropy_filter/src/python/byte_entropy_filter.py"
];
var PLUGIN_INSTALL = "openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse";
var SKILL_CHAIN = [
  "lygo-protocol-stack-operator",
  "lygo-network-builder",
  "lygo-sovereign-super-skill",
  "lygo-haven-star-chart",
  "lygo-lattice-birth"
];
var AUTHORITATIVE_GATE_CMD = "python scripts/gate_submission.py <submission.json>  # from plugin dir; requires LYGO_STACK_ROOT";
var AUTHORITATIVE_ALIGN_CMD = "python tools/verify_lattice_alignment.py  # from stack root";
function textResult(payload) {
  return {
    content: [
      {
        type: "text",
        text: typeof payload === "string" ? payload : JSON.stringify(payload, null, 2)
      }
    ]
  };
}
function resolvePagesBase(cfg) {
  return (cfg?.pagesBase || DEFAULT_PAGES).replace(/\/+$/, "");
}
function resolveStackRoot(cfg) {
  const fromCfg = cfg?.stackRoot?.trim();
  if (fromCfg) return path2.resolve(fromCfg);
  const fromEnv = process.env.LYGO_STACK_ROOT?.trim();
  if (fromEnv) return path2.resolve(fromEnv);
  return null;
}
function rejectUnsafePath(p) {
  return /\.\.|[<>\"|?*]/.test(p) || p.length > 512;
}
function sha256Hex(data) {
  return createHash2("sha256").update(data).digest("hex");
}
async function fetchJson(url, timeoutMs = 2e4) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { "User-Agent": "LYGO-Lattice-Pulse/1.2" }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}
async function pulseLiveLattice(pagesBase) {
  const metaUrl = `${pagesBase}/haven_star_chart/haven_star_chart_meta.json`;
  const dataUrl = `${pagesBase}/haven_star_chart/haven_star_chart_data.json`;
  const queueUrl = `${pagesBase}/haven_star_chart/haven_star_chart_queue.json`;
  const feedUrl = `${pagesBase}/haven_star_chart/haven_star_chart_feed.json`;
  const [meta, data, queue, feed] = await Promise.all([
    fetchJson(metaUrl).catch((e) => ({ error: String(e) })),
    fetchJson(dataUrl).catch((e) => ({ error: String(e) })),
    fetchJson(queueUrl).catch((e) => ({ error: String(e) })),
    fetchJson(feedUrl).catch((e) => ({ error: String(e) }))
  ]);
  const cosmos = data.cosmos || {};
  const feedEntries = Array.isArray(feed.entries) ? feed.entries.slice(0, 8) : [];
  return {
    signature: SIGNATURE,
    pulse_utc: (/* @__PURE__ */ new Date()).toISOString(),
    pages_base: pagesBase,
    live: !data.error,
    meta,
    chart: {
      node_count: data.node_count,
      link_count: data.link_count,
      registry_sha256: data.registry_sha256,
      generated_utc: data.generated_utc,
      galaxy_count: cosmos.galaxy_count,
      nebula_count: cosmos.nebula_count,
      cluster_count: cosmos.cluster_count
    },
    queue,
    feed_tail: feedEntries,
    plugin: PLUGIN_INSTALL,
    skill_chain: [...SKILL_CHAIN],
    package: "clawhub:@deepseekoracle/lygo-lattice-pulse@1.2.0"
  };
}
async function verifyLocalStack(stackRoot) {
  const checks = {
    stack_root: stackRoot,
    exists: existsSync(stackRoot)
  };
  if (!checks.exists) {
    return { signature: SIGNATURE, all_pass: false, checks, errors: ["stack_root_missing"] };
  }
  const missing = [];
  for (const rel of REQUIRED_STACK_MARKERS) {
    const ok = existsSync(path2.join(stackRoot, rel));
    checks[rel] = ok;
    if (!ok) missing.push(rel);
  }
  try {
    const regPath = path2.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
    const raw = await readFile(regPath, "utf8");
    checks.local_registry_sha256 = sha256Hex(raw);
    checks.local_registry_sha16 = checks.local_registry_sha256.slice(0, 16);
  } catch {
    checks.local_registry_sha256 = false;
  }
  try {
    const skills = JSON.parse(
      readFileSync2(path2.join(stackRoot, "clawhub/skills.json"), "utf8")
    );
    checks.clawhub_skill_count = String(skills.skills?.length ?? 0);
    checks.clawhub_count_published = String(skills.count_published ?? 0);
  } catch {
    checks.clawhub_skill_count = "0";
  }
  const alignTool = path2.join(stackRoot, "tools", "verify_lattice_alignment.py");
  checks.lattice_alignment_probe = existsSync(alignTool) ? "deferred_no_subprocess" : "tool_missing";
  checks.lattice_alignment_authoritative = AUTHORITATIVE_ALIGN_CMD;
  return {
    signature: SIGNATURE,
    verified_utc: (/* @__PURE__ */ new Date()).toISOString(),
    all_pass: missing.length === 0,
    checks,
    missing,
    security_note: "Plugin v1.2+ uses read-only checks in-process; no child_process spawn.",
    next_steps: missing.length ? ["Fix missing markers or set LYGO_STACK_ROOT to trusted clone"] : [
      "lygo_alignment_ready \u2014 composite check before live ops",
      AUTHORITATIVE_GATE_CMD,
      AUTHORITATIVE_ALIGN_CMD
    ]
  };
}
async function compareRegistry(stackRoot, pagesBase) {
  const localPath = path2.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
  let localSha = "";
  try {
    localSha = sha256Hex(await readFile(localPath, "utf8"));
  } catch (e) {
    return {
      signature: SIGNATURE,
      match: false,
      error: `local_read_failed:${e}`
    };
  }
  const live = await fetchJson(
    `${pagesBase}/haven_star_chart/haven_star_chart_data.json`
  );
  const liveSha = live.registry_sha256 || "";
  return {
    signature: SIGNATURE,
    compared_utc: (/* @__PURE__ */ new Date()).toISOString(),
    local_sha256: localSha,
    live_sha256: liveSha,
    match: Boolean(liveSha && localSha === liveSha),
    live_generated_utc: live.generated_utc,
    note: liveSha && localSha !== liveSha ? "Local clone differs from Pages \u2014 rebuild or pull before claiming LIVE" : "Registry aligned with published Pages JSON"
  };
}
function p0QuickScan(text) {
  const bytes = Buffer.from(text, "utf8");
  const len = bytes.length;
  if (!len) {
    return { signature: SIGNATURE, verdict: "REJECT", score: 0, reasons: ["empty_payload"] };
  }
  const reasons = [];
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
    "family_bind_salt"
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
    note: "Quick JS heuristic \u2014 run scripts/gate_submission.py for authoritative ACCEPT/REJECT."
  };
}
function consentChecklist(stackRoot) {
  return {
    signature: SIGNATURE,
    policy: "Humans approve live writes; agents propose and gate only.",
    required_before_live_write: [
      "lygo_alignment_ready \u2192 all_pass before submit",
      "lygo_lattice_pulse or lygo_registry_compare",
      "scripts/gate_submission.py \u2192 verdict ACCEPT (authoritative)",
      "Human explicit --i-consent on submit/ingest",
      "Never publish consent_bundle or family_bind_salt"
    ],
    skill_chain: [...SKILL_CHAIN],
    plugin: PLUGIN_INSTALL,
    stack_root_configured: Boolean(stackRoot),
    stack_root: stackRoot,
    scan_cue: "LYGO-HSC-ATTEST-v1; gate=haven_star_chart_gate.py; P0-first; consent-gated; user-reviewed",
    authoritative_gate: AUTHORITATIVE_GATE_CMD
  };
}
function runStarChartGatePreview(stackRoot, submissionPath, exampleBirth) {
  if (exampleBirth) {
    return {
      signature: SIGNATURE,
      gate_utc: (/* @__PURE__ */ new Date()).toISOString(),
      all_pass: false,
      authoritative: false,
      preview_only: true,
      error: "example_birth_requires_authoritative_script",
      run: [
        `cd "${stackRoot}"`,
        "python tools/haven_star_chart_gate.py --example-birth",
        "# or: python <plugin>/scripts/gate_example_birth.py (bundled, no subprocess in plugin)"
      ],
      tool: "haven_star_chart_gate.py"
    };
  }
  const gateTool = path2.join(stackRoot, "tools", "haven_star_chart_gate.py");
  if (!existsSync(gateTool)) {
    return { signature: SIGNATURE, all_pass: false, error: "gate_tool_missing" };
  }
  if (rejectUnsafePath(submissionPath)) {
    return { signature: SIGNATURE, all_pass: false, error: "unsafe_submission_path" };
  }
  const resolved = path2.resolve(submissionPath);
  const stackResolved = path2.resolve(stackRoot);
  const cwdResolved = process.cwd();
  if (!resolved.startsWith(stackResolved + path2.sep) && !resolved.startsWith(cwdResolved + path2.sep) && resolved !== stackResolved && resolved !== cwdResolved) {
    return {
      signature: SIGNATURE,
      all_pass: false,
      error: "submission_must_be_under_stack_root_or_cwd",
      path: resolved
    };
  }
  if (!existsSync(resolved)) {
    return { signature: SIGNATURE, all_pass: false, error: "submission_file_missing", path: resolved };
  }
  let sub;
  try {
    sub = JSON.parse(readFileSync2(resolved, "utf8"));
  } catch (e) {
    return { signature: SIGNATURE, all_pass: false, error: `json_parse_failed:${e}` };
  }
  const registryIds = loadRegistryIds(stackRoot);
  const gate = validateSubmissionPreview(sub, registryIds);
  return {
    signature: SIGNATURE,
    gate_utc: (/* @__PURE__ */ new Date()).toISOString(),
    all_pass: gate.all_pass === true,
    gate,
    submission_path: resolved,
    tool: "lygo-lattice-pulse-gate-preview",
    authoritative_gate_command: AUTHORITATIVE_GATE_CMD
  };
}
async function alignmentReady(cfg) {
  const stackRoot = resolveStackRoot(cfg);
  const pagesBase = resolvePagesBase(cfg);
  const report = {
    signature: SIGNATURE,
    checked_utc: (/* @__PURE__ */ new Date()).toISOString(),
    ready_for_live_ops: false,
    score: 0,
    checks: {}
  };
  const checks = report.checks;
  let score = 0;
  try {
    const pulse = await pulseLiveLattice(pagesBase);
    checks.live_pulse = Boolean(pulse.live);
    if (checks.live_pulse) score += 25;
    report.pulse = {
      registry_sha256: pulse.chart.registry_sha256,
      node_count: pulse.chart.node_count
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
  report.ready_for_live_ops = checks.live_pulse && checks.stack_markers && checks.registry_match && score >= 85;
  report.if_not_ready = report.ready_for_live_ops ? ["Proceed to scripts/gate_submission.py; human --i-consent before submit/ingest"] : [
    !checks.live_pulse && "Fix network or pages_base",
    !checks.stack_markers && "Fix LYGO_STACK_ROOT markers",
    !checks.registry_match && "Rebuild chart or git pull to match Pages",
    "Run authoritative gate via scripts/gate_submission.py before any live write"
  ].filter(Boolean);
  return report;
}
var index_default = definePluginEntry({
  id: "lygo-lattice-pulse",
  name: "LYGO Lattice Pulse",
  description: "Live lattice heartbeat, stack verify, registry compare, and star chart gate preview for LYGO agents (SkillSpector-safe \u2014 no subprocess)",
  register(api) {
    const cfg = () => api.config || {};
    api.registerTool({
      name: "lygo_lattice_pulse",
      description: "Fetch live LYGO Haven Star Chart pulse \u2014 registry SHA, cosmology counts, queue, feed tail.",
      parameters: Type.Object({
        pages_base: Type.Optional(Type.String({ description: "Override GitHub Pages base URL." }))
      }),
      async execute(_id, params) {
        const base = params.pages_base?.trim() || resolvePagesBase(cfg());
        return textResult(await pulseLiveLattice(base));
      }
    });
    api.registerTool(
      {
        name: "lygo_lattice_verify",
        description: "Verify local lygo-protocol-stack root: gate tools, birth codec, registry (read-only; no subprocess).",
        parameters: Type.Object({
          stack_root: Type.Optional(Type.String())
        }),
        async execute(_id, params) {
          const root = params.stack_root?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({
              signature: SIGNATURE,
              all_pass: false,
              error: "Set stackRoot config or LYGO_STACK_ROOT"
            });
          }
          return textResult(await verifyLocalStack(root));
        }
      },
      { optional: true }
    );
    api.registerTool(
      {
        name: "lygo_registry_compare",
        description: "Compare local haven_star_chart_data.json SHA256 against live GitHub Pages registry.",
        parameters: Type.Object({
          stack_root: Type.Optional(Type.String()),
          pages_base: Type.Optional(Type.String())
        }),
        async execute(_id, params) {
          const root = params.stack_root?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({ signature: SIGNATURE, match: false, error: "stack_root_required" });
          }
          const base = params.pages_base?.trim() || resolvePagesBase(cfg());
          return textResult(await compareRegistry(root, base));
        }
      },
      { optional: true }
    );
    api.registerTool(
      {
        name: "lygo_star_chart_gate",
        description: "Gate preview on submission JSON (read-only JS). Authoritative P0+lineage: scripts/gate_submission.py.",
        parameters: Type.Object({
          submission_path: Type.Optional(
            Type.String({ description: "Path to submission JSON under stack or cwd." })
          ),
          example_birth: Type.Optional(
            Type.Boolean({ description: "Instructions for lattice birth example gate." })
          ),
          stack_root: Type.Optional(Type.String())
        }),
        async execute(_id, params) {
          const root = params.stack_root?.trim() || resolveStackRoot(cfg());
          if (!root) {
            return textResult({ signature: SIGNATURE, all_pass: false, error: "stack_root_required" });
          }
          const exampleBirth = params.example_birth === true;
          const subPath = params.submission_path?.trim();
          if (!exampleBirth && !subPath) {
            return textResult({
              signature: SIGNATURE,
              all_pass: false,
              error: "Provide submission_path or example_birth:true"
            });
          }
          return textResult(runStarChartGatePreview(root, subPath || "", exampleBirth));
        }
      },
      { optional: true }
    );
    api.registerTool(
      {
        name: "lygo_p0_quick_scan",
        description: "Quick P0-style heuristic on text (non-authoritative; use gate script for submissions).",
        parameters: Type.Object({
          text: Type.String({ minLength: 1 })
        }),
        async execute(_id, params) {
          return textResult(p0QuickScan(String(params.text || "")));
        }
      },
      { optional: true }
    );
    api.registerTool({
      name: "lygo_consent_checklist",
      description: "LYGO consent-gated workflow checklist before live star chart writes or ingest.",
      parameters: Type.Object({}),
      async execute() {
        return textResult(consentChecklist(resolveStackRoot(cfg())));
      }
    });
    api.registerTool({
      name: "lygo_alignment_ready",
      description: "Composite readiness: live pulse + stack markers + registry SHA match \u2192 ready_for_live_ops.",
      parameters: Type.Object({
        pages_base: Type.Optional(Type.String()),
        stack_root: Type.Optional(Type.String())
      }),
      async execute(_id, params) {
        const merged = {
          ...cfg(),
          pagesBase: params.pages_base?.trim() || cfg().pagesBase,
          stackRoot: params.stack_root?.trim() || cfg().stackRoot
        };
        return textResult(await alignmentReady(merged));
      }
    });
  }
});
export {
  index_default as default
};
