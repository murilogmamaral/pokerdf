# Visual identity

The mark is a card pip turned into a table: a diamond split into four
quadrants, one of them filled with the brand red — the single hand that
stands out of the range.

| File | Use |
| --- | --- |
| `pokerdf-logo-light.png` | Horizontal lockup, for light backgrounds |
| `pokerdf-logo-dark.png` | Horizontal lockup, for dark backgrounds |
| `pokerdf-icon-light.png` | Icon alone, for light backgrounds |
| `pokerdf-icon-dark.png` | Icon alone, for dark backgrounds |

Every file has a transparent background, so the counters of the mark take the
colour of the page instead of punching a white rectangle into it.

## Colours

| Role | Light | Dark |
| --- | --- | --- |
| Ink | `#111113` | `#F0F0F2` |
| Accent | `#D33C30` | `#E4574A` |

The ink flips between the two themes, and the accent is lifted on dark
backgrounds: the light-theme red sits at a 4.0:1 contrast ratio against the
GitHub dark canvas, and the lifted one at 5.2:1.

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
