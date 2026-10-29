"""Folha de fumaça 4×4 (16 baforadas de 128 px) para as partículas: cada baforada é um aglomerado de bolhas
(couve-flor) com borda em fiapos por ruído fractal e volume falso (luz de cima: topo claro, base escura).
RGB = brilho (a cor vem da partícula), A = densidade. Saída: assets/texturas/fumaca.png. Python puro."""
import math, os, random, struct, zlib

N, Q = 4, 128
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'assets', 'texturas', 'fumaca.png')
random.seed(11)


def grade(p):
    return [[random.random() for _ in range(p + 1)] for _ in range(p + 1)]


def suave(t):
    return t * t * (3 - 2 * t)


def ruido(gs, x, y):
    v = 0.0; amp = 1.0; tot = 0.0
    for g, p in gs:
        fx = x * p; fy = y * p
        i, j = int(fx), int(fy); tx, ty = suave(fx - i), suave(fy - j)
        i = min(i, p - 1); j = min(j, p - 1)
        a = g[j][i] + (g[j][i + 1] - g[j][i]) * tx
        b = g[j + 1][i] + (g[j + 1][i + 1] - g[j + 1][i]) * tx
        v += (a + (b - a) * ty) * amp; tot += amp; amp *= 0.5
    return v / tot


img = [[(0, 0, 0, 0)] * (N * Q) for _ in range(N * Q)]
for f in range(N * N):
    gs = [(grade(p), p) for p in (4, 8, 16, 32)]
    bolhas = [(0.5 + random.uniform(-0.05, 0.05), 0.5 + random.uniform(-0.05, 0.05), random.uniform(0.22, 0.28))]
    for _ in range(random.randint(7, 11)):
        a = random.uniform(0, 2 * math.pi); r = random.uniform(0.10, 0.27)
        bolhas.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r * 0.9, random.uniform(0.10, 0.20)))
    gs2 = [(grade(p), p) for p in (3, 6, 12)]
    dens = [[0.0] * Q for _ in range(Q)]
    for y in range(Q):
        for x in range(Q):
            u, v = (x + 0.5) / Q, (y + 0.5) / Q
            d = 0.0
            for bx, by, br in bolhas:
                q = ((u - bx) ** 2 + (v - by) ** 2) / (br * br)
                d += math.exp(-q * 1.6)
            # ruído com o ponto deslocado por outro ruído: fiapos e redemoinhos, não bolha lisa
            wu = u + (ruido(gs2, u, v) - 0.5) * 0.18
            wv = v + (ruido(gs2, v + 0.37, u + 0.11) - 0.5) * 0.18
            n = ruido(gs, wu, wv)
            fino = ruido(gs2, wu * 1.7 + 0.3, wv * 1.7)
            d = 1.0 - math.exp(-d * 0.8)                          # satura devagar: centro denso, nunca chapado
            d = d * (0.30 + 0.95 * n) - 0.18 * (fino - 0.5)
            r = math.hypot(u - 0.5, v - 0.5)
            borda = max(0.0, min(1.0, (0.49 - r) / 0.16))         # some antes da borda do quadro
            dens[y][x] = max(0.0, min(1.0, d * borda))
    # desfoque leve (2 passadas de caixa 5 px): tira o granulado, mantém os rolos
    for _ in range(2):
        tmp = [[0.0] * Q for _ in range(Q)]
        for y in range(Q):
            for x in range(Q):
                acc = 0.0
                for k in range(-2, 3):
                    acc += dens[y][min(max(x + k, 0), Q - 1)]
                tmp[y][x] = acc / 5.0
        for y in range(Q):
            for x in range(Q):
                acc = 0.0
                for k in range(-2, 3):
                    acc += tmp[min(max(y + k, 0), Q - 1)][x]
                dens[y][x] = acc / 5.0
    ox, oy = (f % N) * Q, (f // N) * Q
    for y in range(Q):
        for x in range(Q):
            a = dens[y][x]
            al = max(0.0, min(1.0, (a - 0.05) / 0.75)) ** 1.6 * 0.85
            # volume: inclinação da densidade como normal; luz vindo de cima e um pouco da esquerda
            gx = dens[y][min(x + 2, Q - 1)] - dens[y][max(x - 2, 0)]
            gy = dens[min(y + 2, Q - 1)][x] - dens[max(y - 2, 0)][x]
            luz = 0.78 + 0.9 * (gy * 0.8 + gx * 0.3) + 0.12 * (1.0 - y / Q)
            rolo = ruido(gs, (x + 0.5) / Q * 0.8 + 0.13, (y + 0.5) / Q * 0.8 + 0.29)   # rolos internos claros/escuros
            luz = max(0.3, min(1.0, luz * (0.72 + 0.4 * rolo)))
            c = int(luz * 255)
            img[oy + y][ox + x] = (c, c, c, int(al * 255))

linhas = b''.join(b'\x00' + bytes(v for px in linha for v in px) for linha in img)
def bloco(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
with open(SAIDA, 'wb') as fo:
    fo.write(b'\x89PNG\r\n\x1a\n' + bloco(b'IHDR', struct.pack('>IIBBBBB', N * Q, N * Q, 8, 6, 0, 0, 0))
             + bloco(b'IDAT', zlib.compress(linhas, 9)) + bloco(b'IEND', b''))
print('fumaca.png', N * Q)
