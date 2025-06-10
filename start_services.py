# start_services.py - VERSÃO SIMPLES QUE FUNCIONA
import subprocess
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

def run_dashboard():
    """Executar APENAS dashboard Streamlit"""
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
    """Função principal - APENAS DASHBOARD"""
    logger.info("🚀 Iniciando Dashboard Excel Edition...")
    
    # Configurar Excel
    if not setup_excel():
        logger.error("❌ Falha na configuração do Excel")
        sys.exit(1)
    
    logger.info("📊 Modo Dashboard Only - Iniciando...")
    
    # APENAS dashboard no processo principal
    run_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Aplicação encerrada")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        sys.exit(1)