#!/usr/bin/env python3
"""
Renderiza el flujo de 11 etapas (flow.mmd) a un PNG legible en cualquier visor
de Markdown (GitHub, VS Code, Confluence). Offline, sin dependencias externas
salvo Pillow.

    pip install pillow
    python render_flow.py        # -> flow.png

Los gates van en coral; un gate rojo = STOP (no escribir código). El .mmd sigue
siendo la fuente editable; re-ejecuta esto si cambias el flujo.
"""
from PIL import Image, ImageDraw, ImageFont

SS = 2  # supersampling para nitidez

# paleta (igual que el deck)
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
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size * SS)

# (num, etiqueta, es_gate, nota_de_rama)
NODES = [
    ("1",  "Orientar — history-first Y status-first", False, None),
    ("2",  "Triaje inbound: ¿el síntoma es real en el contrato de salida?", True,
           "No (aguas abajo) →  PUSH BACK · no escribir código"),
    ("3",  "Regresión vs. pre-existente — probarlo antes de asumir", True, None),
    ("4",  "Investigar — oráculo determinista barato primero (aún sin LLM)", False, None),
    ("5",  "Plan — opciones + trade-offs", True,
           "¿Humano de acuerdo?  No → refinar el plan"),
    ("6",  "Implementar — TDD  RED → GREEN, cambio mínimo", False, None),
    ("7",  "Verificar — unit + scoped + regresión + gate outbound", True,
           "Contrato no reproducido → volver a investigar"),
    ("8",  "Documentar — el porqué, el qué, el handover (cada cosa una vez)", False, None),
    ("9",  "Sanitizar — escanear las líneas añadidas (nombres/IDs/secretos)", False, None),
    ("10", "Handoff — el humano hace push / PR / deploy", False, None),
    ("11", "Revisión automática + persistir lecciones", True,
           "Hallazgos válidos → volver a implementar"),
]

# geometría (px lógicos, luego x SS)
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

# título + leyenda
left_text(NX, 52, "Flujo de trabajo con Claude Code — 11 etapas", f_title, TEXT)
left_text(NX, 92, "El agente es un colaborador disciplinado; cada rombo es un GATE (punto de decisión).",
          f_sub, MUTED)
# leyenda de color
lx = NX
rr(lx, 116, 22, 14, 4, fill=PANEL, outline=STROKE, width=1)
left_text(lx+30, 123, "etapa", f_leg, MUTED)
rr(lx+120, 116, 22, 14, 4, fill=CORAL)
left_text(lx+150, 123, "gate (decisión)", f_leg, MUTED)
rr(lx+320, 116, 22, 14, 4, fill=RED)
left_text(lx+350, 123, "rama roja = STOP", f_leg, MUTED)

for i, (num, label, gate, note) in enumerate(NODES):
    y = node_y(i)
    acc = CORAL if gate else BLUE
    # conector al siguiente
    if i < len(NODES) - 1:
        cx = (NX + 26)  # centro del badge
        d.line([cx*SS, (y+NH)*SS, cx*SS, (y+NH+GAP)*SS], fill=STROKE, width=3*SS)
        d.polygon([((cx-6)*SS, (y+NH+GAP-2)*SS), ((cx+6)*SS, (y+NH+GAP-2)*SS),
                   (cx*SS, (y+NH+GAP+8)*SS)], fill=STROKE)
    # caja
    rr(NX, y, NW, NH, 16, fill=PANEL, outline=(CORAL if gate else STROKE), width=2 if gate else 1)
    # badge numerado
    rr(NX+16, y+NH/2-22, 44, 44, 12, fill=acc)
    center_text(NX+16+22, y+NH/2, num, f_num, BG)
    # etiqueta (wrap a 2 líneas)
    lines = wrap(label, f_label, NW-110)
    ly = y + NH/2 - (len(lines)-1)*13
    for ln in lines:
        left_text(NX+80, ly, ln, f_label, TEXT)
        ly += 26
    # nota de rama (a la derecha)
    if note:
        nx = NX + NW + 40
        col = RED if ("STOP" in note or "PUSH BACK" in note) else MUTED
        # flecha corta desde la caja
        d.line([(NX+NW)*SS, (y+NH/2)*SS, (nx-12)*SS, (y+NH/2)*SS], fill=col, width=2*SS)
        nlines = wrap(note, f_note, 560)
        nyy = y + NH/2 - (len(nlines)-1)*10
        for ln in nlines:
            left_text(nx, nyy, ln, f_note, col)
            nyy += 20

# flecha de bucle: de la última etapa de vuelta al inicio.
# Se enruta por un carril a la derecha (x_lane), con los tramos horizontales
# por DEBAJO de la etapa 11 y a la altura de la etapa 1, para no cruzar notas.
badge_x = NX + 26
y1c     = node_y(0) + NH / 2
y11_bot = node_y(len(NODES)-1) + NH
y_bot   = y11_bot + 34
x_lane  = W - 30                       # más a la derecha que las notas (que acaban ~1430)
def gline(x1, y1, x2, y2):
    d.line([x1*SS, y1*SS, x2*SS, y2*SS], fill=GREEN, width=2*SS)
gline(badge_x, y11_bot, badge_x, y_bot)      # baja desde la etapa 11
gline(badge_x, y_bot, x_lane, y_bot)         # cruza por debajo (zona vacía)
gline(x_lane, y_bot, x_lane, y1c)            # sube por el carril derecho
gline(x_lane, y1c, NX + NW, y1c)             # entra a la etapa 1
d.polygon([((NX+NW+12)*SS, (y1c-6)*SS), ((NX+NW+12)*SS, (y1c+6)*SS),
           ((NX+NW)*SS, y1c*SS)], fill=GREEN)
left_text(badge_x + 24, y_bot - 22, "cierra el bucle  →  siguiente tarea", f_note, GREEN)

img = img.resize((W, H), Image.LANCZOS)
img.save("flow.png")
print(f"OK -> flow.png  ({W}x{H})")
