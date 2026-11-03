#!/usr/bin/env bash
# Medições sem janela do checkup (antes × depois de cada mudança): abertura e quadros da demonstração
# (ferramentas/medir.gd), jogo novo com a abertura, e o roteiro `carga patio` (pior caso de fábrica).
# Uso: ferramentas/medir.sh [pasta_de_saida]   — grava um .log por medição e imprime as linhas MEDIR/CARGA/SALVAR
# e os erros de script. Sem janela não há GPU: só CPU.
cd "$(dirname "$0")/.."
G="${GODOT:-godot}"
OUT="${1:-/tmp/pf_medidas}"
mkdir -p "$OUT"
COMUM="--headless --audio-driver Dummy --path ."
timeout 600 "$G" $COMUM --import >/dev/null 2>&1
timeout 600 "$G" $COMUM -s res://ferramentas/medir.gd -- quadros 600 > "$OUT/demo.log" 2>&1
timeout 600 "$G" $COMUM -s res://ferramentas/medir.gd -- novo quadros 600 > "$OUT/novo.log" 2>&1
timeout 900 "$G" $COMUM -- modo demo roteiro carga patio > "$OUT/carga_patio.log" 2>&1
for f in demo novo carga_patio; do
  echo "== $f"
  grep -E "^MEDIR|^CARGA|^SALVAR|SCRIPT ERROR|ERROR|WARNING" "$OUT/$f.log" | grep -vE "resources still in use|ObjectDB instances|at: (cleanup|clear)" | head -40
done
