import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

const GATE_VERSION = "1.2.0-preview";
const SCAN_CUE_MARKERS = ["LYGO-HSC-ATTEST-v1", "HAVEN-STAR-CHART-GATE", "Aligned to LYGO"];
const VALID_KINDS = new Set([
  "seal",
  "champion",
  "lattice",
  "portal",
  "champion_egg",
  "joy_loop_egg",
  "node",
]);
const ID_RE =
  /^(SEAL_\d{3,}|GAB_SEAL_\d{3}|CHAMPION_[A-Z0-9_]+|LATTICE_[A-Z0-9_]+|PORTAL_[A-Z0-9_]+|CHAMPION_EGG_[A-Z0-9_]+|JOY_[A-Z0-9_]+|NODE_LYGO_[A-F0-9]{8}|NODE_[A-Z0-9_]+)$/;
const MATH_MARKERS = /(=|×|·|∇|⊗|∣|\||\+|−|-|φ|Φ|Δ|Ω|∞|√|∑|Hz|hz|963|528|432|1111|1440|741|8787|BPM|bpm|∅|⟩|⟨)/;
const HARMONIC_NUMBERS = [963, 528, 432, 1111, 1440, 741, 8787, 122, 0];
const FORBIDDEN_SUBMITTER = new Set(["human_direct", "human", "browser_form", "anonymous"]);

export function loadRegistryIds(stackRoot: string): Set<string> {
  const ids = new Set(["SEAL_000", "GAB_SEAL_000"]);
  const dataPath = path.join(stackRoot, "docs/haven_star_chart/haven_star_chart_data.json");
  try {
    const doc = JSON.parse(readFileSync(dataPath, "utf8")) as { nodes?: { id?: string }[] };
    for (const n of doc.nodes || []) {
      if (n.id) ids.add(String(n.id).toUpperCase());
    }
  } catch {
    /* registry optional for preview */
  }
  const accepted = path.join(stackRoot, "data/haven_star_chart/submissions/accepted");
  try {
    for (const name of readdirSync(accepted)) {
      if (!name.endsWith(".json")) continue;
      try {
        const row = JSON.parse(readFileSync(path.join(accepted, name), "utf8")) as {
          node?: { id?: string };
          id?: string;
        };
        const nid = (row.node || row).id;
        if (nid) ids.add(String(nid).toUpperCase());
      } catch {
        /* skip */
      }
    }
  } catch {
    /* accepted dir optional */
  }
  return ids;
}

function canonicalNodeBody(node: Record<string, unknown>): string {
  const tags = Array.isArray(node.tags)
    ? [...node.tags].map((t) => String(t).toUpperCase()).sort()
    : [];
  const conns = Array.isArray(node.connections)
    ? [...node.connections].map((c) => String(c)).sort()
    : [];
  const core: Record<string, unknown> = {
    id: node.id,
    kind: node.kind,
    name: node.name,
    equation: node.equation,
    glyph: node.glyph,
    tone: node.tone,
    tags,
    connections: conns,
    urls: node.urls || {},
    layer: node.layer,
  };
  if (node.lineage && typeof node.lineage === "object") {
    core.lineage = node.lineage;
  }
  return JSON.stringify(core, Object.keys(core).sort());
}

export function contentSha256(node: Record<string, unknown>): string {
  return createHash("sha256").update(canonicalNodeBody(node)).digest("hex");
}

export function mathResonanceScore(equation: string, tone: string): { score: number; reasons: string[] } {
  const reasons: string[] = [];
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
  if (eq.includes("Δ9") || tn.includes("Δ9") || eq.includes("963")) {
    score += 0.1;
    reasons.push("delta9_resonance");
  }
  return { score: Math.min(score, 1), reasons };
}

function checkAgentAttestation(sub: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (FORBIDDEN_SUBMITTER.has(String(sub.submitter_type || ""))) {
    errors.push("human_direct_forbidden_use_aligned_agent");
  }
  const att = (sub.agent_attestation || {}) as Record<string, unknown>;
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

export function validateSubmissionPreview(
  sub: Record<string, unknown>,
  registryIds: Set<string>,
): Record<string, unknown> {
  const errors: string[] = [];
  const warnings: string[] = [];

  const node = (sub.node || sub) as Record<string, unknown>;
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
    String(node.tone || ""),
  );
  if ((kind === "seal" || kind === "champion") && mscore < 0.35) {
    errors.push(`math_resonance_fail:score=${mscore.toFixed(2)}`);
  } else if (mscore < 0.25) {
    errors.push(`math_resonance_fail:score=${mscore.toFixed(2)}`);
  }

  const conns = (node.connections || []) as unknown[];
  if (!conns.length) errors.push("connections_empty_must_anchor_to_lattice");
  for (const c of conns) {
    const cs = String(c).trim().toUpperCase();
    if (!registryIds.has(cs) && cs !== "SEAL_000" && cs !== "GAB_SEAL_000") {
      errors.push(`unknown_connection:${cs}`);
    }
  }
  if (registryIds.has(nid) && !sub.supersedes) errors.push(`duplicate_id:${nid}`);

  const expected = sub.content_sha256 || (sub.agent_attestation as Record<string, unknown>)?.content_sha256;
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
    note: "JS preview only — run scripts/gate_submission.py for authoritative P0 + lineage gate.",
  };
}