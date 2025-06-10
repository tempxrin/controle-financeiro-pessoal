# bot_telegram.py - Corrigido para Railway
import os
import logging
from datetime import datetime
import pandas as pd
import yaml
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinanceBot:
    def __init__(self):
        self.config = self.load_config()
        self.excel_file = self.config['storage']['excel_file']
        self.token = self.get_token()
        self.init_excel_file()
        
        logger.info("Bot inicializado com storage Excel")
    
    def get_token(self):
        """Obter token do ambiente ou config"""
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            token = self.config['telegram']['token']
        return token
    
    def load_config(self):
        """Carregar configurações do arquivo YAML"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info("Configurações carregadas com sucesso")
                return config
        except FileNotFoundError:
            logger.error("Arquivo config.yaml não encontrado")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Erro ao carregar config.yaml: {e}")
            raise
    
    def init_excel_file(self):
        """Inicializar arquivo Excel se não existir"""
        try:
            if not os.path.exists(self.excel_file):
                # Criar DataFrame vazio com colunas necessárias
                df_empty = pd.DataFrame(columns=[
                    'id', 'user_id', 'username', 'tipo', 'valor', 
                    'categoria', 'descricao', 'data_criacao'
                ])
                
                # Salvar arquivo Excel
                with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                    df_empty.to_excel(writer, sheet_name='Transacoes', index=False)
                
                logger.info(f"Arquivo Excel criado: {self.excel_file}")
            else:
                logger.info(f"Arquivo Excel encontrado: {self.excel_file}")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar Excel: {e}")
            raise
    
    def read_excel_data(self, user_id=None):
        """Ler dados do Excel"""
        try:
            df = pd.read_excel(self.excel_file, sheet_name='Transacoes')
            
            # Filtrar por usuário se especificado
            if user_id:
                df = df[df['user_id'] == user_id]
            
            return df
            
        except FileNotFoundError:
            logger.warning("Arquivo Excel não encontrado, criando novo")
            self.init_excel_file()
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erro ao ler Excel: {e}")
            return pd.DataFrame()
    
    def save_transaction(self, user_id, username, tipo, valor, categoria, descricao):
        """Salvar transação no Excel"""
        try:
            # Ler dados existentes
            df = self.read_excel_data()
            
            # Criar nova transação
            new_id = len(df) + 1 if not df.empty else 1
            new_transaction = {
                'id': new_id,
                'user_id': user_id,
                'username': username,
                'tipo': tipo,
                'valor': valor,
                'categoria': categoria,
                'descricao': descricao,
                'data_criacao': datetime.now()
            }
            
            # Adicionar à DataFrame
            new_df = pd.concat([df, pd.DataFrame([new_transaction])], ignore_index=True)
            
            # Salvar no Excel
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                new_df.to_excel(writer, sheet_name='Transacoes', index=False)
            
            logger.info(f"Transação salva - {username}: {tipo} R$ {valor:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar transação: {e}")
            return False
    
    def get_user_summary(self, user_id):
        """Obter resumo financeiro do usuário"""
        try:
            df = self.read_excel_data(user_id)
            
            if df.empty:
                return {'receitas': 0, 'gastos': 0, 'saldo': 0}
            
            receitas = df[df['tipo'] == 'receita']['valor'].sum()
            gastos = df[df['tipo'] == 'gasto']['valor'].sum()
            saldo = receitas - gastos
            
            return {
                'receitas': receitas,
                'gastos': gastos,
                'saldo': saldo
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular resumo: {e}")
            return {'receitas': 0, 'gastos': 0, 'saldo': 0}
    
    def get_user_transactions(self, user_id, limit=None):
        """Obter transações do usuário"""
        try:
            df = self.read_excel_data(user_id)
            
            if df.empty:
                return []
            
            # Ordenar por data (mais recentes primeiro)
            df = df.sort_values('data_criacao', ascending=False)
            
            # Aplicar limite se especificado
            if limit:
                df = df.head(limit)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Erro ao buscar transações: {e}")
            return []
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        logger.info(f"Comando /start executado por {username} (ID: {user_id})")
        
        welcome_msg = f"""
🏦 *Olá, {username}! Bem-vindo ao Controle Financeiro Pessoal*

*Comandos disponíveis:*
• `/receita [valor] [categoria] [descrição]` - Adicionar receita
• `/gasto [valor] [categoria] [descrição]` - Adicionar gasto
• `/saldo` - Ver saldo atual
• `/extrato` - Ver últimas transações
• `/categorias` - Ver categorias disponíveis
• `/backup` - Gerar backup Excel
• `/ajuda` - Ver esta mensagem

*Exemplos:*
`/receita 1500.00 salario Salário mensal`
`/gasto 50.00 alimentacao Almoço restaurante`

*Categorias disponíveis:*
**Receitas:** {', '.join(self.config['categories']['receitas'])}
**Gastos:** {', '.join(self.config['categories']['gastos'])}

_Seus dados são salvos em planilha Excel segura! 📊_
        """
        
        try:
            await update.message.reply_text(welcome_msg, parse_mode='Markdown')
            logger.info(f"Mensagem de boas-vindas enviada para {username}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")
    
    async def adicionar_receita(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adicionar receita"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        try:
            args = context.args
            if len(args) < 1:
                await update.message.reply_text(
                    "❌ *Formato incorreto!*\n\n"
                    "*Use:* `/receita [valor] [categoria] [descrição]`\n"
                    "*Exemplo:* `/receita 1500.00 salario Salário mensal`",
                    parse_mode='Markdown'
                )
                return
            
            valor = float(args[0].replace(',', '.'))
            categoria = args[1].lower() if len(args) > 1 else "outros"
            descricao = " ".join(args[2:]) if len(args) > 2 else ""
            
            # Validar categoria
            if categoria not in self.config['categories']['receitas']:
                categorias_validas = ', '.join(self.config['categories']['receitas'])
                await update.message.reply_text(
                    f"⚠️ *Categoria '{categoria}' não encontrada.*\n\n"
                    f"*Categorias de receita:* {categorias_validas}",
                    parse_mode='Markdown'
                )
                return
            
            # Salvar no Excel
            success = self.save_transaction(user_id, username, "receita", valor, categoria, descricao)
            
            if success:
                await update.message.reply_text(
                    f"✅ *Receita adicionada com sucesso!*\n\n"
                    f"💵 Valor: R$ {valor:.2f}\n"
                    f"📂 Categoria: {categoria.title()}\n"
                    f"📝 Descrição: {descricao}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Erro ao salvar receita. Tente novamente.")
            
        except ValueError:
            await update.message.reply_text(
                "❌ *Valor inválido!*\n\n"
                "Use números com ponto ou vírgula (ex: 100.50 ou 100,50)",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text("❌ Erro interno. Tente novamente.")
            logger.error(f"Erro ao adicionar receita: {e}")
    
    async def adicionar_gasto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adicionar gasto"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        try:
            args = context.args
            if len(args) < 1:
                await update.message.reply_text(
                    "❌ *Formato incorreto!*\n\n"
                    "*Use:* `/gasto [valor] [categoria] [descrição]`\n"
                    "*Exemplo:* `/gasto 50.00 alimentacao Almoço`",
                    parse_mode='Markdown'
                )
                return
            
            valor = float(args[0].replace(',', '.'))
            categoria = args[1].lower() if len(args) > 1 else "outros"
            descricao = " ".join(args[2:]) if len(args) > 2 else ""
            
            # Validar categoria
            if categoria not in self.config['categories']['gastos']:
                categorias_validas = ', '.join(self.config['categories']['gastos'])
                await update.message.reply_text(
                    f"⚠️ *Categoria '{categoria}' não encontrada.*\n\n"
                    f"*Categorias de gasto:* {categorias_validas}",
                    parse_mode='Markdown'
                )
                return
            
            # Salvar no Excel
            success = self.save_transaction(user_id, username, "gasto", valor, categoria, descricao)
            
            if success:
                await update.message.reply_text(
                    f"✅ *Gasto adicionado com sucesso!*\n\n"
                    f"💸 Valor: R$ {valor:.2f}\n"
                    f"📂 Categoria: {categoria.title()}\n"
                    f"📝 Descrição: {descricao}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Erro ao salvar gasto. Tente novamente.")
            
        except ValueError:
            await update.message.reply_text(
                "❌ *Valor inválido!*\n\n"
                "Use números com ponto ou vírgula (ex: 100.50 ou 100,50)",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text("❌ Erro interno. Tente novamente.")
            logger.error(f"Erro ao adicionar gasto: {e}")
    
    async def ver_saldo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver saldo atual"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        try:
            summary = self.get_user_summary(user_id)
            
            saldo = summary['saldo']
            emoji = "💰" if saldo >= 0 else "⚠️"
            
            msg = f"""
{emoji} *Resumo Financeiro - {username}*

💵 *Receitas:* R$ {summary['receitas']:.2f}
💸 *Gastos:* R$ {summary['gastos']:.2f}
📊 *Saldo:* R$ {saldo:.2f}

📁 *Arquivo:* {self.excel_file}
_Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_
            """
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text("❌ Erro ao consultar saldo.")
            logger.error(f"Erro ao consultar saldo: {e}")
    
    async def ver_extrato(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver últimas transações"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        try:
            limit = self.config['bot']['extrato_limit']
            transacoes = self.get_user_transactions(user_id, limit)
            
            if not transacoes:
                await update.message.reply_text(
                    "📭 *Nenhuma transação encontrada.*\n\n"
                    "Use `/receita` ou `/gasto` para adicionar transações.",
                    parse_mode='Markdown'
                )
                return
            
            msg = f"📋 *Últimas {len(transacoes)} Transações:*\n\n"
            
            for t in transacoes:
                emoji = "💵" if t['tipo'] == 'receita' else "💸"
                data = pd.to_datetime(t['data_criacao']).strftime("%d/%m")
                categoria = t['categoria'].title()
                descricao = str(t['descricao'])[:30] + "..." if len(str(t['descricao'])) > 30 else t['descricao']
                
                msg += f"{emoji} *{data}* - R$ {t['valor']:.2f}\n"
                msg += f"   {categoria} - {descricao}\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text("❌ Erro ao consultar extrato.")
            logger.error(f"Erro ao consultar extrato: {e}")
    
    async def ver_categorias(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver categorias disponíveis"""
        try:
            receitas = ', '.join(self.config['categories']['receitas'])
            gastos = ', '.join(self.config['categories']['gastos'])
            
            msg = f"""
📂 *Categorias Disponíveis*

💵 *Receitas:*
{receitas}

💸 *Gastos:*
{gastos}

_Use estas categorias nos comandos `/receita` e `/gasto`_
            """
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text("❌ Erro ao listar categorias.")
            logger.error(f"Erro ao listar categorias: {e}")
    
    async def backup_excel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enviar backup do arquivo Excel"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Usuário"
        
        try:
            if os.path.exists(self.excel_file):
                df_user = self.read_excel_data(user_id)
                
                if not df_user.empty:
                    backup_filename = f"backup_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    
                    with pd.ExcelWriter(backup_filename, engine='openpyxl') as writer:
                        df_user.to_excel(writer, sheet_name='Minhas_Transacoes', index=False)
                    
                    with open(backup_filename, 'rb') as file:
                        await update.message.reply_document(
                            document=file,
                            filename=backup_filename,
                            caption=f"📊 *Backup das suas transações*\n\n"
                                   f"Total: {len(df_user)} transações",
                            parse_mode='Markdown'
                        )
                    
                    os.remove(backup_filename)
                else:
                    await update.message.reply_text(
                        "📭 *Nenhuma transação para backup.*",
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text("❌ Arquivo de dados não encontrado.")
                
        except Exception as e:
            await update.message.reply_text("❌ Erro ao gerar backup.")
            logger.error(f"Erro ao gerar backup: {e}")

# FUNÇÃO SIMPLES PARA RAILWAY
def run_bot():
    """Executar bot - versão simplificada para Railway"""
    try:
        import asyncio
        
        # Criar novo event loop para esta thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
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
        
        logger.info("Bot iniciado com sucesso! Dados salvos em Excel.")
        
        # RODAR EM POLLING COM EVENT LOOP CORRETO
        loop.run_until_complete(app.run_polling(drop_pending_updates=True))
        
    except Exception as e:
        logger.error(f"Erro crítico ao iniciar bot: {e}")

# Se executado diretamente (para testes locais)
if __name__ == '__main__':
    run_bot()