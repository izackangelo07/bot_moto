import json
import requests
from config import GITHUB_TOKEN, GIST_ID

# Variável global para os dados
bot_data = {"km": [], "fuel": [], "manu": []}

def load_from_gist():
    """
    Carrega os dados do Gist do GitHub
    Retorna dicionário com listas vazias se não conseguir carregar
    """
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
        
        print(f"🌐 Fazendo requisição para: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data.get("files", {})
            print(f"📄 Arquivos encontrados: {list(files.keys())}")
            
            if "moto_data.json" in files:
                content = files["moto_data.json"]["content"]
                print(f"📊 Conteúdo do arquivo: {len(content)} caracteres")
                
                # Carregar os dados
                loaded_data = json.loads(content)
                bot_data.update(loaded_data)  # Atualiza mantendo a referência
                
                print(f"✅ Dados carregados: {len(bot_data['km'])} KM, {len(bot_data['fuel'])} abastecimentos, {len(bot_data['manu'])} manutenções")
                return bot_data
            else:
                print("❌ Arquivo moto_data.json não encontrado no Gist")
                bot_data = {"km": [], "fuel": [], "manu": []}
        else:
            print(f"❌ Erro na API do GitHub: {response.status_code}")
            bot_data = {"km": [], "fuel": [], "manu": []}
            
    except Exception as e:
        print(f"❌ Erro ao carregar dados do Gist: {e}")
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
