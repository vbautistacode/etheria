#!/usr/bin/env bash
set -euo pipefail

# caminho para efemérides
export SWISS_EPHE_PATH="$(pwd)/ephe"

# cria venv se não existir
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# ativa venv (Git Bash)
# shellcheck disable=SC1091
source .venv/bin/activate

# instala dependências se existir requirements.txt
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install --no-cache-dir -r requirements.txt
fi

# inicia o Streamlit com o python do venv
python -m streamlit run app.py --server.headless=true
# SWISS_EPHE_PATH="$(pwd)/ephe" /c/Users/pncdp/anaconda/envs/etheria/python.exe -m streamlit run app.py
