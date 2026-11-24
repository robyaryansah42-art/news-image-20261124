#!/usr/bin/env python3
"""THE GLOBAL LEDGER -- front page summing up world news of Tuesday 24 November 2026.

Pure standard-library Python (no PIL, no network): draws the whole newspaper
front page into an RGB buffer with a hand-built 5x7 bitmap font, then writes a
deterministic PNG (fixed zlib level, no timestamps) to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png outside the grader).
"""

import math
import os
import struct
import zlib
from binascii import crc32

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 characters; '#' is ink, '.' is blank.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "•": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}
# Normalise fancy punctuation to glyphs we have.
NORMALISE = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "·": "•"}


def glyph(ch):
    ch = NORMALISE.get(ch, ch)
    return FONT.get(ch.upper() if ch.isalpha() else ch, FONT["?"])


def char_advance(scale):
    return 5 * scale + max(1, scale // 4)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * char_advance(scale) - max(1, scale // 4)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if text_width(trial, scale) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
W, H = 1024, 1024
PAPER = (246, 241, 229)
INK = (17, 17, 17)
RED = (179, 35, 27)
BLUE = (0, 51, 153)
GOLD = (255, 204, 0)
NAVY = (16, 42, 92)
GREY = (110, 108, 100)
LIGHT_BLUE = (214, 226, 240)
DARK_GREEN = (24, 64, 44)
ORANGE = (214, 110, 20)

buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3] = PAPER[0]
    buf[_i * 3 + 1] = PAPER[1]
    buf[_i * 3 + 2] = PAPER[2]


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        if 0 <= yy < H:
            base = (yy * W + max(x, 0)) * 3
            for xx in range(max(x, 0), min(x + w, W)):
                buf[base], buf[base + 1], buf[base + 2] = c
                base += 3


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def fill_poly(points, c):
    """Scanline fill of a simple polygon (list of (x, y))."""
    if not points:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[k])), min(W, int(xs[k + 1]) + 1)):
                px(x, y, c)


def disc(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(x, y, c)


def ring(cx, cy, r, c, t=2):
    for y in range(cy - r - t, cy + r + t + 1):
        for x in range(cx - r - t, cx + r + t + 1):
            d = math.hypot(x - cx, y - cy)
            if r - t <= d <= r + t:
                px(x, y, c)


def star_points(cx, cy, r_out, r_in, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / 5
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts


def draw_text(x, y, text, scale, color, align="left"):
    """Draw uppercase bitmap text; (x, y) is the top-left (or anchor)."""
    text = "".join(NORMALISE.get(ch, ch) for ch in text)
    w = text_width(text, scale)
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    adv = char_advance(scale)
    cx = x
    for ch in text:
        g = glyph(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "#":
                    rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += adv
    return w


def draw_lines(x, y, lines, scale, color, leading=None):
    lh = leading if leading is not None else 7 * scale + max(4, scale)
    for line in lines:
        draw_text(x, y, line, scale, color)
        y += lh
    return y


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, width, height, rgb):
    raw = b"".join(
        b"\x00" + bytes(rgb[y * width * 3:(y + 1) * width * 3])
        for y in range(height)
    )
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(raw, 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- front page
MX = 32            # left/right margin of the text block
CW = W - 2 * MX    # 960 content width


def rule(y, t=2, color=INK):
    hline(MX, y, CW, color, t)


def draw_eu_flag(x, y, w, h):
    """EU flag panel: blue field, ring of 12 gold stars, '22ND PACKAGE' label."""
    rect(x, y, w, h, BLUE)
    rect(x, y, w, 3, GOLD)
    rect(x, y + h - 3, w, 3, GOLD)
    cx, cy = x + w // 2, y + h // 2 - 8
    r = 34
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        sx = int(cx + r * math.cos(a))
        sy = int(cy + r * math.sin(a))
        fill_poly(star_points(sx, sy, 7, 3), GOLD)
    draw_text(x + w // 2, y + h - 24, "22ND PACKAGE", 2, GOLD, align="center")


def draw_ship(x, y, w, h):
    """Simple warship silhouette on waves, with smoke."""
    rect(x, y, w, h, LIGHT_BLUE)
    # smoke
    disc(x + 70, y + 12, 7, GREY)
    disc(x + 82, y + 7, 6, GREY)
    disc(x + 94, y + 12, 5, GREY)
    # hull
    fill_poly([(x + 8, y + 30), (x + w - 8, y + 30), (x + w - 26, y + 50),
               (x + 22, y + 50)], NAVY)
    # deck + superstructure
    rect(x + 60, y + 18, 60, 12, NAVY)
    rect(x + 130, y + 12, 26, 18, NAVY)
    # mast + funnel
    vline(x + 150, y + 4, 26, NAVY, 3)
    rect(x + 96, y + 14, 12, 16, RED)
    # waves
    for i, wx in enumerate(range(x + 4, x + w - 4, 26)):
        hline(wx, y + h - 8 - (i % 2) * 3, 16, BLUE, 2)


def draw_chip(x, y, w, h):
    """Computer chip with a rising arrow -- the $1tn rally."""
    rect(x, y, w, h, DARK_GREEN)
    # pins
    for i in range(6):
        rect(x + 14 + i * 34, y - 0, 10, 6, GOLD)
        rect(x + 14 + i * 34, y + h - 6, 10, 6, GOLD)
    # die
    rect(x + 26, y + 12, w - 52, h - 24, INK)
    draw_text(x + 40, y + 18, "$1TN", 3, GOLD)
    # rising arrow (starts right of the label)
    pts = [(x + 130, y + h - 16), (x + 190, y + h - 30), (x + 230, y + h - 26),
           (x + w - 46, y + 22)]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for s in range(steps + 1):
            px(int(x1 + (x2 - x1) * s / steps), int(y1 + (y2 - y1) * s / steps), GOLD)
            px(int(x1 + (x2 - x1) * s / steps), int(y1 + (y2 - y1) * s / steps) + 1, GOLD)
    fill_poly([(x + w - 46, y + 22), (x + w - 62, y + 24), (x + w - 48, y + 38)], GOLD)


def build_page():
    # outer frame
    rect(8, 8, W - 16, 3, INK)
    rect(8, H - 11, W - 16, 3, INK)
    rect(8, 8, 3, H - 16, INK)
    rect(W - 11, 8, 3, H - 16, INK)

    # ---- masthead
    draw_text(W // 2, 26, "THE GLOBAL LEDGER", 9, INK, align="center")
    rule(98, 3)
    draw_text(MX, 108, "WORLD EDITION", 3, INK)
    draw_text(W // 2, 108, "TUESDAY, 24 NOVEMBER 2026", 3, RED, align="center")
    draw_text(W - MX, 108, "NO. 328", 3, INK, align="right")
    rule(134, 2)

    # ---- lead story: EU sanctions
    draw_text(MX, 146, "EUROPE  •  LEAD STORY", 3, RED)
    draw_lines(MX, 172, ["EU UNVEILS 22ND SANCTIONS", "PACKAGE AGAINST RUSSIA"], 6, INK)
    # graphic left, subhead right
    draw_eu_flag(MX, 280, 300, 108)
    sub = ("BRUSSELS PROPOSES BANS ON RUSSIAN TEAMS AND ATHLETES UNDER THE "
           "RUSSIAN FLAG, PLUS CURBS ON BANKS, CRYPTO PLATFORMS AND "
           "EX-COMBATANTS.")
    lines = wrap_text(sub, 3, 624)
    draw_lines(MX + 336, 280, lines, 3, INK)
    rule(400, 2)

    # ---- row 2: two stories
    col_w = (CW - 24) // 2
    x2 = MX + col_w + 24

    draw_text(MX, 412, "UKRAINE  •  WAR AT SEA", 3, RED)
    draw_lines(MX, 438, ["UKRAINE SAYS IT SANK", "A RUSSIAN WARSHIP", "OFF LIBYA"], 4, INK)
    draw_ship(MX, 554, col_w, 56)
    sub = "KYIV SAYS IT SANK A RUSSIAN CORVETTE OFF LIBYA."
    draw_lines(MX, 618, wrap_text(sub, 3, col_w), 3, INK)

    draw_text(x2, 412, "TECH  •  MARKETS", 3, RED)
    draw_lines(x2, 438, ["HUANG IS BACK:", "NVIDIA CLIMBS", "NEARLY $1TN"], 4, INK)
    draw_chip(x2, 554, col_w, 56)
    sub = "TECH STOCKS RALLY AS HUANG RETURNS AS CHIEF EXECUTIVE."
    draw_lines(x2, 618, wrap_text(sub, 3, col_w), 3, INK)
    rule(682, 2)

    # ---- row 3: three stories
    c3 = (CW - 2 * 20) // 3
    xs = [MX, MX + c3 + 20, MX + 2 * (c3 + 20)]
    stories = [
        ("INDONESIA", ["CIKANDE FACTORY", "FIRE TOLL: 24"],
         "RESCUERS HUNT FOR 30 MISSING WORKERS."),
        ("JUSTICE", ["MYANMAR GUILTY", "OF ROHINGYA", "GENOCIDE"],
         "A LANDMARK VERDICT AT THE HAGUE."),
        ("WASHINGTON", ["TRUMP BLAMES", "DEMOCRATS FOR", "MARKET ROUT"],
         "WALL STREET SHED $1TN IN A SELL-OFF."),
    ]
    for i, (kick, head, sub) in enumerate(stories):
        x = xs[i]
        draw_text(x, 694, kick, 3, RED)
        draw_lines(x, 720, head, 3, INK)
        draw_lines(x, 808, wrap_text(sub, 3, c3), 3, GREY)
    rule(872, 2)

    # ---- also today
    draw_text(MX, 884, "ALSO TODAY", 3, RED)
    also = ("ALCARAZ WINS ATP FINALS IN TURIN  •  GUKESH DEFENDS CHESS CROWN "
            "IN GENEVA  •  COP31: NO FOSSIL-FUEL DEAL  •  BOAT CAPSIZES OFF "
            "SENEGAL  •  WAYMO HALTS FREEWAY TAXIS")
    draw_lines(MX, 910, wrap_text(also, 3, CW), 3, INK)


def main():
    build_page()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, W, H, buf)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
