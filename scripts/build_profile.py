#!/usr/bin/env python3
"""Builds assets/profile.svg, the animated card at the top of the profile README.

Edit the facts below, then run:  python3 scripts/build_profile.py
The portrait cutout comes from scripts/cutout.swift (macOS Vision, runs locally):
  swift scripts/cutout.swift scripts/source/portrait.png scripts/source/portrait-cutout.png
"""

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "source"
OUT = ROOT / "assets" / "profile.svg"

# ── Facts ────────────────────────────────────────────────────────────────────

NAME = "Tom Klotz"
PITCH = [
    "I ship features in Photoroom's AI photo editor,",
    "used by millions to make their photos shine.",
]
BEFORE = ["Before that: search at Algolia, data at CastorDoc,", "and three years serving France."]
CAREER = [
    # hash, company, what, role, accent, glyph
    ("a190l1a", "Algolia", "Search engine", "software engineering", "#3E63DD", "A"),
    ("ca570rd", "CastorDoc", "Data catalog", "fullstack engineering", "#FF7847", "C"),
    ("a5m335f", "Ministère des Armées", "Defense, 3 years of service", "software engineering", "#C9A227", "*"),
    (None, "Photoroom", "AI photo editing", "software engineering, now", "#8B6CFF", "P"),
]
CHANGELOG = [
    [("Rookie of the Year", "#FFFFFF", 700), (" at Photoroom, in my first 4.5 months", None, 400)],
    [("350+", "#FFFFFF", 700), (" pull requests merged, and counting", None, 400)],
    [("Shipped ", None, 400), ("Virtual Models, AI Video Gen, Share Links", "#FFFFFF", 700), (", the design system", None, 400)],
]

# ── Palette ──────────────────────────────────────────────────────────────────

INK = "#0B0E14"
PANEL = "#10141D"
LINE = "#1E2533"
TEXT = "#E8ECF4"
SUB = "#B4BDCE"
MUTED = "#8C96AA"
FAINT = "#6E7A92"
BLUE = "#5B8CFF"
FRANCE_BLUE = "#2A63F6"
FRANCE_RED = "#E5484D"
VIOLET = "#8B6CFF"
GREEN = "#3FB950"

W, H = 1000, 1230
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Monaco, 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

# Hero loop: original photo, background removal sweep, then AI backgrounds, in 12 s.
LOOP = 12.0
CANVAS_X, CANVAS_Y, CANVAS = 576, 92, 368


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
    )


def prompt(x: float, y: float, command: str) -> str:
    return (
        f'<text x="{x}" y="{y}" class="mono" font-size="15" fill="{MUTED}">'
        f'<tspan fill="{BLUE}">~</tspan> $ {command}</text>'
    )


def hero() -> str:
    portrait = Image.open(SOURCE / "portrait.png").convert("RGB")
    cutout = Image.open(SOURCE / "portrait-cutout.png").convert("RGBA")
    original_uri = data_uri(portrait, "JPEG", quality=88)
    cutout_uri = data_uri(cutout, "WEBP", quality=90, method=6)
    x, y, s = CANVAS_X, CANVAS_Y, CANVAS
    end = x + s
    sweep = key_times(0, 1, 3, LOOP)
    spline = 'calcMode="spline" keySplines="0 0 1 1; 0.45 0 0.2 1; 0 0 1 1"'

    def fade_in(start: float) -> str:
        return (
            f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="{key_times(0, start, start + 0.5, LOOP)}" '
            f'dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>'
        )

    def caption(text: str, start: float, stop: float, accent: str = SUB) -> str:
        shown = f'values="0;1;0" keyTimes="{key_times(0, start, stop)}"'
        if start == 0:
            shown = f'values="1;0;1" keyTimes="{key_times(0, stop, 11)}"'
        return (
            f'<text x="{x + 64}" y="{y + s + 45}" font-size="15" fill="{accent}" opacity="{1 if start == 0 else 0}">'
            f'{esc(text)}<animate attributeName="opacity" {shown} calcMode="discrete" dur="{LOOP}s" '
            f'begin="0.5s" repeatCount="indefinite"/></text>'
        )

    name_lines = "".join(
        f'<text x="56" y="{298 + i * 30}" font-size="20" fill="{SUB}">{esc(line)}</text>'
        for i, line in enumerate(PITCH)
    )
    before_lines = "".join(
        f'<text x="56" y="{384 + i * 26}" font-size="17" fill="{MUTED}">{esc(line)}</text>'
        for i, line in enumerate(BEFORE)
    )
    return f"""
  <!-- Hero: the Photoroom trick, played on the author's own portrait -->
  {prompt(56, 96, "whoami")}
  <rect class="cursor" x="147" y="83" width="9" height="16" fill="{BLUE}"/>
  <text x="50" y="192" font-size="86" font-weight="800" letter-spacing="-2.5" fill="url(#nameGrad)">{NAME}</text>
  <text x="56" y="238" font-size="24" fill="{TEXT}">Software engineer at <tspan fill="{VIOLET}" font-weight="700">Photoroom</tspan></text>
  {name_lines}
  {before_lines}
  {flag(56, 446)}
  <text x="88" y="459" font-size="16" fill="{MUTED}">Paris, France</text>

  <text x="{x}" y="{y - 16}" class="mono" font-size="13" fill="{FAINT}">tom.jpg</text>
  <g clip-path="url(#canvasClip)">
    <image href="{original_uri}" x="{x}" y="{y}" width="{s}" height="{s}" preserveAspectRatio="xMidYMid slice"/>
    <g clip-path="url(#sweepClip)">
      <animate attributeName="opacity" values="1;1;0;0" keyTimes="{key_times(0, 11, 11.7, LOOP)}" dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" fill="url(#checker)"/>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" fill="url(#studio)" opacity="0">{fade_in(4.5)}</rect>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" fill="url(#white)" opacity="0">{fade_in(7)}</rect>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" fill="url(#dusk)" opacity="0">{fade_in(9)}</rect>
      <image href="{cutout_uri}" x="{x}" y="{y}" width="{s}" height="{s}" preserveAspectRatio="xMidYMid slice"/>
    </g>
    <g opacity="0">
      <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{key_times(0, 1, 2.9, 3.1, LOOP)}" dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      <rect y="{y}" width="40" height="{s}" fill="url(#scanGlow)">
        <animate attributeName="x" values="{x - 40};{x - 40};{end - 40};{end - 40}" keyTimes="{sweep}" {spline} dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      </rect>
      <rect y="{y}" width="2" height="{s}" fill="#FFFFFF">
        <animate attributeName="x" values="{x - 1};{x - 1};{end - 1};{end - 1}" keyTimes="{sweep}" {spline} dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
      </rect>
    </g>
  </g>
  <rect x="{x}" y="{y}" width="{s}" height="{s}" rx="18" stroke="#2A3242" stroke-width="1.5"/>

  <rect x="{x}" y="{y + s + 18}" width="{s}" height="42" rx="21" fill="{PANEL}" stroke="{LINE}"/>
  <g transform="translate({x + 38} {y + s + 39})">
    <path class="spark" d="M0 -10 C1.2 -3 3 -1.2 10 0 C3 1.2 1.2 3 0 10 C-1.2 3 -3 1.2 -10 0 C-3 -1.2 -1.2 -3 0 -10 Z" fill="{VIOLET}"/>
  </g>
  {caption("Original photo", 0, 1)}
  {caption("Removing the background…", 1, 3, TEXT)}
  {caption("Background removed", 3, 4.5, TEXT)}
  {caption("AI background: studio", 4.5, 7, TEXT)}
  {caption("AI background: clean white", 7, 9, TEXT)}
  {caption("AI background: Paris at dusk", 9, 11, TEXT)}
"""


def career() -> str:
    y0 = 560
    line_y = y0 + 150
    xs = [160, 380, 600, 820]
    length = 940 - 96
    draw_begin, draw_dur = 0.4, 2.6
    nodes = []
    for i, (sha, company, what, role, accent, glyph) in enumerate(CAREER):
        cx = xs[i]
        begin = draw_begin + (cx - 96) / length * draw_dur
        appear = f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.4s" fill="freeze"/>'
        grow = f'<animate attributeName="r" values="0;{{r}};{{r}}" keyTimes="0;0.7;1" begin="{begin:.2f}s" dur="0.45s" fill="freeze"/>'
        if glyph == "*":
            mark = (
                f'<path d="M{cx} {line_y - 8} l2.4 4.9 5.4 0.8 -3.9 3.8 0.9 5.4 -4.8 -2.5 -4.8 2.5 0.9 -5.4 '
                f'-3.9 -3.8 5.4 -0.8 z" fill="#1D1608"/>'
            )
        else:
            dark = "#3A1503" if glyph == "C" else "#FFFFFF"
            mark = f'<text x="{cx}" y="{line_y + 5}" text-anchor="middle" class="mono" font-size="15" font-weight="700" fill="{dark}">{glyph}</text>'
        label = (
            f'<text x="{cx}" y="{line_y - 48}" text-anchor="middle" class="mono" font-size="14" fill="{FAINT}">{sha}</text>'
            if sha
            else ""
        )
        nodes.append(
            f"""
    <g opacity="0">{appear}
      {label}
      <circle cx="{cx}" cy="{line_y}" r="0" fill="{INK}" stroke="{accent}" stroke-width="2.5">{grow.format(r=24)}</circle>
      <circle cx="{cx}" cy="{line_y}" r="0" fill="{accent}">{grow.format(r=16)}</circle>
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
  <circle cx="{head_x}" cy="{line_y}" r="150" fill="url(#violetGlow)"/>
  <line x1="96" y1="{line_y}" x2="940" y2="{line_y}" stroke="#2A3242" stroke-width="2" stroke-dasharray="{length}" stroke-dashoffset="{length}">
    <animate attributeName="stroke-dashoffset" from="{length}" to="0" begin="{draw_begin}s" dur="{draw_dur}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/>
  </line>
  <path d="M948 {line_y} l-11 -6 v12 z" fill="#2A3242" opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{draw_begin + draw_dur:.2f}s" dur="0.3s" fill="freeze"/>
  </path>
  <circle cx="{head_x}" cy="{line_y}" r="24" fill="none" stroke="{VIOLET}" stroke-width="2" opacity="0">
    <animate attributeName="r" values="24;46" begin="{head_begin + 0.4:.2f}s" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.7;0" begin="{head_begin + 0.4:.2f}s" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  {"".join(nodes)}
  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{head_begin:.2f}s" dur="0.35s" fill="freeze"/>
    <animateTransform attributeName="transform" type="translate" values="0 -14;0 3;0 0" keyTimes="0;0.6;1" begin="{head_begin:.2f}s" dur="0.6s" fill="freeze"/>
    <rect x="{head_x - 62}" y="{line_y - 72}" width="124" height="30" rx="15" fill="#1A1533" stroke="{VIOLET}"/>
    <text x="{head_x}" y="{line_y - 52}" text-anchor="middle" class="mono" font-size="14" font-weight="700" fill="#D9CEFF">HEAD → main</text>
  </g>
"""


def changelog() -> str:
    y0 = 880
    rows = []
    # Wide enough for Safari's SF Mono, the widest of the fallbacks.
    char_width = 10.6
    begin = 3.6
    for i, parts in enumerate(CHANGELOG):
        baseline = y0 + 84 + i * 42
        text = "".join(
            f'<tspan fill="{color or SUB}" font-weight="{weight}">{esc(chunk)}</tspan>' for chunk, color, weight in parts
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
    <rect width="888" height="186" rx="16" fill="{PANEL}" stroke="{LINE}"/>
    <path d="M0 16 a16 16 0 0 1 16 -16 h128 v36 h-144 z" fill="#161B26"/>
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
    y = 1140
    return f"""
  <!-- Sign-off -->
  <line x1="56" y1="{y - 46}" x2="944" y2="{y - 46}" stroke="{LINE}"/>
  {prompt(56, y + 12, 'exit <tspan fill="' + GREEN + '">0</tspan>')}
  {flag(424, y - 8, 14)}
  <text x="452" y="{y + 4}" font-size="17" font-weight="600" fill="{TEXT}">Made in Paris</text>
  <text x="500" y="{y + 32}" text-anchor="middle" class="mono" font-size="14" fill="{MUTED}">liberté · égalité · déployé</text>
  <text x="944" y="{y + 12}" text-anchor="end" class="mono" font-size="14" fill="{FAINT}">@TomKlotzPro</text>
"""


def build() -> str:
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tom Klotz, software engineer at Photoroom in Paris. An animation removes the background from his portrait, then a git graph of his career: Algolia, CastorDoc, Ministère des Armées, Photoroom. Highlights: Rookie of the Year in his first 4.5 months, 350+ pull requests merged, shipped Virtual Models, AI Video Gen, Share Links and the design system.">
  <defs>
    <clipPath id="panel"><rect width="{W}" height="{H}" rx="24"/></clipPath>
    <clipPath id="canvasClip"><rect x="{CANVAS_X}" y="{CANVAS_Y}" width="{CANVAS}" height="{CANVAS}" rx="18"/></clipPath>
    <clipPath id="sweepClip"><rect x="{CANVAS_X}" y="{CANVAS_Y}" height="{CANVAS}" width="0.01">
      <animate attributeName="width" values="0.01;0.01;{CANVAS};{CANVAS}" keyTimes="{key_times(0, 1, 3, LOOP)}" calcMode="spline" keySplines="0 0 1 1; 0.45 0 0.2 1; 0 0 1 1" dur="{LOOP}s" begin="0.5s" repeatCount="indefinite"/>
    </rect></clipPath>
    <pattern id="checker" width="24" height="24" patternUnits="userSpaceOnUse" x="{CANVAS_X}" y="{CANVAS_Y}">
      <rect width="24" height="24" fill="#1B2130"/><rect width="12" height="12" fill="#262E40"/><rect x="12" y="12" width="12" height="12" fill="#262E40"/>
    </pattern>
    <radialGradient id="studio" cx="0.62" cy="0.55" r="0.75">
      <stop offset="0" stop-color="#B9A6FF"/><stop offset="0.45" stop-color="#7A5CF0"/><stop offset="1" stop-color="#2A1C6B"/>
    </radialGradient>
    <linearGradient id="white" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FAFAFC"/><stop offset="1" stop-color="#D9DDE6"/>
    </linearGradient>
    <linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#22306E"/><stop offset="0.55" stop-color="#C77B8B"/><stop offset="1" stop-color="#F3B57E"/>
    </linearGradient>
    <linearGradient id="scanGlow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0.75"/>
    </linearGradient>
    <linearGradient id="tricolore" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{FRANCE_BLUE}"/><stop offset="0.5" stop-color="#F5F7FA"/><stop offset="1" stop-color="{FRANCE_RED}"/>
    </linearGradient>
    <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0.5">
      <stop offset="0" stop-color="#F7F9FF"/><stop offset="1" stop-color="#AFC4FF"/>
    </linearGradient>
    <radialGradient id="blueGlow"><stop offset="0" stop-color="{FRANCE_BLUE}" stop-opacity="0.26"/><stop offset="1" stop-color="{FRANCE_BLUE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="redGlow"><stop offset="0" stop-color="{FRANCE_RED}" stop-opacity="0.12"/><stop offset="1" stop-color="{FRANCE_RED}" stop-opacity="0"/></radialGradient>
    <radialGradient id="violetGlow"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.16"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
  </defs>
  <style>
    text {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    @keyframes blink {{ 0%, 45% {{ opacity: 1 }} 50%, 95% {{ opacity: 0 }} 100% {{ opacity: 1 }} }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes twinkle {{ 0%, 100% {{ transform: rotate(0deg) scale(1) }} 50% {{ transform: rotate(45deg) scale(0.75) }} }}
    .spark {{ transform-box: fill-box; transform-origin: center; animation: twinkle 2.4s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .cursor, .spark {{ animation: none; }} }}
  </style>
  <g clip-path="url(#panel)">
    <rect width="{W}" height="{H}" fill="{INK}"/>
    <circle cx="{CANVAS_X + CANVAS / 2}" cy="{CANVAS_Y + CANVAS / 2}" r="330" fill="url(#blueGlow)"/>
    <circle cx="90" cy="{H - 40}" r="300" fill="url(#redGlow)"/>
    <rect width="{W}" height="3" fill="url(#tricolore)"/>
    <rect y="{H - 3}" width="{W}" height="3" fill="url(#tricolore)"/>
  </g>
{hero()}
{career()}
{changelog()}
{footer()}
</svg>
"""


# ── Links: one panel cut in three images, since each needs its own <a> in the README ──

LINKS = [
    ("connect-left.svg", "LinkedIn", "tom-klotz", "linkedin"),
    ("connect-mid.svg", "Photoroom", "photoroom.com", "photoroom"),
    ("connect-right.svg", "Pixelheim", "my retro pixel-art RPG", "pixelheim"),
]
LINK_WIDTHS = [333, 334, 333]
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
    card_x = 20 if index == 0 else 10
    card_w = width - card_x - (20 if index == len(LINKS) - 1 else 10)
    return f"""<svg width="{width}" height="{LINK_HEIGHT}" viewBox="0 0 {width} {LINK_HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}: {detail}">
  <defs><clipPath id="panel"><rect x="{-offset}" width="{W}" height="{LINK_HEIGHT}" rx="20"/></clipPath></defs>
  <style>text {{ font-family: {SANS}; }} .mono {{ font-family: {MONO}; }}</style>
  <g clip-path="url(#panel)">
    <rect x="{-offset}" width="{W}" height="{LINK_HEIGHT}" fill="{INK}"/>
    <rect x="{-offset}" y="{LINK_HEIGHT - 3}" width="{W}" height="3" fill="url(#tricolore)"/>
  </g>
  <defs><linearGradient id="tricolore" x1="{-offset}" y1="0" x2="{W - offset}" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{FRANCE_BLUE}"/><stop offset="0.5" stop-color="#F5F7FA"/><stop offset="1" stop-color="{FRANCE_RED}"/>
  </linearGradient></defs>
  <rect x="{card_x}" y="20" width="{card_w}" height="70" rx="14" fill="{PANEL}" stroke="{LINE}"/>
  {link_icon(kind, card_x + 16, 35)}
  <text x="{card_x + 70}" y="51" font-size="17" font-weight="700" fill="{TEXT}">{esc(title)}</text>
  <text x="{card_x + 70}" y="72" class="mono" font-size="13" fill="{MUTED}">{esc(detail)}</text>
  <text x="{card_x + card_w - 18}" y="61" text-anchor="end" font-size="18" fill="{FAINT}">↗</text>
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")
    for i, (file_name, *_rest) in enumerate(LINKS):
        (ROOT / "assets" / file_name).write_text(link_slice(i))
        print(f"wrote assets/{file_name}")
