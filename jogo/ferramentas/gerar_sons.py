"""Sons do jogo sintetizados por código (sem amostras de terceiros): efeitos curtos (sem música).
Saída: assets/sons/*.wav (mono 16 bits). Rodar: python3 ferramentas/gerar_sons.py [nome ...] (sem nome = todos)"""
import math, random, struct, wave, os

TAXA = 22050
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'assets', 'sons')
random.seed(7)


def gravar(nome, amostras, taxa=TAXA):
    pico = max(1e-9, max(abs(a) for a in amostras))
    k = 0.85 / pico
    with wave.open(os.path.join(SAIDA, nome + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, a * k)) * 32767)) for a in amostras))


def env(i, n, ataque=0.005, queda=None):
    t = i / TAXA
    a = min(1.0, t / ataque) if ataque > 0 else 1.0
    d = math.exp(-t / queda) if queda else 1.0 - i / n
    return a * d


def ruido_filtrado(n, corte):
    """Ruído branco passado num passa-baixa de 1 polo (corte em Hz)."""
    rc = 1.0 / (2 * math.pi * corte); dt = 1.0 / TAXA; al = dt / (rc + dt)
    y = 0.0; out = []
    for _ in range(n):
        y += al * (random.uniform(-1, 1) - y); out.append(y)
    return out


def clique():
    n = int(0.05 * TAXA)
    return [math.sin(2 * math.pi * 1800 * i / TAXA) * env(i, n, 0.001, 0.008) for i in range(n)]


def construir():
    n = int(0.22 * TAXA); r = ruido_filtrado(n, 900)
    return [(math.sin(2 * math.pi * (140 - 60 * i / n) * i / TAXA) * 0.8 + r[i] * 0.6) * env(i, n, 0.002, 0.05) for i in range(n)]


def remover():
    n = int(0.25 * TAXA); r = ruido_filtrado(n, 2500)
    return [(r[i] * 0.7 + math.sin(2 * math.pi * (300 + 500 * i / n) * i / TAXA) * 0.3) * env(i, n, 0.01, 0.07) for i in range(n)]


def tiro():
    n = int(0.16 * TAXA); r = ruido_filtrado(n, 3500)
    return [(r[i] + math.sin(2 * math.pi * 95 * i / TAXA) * 0.6) * env(i, n, 0.0005, 0.025) for i in range(n)]


def aranha_morre():
    n = int(0.6 * TAXA); r = ruido_filtrado(n, 1800); out = []
    for i in range(n):
        t = i / TAXA
        metal = sum(math.sin(2 * math.pi * f * t) for f in (523, 811, 1247)) / 3
        out.append((r[i] * 0.8 + metal * 0.4 * math.exp(-t / 0.15)) * env(i, n, 0.001, 0.18))
    return out


def alerta():
    out = []
    for nota in (660, 495, 660, 495):
        n = int(0.16 * TAXA)
        out += [(math.sin(2 * math.pi * nota * i / TAXA) + 0.3 * math.sin(4 * math.pi * nota * i / TAXA)) * env(i, n, 0.01, 0.12) for i in range(n)]
    return out


def pesquisa():
    out = [0.0] * int(1.4 * TAXA)
    for k, nota in enumerate((523.25, 659.25, 783.99, 1046.5)):
        ini = int(k * 0.12 * TAXA)
        for i in range(int(1.0 * TAXA)):
            if ini + i < len(out):
                t = i / TAXA
                out[ini + i] += (math.sin(2 * math.pi * nota * t) + 0.25 * math.sin(6 * math.pi * nota * t)) * math.exp(-t / 0.35) * min(1, t / 0.004)
    return out


def apito_trem():
    n = int(1.1 * TAXA); out = []
    for i in range(n):
        t = i / TAXA; vib = 1 + 0.004 * math.sin(2 * math.pi * 5 * t)
        s = sum(math.sin(2 * math.pi * f * vib * t) + 0.3 * math.sin(4 * math.pi * f * vib * t) for f in (311, 392, 466))
        a = min(1, t / 0.06) * (1 if t < 0.85 else max(0, 1 - (t - 0.85) / 0.25))
        out.append(s * a)
    return out


def derrota():
    out = []
    for nota in (392, 349, 311, 233):
        n = int(0.45 * TAXA)
        out += [(math.sin(2 * math.pi * nota * i / TAXA) + 0.4 * math.sin(2 * math.pi * nota * 1.5 * i / TAXA)) * env(i, n, 0.02, 0.35) for i in range(n)]
    return out


def chuva():
    """6 s em loop: chiado (dois filtros) + gotas esparsas estalando; emenda cruzada no fim."""
    n = int(6.0 * TAXA)
    a = ruido_filtrado(n, 3200); b = ruido_filtrado(n, 700)
    out = [a[i] * 0.55 + b[i] * 0.8 for i in range(n)]
    for _ in range(260):
        ini = random.randint(0, n - 400); f = random.uniform(2500, 5200); amp = random.uniform(0.05, 0.25)
        for i in range(380):
            out[ini + i] += math.sin(2 * math.pi * f * i / TAXA) * math.exp(-i / 60.0) * amp
    x = int(0.5 * TAXA)
    for i in range(x):
        k = i / x
        out[i] = out[i] * k + out[n - x + i] * (1 - k)
    return out[: n - x]


def trovao():
    """Estalo seco seguido de ronco grave que rola e some (4 s)."""
    n = int(4.0 * TAXA)
    grave = ruido_filtrado(n, 90); medio = ruido_filtrado(n, 400)
    out = []
    for i in range(n):
        t = i / TAXA
        estalo = medio[i] * math.exp(-t / 0.12) * 1.6
        rola = grave[i] * min(1.0, t / 0.15) * math.exp(-t / 1.4) * (0.75 + 0.25 * math.sin(2 * math.pi * 1.7 * t))
        out.append(estalo + rola * 3.0)
    return out


def reentrada():
    """5 s: rugido de reentrada — chiado grave que cresce e sobe de tom, com crepitar de calor."""
    n = int(5.0 * TAXA)
    grave = ruido_filtrado(n, 160); medio = ruido_filtrado(n, 900)
    out = []
    for i in range(n):
        t = i / n
        sobe = t ** 1.6
        out.append(grave[i] * (0.4 + 1.6 * sobe) + medio[i] * 0.9 * sobe * (0.7 + 0.3 * math.sin(2 * math.pi * 7 * i / TAXA)))
    for _ in range(140):
        ini = random.randint(int(n * 0.3), n - 300); amp = random.uniform(0.1, 0.4) * ini / n
        for i in range(250):
            out[ini + i] += random.uniform(-1, 1) * math.exp(-i / 40.0) * amp
    return [a * min(1.0, i / (0.4 * TAXA)) for i, a in enumerate(out)]


def impacto():
    """3,5 s: estrondo da queda (baque grave + onda de choque), estalo de metal e cascalho caindo."""
    n = int(3.5 * TAXA)
    grave = ruido_filtrado(n, 70); medio = ruido_filtrado(n, 600)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (55 - 25 * min(t, 1.0)) * t) * math.exp(-t / 0.35) * 1.4
        onda = grave[i] * min(1.0, t / 0.02) * math.exp(-t / 0.9) * 3.0
        metal = sum(math.sin(2 * math.pi * f * t) for f in (310, 467, 731)) * math.exp(-t / 0.25) * 0.25
        out.append(baque + onda + metal + medio[i] * math.exp(-t / 0.15) * 1.2)
    for _ in range(90):
        ini = random.randint(int(0.25 * TAXA), n - 400); amp = random.uniform(0.05, 0.25) * (1.0 - ini / n)
        f = random.uniform(1500, 4000)
        for i in range(380):
            out[ini + i] += math.sin(2 * math.pi * f * i / TAXA) * math.exp(-i / 50.0) * amp
    return out


def fogo():
    """2,5 s de fogo crepitando: chiado grave + estalos secos ao acaso."""
    n = int(2.5 * TAXA)
    base = ruido_filtrado(n, 500)
    out = [b * 0.5 * (0.8 + 0.2 * math.sin(2 * math.pi * 1.3 * i / TAXA)) for i, b in enumerate(base)]
    for _ in range(70):
        ini = random.randint(0, n - 300); amp = random.uniform(0.2, 0.7)
        for i in range(260):
            out[ini + i] += random.uniform(-1, 1) * math.exp(-i / 25.0) * amp
    return out


def faisca():
    """0,35 s: arco elétrico — estalos secos de alta frequência em rajada, zumbido de 120 Hz por baixo, cauda chiada."""
    n = int(0.35 * TAXA)
    rng = random.Random(11)
    out = []
    y_ant = 0.0
    estalos = sorted(rng.uniform(0.0, 0.22) for _ in range(9))
    for i in range(n):
        t = i / TAXA
        x = rng.uniform(-1, 1)
        hp = x - y_ant; y_ant = x                                  # passa-alta grosseiro: chiado agudo
        crep = sum(math.exp(-(t - e) / 0.004) for e in estalos if t >= e) * hp
        zumbido = (1.0 if math.sin(2 * math.pi * 120 * t) > 0 else -1.0) * 0.18 * math.exp(-t / 0.12)
        out.append(crep * 0.9 + zumbido + hp * 0.25 * math.exp(-t / 0.08))
    return out


os.makedirs(SAIDA, exist_ok=True)
for nome, f in [('clique', clique), ('construir', construir), ('remover', remover), ('tiro', tiro),
                ('aranha_morre', aranha_morre), ('alerta', alerta), ('pesquisa', pesquisa), ('apito_trem', apito_trem),
                ('derrota', derrota), ('chuva', chuva), ('trovao', trovao), ('reentrada', reentrada), ('impacto', impacto), ('fogo', fogo), ('faisca', faisca)]:
    import sys
    if len(sys.argv) > 1 and nome not in sys.argv[1:]:
        continue
    gravar(nome, f())
    print('SOM', nome)
