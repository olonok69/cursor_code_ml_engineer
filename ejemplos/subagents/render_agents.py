#!/usr/bin/env python3
"""
Renderiza agents.png — subagentes vs agent teams — en el estilo del deck.
Offline, solo Pillow (igual que ../metodologia/render_flow.py).

    pip install pillow
    python render_agents.py      # -> agents.png

La fuente conceptual editable es agents.mmd; si cambias la arquitectura, actualiza ambos.
"""
from PIL import Image, ImageDraw, ImageFont

SS = 2
BG     = (15, 20, 26)
PANEL  = (26, 33, 43)
PANEL2 = (34, 43, 56)
STROKE = (46, 57, 72)
CORAL  = (217, 119, 87)
BLUE   = (122, 162, 199)
GREEN  = (140, 194, 140)
TEXT   = (232, 234, 237)
MUTED  = (154, 164, 178)

W, H = 1560, 760
img = Image.new("RGB", (W * SS, H * SS), BG)
d = ImageDraw.Draw(img)


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size * SS)


def rr(x, y, w, h, r=14, fill=PANEL, outline=STROKE, width=1):
    d.rounded_rectangle([x*SS, y*SS, (x+w)*SS, (y+h)*SS], radius=r*SS,
                        fill=fill, outline=outline, width=width*SS)


def ctext(cx, cy, txt, fnt, fill=TEXT):
    b = d.textbbox((0, 0), txt, font=fnt)
    d.text((cx*SS - (b[2]-b[0])/2, cy*SS - (b[3]-b[1])/2 - b[1]), txt, font=fnt, fill=fill)


def ltext(x, y, txt, fnt, fill=TEXT):
    d.text((x*SS, y*SS), txt, font=fnt, fill=fill)


def arrow(x1, y1, x2, y2, color=MUTED, width=2, both=False):
    d.line([x1*SS, y1*SS, x2*SS, y2*SS], fill=color, width=width*SS)
    import math
    ang = math.atan2(y2-y1, x2-x1)
    for (tx, ty, a) in ([(x2, y2, ang)] + ([(x1, y1, ang + math.pi)] if both else [])):
        p = [(tx*SS, ty*SS)]
        for da in (2.6, -2.6):
            p.append(((tx - 12*math.cos(a+da*0.5))*SS, (ty - 12*math.sin(a+da*0.5))*SS))
        d.polygon(p, fill=color)


f_t  = font(24, True)
f_h  = font(17, True)
f_b  = font(14, True)
f_s  = font(12)
f_xs = font(11)

ltext(40, 28, "Subagentes vs. Agent Teams — dos formas de escalar", f_t, TEXT)
ltext(40, 66, "Subagente: contexto aislado, vuelve un resumen.  Team: sesiones completas + task list compartida + mensajería.", f_s, MUTED)

# ---------------- panel izquierdo: SUBAGENTES ----------------
rr(40, 110, 700, 560, r=18, fill=(20, 26, 34), outline=STROKE)
ltext(66, 130, "SUBAGENTES  (tool Task)", f_h, BLUE)
ltext(66, 160, "coste bajo · lo caro muere con el subagente", f_xs, MUTED)

# sesión principal
rr(80, 210, 240, 170, fill=PANEL2, outline=BLUE, width=2)
ctext(200, 250, "Sesión principal", f_b, TEXT)
ctext(200, 280, "tu contexto", f_s, MUTED)
ctext(200, 305, "(no se ensucia)", f_s, MUTED)

subs = [("Explore", "read-only"), ("Plan", "arquitectura"),
        ("custom  .claude/agents/*.md", "security-reviewer · refactor-scout")]
for i, (t, sub) in enumerate(subs):
    y = 200 + i * 150
    rr(430, y, 280, 100, fill=PANEL, outline=STROKE)
    ctext(570, y + 32, t, f_b, TEXT)
    ctext(570, y + 62, sub, f_xs, MUTED)
    arrow(320, 270, 430, y + 35, color=MUTED)          # prompt →
    arrow(430, y + 72, 322, 320, color=GREEN)          # resumen ←
ltext(340, 190, "prompt con contexto", f_xs, MUTED)
ltext(330, 560, "solo el RESUMEN vuelve", f_xs, GREEN)
ltext(66, 630, "El subagente NO hereda tu conversación: dale el contexto en el prompt.", f_xs, CORAL)

# ---------------- panel derecho: AGENT TEAM ----------------
rr(790, 110, 730, 560, r=18, fill=(20, 26, 34), outline=STROKE)
ltext(816, 130, "AGENT TEAM  (experimental)", f_h, CORAL)
ltext(816, 160, "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 · coste alto: cada teammate = una sesión", f_xs, MUTED)

# lead
rr(1040, 205, 230, 105, fill=PANEL2, outline=CORAL, width=2)
ctext(1155, 240, "Lead", f_b, TEXT)
ctext(1155, 270, "sesión completa", f_s, MUTED)

# teammates
rr(850, 400, 230, 105, fill=PANEL, outline=STROKE)
ctext(965, 435, "Teammate A", f_b, TEXT)
ctext(965, 465, "sesión completa", f_s, MUTED)
rr(1230, 400, 230, 105, fill=PANEL, outline=STROKE)
ctext(1345, 435, "Teammate B", f_b, TEXT)
ctext(1345, 465, "sesión completa", f_s, MUTED)

arrow(1090, 310, 985, 400, color=MUTED, both=True)
arrow(1220, 310, 1325, 400, color=MUTED, both=True)
arrow(1080, 452, 1230, 452, color=BLUE, both=True)
ctext(1155, 432, "mensajería directa (inboxes)", f_xs, BLUE)

# task list compartida
rr(940, 560, 430, 72, fill=PANEL2, outline=GREEN, width=2)
ctext(1155, 583, "Task list compartida", f_b, GREEN)
ctext(1155, 610, "~/.claude/tasks/<team>/  ·  sobrevive al resume", f_xs, MUTED)
for x in (965, 1155, 1345):
    d.line([x*SS, 505*SS if x != 1155 else 310*SS, x*SS, 560*SS], fill=STROKE, width=2*SS)

ltext(816, 645, "Particiona los ficheros: cada teammate es dueño de los suyos.", f_xs, CORAL)

# footer
ltext(40, 706, "Regla: side-quest de investigación → subagente.  Trabajo paralelo real que necesita debate → team.", f_s, GREEN)

img = img.resize((W, H), Image.LANCZOS)
img.save("agents.png")
print(f"OK -> agents.png  ({W}x{H})")
