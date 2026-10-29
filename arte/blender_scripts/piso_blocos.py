"""Tentativas de piso de fábrica em BLOCOS BRUTOS (estilo Factorio): blocos assentados em fiadas, tamanhos variados,
juntas fundas, bisel com luz de cima-esquerda (cada bloco tem volume), quinas lascadas por ruído, tom e textura
própria por bloco. Em loop sem emenda (512 px = 4 m). Python puro.
Uso: python3 piso_blocos.py <estilo> [saida.png]   estilos: laje, pedra, ia"""
import math, os, random, struct, sys, zlib

N = 512
ESTILO = sys.argv[1] if len(sys.argv) > 1 else 'pedra'
SAIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'texturas', 'piso_%s.png' % ESTILO)
random.seed({'laje': 3, 'pedra': 7, 'ia': 11}[ESTILO])

CFG = {
    # altura das fiadas (px), largura dos blocos (min, máx px), junta, bisel, lascas, cor base, variação de tom
    'laje':  dict(fiada=(96, 160), larg=(110, 260), junta=4, bisel=9,  lasca=7, cor=(0.47, 0.46, 0.44), var=0.07, grao=0.07),
    'pedra': dict(fiada=(48, 80),  larg=(48, 120),  junta=5, bisel=8,  lasca=9, cor=(0.43, 0.41, 0.38), var=0.12, grao=0.10),
    'ia':    dict(fiada=(128, 128), larg=(128, 256), junta=3, bisel=6, lasca=2, cor=(0.20, 0.22, 0.24), var=0.04, grao=0.04),
}[ESTILO]

ondas = [(random.randint(1, 12), random.randint(1, 12), random.uniform(0, math.tau), random.uniform(0.3, 1.0) / (1 + i * 0.3)) for i in range(30)]
finas = [(random.randint(10, 40), random.randint(10, 40), random.uniform(0, math.tau), random.uniform(0.3, 1.0)) for i in range(16)]


def ruido(x, y, os_=ondas):
    return sum(a * math.sin(2 * math.pi * (fx * x + fy * y) / N + f) for fx, fy, f, a in os_) / 6.0


def partir(total, lo, hi):
    """Divide `total` em pedaços entre lo e hi que somam exatamente total (periódico)."""
    out = []
    while sum(out) < total:
        resto = total - sum(out)
        if resto <= hi:
            if resto < lo and out:
                out[-1] += resto
            else:
                out.append(resto)
            break
        out.append(random.randint(lo, min(hi, resto - lo)))
    return out


# fiadas e blocos (cada fiada desloca os blocos: assentamento contrafiado)
fiadas = partir(N, *CFG['fiada'])
blocos = []          # (y0, h, [(x0, w, tom)])
y = 0
for h in fiadas:
    ws = partir(N, *CFG['larg'])
    x0 = random.randint(0, N - 1)
    lista = []
    for w in ws:
        lista.append((x0, w, random.uniform(-CFG['var'], CFG['var']), random.random()))
        x0 = (x0 + w) % N
    blocos.append((y, h, lista))
    y += h


def bloco_em(px, py):
    for y0, h, lista in blocos:
        if y0 <= py < y0 + h:
            for x0, w, tom, sorte in lista:
                dx = (px - x0) % N
                if dx < w:
                    return dx, py - y0, w, h, tom, sorte
    return 0, 0, 1, 1, 0, 0


img = bytearray()
for py in range(N):
    img.append(0)
    for px in range(N):
        dx, dy, w, h, tom, sorte = bloco_em(px, py)
        lasca = CFG['lasca'] * (0.5 + 0.5 * ruido(px * 1.7, py * 1.3, finas))
        # distâncias às 4 bordas (com lascas): esquerda/cima pegam luz, direita/baixo ficam na sombra
        el, et, er, eb = dx - lasca * 0.5, dy - lasca * 0.5, w - dx - lasca * 0.5, h - dy - lasca * 0.5
        j = CFG['junta'] / 2.0
        b = CFG['bisel']
        v = CFG['cor'][0] + tom + CFG['grao'] * ruido(px, py) + 0.04 * ruido(px * 3, py * 3, finas) * CFG['grao'] / 0.07
        v += 0.03 * (random.random() - 0.5)
        dmin = min(el, et, er, eb)
        if dmin < j:
            v = 0.10 + 0.05 * random.random()                       # junta funda
        elif dmin < j + b:
            f = 1.0 - (dmin - j) / b
            if min(el, et) <= min(er, eb):
                v += 0.13 * f                                         # bisel iluminado
            else:
                v -= 0.16 * f                                         # bisel em sombra
        # face levemente abaulada (meio mais claro) e sujeira acumulada perto da junta
        v += 0.03 * (1.0 - abs(dx / w - 0.5) * 2) * (1.0 - abs(dy / h - 0.5) * 2)
        if j + b <= dmin < j + b + 10:
            v -= 0.03
        if ESTILO == 'pedra' and sorte > 0.8:
            v -= 0.05 * (0.5 + 0.5 * ruido(px * 2, py * 2))            # alguns blocos mais gastos
        r = v * (1.0 + (0.02 if ESTILO != 'ia' else -0.04))
        g = v
        bl = v * (0.95 if ESTILO != 'ia' else 1.08)
        if ESTILO == 'ia' and dmin < j + 1.5 and sorte > 0.6:
            r, g, bl = 0.18, 0.55, 0.54                               # veio de luz ciano em algumas juntas
        img += bytes(max(0, min(255, int(c * 255))) for c in (r, g, bl))

def bloco_png(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
with open(SAIDA, 'wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n' + bloco_png(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 2, 0, 0, 0))
            + bloco_png(b'IDAT', zlib.compress(bytes(img), 9)) + bloco_png(b'IEND', b''))
print('piso', ESTILO, SAIDA)
