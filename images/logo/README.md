# Visual identity

The mark is a card pip turned into a table: a diamond split into four
quadrants, one of them filled with the accent — the single hand that stands out
of the range.

## Files

The **SVG is the source**. The PNGs are exports of it and should never be
edited directly: change the SVG, then re-export.

| Source | Export | Use |
| --- | --- | --- |
| `pokerdf-logo-light.svg` | `pokerdf-logo-light.png` (942×330) | Horizontal lockup, light backgrounds |
| `pokerdf-logo-dark.svg` | `pokerdf-logo-dark.png` (942×330) | Horizontal lockup, dark backgrounds |
| `pokerdf-icon-light.svg` | `pokerdf-icon-light.png` (512×512) | Icon alone, light backgrounds |
| `pokerdf-icon-dark.svg` | `pokerdf-icon-dark.png` (512×512) | Icon alone, dark backgrounds |

Every file has a transparent background, and the inner face of the diamond is
punched out with an even-odd fill rather than painted, so the mark takes the
colour of the page instead of stamping a white rectangle onto it.

The lockup artboard is 314 units wide and the icon artboard 128, exported at 3×
and 4× to 942×330 and to the 512×512 that favicons and social preview cards
ask for.

Inside the lockup the two halves keep their original coordinates and are placed
by a `transform` on the group that wraps each: the mark is scaled to three
quarters and the gap between it and the wordmark is 24 units. Composing it this
way means the proportion can be retuned by editing two numbers, without
redrawing a single path.

**The two lockup sources carry no `width` or `height`, only a `viewBox`, and
that is deliberate.** An `<img>` pointing at an SVG with no intrinsic size but a
known ratio is laid out at the full width of its container, so the lockup fills
the column it is dropped into instead of sitting at a fixed size in the middle
of it. Adding the two attributes back would silently shrink the README banner to
314 pixels. The icons keep theirs, since they are placed at a chosen size rather
than stretched to fit.

To re-export after a change, at any size:

```sh
rsvg-convert -w 942 pokerdf-logo-light.svg -o pokerdf-logo-light.png
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
  <source media="(prefers-color-scheme: dark)" srcset=".../pokerdf-logo-dark.svg">
  <img src=".../pokerdf-logo-light.svg" alt="pokerdf">
</picture>
```

Renderers that do not implement `<picture>` — PyPI among them, and it renders
the top-level README on every release — drop the `<source>` and keep the
`<img>`, which is why the light variant is the fallback and why the URLs are
absolute rather than relative to the repository.

The README points at the SVGs rather than the PNGs: a banner that spans the full
column would need an export of some 2500 pixels to stay sharp on a high-DPI
display, where the vector is 5 KB and sharp at every size.
The PNGs remain for the places that will not take a vector, social preview cards
among them.
