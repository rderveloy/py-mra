# Licensing FAQ

Plain-language guidance for figuring out whether what you want to do
with py-mra is covered by AGPL or whether you need a commercial license.

**This document is informational. The [LICENSE](./LICENSE) file is the
legally controlling document.** If your situation doesn't fit any of the
cases below, email
[pymra.step200@aleeas.com](mailto:pymra.step200@aleeas.com) and we'll
give you a written answer.

## The four common use shapes

**1. You're using py-mra locally, you're not distributing software, and
you're not running a public service.** This is most academic research,
hobby projects, internal tools, and evaluation. AGPL's obligations are
gated on *distribution* or *network use*, not on use itself — so this
case triggers nothing. You owe nothing, you don't need a commercial
license, and you don't need to release anything.

**2. You're publishing software that uses py-mra (a GitHub repo
alongside a paper, an open-source library, a public tool).** This is
distribution. AGPL's share-alike applies — your software must be
licensed under AGPL too. For most academic and OSS releases this is
what you wanted to do anyway, so it's not a friction point.

**3. You're running a public service or hosted product that uses
py-mra.** AGPL §13 triggers: users of your service must be offered the
service's source code. If you're using py-mra unmodified, this is
trivial — link the upstream repository. If you modified py-mra, the
modifications must be published under AGPL too.

**4. You're distributing a closed-source binary or running a service
whose source you can't share.** This is the case the commercial license
exists for. Email
[pymra.step200@aleeas.com](mailto:pymra.step200@aleeas.com).

## Specific situations that come up

### "I'm a PhD student"

You're almost certainly in case (1) or case (2) above. AGPL is one of
the more academic-friendly licenses out there because the dominant
research pattern (run it locally, write a paper) generates no
obligation at all, and publishing analysis code under AGPL alongside a
paper is usually what people wanted to do anyway.

If you spin out your research into a startup, that's the moment to
have a conversation about a commercial license — not before.

### "My research project became a startup"

The transition is handled by switching to the commercial license track
for the commercial product, while the original research code can keep
living under AGPL.

Note that the existing AGPL-licensed versions of py-mra remain AGPL
forever — see the "Old versions" section below. So your earlier
academic-use commitments don't need to be revisited, just your
forward-looking commercial use.

### "I work for a company and want to use py-mra at work"

It depends what you're doing with it. If you're running internal
analysis on your own machine or a private server, that's case (1) — no
obligation. If you're embedding it in a product the company sells, or
exposing it as a service to your customers, that's case (3) or (4) —
you need either AGPL compliance (publishing source) or a commercial
license.

When in doubt, ask your legal team, or email us; both paths are valid.

### "I'm running a small hosted demo / Hugging Face Space / Streamlit
app"

This is case (3) — §13 obligations apply. With stock py-mra, compliance
is just linking the upstream repository from your service. With
modifications, those modifications need to be published.

### "I want to embed py-mra in a proprietary product I sell"

That's the canonical case for a commercial license. Email
[pymra.step200@aleeas.com](mailto:pymra.step200@aleeas.com).

## Old versions stay AGPL forever

If you adopt py-mra at version *X* under AGPL and we later release
version *Y* under different terms, **your right to keep using version
*X* under AGPL doesn't go away.** That's how AGPL works — published
under AGPL means published under AGPL, permanently. Forking, packaging,
mirroring, and modifying *that version* remain available to you under
AGPL forever.

What changes for a relicensed *future* version is the terms you'd take
*it* under. You're never forced to upgrade.

## What does the commercial track actually offer?

The commercial license is not just "the AGPL escape hatch." It is a
product, and the things it bundles are what you're paying for:

- **Use in proprietary software** without AGPL's source-sharing
  requirements.
- **Maintainer-provided support** — direct contact for bug reports,
  guidance, and integration questions.
- **Indemnification** typical of commercial software licenses, so the
  customer is not exposed to infringement risk from py-mra's
  dependencies or development history.
- **Access to future versions and bugfix releases** for the duration
  of the license.
- **Use of the project name and identity** in your product's
  attribution materials.

A clean-room or AI-assisted reimplementation (see
[AI_USAGE.md](./AI_USAGE.md)) cannot replicate any of these.

## When in doubt

Email
[pymra.step200@aleeas.com](mailto:pymra.step200@aleeas.com). A quick
question now is much cheaper than a license dispute later, and we are
genuinely happy to talk through ambiguous cases.
