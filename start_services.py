# start_services.py - Versão Final Corrigida
import subprocess
import threading
import time
import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_bot():
    """Executar bot do Telegram em subprocess"""
    logger.info("🤖 Iniciando bot do Telegram...")
    try:
        # Importar e executar bot diretamente
        from bot_telegram import run_bot
        run_bot()
    except Exception as e:
        logger.error(f"❌ Erro no bot: {e}")

def run_dashboard():
    """Executar dashboard Streamlit"""
    logger.info("📊 Iniciando dashboard Streamlit...")
    
    # Usar PORT do Railway
    port = os.getenv('PORT', '8080')
    
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
    telegram_token = "7579338249:AAFYyZRwRSE93p8gLrAe7pICqyCxyoHSxdQ"
    
    if not telegram_token:
        logger.error("❌ TELEGRAM_TOKEN não configurado")
        return False
    
    logger.info("✅ Ambiente verificado")
    return True

def setup_excel():
    """Configurar Excel inicial"""
    logger.info("📊 Configurando Excel...")
    
    try:
        import pandas as pd
        
        excel_file = "financeiro_pessoal.xlsx"
        
        if not os.path.exists(excel_file):
            # Criar Excel vazio
            df_empty = pd.DataFrame(columns=[
                'id', 'user_id', 'username', 'tipo', 'valor', 
                'categoria', 'descricao', 'data_criacao'
            ])
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df_empty.to_excel(writer, sheet_name='Transacoes', index=False)
            
            logger.info(f"✅ Arquivo Excel criado: {excel_file}")
        else:
            logger.info(f"✅ Arquivo Excel encontrado: {excel_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Excel: {e}")
        return False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Controle Financeiro Excel Edition...")
    
    # Verificar ambiente
    if not check_environment():
        logger.error("❌ Falha na verificação do ambiente")
        sys.exit(1)
    
    # Configurar Excel
    if not setup_excel():
        logger.error("❌ Falha na configuração do Excel")
        sys.exit(1)
    
    logger.info("🚄 Modo Railway - Iniciando serviços...")
    
    # Bot em thread separada
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Bot iniciado em background")
    
    # Dashboard no processo principal
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