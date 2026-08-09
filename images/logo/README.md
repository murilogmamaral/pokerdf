# Visual identity

The mark is a card pip turned into a table: a diamond split into four
quadrants, one of them filled with the accent — the single hand that stands out
of the range.

## Files

The **SVG is the source**. The PNGs are exports of it and should never be
edited directly: change the SVG, then re-export.

| Source | Export | Use |
| --- | --- | --- |
| `pokerdf-logo-light.svg` | `pokerdf-logo-light.png` (1080×411) | Horizontal lockup, light backgrounds |
| `pokerdf-logo-dark.svg` | `pokerdf-logo-dark.png` (1080×411) | Horizontal lockup, dark backgrounds |
| `pokerdf-icon-light.svg` | `pokerdf-icon-light.png` (512×512) | Icon alone, light backgrounds |
| `pokerdf-icon-dark.svg` | `pokerdf-icon-dark.png` (512×512) | Icon alone, dark backgrounds |

Every file has a transparent background, and the inner face of the diamond is
punched out with an even-odd fill rather than painted, so the mark takes the
colour of the page instead of stamping a white rectangle onto it.

The lockup artboard is 360 units wide, which is the width the README renders it
at, so the export is exactly 3× and stays crisp on high-DPI displays. The icon
artboard is 128, exported at 4× to the 512×512 that favicons and social preview
cards ask for.

To re-export after a change, at any size:

```sh
rsvg-convert -w 1080 pokerdf-logo-light.svg -o pokerdf-logo-light.png
oxipng -o max --strip safe --alpha pokerdf-logo-light.png
```

## Colours

| Role | Light | Dark |
| --- | --- | --- |
| Ink | `#111113` | `#F0F0F2` |
| Accent | `#E0392B` | `#EC6153` |

The ink flips between the two themes, and the accent is lifted on dark
backgrounds: against the GitHub dark canvas the light-theme red sits at a 4.3:1
contrast ratio and the lifted one at 5.8:1.

## Typography

The wordmark is set in [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed)
Bold by Jeremy Tribby, licensed under the SIL Open Font License 1.1, and is
stored as outlines. Nothing renders the text as text, so the files need no font
installed and cannot fall back to a different face.

## Pairing the two variants

The theme is chosen by the reader's system, not by the file name, so both
variants ship together and the browser picks one:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".../pokerdf-logo-dark.png">
  <img src=".../pokerdf-logo-light.png" alt="PokerDF" width="360">
</picture>
```

Renderers that do not implement `<picture>` — PyPI among them, and it renders
the top-level README on every release — drop the `<source>` and keep the
`<img>`, which is why the light variant is the fallback and why the URLs are
absolute rather than relative to the repository.
