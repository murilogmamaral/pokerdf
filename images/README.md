# Diagram versioning

The data model diagram is versioned by schema: every release whose star
schema changes ships a **new** file (`data-modeling-vX.Y.svg`), and the
README of that release points to it.

Published files are immutable. The README of every release on PyPI fetches
its diagram from the main branch by filename, so modifying or deleting a
file here would silently rewrite the documentation of versions already
published. `data-modeling.svg` (no suffix) is the frozen diagram of the
releases up to 1.5.x.

To update the diagram after a schema change:

1. Edit `data-modeling.dbml` (the source of the diagram).
2. Paste it into [dbdiagram.io](https://dbdiagram.io) and export as SVG.
3. Save the export here as `data-modeling-vX.Y.svg`, where `X.Y` is the
   release that introduces the new schema.
4. Point the image URL of the top-level README at the new file.
