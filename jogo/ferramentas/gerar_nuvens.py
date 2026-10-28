"""Mapa das nuvens (sem emenda, 256²) para a sombra das nuvens e os raios de sol. Python puro.
R = cobertura (fBm de baixa frequência: nuvens grandes e macias); G = rasgos (poucos buracos redondos de borda
irregular, por onde descem os feixes quando o céu está quase fechado).
Saída: assets/texturas/nuvens.png. Rodar: python3 ferramentas/gerar_nuvens.py"""
import math, os, random, struct, zlib

N = 256
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'assets', 'texturas', 'nuvens.png')
random.seed(23)


def grade(p):
    return [[random.random() for _ in range(p)] for _ in range(p)]


def suave(t):
    return t * t * (3 - 2 * t)


def valor(g, p, x, y):
    fx = x / N * p; fy = y / N * p
    x0 = int(fx) % p; y0 = int(fy) % p; x1 = (x0 + 1) % p; y1 = (y0 + 1) % p
    tx = suave(fx - int(fx)); ty = suave(fy - int(fy))
    a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
    b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
    return a + (b - a) * ty


def fbm(periodos, pesos):
    gs = [grade(p) for p in periodos]
    out = [[0.0] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            out[y][x] = sum(w * valor(g, p, x, y) for g, p, w in zip(gs, periodos, pesos)) / sum(pesos)
    return out


def esticar(m):
    v = sorted(c for l in m for c in l)
    lo, hi = v[int(len(v) * 0.02)], v[int(len(v) * 0.98)]
    return [[min(1.0, max(0.0, (c - lo) / (hi - lo))) for c in l] for l in m]


cob = esticar(fbm([4, 8, 16, 32], [1.0, 0.55, 0.28, 0.12]))
borda = fbm([16, 32], [1.0, 0.5])
centros = [(random.uniform(0, N), random.uniform(0, N), random.uniform(5, 12)) for _ in range(30)]
rasgo = [[0.0] * N for _ in range(N)]
for y in range(N):
    for x in range(N):
        r = 0.0
        for cx, cy, raio in centros:
            dx = min(abs(x - cx), N - abs(x - cx)); dy = min(abs(y - cy), N - abs(y - cy))
            d = math.hypot(dx, dy) / raio + 0.45 * (borda[y][x] - 0.5)
            r = max(r, min(1.0, max(0.0, (1.0 - d) / 0.35)))
        rasgo[y][x] = suave(r)

linhas = b''.join(b'\x00' + bytes(v for x in range(N) for v in (int(cob[y][x] * 255), int(rasgo[y][x] * 255), 0)) for y in range(N))
def bloco(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
with open(SAIDA, 'wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n' + bloco(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 2, 0, 0, 0))
            + bloco(b'IDAT', zlib.compress(linhas, 9)) + bloco(b'IEND', b''))
print('nuvens.png', N)
