#!/bin/sh
# Camada B da trava do QA (D6c): impressão digital do conteúdo do repositório, rastreado e não rastreado (exceto ignorados).
# Rodar antes e depois do QA; hashes diferentes = o QA alterou algo, e o resultado do QA é descartado.
set -eu
cd "$(git rev-parse --show-toplevel)"
{
  git diff HEAD --binary
  git ls-files --others --exclude-standard -z | xargs -0 -r sha256sum --
} | sha256sum | cut -d' ' -f1
