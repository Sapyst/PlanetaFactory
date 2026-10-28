#!/usr/bin/env bash
# Importa o projeto (atualiza o cache de classes e os .glb) e roda todos os testes sem janela.
# Uso: ferramentas/testar.sh [filtro]
# Erro de script (que o GDScript não deixa o teste capturar) também conta como falha.
cd "$(dirname "$0")/.."
G="${GODOT:-godot}"
timeout 600 "$G" --headless --path . --import >/dev/null 2>&1
SAIDA=$(timeout 900 "$G" --headless --path . -s res://testes/executar.gd -- "$@" 2>&1)
COD=$?
echo "$SAIDA" | grep -vE "^Godot Engine|^$|resources still in use|ObjectDB instances|at: (cleanup|clear)"
if echo "$SAIDA" | grep -q "SCRIPT ERROR"; then
  echo "FALHA: houve erro de script (ver acima)"
  exit 1
fi
exit $COD
