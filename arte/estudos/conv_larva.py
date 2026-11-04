"""Entrada do para_jogo.py para a cratera das larvas (estudo_larva.py): a cena tem larvas e a cratera em x = 8; só a
cratera vem para a origem. A gosma translúcida das bolhas fica opaca (vidro_opaco), senão o conversor tira.
A larva (corpo deformado por esqueleto) não passa por aqui: é exportada por exportar_larva.py."""
CONFIG = {
    'cratera_larva': dict(script='estudo_larva.py', args=['nada'], estudo='estudo_larva.py', cat='inimigos/larva',
                          tris=3500, tex=1024, tirar=['EFEITO_', 'larva'], centro=(8.0, 0.0), anima=False, por_peca=True,
                          brilho={'nome': 'P_Biomassa', 'cor': (0.42, 0.72, 0.08)},
                          vidro_opaco={'bolhas': (0.45, 0.65, 0.12), 'escorridos': (0.16, 0.22, 0.04), 'ovo': (0.62, 0.58, 0.40)}),
}
