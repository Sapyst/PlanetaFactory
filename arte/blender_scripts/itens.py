"""Itens transportáveis (recursos, intermediários, avançados). Cada um cabe em 0,26 m³, base em z = 0.
Uso: blender --background --python itens.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar

R, I, A = 'itens/recursos', 'itens/intermediarios', 'itens/avancados'

def apoiar(m):
    """Desce a peça para a base tocar z = 0 (pedras irregulares)."""
    for p in m.partes:
        zmin = min(v.co.z for v in p.bm.verts)
        for v in p.bm.verts: v.co.z -= zmin
    return m

# ---------------------------------------------------------------- recursos brutos
def cristal_bruto():
    m = Modelo('cristal_bruto', R, tipo='item', descricao='Cristal arrancado pelo extrator. Base de quase tudo.'); p = m.parte()
    p.pedra((0, 0, 0.03), 0.09, (1.2, 1.0, 0.45), 'P_Pedra', 1)
    p.cil((0.0, 0.0, 0.13), 0.045, 0.20, 'P_Cristal', lados=6, r2=0.0)
    p.cil((0.06, 0.03, 0.10), 0.03, 0.12, 'P_Cristal', lados=6, r2=0.0)
    p.cil((-0.05, -0.04, 0.09), 0.025, 0.10, 'P_Cristal', lados=6, r2=0.0)
    return apoiar(m)

def _minerio(nome, cor_pedra, cor_veio, semente, desc):
    m = Modelo(nome, R, tipo='item', descricao=desc); p = m.parte()
    p.pedra((0, 0, 0), 0.11, (1.0, 0.9, 0.7), cor_pedra, semente)
    for i, (x, y, z) in enumerate(((0.06, 0.04, 0.05), (-0.05, 0.05, 0.06), (0.0, -0.07, 0.04))):
        p.pedra((x, y, z), 0.035, (1, 1, 1), cor_veio, semente*10 + i, sub=1, ruido=0.1)
    return apoiar(m)

def minerio_ferro(): return _minerio('minerio_ferro', 'P_Pedra', 'P_Ferrugem', 2, 'Rocha com veios de ferro.')
def minerio_cobre(): return _minerio('minerio_cobre', 'P_Pedra', 'P_Malaquita', 3, 'Rocha com malaquita (cobre).')

def pedra():
    m = Modelo('pedra', R, tipo='item', descricao='Rocha comum: tijolo, muro, concreto.'); p = m.parte()
    p.pedra((0, 0, 0), 0.115, (1.0, 0.95, 0.75), 'P_Pedra', 4); return apoiar(m)

def carvao():
    m = Modelo('carvao', R, tipo='item', descricao='Combustível das fornalhas e geradores.'); p = m.parte()
    p.pedra((0.02, 0, 0), 0.09, (1, 0.9, 0.8), 'P_Carvao', 5, ruido=0.25)
    p.pedra((-0.06, 0.04, 0), 0.05, (1, 1, 0.9), 'P_Carvao', 6, ruido=0.25)
    return apoiar(m)

def biomassa():
    m = Modelo('biomassa', R, tipo='item', descricao='Fungo vivo do planeta. Combustível e química.'); p = m.parte()
    p.cil((0, 0, 0.05), 0.035, 0.10, 'P_Pedra', lados=6)
    p.cil((0, 0, 0.13), 0.11, 0.07, 'P_Biomassa', lados=8, r2=0.05)
    p.cil((0.07, -0.05, 0.03), 0.02, 0.06, 'P_Pedra', lados=6)
    p.cil((0.07, -0.05, 0.075), 0.05, 0.035, 'P_Biomassa', lados=6, r2=0.02)
    return m

def areia():
    m = Modelo('areia', R, tipo='item', descricao='Saco de areia: vidro e silício.'); p = m.parte()
    p.cil((0, 0, 0.065), 0.11, 0.13, 'P_Areia', lados=8, r2=0.09)
    p.cil((0, 0, 0.145), 0.05, 0.03, 'P_Escuro', lados=6)
    return m

def silex():
    m = Modelo('silex', R, tipo='item', descricao='Sílex: pedra dura e afiada, usada em munição e ferramentas.'); p = m.parte()
    p.prisma([(-0.11, -0.05), (0.02, -0.09), (0.11, -0.02), (0.06, 0.08), (-0.07, 0.07)], 0, 0.07, 'P_Silex')
    p.prisma([(-0.05, -0.03), (0.04, -0.05), (0.06, 0.03), (-0.02, 0.05)], 0.07, 0.11, 'P_Silex')
    return m

# ---------------------------------------------------------------- intermediários
def _placa(nome, mat, desc):
    m = Modelo(nome, I, tipo='item', descricao=desc); p = m.parte()
    for i in range(3): p.caixa_c(0, 0, i*0.035, 0.22, 0.16, 0.03, mat, rot=0.08*(i-1))
    return m
def placa_ferro(): return _placa('placa_ferro', 'P_Metal', 'Pilha de chapas de ferro.')
def placa_cobre(): return _placa('placa_cobre', 'P_Cobre', 'Pilha de chapas de cobre.')

def fio_cobre():
    m = Modelo('fio_cobre', I, tipo='item', descricao='Carretel de fio de cobre.'); p = m.parte()
    p.cil((0, 0, 0.11), 0.07, 0.16, 'P_Cobre', eixo='X')
    for x in (-0.09, 0.09): p.cil((x, 0, 0.11), 0.11, 0.025, 'P_Escuro', eixo='X')
    return m

def engrenagem():
    m = Modelo('engrenagem', I, tipo='item', descricao='Engrenagem de ferro.'); p = m.parte()
    # dentes fundos e peça alta: a 20 m um dente rasinho tem menos de 2 pixels e o contorno "ferve" (serrilhado) andando na esteira
    p.engrenagem((0, 0, 0.035), 0.125, 0.078, 5, 0.07, 'P_Metal')
    p.cil((0, 0, 0.074), 0.042, 0.008, 'P_Escuro', lados=6)   # cubo escuro: lê como engrenagem de longe e separa do branco da lona
    return m

def barra_aco():
    m = Modelo('barra_aco', I, tipo='item', descricao='Lingote de aço.'); p = m.parte()
    p.cil((0, 0, 0.0375), 0.12, 0.075, 'P_Aco', lados=4, r2=0.085, rot=math.pi/4)  # tronco de pirâmide
    for v in p.bm.verts: v.co.y *= 0.55
    return m

def tijolo():
    m = Modelo('tijolo', I, tipo='item', descricao='Par de tijolos de pedra cozida.'); p = m.parte()
    p.caixa_c(0, -0.045, 0, 0.22, 0.085, 0.07, 'P_Tijolo'); p.caixa_c(0, 0.045, 0, 0.22, 0.085, 0.07, 'P_Tijolo')
    p.caixa_c(0, 0, 0.07, 0.085, 0.22, 0.07, 'P_Tijolo')   # fiada cruzada
    return m

def vidro():
    m = Modelo('vidro', I, tipo='item', descricao='Painel de vidro com moldura.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.22, 0.22, 0.015, 'P_Escuro')
    p.caixa_c(0, 0, 0.015, 0.19, 0.19, 0.02, 'P_Vidro')
    return m

def cristal_lapidado():
    m = Modelo('cristal_lapidado', I, tipo='item', descricao='Cristal cortado: foco de energia.'); p = m.parte()
    p.cil((0, 0, 0.05), 0.0, 0.10, 'P_Cristal', lados=6, r2=0.09)
    p.cil((0, 0, 0.155), 0.09, 0.11, 'P_Cristal', lados=6, r2=0.0)
    return m

def tubo():
    m = Modelo('tubo', I, tipo='item', descricao='Tubo de ferro para canos e máquinas.'); p = m.parte()
    p.cil((0, 0, 0.06), 0.06, 0.24, 'P_Metal', eixo='X')
    for x in (-0.11, 0.11): p.cil((x, 0, 0.06), 0.065, 0.02, 'P_Escuro', eixo='X')
    return apoiar(m)

def circuito():
    m = Modelo('circuito', I, tipo='item', descricao='Placa de circuito.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.22, 0.16, 0.02, 'P_Placa')
    p.caixa_c(-0.04, 0.0, 0.02, 0.07, 0.07, 0.025, 'P_Escuro')
    p.caixa_c(0.06, 0.03, 0.02, 0.04, 0.04, 0.02, 'P_Escuro')
    p.caixa_c(0.06, -0.04, 0.02, 0.06, 0.015, 0.008, 'P_Cobre')
    p.caixa_c(-0.09, 0.0, 0.02, 0.015, 0.12, 0.008, 'P_Cobre')
    return m

def bateria():
    m = Modelo('bateria', I, tipo='item', descricao='Bateria química.'); p = m.parte()
    p.cil((0, 0, 0.09), 0.07, 0.18, 'P_Escuro')
    p.cil((0, 0, 0.09), 0.072, 0.04, 'P_Faixa')
    p.cil((0, 0, 0.195), 0.03, 0.03, 'P_Cobre', lados=6)
    return m

def nucleo_cristal():
    m = Modelo('nucleo_cristal', I, tipo='item', descricao='Cristal lapidado preso em gaiola: armazena energia.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.20, 0.20, 0.03, 'P_Metal')
    for x in (-0.085, 0.085):
        for y in (-0.085, 0.085): p.caixa_c(x, y, 0.03, 0.03, 0.03, 0.12, 'P_Escuro')
    p.cil((0, 0, 0.075), 0.0, 0.09, 'P_Cristal', lados=6, r2=0.075)
    p.cil((0, 0, 0.17), 0.075, 0.10, 'P_Cristal', lados=6, r2=0.0)
    return m

# ---------------------------------------------------------------- avançados
def motor():
    m = Modelo('motor', A, tipo='item', descricao='Motor elétrico.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.20, 0.16, 0.03, 'P_Escuro')
    p.cil((-0.01, 0, 0.11), 0.075, 0.16, 'P_Metal', eixo='X')
    p.cil((-0.01, 0, 0.11), 0.082, 0.03, 'P_Escuro', eixo='X')
    p.cil((0.10, 0, 0.11), 0.02, 0.05, 'P_Cobre', eixo='X', lados=6)
    return m

def modulo_controle():
    m = Modelo('modulo_controle', A, tipo='item', descricao='Módulo de controle com tela de cristal.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.22, 0.18, 0.08, 'P_Metal')
    p.caixa_c(0, -0.02, 0.08, 0.16, 0.10, 0.012, 'P_Cristal')
    p.caixa_c(0, 0.07, 0.08, 0.16, 0.03, 0.02, 'P_Escuro')
    p.caixa_c(-0.06, 0.07, 0.10, 0.02, 0.02, 0.02, 'P_Faixa'); p.caixa_c(0.06, 0.07, 0.10, 0.02, 0.02, 0.02, 'P_Faixa')
    return m

def municao():
    m = Modelo('municao', A, tipo='item', descricao='Caixa de munição das torres.'); p = m.parte()
    p.caixa_c(0, 0, 0, 0.22, 0.14, 0.09, 'P_Municao')
    p.caixa_c(0, 0, 0.09, 0.22, 0.02, 0.01, 'P_Faixa')
    for x in (-0.06, 0.0, 0.06):
        p.cil((x, 0.0, 0.12), 0.02, 0.06, 'P_Cobre', lados=5)
        p.cil((x, 0.0, 0.165), 0.02, 0.03, 'P_Silex', lados=5, r2=0.0)
    return m

def celula_energia():
    m = Modelo('celula_energia', A, tipo='item', descricao='Célula de energia portátil.'); p = m.parte()
    p.cil((0, 0, 0.11), 0.07, 0.22, 'P_Metal', eixo='X')
    p.cil((0, 0, 0.11), 0.075, 0.10, 'P_Cristal', eixo='X')
    for x in (-0.10, 0.10): p.cil((x, 0, 0.11), 0.078, 0.025, 'P_Escuro', eixo='X', lados=6)
    return apoiar(m)

def pacote_pesquisa():
    m = Modelo('pacote_pesquisa', A, tipo='item', descricao='Frasco de pesquisa para o laboratório.'); p = m.parte()
    p.cil((0, 0, 0.06), 0.09, 0.12, 'P_Cristal')            # líquido (visível)
    p.cil((0, 0, 0.15), 0.09, 0.06, 'P_Vidro', r2=0.03)
    p.cil((0, 0, 0.21), 0.035, 0.06, 'P_Escuro', lados=6)
    return m

TODOS = [cristal_bruto, minerio_ferro, minerio_cobre, pedra, carvao, biomassa, areia, silex,
         placa_ferro, placa_cobre, fio_cobre, engrenagem, barra_aco, tijolo, vidro, cristal_lapidado,
         tubo, circuito, bateria, nucleo_cristal,
         motor, modulo_controle, municao, celula_energia, pacote_pesquisa]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'itens', '_relatorio_itens.json'))
