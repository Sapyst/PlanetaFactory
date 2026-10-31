#!/usr/bin/env python3
"""Fase 5: junta as fotos de arte/estudos/fotos/final/ (roteiro fotos_finais) num ÚNICO painel.
Uso: painel_final.py "<linha 1 do resultado>" "<linha 2>" ...  → fotos/painel_final.png (e .jpg menor)."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(AQUI, "fotos", "final")
JOGO = os.path.join(AQUI, "..", "..", "jogo", "dados")
COLS, CEL_W, CEL_H, LEG, GAP, MARGEM = 9, 432, 243, 58, 8, 16
LARG = MARGEM * 2 + COLS * CEL_W + (COLS - 1) * GAP
FUNDO, TXT, FRACO, FAIXA = (24, 26, 30), (236, 236, 232), (170, 172, 170), (58, 66, 76)
FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/TTF/DejaVuSans.ttf"
if not os.path.exists(FB):
    FB, FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f_tit, f_res, f_cat, f_nome, f_info = (ImageFont.truetype(FB, 44), ImageFont.truetype(FR, 25), ImageFont.truetype(FB, 30),
                                       ImageFont.truetype(FB, 21), ImageFont.truetype(FR, 16))

menu = json.load(open(os.path.join(JOGO, "menu_construcao.json"), encoding="utf8"))
dados = json.load(open(os.path.join(FINAL, "dados.json"), encoding="utf8"))
mods = dados["modelos"]
rot = menu["rotulos"]
modelo_de = {"esteira": "esteira_reta", "cano": "cano_reto", "trem": "locomotiva", "trem_tanque": "vagao_tanque", "trem_eletrico": "locomotiva_eletrica",
             "rampa_desce": "esteira_rampa", "muro_centro": "muro_centro", "nucleo_queda_fim": "nucleo_queda"}
EXTRA = ["nucleo", "ninho_aranha", "plataforma_agua", "ponte_agua", "plataforma_grade", "plataforma_rio", "poca_seiva", "nucleo_queda", "nucleo_queda_fim", "aranha_montada",
         "drone_reparo", "drone_defesa", "drone_logistico"]
NOMES_EXTRA = {"nucleo": "Núcleo", "ninho_aranha": "Ninho de aranha", "plataforma_agua": "Plataforma na água", "ponte_agua": "Ponte na água",
               "nucleo_queda": "Cápsula do núcleo (descendo)", "nucleo_queda_fim": "Cápsula do núcleo (último quadro)", "aranha_montada": "Aranha (a do jogo, com IK)",
               "plataforma_grade": "Emenda: plataformas e pontes", "plataforma_rio": "Plataformas e ponte no rio", "poca_seiva": "Poça de seiva", "drone_reparo": "Drone de reparo", "drone_defesa": "Drone de combate",
               "drone_logistico": "Drone logístico"}
cats = [(c["nome"], c["pecas"]) for c in menu["categorias"]] + [("Fora do menu (conferência)", EXTRA)]


def cortar(t, fonte, w, d):
    while d.textlength(t, font=fonte) > w and len(t) > 3:
        t = t[:-2].rstrip("…") + "…"
    return t


cab = 70 + 34 * len(sys.argv[1:]) + 12
alt = MARGEM + cab
for _, ps in cats:
    alt += 54 + ((len(ps) + COLS - 1) // COLS) * (CEL_H + LEG + GAP) + 6
img = Image.new("RGB", (LARG, alt), FUNDO)
d = ImageDraw.Draw(img)
n_fotos = sum(len(p) for _, p in cats)
d.text((MARGEM, MARGEM), "PlanetaFactory: todas as estruturas no jogo (%d fotos)" % n_fotos, font=f_tit, fill=TXT)
y = MARGEM + 66
for lin in sys.argv[1:]:
    d.text((MARGEM, y), lin, font=f_res, fill=TXT)
    y += 34
y = MARGEM + cab
faltou = []
for nome_cat, ps in cats:
    d.rectangle((MARGEM, y, LARG - MARGEM, y + 42), fill=FAIXA)
    d.text((MARGEM + 10, y + 3), "%s (%d)" % (nome_cat, len(ps)), font=f_cat, fill=TXT)
    y += 54
    for i, p in enumerate(ps):
        x = MARGEM + (i % COLS) * (CEL_W + GAP)
        yy = y + (i // COLS) * (CEL_H + LEG + GAP)
        cam = os.path.join(FINAL, p + ".jpg")
        if os.path.exists(cam):
            im = Image.open(cam).convert("RGB")
            im.thumbnail((CEL_W, CEL_H), Image.LANCZOS)
            img.paste(im, (x, yy))
        else:
            faltou.append(p)
            d.rectangle((x, yy, x + CEL_W, yy + CEL_H), fill=(90, 20, 20))
        nome = rot.get(p, NOMES_EXTRA.get(p, p))
        d.text((x + 2, yy + CEL_H + 3), cortar(nome, f_nome, CEL_W - 4, d), font=f_nome, fill=TXT)
        m = mods.get(modelo_de.get(p, p), {})
        inf = p
        if m:
            t = m["tam"]
            inf = "%s · %s tris · %.1f×%.1f×%.1f m" % (p, format(m["tris"], ",").replace(",", "."), t[0], t[2], t[1])
        d.text((x + 2, yy + CEL_H + 30), cortar(inf, f_info, CEL_W - 4, d), font=f_info, fill=FRACO)
    y += ((len(ps) + COLS - 1) // COLS) * (CEL_H + LEG + GAP) + 6
saida = os.path.join(AQUI, "fotos", "painel_final.png")
img.save(saida, optimize=True)
pequena = img.copy()
pequena.thumbnail((2600, 99999), Image.LANCZOS)
pequena.save(saida[:-3] + "jpg", quality=88)
print(saida, img.size, os.path.getsize(saida) // 1024 // 1024, "MB; faltou:", faltou)
