@echo off
set PATH=C:\Python\Scripts;%PATH%
python.exe -m streamlit run app.py

export GOOGLE_APPLICATION_CREDENTIALS="C:\Users\pncdp\OneDrive\Arquivos Eubiose\Etheria\etheria-480312-bb275bf290e9.json"
export GOOGLE_CLOUD_PROJECT="etheria-480312"
export GOOGLE_CLOUD_LOCATION="southamerica-east1"
export GENAI_VERTEXAI=1
python.exe -m streamlit run app.py