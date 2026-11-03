"""Sons do jogo sintetizados por código (sem amostras de terceiros): efeitos e ambientes (sem música).
Saída: assets/sons/*.wav (mono 16 bits, 44,1 kHz).
Rodar: python3 ferramentas/gerar_sons.py [nome ...] (sem nome = todos)"""
import math, random, struct, wave, os

TAXA = 44100
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'assets', 'sons')
random.seed(7)


def gravar(nome, amostras, taxa=TAXA, ganho=0.85):
    """Normaliza pelo pico com o ganho desejado e grava em WAV 16 bits mono."""
    pico = max(1e-9, max(abs(a) for a in amostras))
    k = ganho / pico
    caminho = os.path.join(SAIDA, nome + '.wav')
    with wave.open(caminho, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        dados = b''.join(struct.pack('<h', int(max(-1.0, min(1.0, a * k)) * 32767)) for a in amostras)
        w.writeframes(dados)


def env(i, n, ataque=0.005, queda=None):
    """Envelope AD (ataque linear, queda exponencial ou linear). Tempos em segundos."""
    t = i / TAXA
    a = min(1.0, t / ataque) if ataque > 0 else 1.0
    d = math.exp(-t / queda) if queda else max(0.0, 1.0 - i / n)
    return a * d


def ruido_filtrado(n, corte):
    """Ruído branco passado num passa-baixa de 1 polo (corte em Hz)."""
    rc = 1.0 / (2 * math.pi * corte)
    dt = 1.0 / TAXA
    al = dt / (rc + dt)
    y = 0.0
    out = []
    for _ in range(n):
        y += al * (random.uniform(-1, 1) - y)
        out.append(y)
    return out


def ruido_passa_alta(n, corte):
    """Ruído branco passado num passa-alta de 1 polo (corte em Hz)."""
    rc = 1.0 / (2 * math.pi * corte)
    dt = 1.0 / TAXA
    al = rc / (rc + dt)
    y = 0.0
    x_ant = 0.0
    out = []
    for _ in range(n):
        x = random.uniform(-1, 1)
        y = al * (y + x - x_ant)
        x_ant = x
        out.append(y)
    return out


# ==============================================================================
# INTERFACE E AÇÕES GERAIS
# ==============================================================================

def clique():
    """Clique limpo e tátil de precisão para botões e opções."""
    n = int(0.04 * TAXA)
    out = []
    for i in range(n):
        t = i / TAXA
        s = math.sin(2 * math.pi * 2100 * t) * 0.7 + math.sin(2 * math.pi * 3800 * t) * 0.3
        out.append(s * env(i, n, 0.001, 0.006))
    return out


def construir():
    """Assentamento metálico firme com engate pneumático/mecânico."""
    n = int(0.20 * TAXA)
    r = ruido_filtrado(n, 1200)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (160 - 70 * (t / 0.2)) * t) * 0.8
        clique_trav = math.sin(2 * math.pi * 950 * t) * math.exp(-t / 0.02) * 0.4
        out.append((baque + clique_trav + r[i] * 0.5) * env(i, n, 0.002, 0.045))
    return out


def remover():
    """Desengate pneumático suave e clique de liberação de encaixe."""
    n = int(0.22 * TAXA)
    r = ruido_filtrado(n, 2800)
    out = []
    for i in range(n):
        t = i / TAXA
        soprado = r[i] * 0.65 * (1.0 - t / 0.22)
        mola = math.sin(2 * math.pi * (350 + 600 * (t / 0.22)) * t) * 0.35 * math.exp(-t / 0.08)
        out.append((soprado + mola) * env(i, n, 0.008, 0.06))
    return out


def alerta():
    """Alarme industrial nítido com dois tons alternados de aviso."""
    out = []
    for nota in (740, 554, 740, 554):
        n = int(0.14 * TAXA)
        for i in range(n):
            t = i / TAXA
            s = math.sin(2 * math.pi * nota * t) + 0.35 * math.sin(4 * math.pi * nota * t)
            out.append(s * env(i, n, 0.008, 0.09))
    return out


def pesquisa():
    """Arpejo ascendente límpido e cristalino de tecnologia concluída."""
    out = [0.0] * int(1.3 * TAXA)
    notas = (523.25, 659.25, 783.99, 1046.50, 1318.51)
    for k, nota in enumerate(notas):
        ini = int(k * 0.10 * TAXA)
        tam = int(0.8 * TAXA)
        for i in range(tam):
            idx = ini + i
            if idx < len(out):
                t = i / TAXA
                s = math.sin(2 * math.pi * nota * t) + 0.25 * math.sin(2 * math.pi * nota * 2 * t)
                out[idx] += s * math.exp(-t / 0.28) * min(1.0, t / 0.004) * 0.35
    return out


def derrota():
    """Sequência descendente dramática e melancólica."""
    out = []
    for nota in (392, 349, 311, 233, 174):
        n = int(0.35 * TAXA)
        for i in range(n):
            t = i / TAXA
            s = math.sin(2 * math.pi * nota * t) + 0.3 * math.sin(3 * math.pi * nota * t)
            out.append(s * env(i, n, 0.02, 0.28))
    return out


# ==============================================================================
# ARMAS E TIROS
# ==============================================================================

def tiro_metralhadora():
    """Tiro de metralhadora: percussor rápido, punch de pólvora e corpo metálico."""
    n = int(0.12 * TAXA)
    r = ruido_filtrado(n, 4200)
    out = []
    for i in range(n):
        t = i / TAXA
        percussao = math.sin(2 * math.pi * (1600 - 1200 * min(1.0, t / 0.015)) * t) * math.exp(-t / 0.01) * 0.9
        punch = math.sin(2 * math.pi * (180 - 100 * min(1.0, t / 0.04)) * t) * math.exp(-t / 0.025) * 1.2
        out.append((punch + percussao + r[i] * 0.8) * env(i, n, 0.0004, 0.022))
    return out


def tiro():
    """Alias para tiro de metralhadora (compatibilidade)."""
    return tiro_metralhadora()


def tiro_energia():
    """Disparo de torre de energia: laser/plasma sci-fi com modulação descendente."""
    n = int(0.18 * TAXA)
    r = ruido_passa_alta(n, 2000)
    out = []
    for i in range(n):
        t = i / TAXA
        f_base = 1500.0 * math.exp(-t / 0.045) + 280.0
        mod = math.sin(2 * math.pi * 220 * t) * (3.5 * math.exp(-t / 0.06))
        laser = math.sin(2 * math.pi * (f_base + mod * 40.0) * t)
        h2 = math.sin(4 * math.pi * f_base * t) * 0.3
        out.append((laser + h2 + r[i] * 0.25 * math.exp(-t / 0.02)) * env(i, n, 0.001, 0.05))
    return out


def tiro_foguete():
    """Lançador de foguetes: percussão mecânica seguida de forte sopro de jato propulsionado."""
    n = int(0.38 * TAXA)
    grave = ruido_filtrado(n, 350)
    medio = ruido_filtrado(n, 1400)
    out = []
    for i in range(n):
        t = i / TAXA
        gatilho = math.sin(2 * math.pi * 120 * t) * math.exp(-t / 0.03) * 0.8
        jato = (grave[i] * 1.2 + medio[i] * 0.7) * min(1.0, t / 0.04) * math.exp(-t / 0.16)
        ressonancia = math.sin(2 * math.pi * 95 * t) * math.exp(-t / 0.10) * 0.5
        out.append((gatilho + jato + ressonancia) * env(i, n, 0.001, 0.12))
    return out


def tiro_enxame():
    """Lança-mísseis de enxame: disparo rápido de micromísseis com silvo sibilante."""
    n = int(0.20 * TAXA)
    r = ruido_filtrado(n, 2500)
    out = []
    for i in range(n):
        t = i / TAXA
        f = 950.0 * math.exp(-t / 0.05) + 320.0
        sibilo = math.sin(2 * math.pi * f * t) * (0.8 + 0.2 * math.sin(2 * math.pi * 45 * t))
        out.append((sibilo * 0.7 + r[i] * 0.6) * env(i, n, 0.001, 0.05))
    return out


def tiro_artilharia():
    """Canhão de artilharia pesada: estrondo maciço, choque sísmico e cauda reverberante."""
    n = int(0.80 * TAXA)
    sub = ruido_filtrado(n, 90)
    corpo = ruido_filtrado(n, 450)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (75 - 35 * min(1.0, t / 0.1)) * t) * math.exp(-t / 0.12) * 1.5
        onda = sub[i] * 2.2 * math.exp(-t / 0.35)
        cauda = corpo[i] * 0.9 * math.exp(-t / 0.25) * (0.8 + 0.2 * math.sin(2 * math.pi * 2.5 * t))
        out.append((baque + onda + cauda) * env(i, n, 0.0003, 0.26))
    return out


def tiro_perfurante():
    """Munição perfurante: estalo chicoteado hipersônico e zunido penetrante."""
    n = int(0.18 * TAXA)
    r = ruido_passa_alta(n, 3200)
    out = []
    for i in range(n):
        t = i / TAXA
        estalo = math.sin(2 * math.pi * (3200 - 2400 * min(1.0, t / 0.01)) * t) * math.exp(-t / 0.008) * 1.2
        corpo = math.sin(2 * math.pi * 220 * t) * math.exp(-t / 0.025) * 0.8
        out.append((estalo + corpo + r[i] * 0.6) * env(i, n, 0.0003, 0.035))
    return out


def tiro_carregada():
    """Munição eletricamente carregada: zumbido de indução e estalo de arco elétrico."""
    n = int(0.28 * TAXA)
    r = ruido_filtrado(n, 3500)
    out = []
    for i in range(n):
        t = i / TAXA
        arco = (1.0 if math.sin(2 * math.pi * 140 * t) > 0 else -1.0) * math.exp(-t / 0.08) * 0.5
        plasma = math.sin(2 * math.pi * (880 - 450 * min(1.0, t / 0.08)) * t) * math.exp(-t / 0.06) * 0.9
        out.append((plasma + arco + r[i] * 0.5) * env(i, n, 0.001, 0.07))
    return out


def tiro_drone():
    """Blaster de drone de combate: pulso de energia leve, limpo e ágil."""
    n = int(0.10 * TAXA)
    out = []
    for i in range(n):
        t = i / TAXA
        f = 1100.0 * math.exp(-t / 0.025) + 380.0
        s = math.sin(2 * math.pi * f * t) + 0.25 * math.sin(4 * math.pi * f * t)
        out.append(s * env(i, n, 0.0005, 0.028))
    return out


# ==============================================================================
# IMPACTOS E EXPLOSÕES
# ==============================================================================

def impacto_aranha():
    """Impacto em carapaça de aranha: estalo quitinoso e crunch biológico."""
    n = int(0.18 * TAXA)
    alta = ruido_passa_alta(n, 2600)
    baixa = ruido_filtrado(n, 400)
    out = []
    for i in range(n):
        t = i / TAXA
        rachadura = alta[i] * math.exp(-t / 0.02) * 1.3
        crunch = baixa[i] * math.exp(-t / 0.06) * 0.8 * (1.0 + 0.4 * math.sin(2 * math.pi * 160 * t))
        out.append((rachadura + crunch) * env(i, n, 0.0005, 0.045))
    return out


def impacto_chao():
    """Impacto no terreno: baque surdo de terra e espalhamento de areia."""
    n = int(0.22 * TAXA)
    r_terra = ruido_filtrado(n, 180)
    r_areia = ruido_filtrado(n, 900)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * 90 * t) * math.exp(-t / 0.04) * 0.9
        poeira = r_areia[i] * math.exp(-t / 0.08) * 0.5
        out.append((baque + r_terra[i] * 1.1 + poeira) * env(i, n, 0.001, 0.06))
    return out


def impacto_estrutura():
    """Impacto em construção metálica: ricochete e ressonância de chapa de aço."""
    n = int(0.26 * TAXA)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * 210 * t) * math.exp(-t / 0.015) * 0.8
        modos = sum(math.sin(2 * math.pi * f * t) for f in (780, 1340, 2210)) / 3.0 * math.exp(-t / 0.09) * 0.9
        out.append((baque + modos) * env(i, n, 0.0005, 0.07))
    return out


def explosao():
    """Explosão padrão (foguetes, granadas e minas): estalo rápido e onda expansiva."""
    n = int(0.70 * TAXA)
    sub = ruido_filtrado(n, 110)
    medio = ruido_filtrado(n, 550)
    out = []
    for i in range(n):
        t = i / TAXA
        estalo = math.sin(2 * math.pi * (120 - 70 * min(1.0, t / 0.05)) * t) * math.exp(-t / 0.06) * 1.4
        rumble = sub[i] * 2.0 * math.exp(-t / 0.30)
        estilhacos = medio[i] * 0.8 * math.exp(-t / 0.18)
        out.append((estalo + rumble + estilhacos) * env(i, n, 0.0004, 0.20))
    return out


def explosao_grande():
    """Explosão pesada (artilharia e ninhos): estrondo devastador com sub-graves."""
    n = int(1.30 * TAXA)
    sub = ruido_filtrado(n, 65)
    grave = ruido_filtrado(n, 320)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (50 - 25 * min(1.0, t / 0.2)) * t) * math.exp(-t / 0.25) * 1.8
        onda = sub[i] * 2.8 * math.exp(-t / 0.55)
        eco = grave[i] * 1.1 * math.exp(-t / 0.38) * (0.8 + 0.2 * math.sin(2 * math.pi * 1.5 * t))
        out.append((baque + onda + eco) * env(i, n, 0.0005, 0.40))
    return out


def mina_pulso():
    """Pulso da mina de atordoamento: expansão toroidal eletromagnética com zumbido."""
    n = int(0.45 * TAXA)
    r = ruido_filtrado(n, 1200)
    out = []
    for i in range(n):
        t = i / TAXA
        pulso = math.sin(2 * math.pi * (80 - 40 * min(1.0, t / 0.2)) * t) * math.exp(-t / 0.15) * 1.3
        zumbido = math.sin(2 * math.pi * (480 - 200 * t) * t) * (1.0 + math.sin(2 * math.pi * 40 * t)) * 0.4 * math.exp(-t / 0.18)
        out.append((pulso + zumbido + r[i] * 0.3 * math.exp(-t / 0.10)) * env(i, n, 0.001, 0.14))
    return out


# ==============================================================================
# MÁQUINAS, ESTEIRAS E TRENS (COM DISTÂNCIA E LIMITE DE VOZES)
# ==============================================================================

def maq_fornalha():
    """Fornalha ativa: rugido de fundição contínua com calor crepitante."""
    n = int(2.0 * TAXA)
    base = ruido_filtrado(n, 320)
    out = [b * 0.7 * (0.75 + 0.25 * math.sin(2 * math.pi * 1.8 * i / TAXA)) for i, b in enumerate(base)]
    # Estalos ocasionais de forja e faíscas
    for _ in range(45):
        ini = random.randint(0, n - 400)
        amp = random.uniform(0.15, 0.5)
        for i in range(300):
            out[ini + i] += random.uniform(-1, 1) * math.exp(-i / 30.0) * amp
    # Crossfade suave de loop
    x = int(0.15 * TAXA)
    for i in range(x):
        k = i / x
        out[i] = out[i] * k + out[n - x + i] * (1.0 - k)
    return out[: n - x]


def maq_montadora():
    """Montadora trabalhando: ciclo mecânico ritmado de prensas, engrenagens e pistões."""
    n = int(1.6 * TAXA)
    base = ruido_filtrado(n, 800)
    out = [base[i] * 0.25 for i in range(n)]
    # Batida de prensa no início do ciclo
    for i in range(int(0.25 * TAXA)):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (85 - 35 * t / 0.25) * t) * math.exp(-t / 0.04) * 1.2
        metal = math.sin(2 * math.pi * 620 * t) * math.exp(-t / 0.03) * 0.4
        out[i] += baque + metal
    # Giro de engrenagens no meio do ciclo
    for i in range(int(0.2 * TAXA), int(1.2 * TAXA)):
        t = (i - 0.2 * TAXA) / TAXA
        eng = (math.sin(2 * math.pi * 160 * t) + 0.3 * math.sin(2 * math.pi * 320 * t)) * 0.35
        out[i] += eng * math.sin(math.pi * t / 1.0)
    # Encaixe pneumático final
    fim_ini = int(1.15 * TAXA)
    for i in range(int(0.3 * TAXA)):
        t = i / TAXA
        out[fim_ini + i] += math.sin(2 * math.pi * 880 * t) * math.exp(-t / 0.03) * 0.45
    return out


def maq_broca():
    """Broca mineradora: britamento mecânico percussivo e rotação no minério."""
    n = int(1.8 * TAXA)
    base = ruido_filtrado(n, 450)
    out = [base[i] * 0.35 * (0.8 + 0.2 * math.sin(2 * math.pi * 4 * i / TAXA)) for i in range(n)]
    # Batidas percussivas ritmadas da broca
    for golpe in range(6):
        ini = int(golpe * 0.28 * TAXA)
        for i in range(int(0.18 * TAXA)):
            if ini + i < n:
                t = i / TAXA
                percussao = math.sin(2 * math.pi * (130 - 50 * t / 0.18) * t) * math.exp(-t / 0.03) * 0.9
                britado = random.uniform(-1, 1) * math.exp(-t / 0.04) * 0.5
                out[ini + i] += percussao + britado
    return out


def maq_esteira():
    """Esteira transportadora: roletes metálicos contínuos e atrito suave da correia."""
    n = int(1.6 * TAXA)
    grave = ruido_filtrado(n, 220)
    medio = ruido_filtrado(n, 750)
    out = []
    for i in range(n):
        t = i / TAXA
        rolete = math.sin(2 * math.pi * 18 * t) * 0.15
        s = (grave[i] * 0.6 + medio[i] * 0.3) * (0.85 + rolete)
        out.append(s)
    x = int(0.15 * TAXA)
    for i in range(x):
        k = i / x
        out[i] = out[i] * k + out[n - x + i] * (1.0 - k)
    return out[: n - x]


def apito_trem():
    """Apito polifônico de trem com acorde harmônico e vibrato de corneta."""
    n = int(1.1 * TAXA)
    out = []
    for i in range(n):
        t = i / TAXA
        vib = 1.0 + 0.005 * math.sin(2 * math.pi * 5.2 * t)
        s = sum(math.sin(2 * math.pi * f * vib * t) + 0.28 * math.sin(4 * math.pi * f * vib * t) for f in (311, 392, 466))
        a = min(1.0, t / 0.05) * (1.0 if t < 0.85 else max(0.0, 1.0 - (t - 0.85) / 0.25))
        out.append(s * a)
    return out


def trem_trilho():
    """Rodagem de trem nos trilhos: rodas de aço pesadas e claque-claque nas junções."""
    n = int(1.6 * TAXA)
    base = ruido_filtrado(n, 280)
    out = [base[i] * 0.5 for i in range(n)]
    for batida in (0.1, 0.22, 0.85, 0.97):
        ini = int(batida * TAXA)
        for i in range(int(0.08 * TAXA)):
            if ini + i < n:
                t = i / TAXA
                junta = math.sin(2 * math.pi * 180 * t) * math.exp(-t / 0.018) * 0.8
                out[ini + i] += junta
    return out


# ==============================================================================
# CLIMA (CHUVA, TROVÃO, VENTO FORTE)
# ==============================================================================

def chuva():
    """Chuva em loop: chiado em duas bandas + gotas estalando, com emenda cruzada."""
    n = int(6.0 * TAXA)
    a = ruido_filtrado(n, 3400)
    b = ruido_filtrado(n, 650)
    out = [a[i] * 0.5 + b[i] * 0.75 for i in range(n)]
    for _ in range(350):
        ini = random.randint(0, n - 600)
        f = random.uniform(2600, 5400)
        amp = random.uniform(0.06, 0.28)
        for i in range(500):
            t = i / TAXA
            out[ini + i] += math.sin(2 * math.pi * f * t) * math.exp(-t / 0.003) * amp
    x = int(0.5 * TAXA)
    for i in range(x):
        k = i / x
        out[i] = out[i] * k + out[n - x + i] * (1.0 - k)
    return out[: n - x]


def trovao():
    """Trovão: estalo sônico rasgando a atmosfera seguido de ronco grave que rola."""
    n = int(4.0 * TAXA)
    grave = ruido_filtrado(n, 85)
    medio = ruido_filtrado(n, 380)
    out = []
    for i in range(n):
        t = i / TAXA
        estalo = medio[i] * math.exp(-t / 0.10) * 1.8
        rola = grave[i] * min(1.0, t / 0.12) * math.exp(-t / 1.3) * (0.75 + 0.25 * math.sin(2 * math.pi * 1.6 * t))
        out.append(estalo + rola * 3.2)
    return out


def vento_forte():
    """Vento forte em loop: uivo turbulento com modulação e ar passando pelas estruturas."""
    n = int(5.0 * TAXA)
    base = ruido_filtrado(n, 520)
    out = []
    for i in range(n):
        t = i / TAXA
        rajada = 0.65 + 0.35 * math.sin(2 * math.pi * 0.45 * t) * math.sin(2 * math.pi * 1.1 * t)
        out.append(base[i] * rajada * 0.85)
    x = int(0.5 * TAXA)
    for i in range(x):
        k = i / x
        out[i] = out[i] * k + out[n - x + i] * (1.0 - k)
    return out[: n - x]


# ==============================================================================
# INIMIGOS (ARANHAS)
# ==============================================================================

def aranha_passo():
    """Passo leve de pata quitinosa batendo no solo mineral."""
    n = int(0.06 * TAXA)
    r = ruido_passa_alta(n, 2200)
    out = []
    for i in range(n):
        t = i / TAXA
        estalo = math.sin(2 * math.pi * 1850 * t) * math.exp(-t / 0.007) * 0.8
        out.append((estalo + r[i] * 0.4) * env(i, n, 0.0003, 0.012))
    return out


def aranha_morre():
    """Morte da aranha: ruptura quitinosa da carapaça e spray de fluido ácido."""
    n = int(0.55 * TAXA)
    r = ruido_filtrado(n, 1900)
    out = []
    for i in range(n):
        t = i / TAXA
        metal = sum(math.sin(2 * math.pi * f * t) for f in (520, 815, 1260)) / 3.0
        out.append((r[i] * 0.85 + metal * 0.45 * math.exp(-t / 0.12)) * env(i, n, 0.0008, 0.16))
    return out


# ==============================================================================
# SONS DE CENA / AMBIENTE RETROCOMPATÍVEIS
# ==============================================================================

def reentrada():
    """Rugido de reentrada atmosférica da cápsula semente."""
    n = int(5.0 * TAXA)
    grave = ruido_filtrado(n, 160)
    medio = ruido_filtrado(n, 900)
    out = []
    for i in range(n):
        t = i / n
        sobe = t ** 1.6
        out.append(grave[i] * (0.4 + 1.6 * sobe) + medio[i] * 0.9 * sobe * (0.7 + 0.3 * math.sin(2 * math.pi * 7 * i / TAXA)))
    for _ in range(140):
        ini = random.randint(int(n * 0.3), n - 300)
        amp = random.uniform(0.1, 0.4) * ini / n
        for i in range(250):
            out[ini + i] += random.uniform(-1, 1) * math.exp(-i / 40.0) * amp
    return [a * min(1.0, i / (0.4 * TAXA)) for i, a in enumerate(out)]


def impacto():
    """Estrondo colossal da queda da cápsula/semente no solo."""
    n = int(3.5 * TAXA)
    grave = ruido_filtrado(n, 70)
    medio = ruido_filtrado(n, 600)
    out = []
    for i in range(n):
        t = i / TAXA
        baque = math.sin(2 * math.pi * (55 - 25 * min(t, 1.0)) * t) * math.exp(-t / 0.35) * 1.4
        onda = grave[i] * min(1.0, t / 0.02) * math.exp(-t / 0.9) * 3.0
        metal = sum(math.sin(2 * math.pi * f * t) for f in (310, 467, 731)) * math.exp(-t / 0.25) * 0.25
        out.append(baque + onda + metal + medio[i] * math.exp(-t / 0.15) * 1.2)
    for _ in range(90):
        ini = random.randint(int(0.25 * TAXA), n - 400)
        amp = random.uniform(0.05, 0.25) * (1.0 - ini / n)
        f = random.uniform(1500, 4000)
        for i in range(380):
            out[ini + i] += math.sin(2 * math.pi * f * i / TAXA) * math.exp(-i / 50.0) * amp
    return out


def fogo():
    """Labaredas crepitando."""
    n = int(2.5 * TAXA)
    base = ruido_filtrado(n, 500)
    out = [b * 0.5 * (0.8 + 0.2 * math.sin(2 * math.pi * 1.3 * i / TAXA)) for i, b in enumerate(base)]
    for _ in range(70):
        ini = random.randint(0, n - 300)
        amp = random.uniform(0.2, 0.7)
        for i in range(260):
            out[ini + i] += random.uniform(-1, 1) * math.exp(-i / 25.0) * amp
    return out


def faisca():
    """Arco elétrico de faísca rápida."""
    n = int(0.35 * TAXA)
    rng = random.Random(11)
    out = []
    y_ant = 0.0
    estalos = sorted(rng.uniform(0.0, 0.22) for _ in range(9))
    for i in range(n):
        t = i / TAXA
        x = rng.uniform(-1, 1)
        hp = x - y_ant
        y_ant = x
        crep = sum(math.exp(-(t - e) / 0.004) for e in estalos if t >= e) * hp
        zumbido = (1.0 if math.sin(2 * math.pi * 120 * t) > 0 else -1.0) * 0.18 * math.exp(-t / 0.12)
        out.append(crep * 0.9 + zumbido + hp * 0.25 * math.exp(-t / 0.08))
    return out


# ==============================================================================
# TABELA DE GERAÇÃO COM GANHOS EQUILIBRADOS
# ==============================================================================

SONS = [
    # Interface
    ('clique', clique, 0.50),
    ('construir', construir, 0.60),
    ('remover', remover, 0.55),
    ('alerta', alerta, 0.70),
    ('pesquisa', pesquisa, 0.70),
    ('derrota', derrota, 0.75),

    # Tiros
    ('tiro', tiro, 0.80),
    ('tiro_metralhadora', tiro_metralhadora, 0.80),
    ('tiro_energia', tiro_energia, 0.75),
    ('tiro_foguete', tiro_foguete, 0.80),
    ('tiro_enxame', tiro_enxame, 0.75),
    ('tiro_artilharia', tiro_artilharia, 0.88),
    ('tiro_perfurante', tiro_perfurante, 0.82),
    ('tiro_carregada', tiro_carregada, 0.80),
    ('tiro_drone', tiro_drone, 0.70),

    # Impactos e Explosões
    ('impacto', impacto, 0.85),
    ('impacto_aranha', impacto_aranha, 0.55),
    ('impacto_chao', impacto_chao, 0.50),
    ('impacto_estrutura', impacto_estrutura, 0.58),
    ('explosao', explosao, 0.85),
    ('explosao_grande', explosao_grande, 0.90),
    ('mina_pulso', mina_pulso, 0.75),

    # Máquinas e Trens
    ('maq_fornalha', maq_fornalha, 0.45),
    ('maq_montadora', maq_montadora, 0.48),
    ('maq_broca', maq_broca, 0.46),
    ('maq_esteira', maq_esteira, 0.42),
    ('apito_trem', apito_trem, 0.70),
    ('trem_trilho', trem_trilho, 0.48),

    # Clima
    ('chuva', chuva, 0.55),
    ('trovao', trovao, 0.85),
    ('vento_forte', vento_forte, 0.52),

    # Aranhas
    ('aranha_passo', aranha_passo, 0.35),
    ('aranha_morre', aranha_morre, 0.65),

    # Cenas
    ('reentrada', reentrada, 0.85),
    ('fogo', fogo, 0.50),
    ('faisca', faisca, 0.60),
]


if __name__ == '__main__':
    import sys
    os.makedirs(SAIDA, exist_ok=True)
    alvos = sys.argv[1:] if len(sys.argv) > 1 else None
    for nome, func, ganho in SONS:
        if alvos and nome not in alvos:
            continue
        gravar(nome, func(), taxa=TAXA, ganho=ganho)
        print(f"SOM {nome} (44,1 kHz, ganho {ganho})")
