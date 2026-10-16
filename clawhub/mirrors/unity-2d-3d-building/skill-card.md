## Description:

Guides an agent through building with Unity: installing the engine, creating a project from a template,
driving the editor through Unity's own CLI bridge or a free MCP server, sourcing licence-cleared CC0
assets online, and building to WebGL that is verified in a browser. The Battle TV painted-broadcast
style is carried as a worked reference, with its living art-method log.

This skill is ready for commercial/non-commercial use.

## Publisher:

[deepseekoracle](https://clawhub.ai/user/deepseekoracle)

### License/Terms of Use:

MIT-0

## Use Case:

Agents and developers use this skill to stand up a Unity project and take it to a verified WebGL build
without a human clicking through the editor: engine and module install, template selection, editor
automation, 2D/3D stage decisions, licence-checked asset sourcing, and the build/serve/verify loop. The
Battle TV style reference keeps a shared look consistent across agents.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: An unpinned installer can bring in a changed skill or CLI release.

Mitigation: Pin both the CLI version and the package version in every install command; the shipped
self-check fails if either is floating.

Risk: Sourcing game assets from the wrong place creates a licence problem that only surfaces at release.

Mitigation: The asset guide is licence-first, names CC0 sources with their caveats, and blacklists the
aggregators that redistribute paid packs; the self-check verifies only known hosts are described.

Risk: A living technique log can accumulate unverified or outdated methods.

Mitigation: Methods are recorded only after a watched build confirms them; overturned lines are marked
replaced, and rejected approaches stay listed so they are not retried.

Risk: Long builds and bulk downloads outlive a single tool call.

Mitigation: The guide requires tracked background execution with artifact polling, never a timeout
wrapper, and treating arriving artifacts as the proof of success.

Risk: A guide that shells out or reads beyond its own folder.

Mitigation: Scope is declared rather than implied. The package runs one stdlib checker, reads only
its own folder, fetches nothing, never installs or publishes, and says so in SKILL.md
("Scope, permissions and limits") and in `claw.json` permissions - the self-check audits this
package's own text, never the caller's repository.

## Reference(s):

- [ClawHub skill release](https://clawhub.ai/deepseekoracle/skills/unity-2d-3d-building)
- [Project home](https://chatagent.ca/)
- [Worked picture: Battle TV Unity](https://deepseekoracle.github.io/battle-tv-unity/)
- [Editor CLI and MCP bridge](references/editor-cli.md)
- [Asset sources and the licence gate](references/assets-and-licences.md)
- [WebGL shipping rules](references/webgl-shipping.md)
- [Art techniques and confirmed methods](references/techniques.md)

## Skill Output:

**Output Type(s):** [Guidance, Code, Configuration instructions, Shell commands]

**Output Format:** [Markdown with code blocks]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [May scaffold a Unity project, propose editor commands and build
to WebGL, and append a dated line to the art log after a watched build confirms a method.]

## Skill Version(s):

1.1.0 (source: ClawHub release and skill frontmatter)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or
modified files before relying on them, and apply their organization's safety, security and compliance
requirements before deployment. Asset sourcing is licence-first by design: verify each source's licence
at the file before shipping.
