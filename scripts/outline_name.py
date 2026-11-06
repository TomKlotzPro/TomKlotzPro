"""Writes scripts/source/name.svg, the masthead name as outlines, so it renders the same on every OS.

Bodoni Moda (SIL Open Font License, github.com/indestructible-type/Bodoni), the variable font from Google Fonts:
  uv run --with fonttools --with uharfbuzz python3 scripts/outline_name.py "BodoniModa[opsz,wght].ttf"
"""

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

TEXT = "Tom Klotz"
AXES = {"wght": 800, "opsz": 96}
TRACKING = -0.02  # em

OUT = Path(__file__).resolve().parent / "source" / "name.svg"

font_path = sys.argv[1]
blob = hb.Blob.from_file_path(font_path)
hb_font = hb.Font(hb.Face(blob))
hb_font.set_variations(AXES)
buffer = hb.Buffer()
buffer.add_str(TEXT)
buffer.guess_segment_properties()
hb.shape(hb_font, buffer, {"kern": True, "liga": True})
assert all(info.codepoint for info in buffer.glyph_infos), f"the font has no glyph for a letter of {TEXT!r}"

font = instantiateVariableFont(TTFont(font_path), AXES)
glyphs = font.getGlyphSet()
order = font.getGlyphOrder()
upem = font["head"].unitsPerEm

pen, bounds = SVGPathPen(glyphs, ntos=lambda v: f"{round(v)}"), BoundsPen(glyphs)
x = 0
for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
    # Fonts are y-up and SVG is y-down: flip, so the baseline sits at y=0.
    for target in (pen, bounds):
        glyphs[order[info.codepoint]].draw(TransformPen(target, (1, 0, 0, -1, x + pos.x_offset, 0)))
    x += pos.x_advance + TRACKING * upem
x0, y0, x1, y1 = (round(v) for v in bounds.bounds)
OUT.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">'
    f'<path d="{pen.getCommands()}"/></svg>\n'
)
print(f"wrote {OUT.name}: {x1 - x0} x {y1 - y0} units at {upem} per em, {len(pen.getCommands()) / 1024:.1f} KB of path data")
