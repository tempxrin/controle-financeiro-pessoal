# start_services.py - Corrigido para Railway
import subprocess
import threading
import time
import os
import sys
import logging
import yaml

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Apenas console para Railway
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Carregar configurações do YAML"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            logger.info("Configurações carregadas com sucesso")
            return config
    except FileNotFoundError:
        logger.error("Arquivo config.yaml não encontrado")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Erro ao carregar config.yaml: {e}")
        return None

def setup_excel_environment():
    """Configurar ambiente Excel"""
    logger.info("🔧 Configurando ambiente Excel...")
    
    config = load_config()
    if not config:
        return False
    
    try:
        # Criar arquivo Excel se não existir
        excel_file = config['storage']['excel_file']
        
        if not os.path.exists(excel_file):
            import pandas as pd
            
            # Criar DataFrame vazio
            df_empty = pd.DataFrame(columns=[
                'id', 'user_id', 'username', 'tipo', 'valor', 
                'categoria', 'descricao', 'data_criacao'
            ])
            
            # Salvar arquivo Excel
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df_empty.to_excel(writer, sheet_name='Transacoes', index=False)
            
            logger.info(f"✅ Arquivo Excel criado: {excel_file}")
        else:
            logger.info(f"✅ Arquivo Excel encontrado: {excel_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Excel: {e}")
        return False

def run_bot():
    """Executar bot do Telegram"""
    logger.info("🤖 Iniciando bot do Telegram...")
    try:
        subprocess.run([sys.executable, 'bot_telegram.py'], check=False)
    except Exception as e:
        logger.error(f"❌ Erro no bot: {e}")

def run_dashboard():
    """Executar dashboard Streamlit"""
    logger.info("📊 Iniciando dashboard Streamlit...")
    
    # IMPORTANTE: Usar PORT do Railway
    port = os.getenv('PORT', '8501')
    
    try:
        cmd = [
            'streamlit', 'run', 'dashboard.py',
            '--server.address', '0.0.0.0',
            '--server.port', port,
            '--server.headless', 'true',
            '--server.fileWatcherType', 'none',
            '--browser.gatherUsageStats', 'false'
        ]
        
        logger.info(f"🚀 Executando dashboard na porta {port}")
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        logger.error(f"❌ Erro no dashboard: {e}")
        raise

def check_environment():
    """Verificar ambiente"""
    logger.info("🔍 Verificando ambiente...")
    
    # Verificar token do Telegram
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token:
        # Tentar carregar do config
        config = load_config()
        if config:
            telegram_token = config.get('telegram', {}).get('token')
    
    if not telegram_token or telegram_token == "SEU_TOKEN_AQUI":
        logger.error("❌ TELEGRAM_TOKEN não configurado")
        return False
    
    logger.info("✅ Ambiente verificado")
    return True

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Controle Financeiro Excel Edition...")
    
    # Verificar ambiente
    if not check_environment():
        logger.error("❌ Falha na verificação do ambiente")
        sys.exit(1)
    
    # Configurar Excel
    if not setup_excel_environment():
        logger.error("❌ Falha na configuração do Excel")
        sys.exit(1)
    
    # No Railway, executar bot em background e dashboard em foreground
    logger.info("🚄 Modo Railway - Iniciando serviços...")
    
    # Bot em thread separada
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Bot iniciado em background")
    
    # Dashboard no processo principal (OBRIGATÓRIO para Railway)
    time.sleep(3)
    logger.info("✅ Iniciando dashboard...")
    run_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Aplicação encerrada")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        sys.exit(1)