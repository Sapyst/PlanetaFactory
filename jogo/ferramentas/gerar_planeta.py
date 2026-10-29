"""Texturas da abertura (Python puro): planeta pintado em pixel (mapa 256×128, continentes, mar raso/fundo, praia,
campo, floresta, deserto, montanha, gelo nos polos) ampliado e borrado; nuvens (alfa) da mesma forma; sol (núcleo)
e raios do sol. Saída em assets/texturas/: planeta.png, planeta_nuvens.png, sol.png, sol_raios.png."""
import math, os, random, struct, zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, '..', 'assets', 'texturas')
random.seed(5)


def png(nome, w, h, px, alfa):
    linhas = b''.join(b'\x00' + bytes(v for p in px[y * w:(y + 1) * w] for v in (p if alfa else p[:3])) for y in range(h))
    def bloco(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(os.path.join(PASTA, nome), 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + bloco(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6 if alfa else 2, 0, 0, 0))
                + bloco(b'IDAT', zlib.compress(linhas, 9)) + bloco(b'IEND', b''))


def grade(p, q):
    return [[random.random() for _ in range(p)] for _ in range(q + 1)]


def suave(t): return t * t * (3 - 2 * t)


def fbm(gs, u, v):
    """u em [0,1) dá a volta (emenda leste–oeste); v em [0,1]."""
    s = 0.0; a = 1.0; tot = 0.0
    for g, p, q in gs:
        x = u * p; y = v * q
        i = int(x) % p; j = min(int(y), q - 1); tx, ty = suave(x - int(x)), suave(y - int(y))
        i2 = (i + 1) % p
        c0 = g[j][i] + (g[j][i2] - g[j][i]) * tx
        c1 = g[j + 1][i] + (g[j + 1][i2] - g[j + 1][i]) * tx
        s += (c0 + (c1 - c0) * ty) * a; tot += a; a *= 0.5
    return s / tot


def borrar(px, w, h, r, canais):
    """Desfoque de caixa (2 passadas) com volta no eixo x."""
    for _ in range(2):
        tmp = [None] * (w * h)
        for y in range(h):
            for x in range(w):
                acc = [0.0] * canais
                for k in range(-r, r + 1):
                    p = px[y * w + (x + k) % w]
                    for c in range(canais): acc[c] += p[c]
                tmp[y * w + x] = [a / (2 * r + 1) for a in acc]
        for y in range(h):
            for x in range(w):
                acc = [0.0] * canais
                for k in range(-r, r + 1):
                    p = tmp[min(max(y + k, 0), h - 1) * w + x]
                    for c in range(canais): acc[c] += p[c]
                px[y * w + x] = [a / (2 * r + 1) for a in acc]
    return px


def ampliar(px, w, h, f):
    out = []
    for y in range(h * f):
        for x in range(w * f):
            out.append(px[(y // f) * w + (x // f)])
    return out


# ---------------------------------------------------------------- planeta em pixel
W, H = 256, 128
gt = [(grade(p, q), p, q) for p, q in ((4, 2), (8, 4), (16, 8), (32, 16), (64, 32))]
gu = [(grade(p, q), p, q) for p, q in ((6, 3), (12, 6), (24, 12))]
PAL = {'fundo': (18, 40, 74), 'raso': (34, 78, 112), 'praia': (176, 160, 118), 'campo': (72, 110, 58),
       'floresta': (40, 78, 44), 'deserto': (170, 140, 92), 'montanha': (110, 104, 96), 'gelo': (226, 232, 236)}
px = []
for y in range(H):
    for x in range(W):
        u, v = x / W, (y + 0.5) / H
        e = fbm(gt, u, v)
        um = fbm(gu, u, v)
        lat = abs(v - 0.5) * 2
        if lat > 0.86 - 0.06 * e: c = PAL['gelo']
        elif e < 0.47: c = PAL['fundo']
        elif e < 0.52: c = PAL['raso']
        elif e < 0.535: c = PAL['praia']
        elif e > 0.68: c = PAL['montanha']
        elif um < 0.42 and lat < 0.5: c = PAL['deserto']
        elif um > 0.56: c = PAL['floresta']
        else: c = PAL['campo']
        px.append(list(c))
px = borrar(ampliar(px, W, H, 4), W * 4, H * 4, 2, 3)
png('planeta.png', W * 4, H * 4, [tuple(int(c) for c in p) + (255,) for p in px], False)
print('planeta.png')

# ---------------------------------------------------------------- nuvens (pixel e borradas)
gn = [(grade(p, q), p, q) for p, q in ((8, 4), (16, 8), (32, 16), (64, 32))]
nv = []
for y in range(H):
    for x in range(W):
        u, v = x / W, (y + 0.5) / H
        n = fbm(gn, u, v)
        faixa = 0.08 * math.sin(v * math.pi * 6)                # bandas de clima
        a = 1.0 if n + faixa > 0.53 else (0.55 if n + faixa > 0.49 else 0.0)
        nv.append([255.0, 255.0, 255.0, a * 255])
nv = borrar(ampliar(nv, W, H, 4), W * 4, H * 4, 3, 4)
png('planeta_nuvens.png', W * 4, H * 4, [tuple(int(c) for c in p) for p in nv], True)
print('planeta_nuvens.png')

# ---------------------------------------------------------------- sol e raios
S = 256
sol = []
for y in range(S):
    for x in range(S):
        r = math.hypot(x - S / 2 + 0.5, y - S / 2 + 0.5) / (S / 2)
        a = max(0.0, 1.0 - r)
        nucleo = 1.0 if r < 0.18 else math.exp(-(r - 0.18) * 7.0)
        sol.append((255, int(230 + 25 * nucleo), int(150 + 105 * nucleo), int(255 * min(1.0, nucleo * 1.0 + a ** 3 * 0.35))))
png('sol.png', S, S, sol, True)
R = 512
raios = []
angs = [random.uniform(0, 2 * math.pi) for _ in range(28)]
larg = [random.uniform(0.012, 0.05) for _ in angs]
forca = [random.uniform(0.35, 1.0) for _ in angs]
for y in range(R):
    for x in range(R):
        dx, dy = x - R / 2 + 0.5, y - R / 2 + 0.5
        r = math.hypot(dx, dy) / (R / 2)
        a = math.atan2(dy, dx)
        s = 0.0
        for ang, l, f in zip(angs, larg, forca):
            d = abs((a - ang + math.pi) % (2 * math.pi) - math.pi)
            s += f * math.exp(-(d / l) ** 2)
        v = min(1.0, s) * max(0.0, 1.0 - r) ** 1.6 * (1.0 if r > 0.06 else r / 0.06)
        raios.append((255, 235, 170, int(255 * v)))
png('sol_raios.png', R, R, raios, True)
print('sol.png sol_raios.png')
