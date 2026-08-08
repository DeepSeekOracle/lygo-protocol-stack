import { Type } from "typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import {
  CLAIM_KINDS,
  handoffMarkdown,
  runDemo,
  sealCapsule,
  SIG,
  type Claim,
  verifyCapsule,
} from "./continuum_core.js";

const PLUGIN_INSTALL = "openclaw plugins install clawhub:@deepseekoracle/lygo-continuum";
const PORTAL = "https://chatagent.ca/lygo-continuum.html";

type PluginConfig = {
  defaultBase?: string;
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

function resolveBase(cfg: PluginConfig, paramBase?: string): string | null {
  const b = (paramBase || cfg.defaultBase || process.env.LYGO_CONTINUUM_BASE || "").trim();
  return b ? path.resolve(b) : process.cwd();
}

function loadCapsule(capsule_json?: string, capsule_path?: string): Record<string, unknown> {
  if (capsule_json && capsule_json.trim()) {
    return JSON.parse(capsule_json) as Record<string, unknown>;
  }
  if (capsule_path && capsule_path.trim()) {
    const p = path.resolve(capsule_path.trim());
    if (p.includes("..") || p.length > 512) throw new Error("unsafe capsule_path");
    if (!existsSync(p)) throw new Error(`capsule_path missing: ${p}`);
    return JSON.parse(readFileSync(p, "utf8")) as Record<string, unknown>;
  }
  throw new Error("Provide capsule_json or capsule_path");
}

function parseClaims(claims_json: string): Claim[] {
  const raw = JSON.parse(claims_json);
  if (Array.isArray(raw)) return raw as Claim[];
  if (raw && typeof raw === "object" && Array.isArray((raw as { claims?: unknown }).claims)) {
    return (raw as { claims: Claim[] }).claims;
  }
  throw new Error("claims_json must be an array or {claims:[]}");
}

export default definePluginEntry({
  id: "lygo-continuum",
  name: "LYGO Continuum",
  description:
    "Falsifiable work capsules for OpenClaw agents: seal done-claims, re-verify, detect drift, handoff packs. Pure local — no network, no subprocess.",
  register(api) {
    const cfg = () => (api.config || {}) as PluginConfig;

    api.registerTool({
      name: "lygo_continuum_kinds",
      description: "List Continuum claim kinds and plugin signature.",
      parameters: Type.Object({}),
      async execute() {
        return textResult({
          signature: SIG,
          kinds: [...CLAIM_KINDS],
          portal: PORTAL,
          install: PLUGIN_INSTALL,
          policy: "Agents must not claim done unless lygo_continuum_preflight_done returns can_claim_done:true",
        });
      },
    });

    api.registerTool({
      name: "lygo_continuum_seal",
      description:
        "Seal falsifiable claims into a Continuum capsule. Auto-fills file_sha256 expect when omitted. Returns capsule JSON with root_hash and sealed_results.",
      parameters: Type.Object({
        claims_json: Type.String({
          description: 'JSON array of claims, e.g. [{"kind":"file_exists","path":"a.py"}]',
        }),
        task_summary: Type.String({ description: "Human-readable task summary" }),
        agent: Type.Optional(Type.String()),
        base: Type.Optional(Type.String({ description: "Base dir for relative claim paths" })),
        decisions_json: Type.Optional(Type.String({ description: "JSON string array of decisions" })),
        next_actions_json: Type.Optional(Type.String({ description: "JSON string array of next actions" })),
      }),
      async execute(_id, params) {
        try {
          const claims = parseClaims(String(params.claims_json));
          const decisions = params.decisions_json
            ? (JSON.parse(String(params.decisions_json)) as string[])
            : [];
          const next_actions = params.next_actions_json
            ? (JSON.parse(String(params.next_actions_json)) as string[])
            : [];
          const base = resolveBase(cfg(), params.base as string | undefined);
          const capsule = sealCapsule({
            claims,
            task_summary: String(params.task_summary),
            agent: (params.agent as string) || "openclaw",
            decisions: Array.isArray(decisions) ? decisions : [],
            next_actions: Array.isArray(next_actions) ? next_actions : [],
            base,
          });
          return textResult(capsule);
        } catch (e) {
          return textResult({ ok: false, error: String(e), signature: SIG });
        }
      },
    });

    api.registerTool({
      name: "lygo_continuum_verify",
      description:
        "Re-verify a Continuum capsule against the current filesystem. Returns integrity_ok, claims_ok, drift, pass/fail.",
      parameters: Type.Object({
        capsule_json: Type.Optional(Type.String()),
        capsule_path: Type.Optional(Type.String()),
        base: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        try {
          const capsule = loadCapsule(
            params.capsule_json as string | undefined,
            params.capsule_path as string | undefined,
          );
          const base = resolveBase(cfg(), params.base as string | undefined);
          return textResult(verifyCapsule(capsule, base));
        } catch (e) {
          return textResult({ ok: false, error: String(e), signature: SIG });
        }
      },
    });

    api.registerTool({
      name: "lygo_continuum_drift",
      description:
        "Verify capsule and return a slim drift report (what changed since seal).",
      parameters: Type.Object({
        capsule_json: Type.Optional(Type.String()),
        capsule_path: Type.Optional(Type.String()),
        base: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        try {
          const capsule = loadCapsule(
            params.capsule_json as string | undefined,
            params.capsule_path as string | undefined,
          );
          const base = resolveBase(cfg(), params.base as string | undefined);
          const report = verifyCapsule(capsule, base);
          return textResult({
            ok: report.ok,
            drift_count: report.drift_count,
            drift: report.drift,
            pass: report.pass,
            fail: report.fail,
            total: report.total,
            integrity_ok: report.integrity_ok,
            capsule_id: report.capsule_id,
            verified_utc: report.verified_utc,
            signature: SIG,
          });
        } catch (e) {
          return textResult({ ok: false, error: String(e), signature: SIG });
        }
      },
    });

    api.registerTool({
      name: "lygo_continuum_handoff",
      description:
        "Emit a markdown handoff pack (claims + decisions + optional live verify + embedded capsule JSON) for the next agent or human.",
      parameters: Type.Object({
        capsule_json: Type.Optional(Type.String()),
        capsule_path: Type.Optional(Type.String()),
        base: Type.Optional(Type.String()),
        verify: Type.Optional(Type.Boolean({ description: "Include live verify status (default true)" })),
      }),
      async execute(_id, params) {
        try {
          const capsule = loadCapsule(
            params.capsule_json as string | undefined,
            params.capsule_path as string | undefined,
          );
          const doVerify = params.verify !== false;
          const base = resolveBase(cfg(), params.base as string | undefined);
          const report = doVerify ? verifyCapsule(capsule, base) : null;
          return textResult(handoffMarkdown(capsule, report));
        } catch (e) {
          return textResult({ ok: false, error: String(e), signature: SIG });
        }
      },
    });

    api.registerTool({
      name: "lygo_continuum_preflight_done",
      description:
        "BEFORE claiming work is done: seal claims and require all pass. Returns can_claim_done true only if sealed_ok. Agents must call this instead of asserting done in prose.",
      parameters: Type.Object({
        claims_json: Type.String(),
        task_summary: Type.String(),
        base: Type.Optional(Type.String()),
        agent: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        try {
          const claims = parseClaims(String(params.claims_json));
          const base = resolveBase(cfg(), params.base as string | undefined);
          const capsule = sealCapsule({
            claims,
            task_summary: String(params.task_summary),
            agent: (params.agent as string) || "openclaw",
            base,
          });
          const sealed_ok = capsule.sealed_ok === true;
          const verify = verifyCapsule(capsule, base);
          return textResult({
            can_claim_done: sealed_ok && verify.ok === true,
            sealed_ok,
            verify_ok: verify.ok,
            sealed_pass: capsule.sealed_pass,
            sealed_fail: capsule.sealed_fail,
            total: verify.total,
            fail_results: (verify.results as { ok: boolean; id: string; detail: string }[]).filter(
              (r) => !r.ok,
            ),
            capsule_id: capsule.id,
            root_hash: capsule.root_hash,
            capsule,
            policy:
              "If can_claim_done is false, do NOT tell the user the task is done. Fix files or claims first.",
            signature: SIG,
            portal: PORTAL,
          });
        } catch (e) {
          return textResult({
            can_claim_done: false,
            ok: false,
            error: String(e),
            signature: SIG,
          });
        }
      },
    });

    api.registerTool({
      name: "lygo_continuum_demo",
      description:
        "Self-contained demo: seal → verify HOLDS → tamper → drift. No network. Returns ok:true if engine works.",
      parameters: Type.Object({}),
      async execute() {
        return textResult(runDemo());
      },
    });
  },
});
