# bot_runner.py - Bot rodando sozinho
import asyncio
import os
import logging
from bot_telegram import FinanceBot
from telegram.ext import Application, CommandHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Executar bot no processo principal"""
    try:
        logger.info("🤖 Iniciando bot standalone...")
        
        bot = FinanceBot()
        
        # Configurar aplicação
        app = Application.builder().token(bot.token).build()
        
        # Adicionar handlers
        app.add_handler(CommandHandler("start", bot.start))
        app.add_handler(CommandHandler("ajuda", bot.start))
        app.add_handler(CommandHandler("receita", bot.adicionar_receita))
        app.add_handler(CommandHandler("gasto", bot.adicionar_gasto))
        app.add_handler(CommandHandler("saldo", bot.ver_saldo))
        app.add_handler(CommandHandler("extrato", bot.ver_extrato))
        app.add_handler(CommandHandler("categorias", bot.ver_categorias))
        app.add_handler(CommandHandler("backup", bot.backup_excel))
        
        logger.info("✅ Bot configurado e pronto!")
        
        # RODAR NO MAIN THREAD
        await app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Erro no bot: {e}")

if __name__ == '__main__':
    asyncio.run(main())