import json
import requests
from config import GITHUB_TOKEN, GIST_ID

# No carregamento inicial, garantir que manutenções antigas tenham campo de preço
def load_from_gist():
    global bot_data
    
    print(f"📂 Tentando carregar dados do Gist: {GIST_ID}")
    
    if not GITHUB_TOKEN or not GIST_ID:
        print("❌ GITHUB_TOKEN ou GIST_ID não configurados")
        bot_data = {"km": [], "fuel": [], "manu": []}
        return bot_data
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data.get("files", {})
            if "moto_data.json" in files:
                content = files["moto_data.json"]["content"]
                loaded_data = json.loads(content)
                
                # Garantir que manutenções antigas tenham campo de preço
                for manu in loaded_data.get("manu", []):
                    if "price" not in manu:
                        manu["price"] = 0.0  # Valor padrão para manutenções antigas
                
                bot_data.update(loaded_data)
                print(f"✅ Dados carregados: {len(bot_data['km'])} KM, {len(bot_data['fuel'])} abastecimentos, {len(bot_data['manu'])} manutenções")
        else:
            bot_data = {"km": [], "fuel": [], "manu": []}
            
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        bot_data = {"km": [], "fuel": [], "manu": []}
    
    return bot_data

def save_to_gist(data):
    """
    Salva os dados no Gist do GitHub
    Retorna True se salvou com sucesso, False se falhou
    """
    print(f"💾 Tentando salvar dados no Gist: {GIST_ID}")
    
    if not GITHUB_TOKEN or not GIST_ID:
        print("❌ GITHUB_TOKEN ou GIST_ID não configurados")
        return False
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "files": {
                "moto_data.json": {
                    "content": json.dumps(data, indent=2, ensure_ascii=False)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        success = response.status_code == 200
        
        if success:
            print("✅ Dados salvos com sucesso no Gist")
        else:
            print(f"❌ Erro ao salvar: {response.status_code} - {response.text}")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao salvar dados: {e}")
        return False

def get_bot_data():
    """Retorna os dados do bot"""
    return bot_data

def update_bot_data(new_data):
    """Atualiza os dados do bot"""
    global bot_data
    bot_data = new_data
    print(f"🔄 Dados atualizados: {len(bot_data['km'])} KM, {len(bot_data['fuel'])} abastecimentos, {len(bot_data['manu'])} manutenções")
