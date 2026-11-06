#!/usr/bin/env python3
"""Builds the animated card at the top of the profile README, in a light and a dark version:
assets/profile-{light,dark}.svg and the link slices assets/link-*-{light,dark}.svg.

Edit the facts below, then run:  python3 scripts/build_profile.py

Sources in scripts/source are square crops of the same photo, so the subject lines up from frame to frame:
  portrait.jpg              the original photo
  portrait-cutout.png       its cutout, from scripts/cutout.swift (macOS Vision, runs locally)
  backgrounds/*.jpg         real AI backgrounds, generated in the Photoroom app on that photo
  name.svg                  the name as outlines, from scripts/outline_name.py
"""

import base64
import io
import re
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "source"

# ── Facts ────────────────────────────────────────────────────────────────────

PITCH = [
    "I ship features in Photoroom's AI photo editor,",
    "used by millions to make their photos shine.",
]
CAREER = [
    # hash, company, what, role, glyph (node colours are per theme, in THEMES)
    ("a190l1a", "Algolia", "Search engine", "software engineering", "A"),
    ("ca570rd", "CastorDoc", "Data catalog", "fullstack engineering", "C"),
    ("a5m335f", "Ministère des Armées", "Defense, 3 years of service", "software engineering", "*"),
    (None, "Photoroom", "AI photo editing", "software engineering, since 2026", "P"),
]
# Photoroom since Feb 16, 2026. Counts from `gh search prs --owner Photoroom --author @me --merged`
# and `--reviewed-by @me` (2026-10-06); Code Connect coverage from the July 31 audit (367/385).
CHANGELOG = [
    [("Rookie of the Year", None, 700), (" at Photoroom, in my first 4.5 months", None, 400)],
    [("570+", None, 700), (" pull requests merged and ", None, 400), ("540+", None, 700), (" reviewed, in 8 months", None, 400)],
    [("Shipped ", None, 400), ("Virtual Models, AI Video Gen, Share Links, Recommended edits", None, 700)],
    [("Design system: Code Connect coverage from ", None, 400), ("22% to 95%", None, 700)],
]

# ── Palette: a blueprint on GitHub's own canvas, with a light and a dark card ──
# The ground is GitHub's page colour, the blueprint is sky-blue linework, and only the hero (whoami, the photo and
# the name) is a solid blue block. The README's <picture> shows the card matching the viewer's GitHub theme: GitHub
# wraps it in <themed-picture>, which rewrites the media query from that setting, not just the OS.
# Every text holds 4.5:1 against what is behind it (3:1 when large), a grid line under it included.

SKY = "#0099FF"  # the light inside the hero block
CLOUD = "#FDFDFE"  # type, frame and grid on the hero block
LIME = "#E0F354"  # the touch
NAVY = "#05264D"  # glyphs on light nodes and on lime, the photo's top scrim
CHIP, CHIP_TEXT, CHIP_SUB = "#05305F", CLOUD, "#DCE9F7"  # the caption chip on the photo
CHECKER = ("#0A4C99", "#0A58AE")  # the "transparent" squares, in blueprint blue
FRANCE_BLUE = "#2A63F6"
FRANCE_RED = "#E5484D"
THEMES = {
    "light": dict(
        PAGE="#FFFFFF", HERO="#0969DA", TEXT="#1F2328", SUB="#1F2328", MUTED="#59636E", FAINT="#59636E",
        ACCENT="#0969DA", LINE="#D0D7DE", PANEL="#FFFFFF", LOG_PANEL="#F6F8FA", LOG_TAB="#EAEEF2",
        BLUE="#0969DA", GREEN="#116329", LINEWORK="#0969DA", GRID=(0.07, 0.12), SKYLINE_OPACITY=0.45, HEAD_GLOW=0.1,
        HERO_TEXT=CLOUD, HERO_TILDE=CLOUD,  # lime is 4.2:1 on GitHub blue, too low for 15 px text
        # node fill, ring, glyph: one blue family toward a lime present; the rings hold 3:1 on the page
        NODES=[("#8EB9E6", "#0969DA", NAVY), ("#5C9CE4", "#0969DA", NAVY), ("#0969DA", "#0969DA", "#FFFFFF"), (LIME, "#0969DA", NAVY)],
        PRESENT="#0969DA", HEAD_EDGE="#7F9010",  # arrow and HEAD pulse; lime alone vanishes on white
    ),
    "dark": dict(
        PAGE="#0D1117", HERO="#0E2A4F", TEXT="#E6EDF3", SUB="#C9D1D9", MUTED="#9198A1", FAINT="#9198A1",
        ACCENT="#4493F8", LINE="#30363D", PANEL="#0D1117", LOG_PANEL="#161B22", LOG_TAB="#21262D",
        BLUE=LIME, GREEN=LIME, LINEWORK="#4493F8", GRID=(0.09, 0.14), SKYLINE_OPACITY=0.5, HEAD_GLOW=0.18,
        HERO_TEXT="#E6F1FC", HERO_TILDE=LIME,
        NODES=[("#1F4E8C", "#4493F8", "#FFFFFF"), ("#2F6FC4", "#4493F8", "#FFFFFF"), ("#4493F8", "#4493F8", "#0D1117"), (LIME, "#4493F8", NAVY)],
        PRESENT=LIME, HEAD_EDGE=LIME,
    ),
}
# The palette is module-level, like the rest of the generator; the build loop switches it per theme.
globals().update(THEMES["light"])

W = 1000
# The README top-aligns the card (align="top") so GitHub leaves no line-box gap between it and the links.
SEAM = 0
RADIUS = 7  # GitHub's 6 px Box corners at the card's 846 / 1000 scale
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Monaco, 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

# Hero loop: original photo, background removal sweep, then each AI background, then back to the original.
LOOP = 13.0
SWEEP_START, SWEEP_END, REMOVED_END = 1.0, 3.0, 4.5
AI_BACKGROUNDS = [
    # file, caption, shown from (s)
    ("space.jpg", "AI background: outer space", REMOVED_END),
    ("paris.jpg", "AI background: Paris at dusk", 8.5),
]
RESET = 12.2
# The hero is a magazine cover: the name sits between the background and the cutout, so once the background
# is gone Tom stands in front of it. The banner shows a band of the square photos, from WINDOW_TOP down.
BANNER_X, BANNER_Y, BANNER_W, BANNER_H = 56, 92, 888, 440
WINDOW_TOP = 0.26
NAME_X, NAME_W = 84, 832
# On the square photo his hair starts at 0.43, so the head covers the bottom third of the letters it crosses.
NAME_BASELINE = BANNER_Y + (0.47 - WINDOW_TOP) * BANNER_W
HERO_H = BANNER_Y + BANNER_H + 20  # the solid blue block
ROLE_Y = HERO_H + 48  # the role line's baseline, with air under the block
CAREER_Y = ROLE_Y + 104
CHANGELOG_Y = CAREER_Y + 300
CHANGELOG_H = 60 + 42 * len(CHANGELOG)
FOOTER_Y = CHANGELOG_Y + CHANGELOG_H + 60
H = FOOTER_Y + 90


def data_uri(image: Image.Image, fmt: str, **options) -> str:
    buffer = io.BytesIO()
    image.save(buffer, fmt, **options)
    mime = "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"
    return f"data:{mime};base64,{base64.b64encode(buffer.getvalue()).decode()}"


def key_times(*seconds: float) -> str:
    return ";".join(f"{s / LOOP:.4f}" for s in seconds)


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def flag(x: float, y: float, height: float = 16) -> str:
    w = height / 2
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{height}" rx="2" fill="{FRANCE_BLUE}"/>'
        f'<rect x="{x + w}" y="{y}" width="{w}" height="{height}" fill="#F5F7FA"/>'
        f'<rect x="{x + 2 * w}" y="{y}" width="{w}" height="{height}" rx="2" fill="{FRANCE_RED}"/>'
        f'<rect x="{x}" y="{y}" width="{3 * w}" height="{height}" rx="2" stroke="{LINE}" stroke-width="0.75"/>'
    )


def prompt(x: float, y: float, command: str, text: str = "", tilde: str = "") -> str:
    return (
        f'<text x="{x}" y="{y}" class="mono" font-size="15" fill="{text or MUTED}">'
        f'<tspan fill="{tilde or BLUE}">~</tspan> $ {command}</text>'
    )


def embedded(name: str) -> str:
    image = Image.open(SOURCE / name)
    side = image.width
    top = round(WINDOW_TOP * side)
    image = image.crop((0, top, side, top + round(side * BANNER_H / BANNER_W)))
    if image.mode == "RGBA":
        # Shrink the matte by a pixel: its outer edge still carries the sunset sky as a pale halo.
        image.putalpha(image.getchannel("A").filter(ImageFilter.MinFilter(3)))
        return data_uri(image, "WEBP", quality=88, method=6)
    return data_uri(image.convert("RGB"), "JPEG", quality=82, optimize=True, progressive=True)


def masthead() -> str:
    view_box, path = re.search(r'viewBox="([^"]+)".*? d="([^"]+)"', (SOURCE / "name.svg").read_text()).groups()
    left = float(view_box.split()[0])
    scale = NAME_W / float(view_box.split()[2])
    return (
        f'<path transform="translate({NAME_X - left * scale:.1f} {NAME_BASELINE:.1f}) scale({scale:.5f})" '
        f'd="{path}" fill="#F5F7FA"/>'
    )


def hero() -> str:
    original_uri = embedded("portrait.jpg")
    cutout_uri = embedded("portrait-cutout.png")
    x, y, w, h = BANNER_X, BANNER_Y, BANNER_W, BANNER_H
    end = x + w
    sweep = key_times(0, SWEEP_START, SWEEP_END, LOOP)
    spline = 'calcMode="spline" keySplines="0 0 1 1; 0.45 0 0.2 1; 0 0 1 1"'
    chip_y = y + h - 58
    reset = (
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="{key_times(0, RESET, RESET + 0.6, LOOP)}" '
        f'dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>'
    )

    def fade_in(start: float) -> str:
        return (
            f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="{key_times(0, start, start + 0.5, LOOP)}" '
            f'dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>'
        )

    def caption(text: str, start: float, stop: float, accent: str = CHIP_SUB) -> str:
        shown = f'values="0;1;0" keyTimes="{key_times(0, start, stop)}"'
        if start == 0:
            shown = f'values="1;0;1" keyTimes="{key_times(0, stop, RESET)}"'
        return (
            f'<text x="{x + 62}" y="{chip_y + 27}" font-size="15" fill="{accent}" opacity="{1 if start == 0 else 0}">'
            f'{esc(text)}<animate attributeName="opacity" {shown} calcMode="discrete" dur="{LOOP}s" '
            f'begin="0.5s" repeatCount="indefinite"/></text>'
        )

    pitch_lines = "".join(
        f'<text x="56" y="{ROLE_Y + 36 + i * 28}" font-size="19" fill="{SUB}">{esc(line)}</text>'
        for i, line in enumerate(PITCH)
    )
    backgrounds = "".join(
        f'<image href="{embedded("backgrounds/" + file)}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" opacity="0">{fade_in(start)}</image>'
        for file, _, start in AI_BACKGROUNDS
    )
    stops = [start for _, _, start in AI_BACKGROUNDS[1:]] + [RESET]
    ai_captions = "".join(
        caption(text, start, stop, CHIP_TEXT) for (_, text, start), stop in zip(AI_BACKGROUNDS, stops)
    )
    return f"""
  <!-- Hero: the Photoroom trick, played on the author's own portrait. Layers, bottom to top: the photo,
       the swept-in background, the name, the swept-in cutout. -->
  {prompt(56, 66, "whoami", HERO_TEXT, HERO_TILDE)}
  <rect class="cursor" x="147" y="53" width="9" height="16" fill="{LIME}"/>
  <text x="{end}" y="66" text-anchor="end" class="mono" font-size="13" fill="{HERO_TEXT}">tom.jpg</text>
  <g clip-path="url(#bannerClip)">
    <image href="{original_uri}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none"/>
    <g clip-path="url(#sweepClip)">{reset}
      <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#checker)"/>
      {backgrounds}
    </g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#scrim)"/>
    {masthead()}
    <g clip-path="url(#sweepClip)">{reset}
      <image href="{cutout_uri}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" filter="url(#lift)"/>
    </g>
    <g opacity="0">
      <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{key_times(0, SWEEP_START, SWEEP_END - 0.1, SWEEP_END + 0.1, LOOP)}" dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      <rect y="{y}" width="40" height="{h}" fill="url(#scanGlow)">
        <animate attributeName="x" values="{x - 40};{x - 40};{end - 40};{end - 40}" keyTimes="{sweep}" {spline} dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      </rect>
      <rect y="{y}" width="2" height="{h}" fill="#FFFFFF">
        <animate attributeName="x" values="{x - 1};{x - 1};{end - 1};{end - 1}" keyTimes="{sweep}" {spline} dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      </rect>
    </g>
  </g>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" stroke="{CLOUD}" stroke-width="1.5"/>

  <rect x="{x + 16}" y="{chip_y}" width="300" height="42" rx="21" fill="{CHIP}" fill-opacity="0.86" stroke="{LINE}"/>
  <g transform="translate({x + 38} {chip_y + 21})">
    <path class="spark" d="M0 -10 C1.2 -3 3 -1.2 10 0 C3 1.2 1.2 3 0 10 C-1.2 3 -3 1.2 -10 0 C-3 -1.2 -1.2 -3 0 -10 Z" fill="{LIME}"/>
  </g>
  {caption("Original photo", 0, SWEEP_START)}
  {caption("Removing the background…", SWEEP_START, SWEEP_END, CHIP_TEXT)}
  {caption("Background removed", SWEEP_END, REMOVED_END, CHIP_TEXT)}
  {ai_captions}

  <text x="56" y="{ROLE_Y}" font-size="26" fill="{TEXT}">Software engineer at <tspan fill="{ACCENT}" font-weight="700">Photoroom</tspan></text>
  {pitch_lines}
  {flag(920, ROLE_Y - 14)}
  <text x="908" y="{ROLE_Y}" text-anchor="end" font-size="17" fill="{MUTED}">Paris, France</text>
"""


def career() -> str:
    y0 = CAREER_Y
    line_y = y0 + 150
    xs = [160, 380, 600, 820]
    length = 940 - 96
    draw_begin, draw_dur = 0.4, 2.6
    nodes = []
    for i, (sha, company, what, role, glyph) in enumerate(CAREER):
        cx = xs[i]
        fill, ring, glyph_colour = NODES[i]
        begin = draw_begin + (cx - 96) / length * draw_dur
        appear = f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.4s" fill="freeze"/>'
        grow = f'<animate attributeName="r" values="0;{{r}};{{r}}" keyTimes="0;0.7;1" begin="{begin:.2f}s" dur="0.45s" fill="freeze"/>'
        if glyph == "*":
            mark = (
                f'<path d="M{cx} {line_y - 8} l2.4 4.9 5.4 0.8 -3.9 3.8 0.9 5.4 -4.8 -2.5 -4.8 2.5 0.9 -5.4 '
                f'-3.9 -3.8 5.4 -0.8 z" fill="{glyph_colour}"/>'
            )
        else:
            mark = f'<text x="{cx}" y="{line_y + 5}" text-anchor="middle" class="mono" font-size="15" font-weight="700" fill="{glyph_colour}">{glyph}</text>'
        label = (
            f'<text x="{cx}" y="{line_y - 48}" text-anchor="middle" class="mono" font-size="14" fill="{FAINT}">{sha}</text>'
            if sha
            else ""
        )
        nodes.append(
            f"""
    <g opacity="0">{appear}
      {label}
      <circle cx="{cx}" cy="{line_y}" r="0" fill="{PAGE}" stroke="{ring}" stroke-width="2.5">{grow.format(r=24)}</circle>
      <circle cx="{cx}" cy="{line_y}" r="0" fill="{fill}">{grow.format(r=16)}</circle>
      {mark}
      <text x="{cx}" y="{line_y + 56}" text-anchor="middle" font-size="19" font-weight="700" fill="{TEXT}">{esc(company)}</text>
      <text x="{cx}" y="{line_y + 80}" text-anchor="middle" font-size="15" fill="{SUB}">{esc(what)}</text>
      <text x="{cx}" y="{line_y + 101}" text-anchor="middle" font-size="13" fill="{FAINT}">{esc(role)}</text>
    </g>"""
        )
    head_begin = draw_begin + draw_dur + 0.2
    head_x = xs[-1]
    return f"""
  <!-- Career: a git graph that draws itself, HEAD lands on Photoroom -->
  <line x1="56" y1="{y0}" x2="944" y2="{y0}" stroke="{LINE}"/>
  {prompt(56, y0 + 52, 'git log --reverse --graph <tspan fill="' + FAINT + '">career/</tspan>')}
  <circle cx="{head_x}" cy="{line_y}" r="150" fill="url(#skyGlow)"/>
  <defs><linearGradient id="careerLine" x1="96" y1="0" x2="940" y2="0" gradientUnits="userSpaceOnUse">
    {"".join(f'<stop offset="{(x - 96) / length:.3f}" stop-color="{fill}"/>' for x, (fill, _, _) in zip(xs, NODES))}<stop offset="1" stop-color="{LIME}"/>
  </linearGradient></defs>
  <line x1="96" y1="{line_y}" x2="940" y2="{line_y}" stroke="url(#careerLine)" stroke-width="2" stroke-dasharray="{length}" stroke-dashoffset="{length}">
    <animate attributeName="stroke-dashoffset" from="{length}" to="0" begin="{draw_begin}s" dur="{draw_dur}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/>
  </line>
  <path d="M948 {line_y} l-11 -6 v12 z" fill="{PRESENT}" opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{draw_begin + draw_dur:.2f}s" dur="0.3s" fill="freeze"/>
  </path>
  <circle cx="{head_x}" cy="{line_y}" r="24" fill="none" stroke="{PRESENT}" stroke-width="2" opacity="0">
    <animate attributeName="r" values="24;46" begin="{head_begin + 0.4:.2f}s" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.7;0" begin="{head_begin + 0.4:.2f}s" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  {"".join(nodes)}
  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{head_begin:.2f}s" dur="0.35s" fill="freeze"/>
    <animateTransform attributeName="transform" type="translate" values="0 -14;0 3;0 0" keyTimes="0;0.6;1" begin="{head_begin:.2f}s" dur="0.6s" fill="freeze"/>
    <rect x="{head_x - 62}" y="{line_y - 72}" width="124" height="30" rx="15" fill="{LIME}" stroke="{HEAD_EDGE}"/>
    <text x="{head_x}" y="{line_y - 52}" text-anchor="middle" class="mono" font-size="14" font-weight="700" fill="{NAVY}">HEAD → main</text>
  </g>
"""


def changelog() -> str:
    y0 = CHANGELOG_Y
    rows = []
    # Wide enough for Safari's SF Mono, the widest of the fallbacks.
    char_width = 10.6
    begin = 3.6
    for i, parts in enumerate(CHANGELOG):
        baseline = y0 + 84 + i * 42
        text = "".join(
            f'<tspan fill="{color or (TEXT if weight == 700 else SUB)}" font-weight="{weight}">{esc(chunk)}</tspan>' for chunk, color, weight in parts
        )
        width = sum(len(chunk) for chunk, _, _ in parts) * char_width + 6
        dur = max(0.9, width / 520)
        rows.append(
            f"""
    <clipPath id="type{i}"><rect x="140" y="{baseline - 22}" height="32" width="0.01">
      <animate attributeName="width" from="0.01" to="{width:.0f}" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>
    </rect></clipPath>
    <text x="84" y="{baseline}" class="mono" font-size="17" fill="{FAINT}" text-anchor="end">{i + 1}</text>
    <text x="114" y="{baseline}" class="mono" font-size="17" font-weight="700" fill="{GREEN}" opacity="0">+<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.2s" fill="freeze"/></text>
    <text x="140" y="{baseline}" class="mono" font-size="17" clip-path="url(#type{i})">{text}</text>
    <rect y="{baseline - 16}" width="10" height="20" fill="{BLUE}" opacity="0">
      <animate attributeName="x" from="140" to="{140 + width:.0f}" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.98;1" begin="{begin:.2f}s" dur="{dur + 0.25 if i < len(CHANGELOG) - 1 else dur + 0.1:.2f}s" fill="{'remove' if i < len(CHANGELOG) - 1 else 'freeze'}"/>
    </rect>"""
        )
        last_end = begin + dur
        begin += dur + 0.35
    final_cursor_x = 140 + sum(len(chunk) for chunk, _, _ in CHANGELOG[-1]) * char_width + 10
    final_baseline = y0 + 84 + (len(CHANGELOG) - 1) * 42
    return f"""
  <!-- Highlights, typed into a changelog (clips start at 0.01: Safari ignores an empty clip) -->
  <g transform="translate(56 {y0})">
    <rect width="888" height="{CHANGELOG_H}" rx="{RADIUS}" fill="{LOG_PANEL}" stroke="{LINE}"/>
    <path d="M0 {RADIUS} a{RADIUS} {RADIUS} 0 0 1 {RADIUS} -{RADIUS} h{144 - RADIUS} v36 h-144 z" fill="{LOG_TAB}"/>
    <text x="22" y="24" class="mono" font-size="14" fill="{SUB}">CHANGELOG.md</text>
    <line x1="0" y1="36" x2="888" y2="36" stroke="{LINE}"/>
  </g>
  {"".join(rows)}
  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{last_end:.2f}s" dur="0.01s" fill="freeze"/>
    <rect class="cursor" x="{final_cursor_x:.0f}" y="{final_baseline - 16}" width="10" height="20" fill="{BLUE}"/>
  </g>
"""


def footer() -> str:
    y = FOOTER_Y
    return f"""
  <!-- Sign-off -->
  <line x1="56" y1="{y - 46}" x2="944" y2="{y - 46}" stroke="{LINE}"/>
  {prompt(56, y + 12, 'exit <tspan fill="' + GREEN + '">0</tspan>')}
  {flag(424, y - 8, 14)}
  <text x="452" y="{y + 4}" font-size="17" font-weight="600" fill="{TEXT}">Made in Paris</text>
  <text x="500" y="{y + 32}" text-anchor="middle" class="mono" font-size="14" fill="{MUTED}">liberté · égalité · déployé</text>
  <text x="944" y="{y + 12}" text-anchor="end" class="mono" font-size="14" fill="{FAINT}">@TomKlotzPro</text>
"""


# Paris roofs along the bottom of the card, and the tower between the motto and the handle, as linework drawn
# for a card bottom at y=1440; build() moves it to the real bottom.
SKYLINE_BOTTOM = 1440
SKYLINE = (
    "M0 1440 V1414 h40 l10 -14 h60 l10 14 h20 v-22 h8 v22 h30 l12 -18 h70 l12 18 h24 v-10 h6 v10 h40 l14 -20 h84 l14 20 h30 v-16 h8 v16"
    " h50 l10 -12 h56 l10 12 h20 v-24 h6 v24 h34 l12 -16 h70 l12 16 h30 l10 -12 h40 l10 12 h18 v-18 h8 v18 h42 l14 -20 h80 l14 20 h29 V1440"
    " M694 1440 L718 1388 L723 1356 L726 1334 L728 1318 L730 1334 L733 1356 L738 1388 L762 1440"
    " M703 1418 H753 M713 1392 H743 M720 1362 H736 M705 1418 L740 1392 M751 1418 L716 1392 M715 1392 L734 1362 M741 1392 L722 1362"
    " M712 1440 Q728 1424 744 1440"
)


def grid(grid_id: str, colour: str, minor: float, major: float) -> str:
    return (
        f'<pattern id="{grid_id}" width="120" height="120" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0V120M48 0V120M72 0V120M96 0V120M0 24H120M0 48H120M0 72H120M0 96H120" stroke="{colour}" stroke-opacity="{minor}"/>'
        f'<path d="M0 0V120M0 0H120" stroke="{colour}" stroke-opacity="{major}"/></pattern>'
    )


def ground(dx: float = 0, dy: float = 0) -> str:
    """GitHub's page colour with the blueprint grid, in card coordinates; a link slice shifts it by its own offset."""
    total = H + SEAM + LINK_HEIGHT
    return (
        f'<g transform="translate({dx} {dy})"><rect width="{W}" height="{total}" fill="{PAGE}"/>'
        f'<rect width="{W}" height="{total}" fill="url(#grid)"/></g>'
    )


def build() -> str:
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tom Klotz, software engineer at Photoroom in Paris. His name is set like a magazine cover over his portrait; an animation removes the photo's background so he steps in front of his own name, then swaps in AI backgrounds made with Photoroom, outer space then Paris at dusk. Then a git graph of his career: Algolia, CastorDoc, Ministère des Armées, Photoroom. Highlights: Rookie of the Year in his first 4.5 months, 570+ pull requests merged and 540+ reviewed in 8 months, shipped Virtual Models, AI Video Gen, Share Links and Recommended edits, Code Connect coverage from 22% to 95%.">
  <defs>
    <clipPath id="panel"><rect width="{W}" height="{H + 24}" rx="{RADIUS}"/></clipPath>
    <clipPath id="bannerClip"><rect x="{BANNER_X}" y="{BANNER_Y}" width="{BANNER_W}" height="{BANNER_H}" rx="18"/></clipPath>
    <clipPath id="sweepClip"><rect x="{BANNER_X}" y="{BANNER_Y}" height="{BANNER_H}" width="0.01">
      <animate attributeName="width" values="0.01;0.01;{BANNER_W};{BANNER_W}" keyTimes="{key_times(0, SWEEP_START, SWEEP_END, LOOP)}" calcMode="spline" keySplines="0 0 1 1; 0.45 0 0.2 1; 0 0 1 1" dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
    </rect></clipPath>
    <pattern id="checker" width="24" height="24" patternUnits="userSpaceOnUse" x="{BANNER_X}" y="{BANNER_Y}">
      <rect width="24" height="24" fill="{CHECKER[0]}"/><rect width="12" height="12" fill="{CHECKER[1]}"/><rect x="12" y="12" width="12" height="12" fill="{CHECKER[1]}"/>
    </pattern>
    <linearGradient id="scanGlow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{CLOUD}" stop-opacity="0"/><stop offset="1" stop-color="{CLOUD}" stop-opacity="0.75"/>
    </linearGradient>
    <linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{NAVY}" stop-opacity="0.6"/><stop offset="0.55" stop-color="{NAVY}" stop-opacity="0"/>
    </linearGradient>
    <filter id="lift" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000" flood-opacity="0.45"/></filter>
    <radialGradient id="skyGlow"><stop offset="0" stop-color="{ACCENT}" stop-opacity="{HEAD_GLOW}"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>
    <radialGradient id="skylight"><stop offset="0" stop-color="{SKY}" stop-opacity="0.55"/><stop offset="1" stop-color="{SKY}" stop-opacity="0"/></radialGradient>
    {grid("grid", LINEWORK, *GRID)}
    {grid("heroGrid", CLOUD, 0.06, 0.12)}
  </defs>
  <style>
    text {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    @keyframes blink {{ 0%, 45% {{ opacity: 1 }} 50%, 95% {{ opacity: 0 }} 100% {{ opacity: 1 }} }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes twinkle {{ 0%, 100% {{ transform: rotate(0deg) scale(1) }} 50% {{ transform: rotate(45deg) scale(0.75) }} }}
    .spark {{ transform-box: fill-box; transform-origin: center; animation: twinkle 2.4s ease-in-out infinite; }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1 }} to {{ stroke-dashoffset: 0 }} }}
    .drawn {{ stroke-dasharray: 1; animation: draw 3.2s cubic-bezier(0.4, 0, 0.2, 1) 0.6s both; }}
    @media (prefers-reduced-motion: reduce) {{ .cursor, .spark, .drawn {{ animation: none; }} }}
  </style>
  <g clip-path="url(#panel)">
    {ground()}
    <rect width="{W}" height="{HERO_H}" fill="{HERO}"/>
    <rect width="{W}" height="{HERO_H}" fill="url(#heroGrid)"/>
    <circle cx="500" cy="220" r="330" fill="url(#skylight)" opacity="0.6"/>
    <path transform="translate(0 {H - SKYLINE_BOTTOM})" class="drawn" d="{SKYLINE}" stroke="{LINEWORK}" stroke-opacity="{SKYLINE_OPACITY}" stroke-width="1.4" stroke-linejoin="round" pathLength="1"/>
  </g>
{hero()}
{career()}
{changelog()}
{footer()}
</svg>
"""


# ── Links: one panel cut in three images, since each needs its own <a> in the README ──

# New file names on purpose: GitHub kept serving the old connect-*.svg slices at the new widths.
LINKS = [
    ("link-linkedin.svg", "LinkedIn", "tom-klotz", "linkedin"),
    ("link-photoroom.svg", "Photoroom", "photoroom.com", "photoroom"),
    ("link-pixelheim.svg", "Pixelheim", "my retro pixel-art RPG", "pixelheim"),
]
# The cards line up with the card's content column (x 56 to 944), so the slices are cut in the gaps between them.
LINK_GAP = 20
LINK_CARD_W = (W - 2 * 56 - 2 * LINK_GAP) / 3
LINK_WIDTHS = [349, 302, 349]
LINK_HEIGHT = 112

SWORD = [
    (7, 0, "#E8ECF4"), (6, 1, "#E8ECF4"), (5, 2, "#E8ECF4"), (4, 3, "#E8ECF4"), (1, 3, "#C9A227"),
    (2, 4, "#C9A227"), (3, 4, "#E8ECF4"), (2, 5, "#B07A3B"), (3, 5, "#C9A227"), (1, 6, "#B07A3B"),
    (4, 6, "#C9A227"), (0, 7, "#B07A3B"),
]


def link_icon(kind: str, x: float, y: float) -> str:
    box = f'<rect x="{x}" y="{y}" width="40" height="40" rx="10" fill="{{fill}}"/>'
    if kind == "linkedin":
        return box.format(fill="#0A66C2") + (
            f'<text x="{x + 20}" y="{y + 27}" text-anchor="middle" font-size="19" font-weight="800" fill="#FFFFFF">in</text>'
        )
    if kind == "photoroom":
        return box.format(fill="#6B4EFF") + (
            f'<text x="{x + 20}" y="{y + 27}" text-anchor="middle" font-size="19" font-weight="800" fill="#FFFFFF">P</text>'
        )
    pixels = "".join(
        f'<rect x="{x + 6 + col * 3.5}" y="{y + 6 + row * 3.5}" width="3.5" height="3.5" fill="{color}"/>'
        for col, row, color in SWORD
    )
    return box.format(fill="#1B2130") + pixels


def link_slice(index: int) -> str:
    file_name, title, detail, kind = LINKS[index]
    width = LINK_WIDTHS[index]
    offset = sum(LINK_WIDTHS[:index])
    card_w = LINK_CARD_W
    card_x = round(56 + index * (LINK_CARD_W + LINK_GAP) - offset, 2)
    return f"""<svg width="{width}" height="{LINK_HEIGHT}" viewBox="0 0 {width} {LINK_HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}: {detail}">
  <defs><clipPath id="panel"><rect x="{-offset}" y="-20" width="{W}" height="{LINK_HEIGHT + 20}" rx="{RADIUS}"/></clipPath></defs>
  <style>text {{ font-family: {SANS}; }} .mono {{ font-family: {MONO}; }}</style>
  <g clip-path="url(#panel)">
    {ground(-offset, -H - SEAM)}
  </g>
  <defs>{grid("grid", LINEWORK, *GRID)}</defs>
  <rect x="{card_x}" y="20" width="{card_w}" height="70" rx="{RADIUS}" fill="{PANEL}" stroke="{LINE}"/>
  {link_icon(kind, card_x + 16, 35)}
  <text x="{card_x + 70}" y="51" font-size="17" font-weight="700" fill="{TEXT}">{esc(title)}</text>
  <text x="{card_x + 70}" y="72" class="mono" font-size="13" fill="{MUTED}">{esc(detail)}</text>
  <path d="M{card_x + card_w - 31} 50 l9 -9 m-7 0 h7 v7" stroke="{FAINT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


if __name__ == "__main__":
    for theme, palette in THEMES.items():
        globals().update(palette)
        out = ROOT / "assets" / f"profile-{theme}.svg"
        out.write_text(build())
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f} KB)")
        for i, (file_name, *_rest) in enumerate(LINKS):
            (ROOT / "assets" / file_name.replace(".svg", f"-{theme}.svg")).write_text(link_slice(i))
            print(f"wrote assets/{file_name.replace('.svg', f'-{theme}.svg')}")
