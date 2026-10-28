"""Texturas de chão em loop (sem emenda) por bioma, geradas por ruído espectral (FFT = periódico por construção).
Saída: arte/texturas/<bioma>.png (512², RGB) + _prancha_texturas.png (cada uma repetida 2×2) + relatório de emenda.
Uso: blender --background --python texturas.py
"""
import bpy, os, json
import numpy as np

N = 512
SAIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'texturas'))
os.makedirs(SAIDA, exist_ok=True)

def ruido(semente, escala, expo=2.0):
    """Ruído 1/f^expo periódico. `escala` = frequência de corte baixa (manchas maiores com valor menor)."""
    rng = np.random.default_rng(semente)
    f = np.fft.fftfreq(N)[:, None]**2 + np.fft.fftfreq(N)[None, :]**2
    f = np.sqrt(f) * N
    amp = 1.0 / np.maximum(f, escala)**expo
    amp[0, 0] = 0
    z = np.fft.ifft2(amp * np.exp(2j*np.pi*rng.random((N, N)))).real
    z -= z.min(); z /= z.max(); return z

def pintas(semente, densidade, raio):
    """Pontinhos (seixos, cristais) periódicos."""
    rng = np.random.default_rng(semente); m = np.zeros((N, N))
    yy, xx = np.mgrid[-raio:raio+1, -raio:raio+1]; disco = (xx**2 + yy**2 <= raio**2).astype(float)
    for _ in range(int(densidade * N * N / 1000)):
        y, x = rng.integers(0, N, 2)
        ys = (np.arange(y - raio, y + raio + 1) % N)[:, None]; xs = (np.arange(x - raio, x + raio + 1) % N)[None, :]
        m[ys, xs] = np.maximum(m[ys, xs], disco * rng.uniform(0.6, 1.0))
    return m

def veios(semente, escala, largura):
    z = ruido(semente, escala, 2.2); return np.clip(1 - np.abs(z - 0.5) / largura, 0, 1)**2

def mistura(c0, c1, t):
    return np.asarray(c0)[None, None, :]*(1 - t[..., None]) + np.asarray(c1)[None, None, :]*t[..., None]

def campina():
    a = ruido(1, 6); b = ruido(2, 40)
    img = mistura((0.25, 0.32, 0.19), (0.35, 0.42, 0.25), np.clip(a*1.3 - 0.15, 0, 1))
    img = mistura_sobre(img, (0.47, 0.45, 0.31), b > 0.62, 0.35)
    return img * (0.9 + 0.2*ruido(3, 120)[..., None])

def floresta_fungica():
    a = ruido(11, 5); v = veios(12, 10, 0.05)
    img = mistura((0.18, 0.15, 0.16), (0.28, 0.23, 0.25), a)
    img = mistura_sobre(img, (0.44, 0.32, 0.46), v, 0.55)
    return img * (0.9 + 0.2*ruido(13, 100)[..., None])

def deserto_silex():
    a = ruido(21, 4); p = pintas(22, 2.0, 3)
    img = mistura((0.62, 0.54, 0.42), (0.74, 0.65, 0.50), a)
    img = mistura_sobre(img, (0.34, 0.35, 0.38), p, 0.8)
    return img * (0.93 + 0.14*ruido(23, 150)[..., None])

def planalto_rochoso():
    a = ruido(31, 5); r = veios(32, 14, 0.035)
    img = mistura((0.33, 0.32, 0.31), (0.50, 0.48, 0.46), a)
    img = mistura_sobre(img, (0.16, 0.16, 0.17), r, 0.9)
    return img * (0.9 + 0.2*ruido(33, 90)[..., None])

def campo_cristal():
    a = ruido(41, 6); p = pintas(42, 1.2, 2)
    img = mistura((0.44, 0.44, 0.47), (0.58, 0.58, 0.61), a)
    img = mistura_sobre(img, (0.56, 0.78, 0.76), p, 0.65)
    return img * (0.92 + 0.16*ruido(43, 120)[..., None])

def pantano():
    a = ruido(51, 4); u = ruido(52, 8)
    img = mistura((0.20, 0.21, 0.14), (0.30, 0.29, 0.19), a)
    img = mistura_sobre(img, (0.10, 0.14, 0.12), np.clip((u - 0.55)*4, 0, 1), 0.85)
    return img * (0.9 + 0.2*ruido(53, 110)[..., None])

def cinzal():
    a = ruido(61, 5); r = veios(62, 9, 0.03)
    img = mistura((0.26, 0.25, 0.25), (0.40, 0.39, 0.39), a)
    img = mistura_sobre(img, (0.66, 0.32, 0.14), r, 0.45)
    return img * (0.9 + 0.2*ruido(63, 100)[..., None])

def agua_rasa():
    a = ruido(71, 6); return mistura((0.13, 0.27, 0.29), (0.21, 0.37, 0.37), a)

def agua_funda():
    a = ruido(81, 5); return mistura((0.05, 0.11, 0.17), (0.08, 0.17, 0.24), a)

def praia():
    a = ruido(91, 6); p = pintas(92, 0.8, 2)
    img = mistura((0.70, 0.63, 0.50), (0.80, 0.73, 0.60), a)
    return mistura_sobre(img, (0.55, 0.52, 0.48), p, 0.6)

def jazida():
    a = ruido(111, 7); r = veios(112, 12, 0.04); p = pintas(113, 1.5, 2)
    img = mistura((0.20, 0.19, 0.21), (0.31, 0.29, 0.31), a)
    img = mistura_sobre(img, (0.12, 0.11, 0.13), r, 0.8)
    return mistura_sobre(img, (0.45, 0.43, 0.42), p, 0.6)

def ruido_detalhe():
    z = ruido(101, 60, 1.2); return np.repeat(z[..., None], 3, axis=2)

def mistura_sobre(img, cor, mascara, forca):
    t = np.clip(np.asarray(mascara, float), 0, 1) * forca
    return img*(1 - t[..., None]) + np.asarray(cor)[None, None, :]*t[..., None]

TEXTURAS = dict(campina=campina, floresta_fungica=floresta_fungica, deserto_silex=deserto_silex,
                planalto_rochoso=planalto_rochoso, campo_cristal=campo_cristal, pantano=pantano, cinzal=cinzal,
                agua_rasa=agua_rasa, agua_funda=agua_funda, praia=praia, jazida=jazida, ruido_detalhe=ruido_detalhe)

def salvar(nome, img):
    img = np.clip(img, 0, 1)
    im = bpy.data.images.new(nome, N, N, alpha=False)
    im.colorspace_settings.name = 'Non-Color' if nome == 'ruido_detalhe' else 'sRGB'   # antes dos pixels: trocar depois zera a imagem
    rgba = np.ones((N, N, 4), dtype=np.float32); rgba[..., :3] = img[::-1]   # Blender guarda de baixo p/ cima
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = os.path.join(SAIDA, nome + '.png'); im.file_format = 'PNG'
    im.save(); return img

def emenda(img):
    """Razão entre o salto na emenda (borda→borda oposta) e o salto médio entre pixels vizinhos. ≈1 = sem emenda."""
    viz = np.mean(np.abs(np.diff(img, axis=1)))
    borda = np.mean(np.abs(img[:, 0] - img[:, -1])) + np.mean(np.abs(img[0, :] - img[-1, :]))
    return float(borda / 2 / viz)

if __name__ == '__main__':
    rel = {}; mosaico = []
    for nome, fn in TEXTURAS.items():
        img = salvar(nome, fn()); rel[nome] = round(emenda(img), 3)
        mosaico.append(np.tile(img[::2, ::2], (2, 2, 1)))
    linhas = [np.concatenate(mosaico[i:i+4] + [np.zeros_like(mosaico[0])]*(4 - len(mosaico[i:i+4])), axis=1) for i in range(0, len(mosaico), 4)]
    pr = np.concatenate(linhas, axis=0); H, W = pr.shape[:2]
    im = bpy.data.images.new('_prancha', W, H, alpha=False); rgba = np.ones((H, W, 4), np.float32); rgba[..., :3] = pr[::-1]
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = os.path.join(SAIDA, '_prancha_texturas.png'); im.file_format = 'PNG'; im.save()
    json.dump(rel, open(os.path.join(SAIDA, '_emenda.json'), 'w'), indent=1)
    print('EMENDA', rel)
