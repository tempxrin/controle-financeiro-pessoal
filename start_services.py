# start_services.py - Excel Edition
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
        logging.FileHandler('services.log'),
        logging.StreamHandler()
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
        
        # Criar pasta de backup se configurada
        backup_folder = config['storage'].get('backup_folder')
        if backup_folder and not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
            logger.info(f"✅ Pasta de backup criada: {backup_folder}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Excel: {e}")
        return False

def run_bot():
    """Executar bot do Telegram"""
    logger.info("🤖 Iniciando bot do Telegram...")
    try:
        result = subprocess.run([sys.executable, 'bot_telegram.py'], 
                              capture_output=True, text=True, check=True)
        logger.info("Bot executado com sucesso")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao executar bot: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ Erro inesperado no bot: {e}")

def run_dashboard():
    """Executar dashboard Streamlit"""
    logger.info("📊 Iniciando dashboard Streamlit...")
    
    # Carregar configurações
    config = load_config()
    port = str(config['dashboard']['port']) if config else '8501'
    
    # Usar PORT do ambiente se disponível (Railway)
    port = os.getenv('PORT', port)
    
    try:
        cmd = [
            'streamlit', 'run', 'dashboard.py',
            '--server.address', '0.0.0.0',
            '--server.port', port,
            '--server.headless', 'true',
            '--server.fileWatcherType', 'none',
            '--browser.gatherUsageStats', 'false',
            '--theme.base', 'dark'
        ]
        
        logger.info(f"Executando dashboard na porta {port}")
        result = subprocess.run(cmd, check=True)
        logger.info("Dashboard executado com sucesso")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao executar dashboard: {e}")
    except Exception as e:
        logger.error(f"❌ Erro inesperado no dashboard: {e}")

def check_environment():
    """Verificar variáveis de ambiente e arquivos necessários"""
    logger.info("🔍 Verificando ambiente...")
    
    # Verificar arquivos necessários
    required_files = ['config.yaml', 'bot_telegram.py', 'dashboard.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)