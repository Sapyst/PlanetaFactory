"""Textura do piso de fábrica (concreto em placas), 512×512 em loop sem emenda: 4 m de lado, placas de 1 m alinhadas
aos tiles, juntas escuras, manchas de óleo e desgaste. Ruído só com frequências inteiras → periódico por construção.
Uso: python3 piso_fabrica.py   (saída: ../texturas/piso_fabrica.png)"""
import math, os, random, struct, zlib

N = 512
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'texturas', 'piso_fabrica.png')
random.seed(11)
ondas = [(random.randint(1, 9), random.randint(1, 9), random.uniform(0, math.tau), random.uniform(0.3, 1.0) / (1 + i * 0.35)) for i in range(26)]
manchas = [(random.uniform(0, N), random.uniform(0, N), random.uniform(18, 60), random.uniform(0.04, 0.10)) for _ in range(9)]


def ruido(x, y):
    return sum(a * math.sin(2 * math.pi * (fx * x + fy * y) / N + f) for fx, fy, f, a in ondas) / 6.0


def periodico(dx):
    return min(abs(dx), N - abs(dx))


linhas = []
for y in range(N):
    linha = bytearray([0])
    for x in range(N):
        v = 0.47 + 0.06 * ruido(x, y) + 0.025 * (random.random() - 0.5)
        # placas de 128 px (1 m): junta escura de 3 px e bisel claro
        jx, jy = x % 128, y % 128
        if jx < 3 or jy < 3:
            v *= 0.55
        elif jx < 5 or jy < 5:
            v *= 1.08
        # cada placa com tom próprio (concretagem diferente)
        px, py = x // 128, y // 128
        v *= 0.94 + 0.12 * ((px * 7 + py * 13) % 5) / 4.0
        for mx, my, r, k in manchas:              # óleo/sujeira (distância periódica)
            d = math.hypot(periodico(x - mx), periodico(y - my))
            if d < r:
                v -= k * (1 - d / r) ** 1.5
        r_, g_, b_ = v * 0.98, v * 0.98, v * 1.03
        linha += bytes(max(0, min(255, int(c * 255))) for c in (r_, g_, b_))
    linhas.append(bytes(linha))


def chunk(tipo, dados):
    return struct.pack('>I', len(dados)) + tipo + dados + struct.pack('>I', zlib.crc32(tipo + dados) & 0xffffffff)


png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 2, 0, 0, 0)) + \
      chunk(b'IDAT', zlib.compress(b''.join(linhas), 9)) + chunk(b'IEND', b'')
open(SAIDA, 'wb').write(png)
print('PISO', SAIDA)
