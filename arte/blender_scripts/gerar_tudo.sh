#!/usr/bin/env bash
# Regenera todos os modelos, as pranchas e o catálogo. Uso: ./gerar_tudo.sh
set -e
cd "$(dirname "$0")"
B="${BLENDER:-$HOME/.local/share/Steam/steamapps/common/Blender/blender}"
for s in itens logistica maquinas limpeza estruturas_extra mapa arvores transporte inimigos; do
  "$B" -b --factory-startup --python "$s.py" 2>&1 | grep -E "^(OK|ERRO)"
done
"$B" -b --factory-startup --python texturizar.py 2>&1 | grep -E "^(TEX|ERRO)"
"$B" -b --factory-startup --python prancha.py >/dev/null 2>&1
"$B" -b --factory-startup --python prancha.py -- logistica >/dev/null 2>&1
"$B" -b --factory-startup --python prancha.py -- maquinas >/dev/null 2>&1
for p in biomas transporte; do "$B" -b --factory-startup --python prancha.py -- $p >/dev/null 2>&1; done
"$B" -b --factory-startup --python icones.py 2>&1 | grep ICONES
"$B" -b --factory-startup --python texturas.py 2>&1 | grep EMENDA
python3 piso_blocos.py pedra ../texturas/piso_fabrica.png
python3 catalogo.py
python3 ../../jogo/ferramentas/sincronizar_arte.py
rm -rf ../modelos/_tmp __pycache__
