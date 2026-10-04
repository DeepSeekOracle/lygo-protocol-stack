# `docs/` - this kit's own documentation folder

`config/admin.json` maps this folder as a **search root** (`{kit}\docs`): it is where the console,
the limbs and an agent look for documents that belong to *this kit* rather than to the LYGO builder
key as a whole (that one lives at the key root's `docs/`).

What belongs here: the kit's own build notes and release records, module specs and handover
checklists, and any operator-facing instructions that travel with the console.

What does not: secrets, keys or credentials. This folder is inside the kit, and the kit is copied
and published - anything with a private key, a token or a password in it must live in the key root
and be referenced by path, never copied here.

The folder exists because a mapped root that does not resolve is a defect: the module strip's
Environment watch card reports exactly that (see `src/modules/lygo.envwatch/`).
