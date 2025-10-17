import os
import json

creds_json = os.getenv("GOOGLE_CREDENTIALS")

if creds_json is None:
    print("❌ ERRO: Variável GOOGLE_CREDENTIALS não foi encontrada!")
else:
    print("✅ Variável encontrada!")
    print("Tamanho:", len(creds_json))
    try:
        data = json.loads(creds_json)
        print("✅ JSON válido com chave:", list(data.keys())[0])
    except Exception as e:
        print("⚠️ JSON inválido:", e)
