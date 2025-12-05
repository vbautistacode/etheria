# Etheria

Etheria — Painel esotérico com numerologia, arcanos e ciclos (Astrológico / Teosófico / Maior).

## Requisitos
- Python 3.9+
- pip

## Instalação rápida
```bash
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
.venv\Scripts\activate       # Windows
pip install -r requirements.txt

## Como rodar localmente (recomendado: conda `etheria`)

1. Ative o ambiente conda `etheria` (ou crie com `environment.yml`):
```powershell
conda activate etheria
Defina a variável de ambiente SWISS_EPHE_PATH e inicie o Streamlit com o Python do ambiente:

powershell
$env:SWISS_EPHE_PATH = (Resolve-Path .\ephe).Path
python -m streamlit run app.py --server.address=127.0.0.1 --logger.level=debug
Observações:

Use o mesmo python do ambiente onde instalou as dependências (conda ou .venv).

Se preferir usar .venv, ative-o antes de rodar:

Git Bash: source .venv/bin/activate

PowerShell: .\.venv\Scripts\Activate.ps1

Se a página mapa_astral reclamar de módulos faltando (ex.: geopy), verifique qual python está sendo usado (veja os prints DEBUG: ... python exe: no terminal) e instale as dependências nesse Python.


---

### Instalação rápida de dependências (comandos)
Se estiver usando **.venv** (no diretório do projeto):

```bash
# ative o venv
source .venv/bin/activate   # Git Bash
# ou
.\.venv\Scripts\Activate.ps1  # PowerShell

# instale dependências
pip install --upgrade pip
pip install -r requirements.txt
# ou instale manualmente
pip install geopy timezonefinder plotly pytz pyswisseph streamlit

# configurar credenciais (local)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json"
export GOOGLE_CLOUD_PROJECT="etheria-480312"
export GOOGLE_CLOUD_LOCATION="us-central1"

Custo de criação e implantação de modelos de IA na Vertex AI
https://cloud.google.com/vertex-ai/generative-ai/pricing?hl=pt-br&_gl=1*fg9ai9*_ga*MTMzNjA1OTU2LjE3NjQ5Mzg2NDQ.*_ga_WH2QY8WWF5*czE3NjQ5NjQwMjAkbzUkZzEkdDE3NjQ5NjQwMjUkajU1JGwwJGgw