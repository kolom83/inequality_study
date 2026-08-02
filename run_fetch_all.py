from dotenv import load_dotenv

load_dotenv("D:/project/inequality_study/.env")
import os

from src.wid_client import WidClient

os.makedirs(".cache", exist_ok=True)
client = WidClient()
df = client.fetch_all()
df.to_csv("data_wid.csv", index=False)
print(f"Сохранено {len(df)} строк в data_wid.csv")
print("Уникальных стран:", df["country"].nunique())
print("Уникальных переменных:", df["variable"].nunique())
print(df.groupby(["country", "variable"]).size().reset_index(name="n").head(20).to_string())
