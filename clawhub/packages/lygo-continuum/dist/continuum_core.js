// src/continuum_core.ts
import { createHash, randomBytes } from "node:crypto";
import {
  existsSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync
} from "node:fs";
import os from "node:os";
import path from "node:path";
var SIG = "Delta9Phi963-CONTINUUM-v1.0.0";
var VERSION = "1.0.0";
var SCHEMA = "lygo.continuum.v1";
var CLAIM_KINDS = [
  "file_exists",
  "file_missing",
  "file_sha256",
  "file_contains",
  "file_not_contains",
  "line_count_gte",
  "line_count_eq",
  "bytes_gte",
  "bytes_eq",
  "glob_count_gte",
  "json_path_eq",
  "text_sha256",
  "regex_match",
  "regex_not_match"
];
function sha256Bytes(data) {
  return createHash("sha256").update(data).digest("hex");
}
function sha256Text(text) {
  return sha256Bytes(Buffer.from(text, "utf8"));
}
function sha256File(filePath) {
  return sha256Bytes(readFileSync(filePath));
}
function stableStringify(value) {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => stableStringify(v)).join(",")}]`;
  }
  const o = value;
  const keys = Object.keys(o).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(o[k])}`).join(",")}}`;
}
function rootHashOf(capsule) {
  const body = {};
  for (const k of Object.keys(capsule).sort()) {
    if (k === "root_hash" || k === "chain" || k === "last_verify") continue;
    body[k] = capsule[k];
  }
  return sha256Text(stableStringify(body));
}
function utcNow() {
  return (/* @__PURE__ */ new Date()).toISOString().replace(/\.\d{3}Z$/, "Z");
}
function newCapsuleId() {
  return "CONT-" + randomBytes(6).toString("hex").toUpperCase();
}
function resolvePath(pathStr, base) {
  if (path.isAbsolute(pathStr)) return path.resolve(pathStr);
  if (base) return path.resolve(base, pathStr);
  return path.resolve(pathStr);
}
function getJsonPath(data, dotted) {
  if (!dotted) return data;
  let cur = data;
  for (const part of dotted.split(".")) {
    if (cur == null) return void 0;
    if (Array.isArray(cur)) {
      const idx = Number(part);
      if (!Number.isInteger(idx) || idx < 0 || idx >= cur.length) return void 0;
      cur = cur[idx];
    } else if (typeof cur === "object") {
      const o = cur;
      if (!(part in o)) return void 0;
      cur = o[part];
    } else return void 0;
  }
  return cur;
}
function safeGlobCount(root, pattern) {
  if (pattern.includes("**") || pattern.includes("..") || pattern.length > 200) {
    return -1;
  }
  const parts = pattern.replace(/\\/g, "/").split("/");
  let dirs = [root];
  for (let i = 0; i < parts.length; i++) {
    const seg = parts[i];
    const isLast = i === parts.length - 1;
    const next = [];
    const rx = new RegExp(
      "^" + seg.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".") + "$"
    );
    for (const d of dirs) {
      let names = [];
      try {
        names = readdirSync(d);
      } catch {
        continue;
      }
      for (const name of names) {
        if (!rx.test(name)) continue;
        const full = path.join(d, name);
        let st;
        try {
          st = statSync(full);
        } catch {
          continue;
        }
        if (isLast) {
          if (st.isFile() || st.isDirectory()) next.push(full);
        } else if (st.isDirectory()) {
          next.push(full);
        }
      }
    }
    dirs = next;
  }
  return dirs.length;
}
function evaluateClaim(claim, base) {
  const kind = String(claim.kind || "").trim();
  const id = String(claim.id || "?");
  const out = {
    id,
    kind,
    ok: false,
    detail: "",
    observed: null,
    expected: null
  };
  if (!CLAIM_KINDS.includes(kind)) {
    out.detail = `unknown kind: ${kind}`;
    return out;
  }
  try {
    if (kind === "text_sha256") {
      const text2 = String(claim.text ?? "");
      const expect = String(claim.expect ?? claim.sha256 ?? "").toLowerCase();
      const got = sha256Text(text2);
      out.observed = got;
      out.expected = expect;
      out.ok = !!expect && got === expect;
      out.detail = out.ok ? "match" : "text hash mismatch";
      return out;
    }
    if (kind === "glob_count_gte") {
      const pattern = String(claim.pattern ?? claim.glob ?? "");
      if (!pattern) {
        out.detail = "missing pattern";
        return out;
      }
      const root = base || process.cwd();
      const n = Number(claim.n ?? claim.expect ?? 0);
      const count = safeGlobCount(root, pattern);
      if (count < 0) {
        out.detail = "unsafe or unsupported glob";
        return out;
      }
      out.observed = count;
      out.expected = n;
      out.ok = count >= n;
      out.detail = out.ok ? `found ${count} >= ${n}` : `found ${count} < ${n}`;
      return out;
    }
    const pathStr = claim.path || claim.file;
    if (!pathStr) {
      out.detail = "missing path";
      return out;
    }
    const filePath = resolvePath(String(pathStr), base);
    if (kind === "file_exists") {
      const ok = existsSync(filePath) && statSync(filePath).isFile();
      out.observed = ok;
      out.expected = true;
      out.ok = ok;
      out.detail = ok ? "exists" : `missing: ${filePath}`;
      return out;
    }
    if (kind === "file_missing") {
      const missing = !existsSync(filePath);
      out.observed = missing;
      out.expected = true;
      out.ok = missing;
      out.detail = missing ? "absent" : `still present: ${filePath}`;
      return out;
    }
    if (!existsSync(filePath) || !statSync(filePath).isFile()) {
      out.detail = `file not found: ${pathStr}`;
      return out;
    }
    if (kind === "file_sha256") {
      const expect = String(claim.expect ?? claim.sha256 ?? "").toLowerCase();
      const got = sha256File(filePath);
      out.observed = got;
      out.expected = expect;
      out.ok = !!expect && got === expect;
      out.detail = out.ok ? "hash match" : "hash mismatch";
      return out;
    }
    const raw = readFileSync(filePath);
    const text = raw.toString("utf8");
    if (kind === "file_contains") {
      const needle = String(claim.needle ?? claim.expect ?? "");
      out.expected = needle;
      out.observed = needle ? text.includes(needle) : false;
      out.ok = !!needle && text.includes(needle);
      out.detail = out.ok ? "contains" : "needle not found";
      return out;
    }
    if (kind === "file_not_contains") {
      const needle = String(claim.needle ?? claim.expect ?? "");
      const found = !!needle && text.includes(needle);
      out.expected = `NOT ${needle}`;
      out.observed = !found;
      out.ok = !!needle && !found;
      out.detail = out.ok ? "absent" : "needle present (fail)";
      return out;
    }
    if (kind === "line_count_gte") {
      const n = Number(claim.n ?? claim.expect ?? 0);
      const lines = text === "" ? 0 : text.split(/\r?\n/).length;
      out.observed = lines;
      out.expected = n;
      out.ok = lines >= n;
      out.detail = `${lines} >= ${n}`;
      return out;
    }
    if (kind === "line_count_eq") {
      const n = Number(claim.n ?? claim.expect ?? 0);
      const lines = text === "" ? 0 : text.split(/\r?\n/).length;
      out.observed = lines;
      out.expected = n;
      out.ok = lines === n;
      out.detail = `${lines} == ${n}`;
      return out;
    }
    if (kind === "bytes_gte") {
      const n = Number(claim.n ?? claim.expect ?? 0);
      out.observed = raw.length;
      out.expected = n;
      out.ok = raw.length >= n;
      out.detail = `${raw.length} >= ${n}`;
      return out;
    }
    if (kind === "bytes_eq") {
      const n = Number(claim.n ?? claim.expect ?? 0);
      out.observed = raw.length;
      out.expected = n;
      out.ok = raw.length === n;
      out.detail = `${raw.length} == ${n}`;
      return out;
    }
    if (kind === "json_path_eq") {
      const jpath = String(claim.jpath ?? claim.json_path ?? "");
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        out.detail = `invalid json: ${e}`;
        return out;
      }
      const got = getJsonPath(data, jpath);
      out.observed = got;
      out.expected = claim.expect;
      out.ok = stableStringify(got) === stableStringify(claim.expect);
      out.detail = out.ok ? "json path match" : `${jpath} mismatch`;
      return out;
    }
    if (kind === "regex_match" || kind === "regex_not_match") {
      const pattern = String(claim.pattern ?? claim.expect ?? "");
      if (!pattern || pattern.length > 500) {
        out.detail = "bad pattern";
        return out;
      }
      let rx;
      try {
        rx = new RegExp(pattern, "m");
      } catch (e) {
        out.detail = `bad regex: ${e}`;
        return out;
      }
      const found = rx.test(text);
      if (kind === "regex_match") {
        out.expected = true;
        out.observed = found;
        out.ok = found;
        out.detail = found ? "matched" : "no match";
      } else {
        out.expected = false;
        out.observed = found;
        out.ok = !found;
        out.detail = !found ? "no match (ok)" : "matched (fail)";
      }
      return out;
    }
    out.detail = `unhandled kind: ${kind}`;
    return out;
  } catch (e) {
    out.detail = `error: ${e instanceof Error ? e.message : String(e)}`;
    return out;
  }
}
function sealCapsule(opts) {
  const base = opts.base ?? null;
  const normalized = opts.claims.map((c, i) => {
    const cc = { ...c, id: c.id || `c${i + 1}` };
    if (cc.kind === "file_sha256" && !cc.expect && !cc.sha256) {
      const p = cc.path || cc.file;
      if (p) {
        const fp = resolvePath(String(p), base);
        if (existsSync(fp) && statSync(fp).isFile()) {
          cc.expect = sha256File(fp);
        }
      }
    }
    if (cc.kind === "text_sha256" && !cc.expect && cc.text != null) {
      cc.expect = sha256Text(String(cc.text));
    }
    return cc;
  });
  const capsule = {
    schema: SCHEMA,
    version: VERSION,
    signature: SIG,
    id: newCapsuleId(),
    created_utc: utcNow(),
    agent: opts.agent || "openclaw",
    task_summary: opts.task_summary,
    base_hint: base,
    decisions: opts.decisions || [],
    next_actions: opts.next_actions || [],
    claims: normalized,
    meta: opts.meta || {}
  };
  if (opts.evaluate_now !== false) {
    const sealed_results = normalized.map((c) => evaluateClaim(c, base));
    capsule.sealed_results = sealed_results;
    capsule.sealed_ok = sealed_results.every((r) => r.ok);
    capsule.sealed_pass = sealed_results.filter((r) => r.ok).length;
    capsule.sealed_fail = sealed_results.filter((r) => !r.ok).length;
  }
  capsule.root_hash = rootHashOf(capsule);
  capsule.chain = [
    {
      event: "seal",
      utc: capsule.created_utc,
      root_hash: capsule.root_hash,
      claim_count: normalized.length,
      sealed_ok: capsule.sealed_ok
    }
  ];
  return capsule;
}
function verifyCapsule(capsule, base) {
  const stored = String(capsule.root_hash || "");
  const recomputed = rootHashOf(capsule);
  const integrity_ok = stored === recomputed;
  let baseUse = base ?? null;
  if (!baseUse && capsule.base_hint) {
    baseUse = String(capsule.base_hint);
  }
  const claims = Array.isArray(capsule.claims) ? capsule.claims : [];
  const results = claims.map((c) => evaluateClaim(c, baseUse));
  const all_ok = results.length === 0 ? true : results.every((r) => r.ok);
  const pass_n = results.filter((r) => r.ok).length;
  const fail_n = results.filter((r) => !r.ok).length;
  const drift = [];
  const sealed = Array.isArray(capsule.sealed_results) ? capsule.sealed_results : [];
  const byId = new Map(sealed.map((r) => [r.id, r]));
  for (const r of results) {
    const prev = byId.get(r.id);
    if (!prev) continue;
    if (Boolean(prev.ok) !== Boolean(r.ok) || stableStringify(prev.observed) !== stableStringify(r.observed)) {
      drift.push({
        id: r.id,
        kind: r.kind,
        was_ok: prev.ok,
        now_ok: r.ok,
        was_observed: prev.observed,
        now_observed: r.observed,
        detail: r.detail
      });
    }
  }
  return {
    ok: integrity_ok && all_ok,
    integrity_ok,
    claims_ok: all_ok,
    pass: pass_n,
    fail: fail_n,
    total: results.length,
    drift_count: drift.length,
    drift,
    results,
    capsule_id: capsule.id,
    root_hash: stored,
    root_hash_recomputed: recomputed,
    verified_utc: utcNow(),
    signature: SIG,
    version: VERSION
  };
}
function handoffMarkdown(capsule, verifyReport) {
  const lines = [
    `# LYGO Continuum Handoff \u2014 ${capsule.id ?? "?"}`,
    "",
    `**Schema:** \`${capsule.schema}\` \xB7 **Root:** \`${String(capsule.root_hash || "").slice(0, 16)}\u2026\``,
    `**Agent:** ${capsule.agent} \xB7 **Sealed:** ${capsule.created_utc}`,
    `**Task:** ${capsule.task_summary}`,
    "",
    "## Claims (falsifiable)",
    ""
  ];
  for (const c of capsule.claims || []) {
    const pathHint = c.path || c.file || c.pattern || "(inline)";
    const expect = c.expect ?? c.needle ?? c.n ?? c.sha256 ?? "";
    lines.push(`- \`${c.id}\` **${c.kind}** \`${pathHint}\` \u2192 \`${expect}\``);
  }
  if (Array.isArray(capsule.decisions) && capsule.decisions.length) {
    lines.push("", "## Decisions", "");
    for (const d of capsule.decisions) lines.push(`- ${d}`);
  }
  if (Array.isArray(capsule.next_actions) && capsule.next_actions.length) {
    lines.push("", "## Next actions", "");
    for (const a of capsule.next_actions) lines.push(`- ${a}`);
  }
  if (verifyReport) {
    const status = verifyReport.ok ? "HOLDS" : "BROKEN / DRIFT";
    lines.push(
      "",
      `## Verify status: **${status}**`,
      `- pass ${verifyReport.pass}/${verifyReport.total} \xB7 drift ${verifyReport.drift_count}`,
      `- integrity: ${verifyReport.integrity_ok}`,
      `- at: ${verifyReport.verified_utc}`
    );
  }
  lines.push(
    "",
    "## Capsule JSON",
    "",
    "```json",
    JSON.stringify(capsule, null, 2),
    "```",
    "",
    "_Re-verify with lygo-continuum plugin tools or https://chatagent.ca/lygo-continuum.html_",
    "",
    `_${SIG}_`
  );
  return lines.join("\n");
}
function runDemo() {
  const td = mkdtempSync(path.join(os.tmpdir(), "lygo-continuum-"));
  try {
    writeFileSync(
      path.join(td, "app.py"),
      "# demo app\nSTATUS = 'ready'\ndef main():\n    return 42\n",
      "utf8"
    );
    writeFileSync(path.join(td, "out.json"), '{"status":"ok","score":0.99}\n', "utf8");
    writeFileSync(path.join(td, "README.md"), "# Continuum Demo\nDone claim sealed.\n", "utf8");
    const claims = [
      { id: "c1", kind: "file_exists", path: "app.py" },
      { id: "c2", kind: "file_sha256", path: "app.py" },
      { id: "c3", kind: "file_contains", path: "app.py", needle: "STATUS = 'ready'" },
      { id: "c4", kind: "json_path_eq", path: "out.json", jpath: "status", expect: "ok" },
      { id: "c5", kind: "line_count_gte", path: "README.md", n: 2 },
      { id: "c6", kind: "glob_count_gte", pattern: "*.py", n: 1 },
      {
        id: "c7",
        kind: "text_sha256",
        text: "portable witness",
        expect: sha256Text("portable witness")
      }
    ];
    const capsule = sealCapsule({
      claims,
      task_summary: "Demo: prove a mini project still holds",
      agent: "lygo-continuum-plugin-demo",
      decisions: ["node in-process only", "no network"],
      next_actions: ["hand off capsule"],
      base: td
    });
    const report = verifyCapsule(capsule, td);
    writeFileSync(path.join(td, "app.py"), "# demo app\nSTATUS = 'broken'\n", "utf8");
    const driftReport = verifyCapsule(capsule, td);
    return {
      ok: report.ok === true && driftReport.ok === false && Number(driftReport.drift_count) >= 1,
      signature: SIG,
      capsule_id: capsule.id,
      root_hash: capsule.root_hash,
      verify_holds: report.ok,
      after_tamper_ok: driftReport.ok,
      drift_count: driftReport.drift_count,
      message: "Continuum plugin demo: seal \u2192 verify HOLDS \u2192 tamper \u2192 drift"
    };
  } finally {
    try {
      rmSync(td, { recursive: true, force: true });
    } catch {
    }
  }
}
export {
  CLAIM_KINDS,
  SCHEMA,
  SIG,
  VERSION,
  evaluateClaim,
  handoffMarkdown,
  rootHashOf,
  runDemo,
  sealCapsule,
  sha256Text,
  stableStringify,
  verifyCapsule
};
