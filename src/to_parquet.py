import pandas as pd
from transforms import precos_comparativo
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PRECOS_EMPRESA_PATH = BASE_DIR / "Auxiliares" / "Precos Empresa.xlsx"
    
precos_empresa = pd.read_excel(PRECOS_EMPRESA_PATH)

precos_empresa.to_parquet('Precos Empresa.parquet', index=False)



