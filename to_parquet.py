import pandas as pd
from transforms import precos_comparativo
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PRECOS_ROLEMAR_PATH = BASE_DIR / "Auxiliares" / "Precos Rolemar.xlsx"
    
precos_rolemar = pd.read_excel(PRECOS_ROLEMAR_PATH)

precos_rolemar.to_parquet('Precos Rolemar.parquet', index=False)



