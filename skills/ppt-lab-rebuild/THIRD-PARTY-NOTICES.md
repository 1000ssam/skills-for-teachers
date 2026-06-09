# Third-Party Notices

ppt-lab incorporates design **specifications** and **design tokens** adapted from
third-party open-source projects. This file records those sources and their
licenses, as required by the MIT License.

ppt-lab distributes only *specifications of visual principles* (color relationships,
type scales, grids, component rules, "do / don't" guidance) and machine-readable
tokens. It does **not** redistribute any third party's original visual assets,
trademarks, logos, photography, or proprietary fonts.

---

## Design Diversity (design-pick)

- **Project:** Design Diversity
- **Repository:** https://github.com/epoko77-ai/design-diversity
- **License:** MIT
- **What ppt-lab uses:** Design-pack *specifications* (`prompt.md`) and *tokens*
  (`tokens.json`) are translated into ppt-lab's 3-axis SSOT
  (style × palette × layout). The MIT License of Design Diversity covers these
  specifications, tokens, and documentation only.
- **Scope note (from the upstream LICENSE):** the upstream MIT grant does **not**
  extend to original visual assets, trademarks, or proprietary design systems
  referenced by individual packs. Brand, firm, or institution names that appear
  in pack identifiers are **nominative references** describing the visual style a
  pack emulates — they do not imply endorsement, and no brand assets are copied.
  Proprietary fonts are replaced with open-licensed fonts; logos, wordmarks, and
  photography are represented by placeholders.

### Adapted looks (running log)

ppt-lab preserves **all 110 design-pick looks** as self-contained presets in the
`looks` section of `references/design-tokens.json`. Each look keeps its OWN colors,
fonts, and card treatment, translated deterministically from that pack's
`tokens.json` + `meta.yaml` (not from `prompt.md`, not pixel-measured). A look is
applied as one unit with `--look <slug>`, while the LAYOUT axis stays orthogonal.

- `_from` / `attribution` on every `looks.<slug>` entry records its upstream source and the MIT grant.
- The ppt-lab style axis (styles `house`, `myeongmungo`, `consulting`, `velis`)
  is unchanged; looks are additive.

> Fonts named by looks (Playfair Display, Archivo Black, Space Grotesk, IBM Plex
> Mono, Quicksand, Cormorant Garamond, etc.) are open-licensed (SIL OFL); install
> them for faithful rendering, else PowerPoint substitutes. Hangul always falls
> back to Pretendard. A few premium packs reference proprietary brand fonts
> (e.g. Hyundai Sans) which are NOT redistributed and will substitute on render.
>
> Korean serif faces used by the 12 serif looks via the `fonts.display` tier
> (covers/headings) and Hangul body text are all open-licensed:
> - **Song Myung** — SIL OFL 1.1 (Kang Min Koo / Google Fonts). High-contrast
>   display serif; used as the cover/heading face (`fonts.display.ea`) on all 12.
> - **MaruBuri** — Naver MaruBuri OFL-style license (free, embeddable); the Hangul
>   body face for the 8 editorial/luxury looks.
> - **Gowun Batang** — SIL OFL 1.1 (Google Fonts); available as an alternate
>   display face (not currently mapped).
> Hangul body for the 4 data/report looks stays on Pretendard (SIL OFL 1.1).

```
MIT License

Copyright (c) 2026 Design Diversity contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## velis (lrk-slides-velis)

- **Project:** lrk-slides-velis (`lrk-slides-velis.potx`)
- **Author:** Laurens R. Krol
- **License:** CC0 1.0 Universal (public domain dedication)
- **What ppt-lab uses:** Only the template's font (Arial) and palette
  (teal / pink) were absorbed into the `velis` style + `Velis Teal` palette.
  The template ships zero slides, so no component geometry was measured; the
  `velis` style falls back to the `house` component look (explicit copy).
- **Attribution:** CC0 carries **no** attribution obligation; this notice is
  recorded as a professional courtesy only.

```
CC0 1.0 Universal — Public Domain Dedication

The person who associated a work with this deed has dedicated the work to the
public domain by waiving all of his or her rights to the work worldwide under
copyright law, including all related and neighboring rights, to the extent
allowed by law. You can copy, modify, distribute and perform the work, even for
commercial purposes, all without asking permission.

Full text: https://creativecommons.org/publicdomain/zero/1.0/legalcode
```

---

## Production-use guidance

ppt-lab generates editable presentation/web output. When you publish material
produced with a brand-emulating look:

- Use **your own** company name, wordmark, and logo — not the emulated brand's.
- Keep the **open-licensed font** substitutions (or your own licensed fonts);
  do not embed proprietary fonts you are not licensed for.
- Supply your own photography/imagery; emulated brand photography is not included.

The license obligations above apply to ppt-lab's distributed specifications and
tokens. Responsibility for trademark-safe *output* rests with the end user, as
is standard for design-system tooling.
