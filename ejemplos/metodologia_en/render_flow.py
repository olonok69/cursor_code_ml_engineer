#!/usr/bin/env python3
"""
Renders the 11-stage flow (flow.mmd) to a PNG readable in any Markdown viewer
(GitHub, VS Code, Confluence). Offline, no external deps beyond Pillow.

    pip install pillow
    python render_flow.py        # -> flow.png

Gates are coral; a red gate = STOP (do not write code). The .mmd remains
the editable source; re-run this if you change the flow.
"""
from PIL import Image, ImageDraw, ImageFont

SS = 2  # supersampling for sharpness

# palette (same as the deck)
BG     = (15, 20, 26)
PANEL  = (26, 33, 43)
STROKE = (46, 57, 72)
CORAL  = (217, 119, 87)
BLUE   = (122, 162, 199)
GREEN  = (140, 194, 140)
RED    = (200, 90, 80)
TEXT   = (232, 234, 237)
MUTED  = (154, 164, 178)

def font(size, bold=False):
    import os
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates = (
        ["DejaVuSans-Bold.ttf", os.path.join(windir, "Fonts", "seguisb.ttf"),
         os.path.join(windir, "Fonts", "arialbd.ttf")]
        if bold else
        ["DejaVuSans.ttf", os.path.join(windir, "Fonts", "segoeui.ttf"),
         os.path.join(windir, "Fonts", "arial.ttf")]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size * SS)
        except OSError:
            continue
    return ImageFont.load_default()

# (num, label, is_gate, branch_note)
NODES = [
    ("1",  "Orient — history-first AND status-first", False, None),
    ("2",  "Inbound triage: is the symptom real on the output contract?", True,
           "No (downstream) →  PUSH BACK · do not write code"),
    ("3",  "Regression vs. pre-existing — prove it before assuming", True, None),
    ("4",  "Investigate — cheap deterministic oracle first (still no LLM)", False, None),
    ("5",  "Plan — options + trade-offs", True,
           "Human agrees?  No → refine the plan"),
    ("6",  "Implement — TDD  RED → GREEN, minimal change", False, None),
    ("7",  "Verify — unit + scoped + regression + outbound gate", True,
           "Contract not reproduced → go back to investigate"),
    ("8",  "Document — the why, the what, the handover (each once)", False, None),
    ("9",  "Sanitise — scan added lines (names/IDs/secrets)", False, None),
    ("10", "Handoff — the human does push / PR / deploy", False, None),
    ("11", "Automated review + persist lessons", True,
           "Valid findings → go back to implement"),
]

# geometry (logical px, then x SS)
W = 1520
NX, NW, NH = 70, 760, 104
GAP = 46
TOP = 172
node_y = lambda i: TOP + i * (NH + GAP)
H = node_y(len(NODES)) + 150

img = Image.new("RGB", (W * SS, H * SS), BG)
d = ImageDraw.Draw(img)

def rr(x, y, w, h, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle([x*SS, y*SS, (x+w)*SS, (y+h)*SS], radius=radius*SS,
                        fill=fill, outline=outline, width=width*SS)

def center_text(cx, cy, txt, fnt, fill):
    b = d.textbbox((0, 0), txt, font=fnt)
    d.text((cx*SS - (b[2]-b[0])/2, cy*SS - (b[3]-b[1])/2 - b[1]), txt, font=fnt, fill=fill)

def left_text(x, cy, txt, fnt, fill):
    b = d.textbbox((0, 0), txt, font=fnt)
    d.text((x*SS, cy*SS - (b[3]-b[1])/2 - b[1]), txt, font=fnt, fill=fill)

def wrap(txt, fnt, max_w):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= max_w*SS:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

f_title = font(26, True)
f_sub   = font(14)
f_num   = font(20, True)
f_label = font(16, True)
f_note  = font(13)
f_leg   = font(13)

# title + legend
left_text(NX, 52, "Agent workflow (Cursor) — 11 stages", f_title, TEXT)
left_text(NX, 92, "The agent is a disciplined collaborator; each diamond is a GATE (decision point).",
          f_sub, MUTED)
# color legend
lx = NX
rr(lx, 116, 22, 14, 4, fill=PANEL, outline=STROKE, width=1)
left_text(lx+30, 123, "stage", f_leg, MUTED)
rr(lx+120, 116, 22, 14, 4, fill=CORAL)
left_text(lx+150, 123, "gate (decision)", f_leg, MUTED)
rr(lx+320, 116, 22, 14, 4, fill=RED)
left_text(lx+350, 123, "red branch = STOP", f_leg, MUTED)

for i, (num, label, gate, note) in enumerate(NODES):
    y = node_y(i)
    acc = CORAL if gate else BLUE
    # connector to next
    if i < len(NODES) - 1:
        cx = (NX + 26)  # badge center
        d.line([cx*SS, (y+NH)*SS, cx*SS, (y+NH+GAP)*SS], fill=STROKE, width=3*SS)
        d.polygon([((cx-6)*SS, (y+NH+GAP-2)*SS), ((cx+6)*SS, (y+NH+GAP-2)*SS),
                   (cx*SS, (y+NH+GAP+8)*SS)], fill=STROKE)
    # box
    rr(NX, y, NW, NH, 16, fill=PANEL, outline=(CORAL if gate else STROKE), width=2 if gate else 1)
    # numbered badge
    rr(NX+16, y+NH/2-22, 44, 44, 12, fill=acc)
    center_text(NX+16+22, y+NH/2, num, f_num, BG)
    # label (wrap to 2 lines)
    lines = wrap(label, f_label, NW-110)
    ly = y + NH/2 - (len(lines)-1)*13
    for ln in lines:
        left_text(NX+80, ly, ln, f_label, TEXT)
        ly += 26
    # branch note (to the right)
    if note:
        nx = NX + NW + 40
        col = RED if ("STOP" in note or "PUSH BACK" in note) else MUTED
        # short arrow from the box
        d.line([(NX+NW)*SS, (y+NH/2)*SS, (nx-12)*SS, (y+NH/2)*SS], fill=col, width=2*SS)
        nlines = wrap(note, f_note, 560)
        nyy = y + NH/2 - (len(nlines)-1)*10
        for ln in nlines:
            left_text(nx, nyy, ln, f_note, col)
            nyy += 20

# loop arrow: from the last stage back to the start.
# Routed via a right lane (x_lane), with horizontal segments
# BELOW stage 11 and at stage 1 height, so they do not cross notes.
badge_x = NX + 26
y1c     = node_y(0) + NH / 2
y11_bot = node_y(len(NODES)-1) + NH
y_bot   = y11_bot + 34
x_lane  = W - 30                       # farther right than notes (which end ~1430)
def gline(x1, y1, x2, y2):
    d.line([x1*SS, y1*SS, x2*SS, y2*SS], fill=GREEN, width=2*SS)
gline(badge_x, y11_bot, badge_x, y_bot)      # down from stage 11
gline(badge_x, y_bot, x_lane, y_bot)         # across below (empty zone)
gline(x_lane, y_bot, x_lane, y1c)            # up the right lane
gline(x_lane, y1c, NX + NW, y1c)             # into stage 1
d.polygon([((NX+NW+12)*SS, (y1c-6)*SS), ((NX+NW+12)*SS, (y1c+6)*SS),
           ((NX+NW)*SS, y1c*SS)], fill=GREEN)
left_text(badge_x + 24, y_bot - 22, "closes the loop  →  next task", f_note, GREEN)

img = img.resize((W, H), Image.LANCZOS)
img.save("flow.png")
print(f"OK -> flow.png  ({W}x{H})")
