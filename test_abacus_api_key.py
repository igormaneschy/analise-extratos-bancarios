from abacusai import ApiClient
import os

API_KEY = os.getenv("ABACUS_API_KEY")

if not API_KEY:
    print("[TEST] ABACUS_API_KEY não está definida no ambiente.")
    exit(1)

try:
    client = ApiClient(API_KEY)
    # Testar uma chamada para listar modelos disponíveis
    models = client.list_models()  # Ajuste conforme método correto da API
    print(f"[TEST] Chave API válida. Modelos disponíveis: {models}")
except Exception as e:
    print(f"[TEST] Erro ao validar chave API: {e}")
