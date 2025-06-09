# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
import yaml
import os
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinanceDashboard:
    def __init__(self):
        self.config = self.load_config()
        self.excel_file = self.config['storage']['excel_file']
        self.setup_page()
        logger.info("Dashboard inicializado com Excel storage")
    
    def load_config(self):
        """Carregar configurações do arquivo YAML"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info("Configurações do dashboard carregadas")
                return config
        except FileNotFoundError:
            logger.error("Arquivo config.yaml não encontrado")
            st.error("❌ Arquivo config.yaml não encontrado!")
            st.stop()
        except yaml.YAMLError as e:
            logger.error(f"Erro ao carregar config.yaml: {e}")
            st.error(f"❌ Erro no arquivo config.yaml: {e}")
            st.stop()
    
    def setup_page(self):
        """Configurar página do Streamlit"""
        st.set_page_config(
            page_title=self.config['dashboard']['title'],
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS customizado
        st.markdown("""
        <style>
            .main { background-color: #0E1117; }
            .stMetric { 
                background-color: #1E1E1E; 
                padding: 1rem; 
                border-radius: 0.5rem; 
                border: 1px solid #333;
            }
            .excel-info {
                background-color: #1E3A8A;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #3B82F6;
                margin: 1rem 0;
            }
        </style>
        """, unsafe_allow_html=True)
    
    @st.cache_data(ttl=60)  # Cache por 1 minuto (mais rápido para Excel)
    def get_data(_self):
        """Buscar dados do arquivo Excel"""
        try:
            logger.info(f"Carregando dados do Excel: {_self.excel_file}")
            
            if not os.path.exists(_self.excel_file):
                logger.warning("Arquivo Excel não encontrado")
                return pd.DataFrame()
            
            # Ler dados do Excel
            df = pd.read_excel(_self.excel_file, sheet_name='Transacoes')
            
            # Converter data_criacao para datetime se for string
            if not df.empty:
                df['data_criacao'] = pd.to_datetime(df['data_criacao'])
            
            logger.info(f"Dados carregados: {len(df)} transações do Excel")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler Excel: {e}")
            st.error(f"❌ Erro ao ler arquivo Excel: {e}")
            return pd.DataFrame()
    
    def show_excel_info(self, df):
        """Exibir informações sobre o arquivo Excel"""
        if os.path.exists(self.excel_file):
            file_size = os.path.getsize(self.excel_file)
            file_modified = datetime.fromtimestamp(os.path.getmtime(self.excel_file))
            
            st.markdown(f"""
            <div class="excel-info">
                📊 <strong>Arquivo Excel:</strong> {self.excel_file}<br>
                📁 <strong>Tamanho:</strong> {file_size:,} bytes<br>
                🕐 <strong>Última modificação:</strong> {file_modified.strftime('%d/%m/%Y às %H:%M:%S')}<br>
                📝 <strong>Total de registros:</strong> {len(df) if not df.empty else 0}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("📁 Arquivo Excel ainda não foi criado. Use o bot do Telegram para adicionar transações!")
    
    def show_metrics(self, df):
        """Exibir métricas principais"""
        try:
            if df.empty:
                st.warning("📭 Nenhuma transação encontrada no Excel")
                return
            
            # Calcular métricas
            receitas = df[df['tipo'] == 'receita']['valor'].sum()
            gastos = df[df['tipo'] == 'gasto']['valor'].sum()
            saldo = receitas - gastos
            usuarios = df['username'].nunique() if 'username' in df.columns else df['user_id'].nunique()
            transacoes = len(df)
            
            # Exibir métricas em colunas
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "💵 Total Receitas", 
                    f"R$ {receitas:,.2f}",
                    help="Soma de todas as receitas registradas"
                )
            
            with col2:
                st.metric(
                    "💸 Total Gastos", 
                    f"R$ {gastos:,.2f}",
                    help="Soma de todos os gastos registrados"
                )
            
            with col3:
                delta_color = "normal" if saldo >= 0 else "inverse"
                st.metric(
                    "📊 Saldo Total", 
                    f"R$ {saldo:,.2f}",
                    delta=f"{'✅ Positivo' if saldo >= 0 else '⚠️ Negativo'}",
                    help="Diferença entre receitas e gastos"
                )
            
            with col4:
                st.metric(
                    "📝 Transações", 
                    transacoes,
                    help="Total de transações registradas"
                )
            
            with col5:
                st.metric(
                    "👥 Usuários", 
                    usuarios,
                    help="Número de usuários únicos"
                )
            
            logger.info(f"Métricas exibidas - Saldo: R$ {saldo:.2f}")
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            st.error("❌ Erro ao calcular métricas")
    
    def show_charts(self, df):
        """Exibir gráficos"""
        try:
            if df.empty:
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Receitas vs Gastos")
                
                # Gráfico de barras
                receitas = df[df['tipo'] == 'receita']['valor'].sum()
                gastos = df[df['tipo'] == 'gasto']['valor'].sum()
                
                totals = pd.DataFrame({
                    'Tipo': ['Receitas', 'Gastos'],
                    'Valor': [receitas, gastos]
                })
                
                fig_bar = px.bar(
                    totals, 
                    x='Tipo', 
                    y='Valor',
                    color='Tipo',
                    color_discrete_map={'Receitas': '#2E8B57', 'Gastos': '#DC143C'},
                    title="Comparativo Total"
                )
                fig_bar.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                st.subheader("🥧 Gastos por Categoria")
                
                # Gráfico de pizza para gastos
                gastos_cat = df[df['tipo'] == 'gasto'].groupby('categoria')['valor'].sum()
                
                if not gastos_cat.empty:
                    fig_pie = px.pie(
                        values=gastos_cat.values,
                        names=[cat.title() for cat in gastos_cat.index],
                        title="Distribuição dos Gastos"
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("📊 Nenhum gasto registrado ainda")
            
            # Gráfico de usuários (se múltiplos usuários)
            if 'username' in df.columns and df['username'].nunique() > 1:
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("👥 Gastos por Usuário")
                    gastos_user = df[df['tipo'] == 'gasto'].groupby('username')['valor'].sum().sort_values(ascending=False)
                    
                    fig_user = px.bar(
                        x=gastos_user.index,
                        y=gastos_user.values,
                        title="Gastos por Usuário",
                        labels={'x': 'Usuário', 'y': 'Valor Total (R$)'}
                    )
                    fig_user.update_layout(height=400)
                    st.plotly_chart(fig_user, use_container_width=True)
                
                with col4:
                    st.subheader("💰 Saldo por Usuário")
                    
                    saldos_user = []
                    for user in df['username'].unique():
                        user_data = df[df['username'] == user]
                        receitas_user = user_data[user_data['tipo'] == 'receita']['valor'].sum()
                        gastos_user = user_data[user_data['tipo'] == 'gasto']['valor'].sum()
                        saldo_user = receitas_user - gastos_user
                        saldos_user.append({'Usuario': user, 'Saldo': saldo_user})
                    
                    df_saldos = pd.DataFrame(saldos_user)
                    
                    fig_saldo = px.bar(
                        df_saldos,
                        x='Usuario',
                        y='Saldo',
                        title="Saldo por Usuário",
                        color='Saldo',
                        color_continuous_scale=['red', 'yellow', 'green']
                    )
                    fig_saldo.update_layout(height=400)
                    st.plotly_chart(fig_saldo, use_container_width=True)
            
            # Gráfico temporal
            st.subheader("📊 Evolução Temporal")
            
            df_temporal = df.copy()
            df_temporal['data'] = df_temporal['data_criacao'].dt.date
            
            # Agrupar por data e tipo
            daily_data = []
            for date in df_temporal['data'].unique():
                day_data = df_temporal[df_temporal['data'] == date]
                receitas_dia = day_data[day_data['tipo'] == 'receita']['valor'].sum()
                gastos_dia = day_data[day_data['tipo'] == 'gasto']['valor'].sum()
                
                if receitas_dia > 0:
                    daily_data.append({'data': date, 'tipo': 'Receitas', 'valor': receitas_dia})
                if gastos_dia > 0:
                    daily_data.append({'data': date, 'tipo': 'Gastos', 'valor': gastos_dia})
            
            if daily_data:
                df_daily = pd.DataFrame(daily_data)
                fig_line = px.line(
                    df_daily,
                    x='data',
                    y='valor',
                    color='tipo',
                    title="Fluxo de Caixa Diário",
                    color_discrete_map={'Receitas': '#2E8B57', 'Gastos': '#DC143C'}
                )
                fig_line.update_layout(height=400)
                st.plotly_chart(fig_line, use_container_width=True)
            
            logger.info("Gráficos exibidos com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráficos: {e}")
            st.error("❌ Erro ao gerar gráficos")
    
    def show_transactions_table(self, df, filtros):
        """Exibir tabela de transações com filtros"""
        try:
            if df.empty:
                return
            
            st.subheader("📋 Transações do Excel")
            
            # Aplicar filtros
            df_filtered = df.copy()
            
            # Filtro por período
            if filtros['periodo'] != "Todos":
                dias_map = {
                    "Últimos 7 dias": 7,
                    "Últimos 30 dias": 30,
                    "Últimos 90 dias": 90
                }
                if filtros['periodo'] in dias_map:
                    data_limite = datetime.now() - timedelta(days=dias_map[filtros['periodo']])
                    df_filtered = df_filtered[df_filtered['data_criacao'] >= data_limite]
            
            # Filtro por tipo
            if filtros['tipos']:
                df_filtered = df_filtered[df_filtered['tipo'].isin(filtros['tipos'])]
            
            # Filtro por categoria
            if filtros['categorias']:
                df_filtered = df_filtered[df_filtered['categoria'].isin(filtros['categorias'])]
            
            # Filtro por usuário
            if filtros['usuarios']:
                if 'username' in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered['username'].isin(filtros['usuarios'])]
            
            # Formatar dados para exibição
            if not df_filtered.empty:
                df_display = df_filtered.copy()
                df_display = df_display.sort_values('data_criacao', ascending=False)
                
                # Formatar colunas
                df_display['Data'] = df_display['data_criacao'].dt.strftime('%d/%m/%Y %H:%M')
                df_display['Tipo'] = df_display['tipo'].apply(
                    lambda x: f"💵 {x.title()}" if x == 'receita' else f"💸 {x.title()}"
                )
                df_display['Valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                df_display['Categoria'] = df_display['categoria'].str.title()
                df_display['Descrição'] = df_display['descricao'].fillna("").astype(str)
                
                # Adicionar usuário se disponível
                if 'username' in df_display.columns:
                    df_display['Usuário'] = df_display['username']
                    cols_to_show = ['Data', 'Usuário', 'Tipo', 'Valor', 'Categoria', 'Descrição']
                else:
                    cols_to_show = ['Data', 'Tipo', 'Valor', 'Categoria', 'Descrição']
                
                st.dataframe(
                    df_display[cols_to_show],
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Estatísticas do filtro
                receitas_filtradas = df_filtered[df_filtered['tipo'] == 'receita']['valor'].sum()
                gastos_filtrados = df_filtered[df_filtered['tipo'] == 'gasto']['valor'].sum()
                saldo_filtrado = receitas_filtradas - gastos_filtrados
                
                st.info(
                    f"📊 **Filtro aplicado:** {len(df_filtered)} transações | "
                    f"Receitas: R$ {receitas_filtradas:.2f} | "
                    f"Gastos: R$ {gastos_filtrados:.2f} | "
                    f"Saldo: R$ {saldo_filtrado:.2f}"
                )
                
                # Botão para download dos dados filtrados
                if st.button("📥 Baixar dados filtrados"):
                    csv = df_filtered.to_csv(index=False)
                    st.download_button(
                        "💾 Download CSV",
                        csv,
                        f"transacoes_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
            else:
                st.warning("🔍 Nenhuma transação encontrada com os filtros aplicados")
            
            logger.info(f"Tabela exibida com {len(df_filtered)} transações filtradas")
            
        except Exception as e:
            logger.error(f"Erro ao exibir tabela: {e}")
            st.error("❌ Erro ao exibir transações")
    
    def show_sidebar(self, df):
        """Exibir sidebar com filtros e informações"""
        st.sidebar.header("🔍 Filtros e Controles")
        
        # Filtros
        filtros = {}
        
        # Filtro por período
        filtros['periodo'] = st.sidebar.selectbox(
            "📅 Período",
            ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"],
            help="Filtrar transações por período"
        )
        
        # Filtro por tipo
        tipos_disponiveis = df['tipo'].unique() if not df.empty else []
        filtros['tipos'] = st.sidebar.multiselect(
            "💰 Tipo de Transação",
            tipos_disponiveis,
            default=list(tipos_disponiveis),
            help="Selecionar tipos de transação"
        )
        
        # Filtro por categoria
        categorias_disponiveis = df['categoria'].unique() if not df.empty else []
        filtros['categorias'] = st.sidebar.multiselect(
            "📂 Categorias",
            categorias_disponiveis,
            default=list(categorias_disponiveis),
            help="Selecionar categorias específicas"
        )
        
        # Filtro por usuário (se múltiplos usuários)
        if not df.empty and 'username' in df.columns and df['username'].nunique() > 1:
            usuarios_disponiveis = df['username'].unique()
            filtros['usuarios'] = st.sidebar.multiselect(
                "👥 Usuários",
                usuarios_disponiveis,
                default=list(usuarios_disponiveis),
                help="Selecionar usuários específicos"
            )
        else:
            filtros['usuarios'] = []
        
        st.sidebar.markdown("---")
        
        # Informações sobre o Excel
        st.sidebar.header("📊 Arquivo Excel")
        if os.path.exists(self.excel_file):
            file_size = os.path.getsize(self.excel_file)
            st.sidebar.text(f"📁 Arquivo: {os.path.basename(self.excel_file)}")
            st.sidebar.text(f"📏 Tamanho: {file_size:,} bytes")
            st.sidebar.text(f"📝 Registros: {len(df)}")
            
            if st.sidebar.button("📥 Download Excel Completo"):
                with open(self.excel_file, 'rb') as file:
                    st.sidebar.download_button(
                        "💾 Baixar Excel",
                        file.read(),
                        f"financeiro_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.sidebar.warning("📁 Arquivo Excel não encontrado")
        
        st.sidebar.markdown("---")
        
        # Informações sobre o bot
        st.sidebar.header("🤖 Bot Telegram")
        st.sidebar.markdown(f"""
        **Comandos disponíveis:**
        
        🏠 `/start` - Iniciar bot
        💵 `/receita [valor] [categoria] [descrição]`
        💸 `/gasto [valor] [categoria] [descrição]`
        📊 `/saldo` - Ver saldo atual
        📋 `/extrato` - Últimas {self.config['bot']['extrato_limit']} transações
        📂 `/categorias` - Ver categorias disponíveis
        📥 `/backup` - Receber backup Excel pessoal
        ❓ `/ajuda` - Ajuda completa
        """)
        
        # Estatísticas rápidas
        if not df.empty:
            st.sidebar.markdown("---")
            st.sidebar.header("📈 Estatísticas Rápidas")
            
            total_transacoes = len(df)
            if len(df[df['tipo'] == 'gasto']) > 0:
                categoria_mais_gasta = df[df['tipo'] == 'gasto'].groupby('categoria')['valor'].sum().idxmax()
                maior_gasto = df[df['tipo'] == 'gasto']['valor'].max()
            else:
                categoria_mais_gasta = "N/A"
                maior_gasto = 0
            
            st.sidebar.metric("📝 Total Transações", total_transacoes)
            st.sidebar.metric("💸 Maior Gasto", f"R$ {maior_gasto:.2f}")
            st.sidebar.text(f"🔥 Categoria + Gasta:\n{categoria_mais_gasta.title()}")
            
            if 'username' in df.columns:
                usuario_mais_ativo = df['username'].value_counts().index[0]
                st.sidebar.text(f"👤 Usuário + Ativo:\n{usuario_mais_ativo}")
        
        # Configurações
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Controles")
        
        if st.sidebar.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
            
        if st.sidebar.button("🗑️ Limpar Cache"):
            st.cache_data.clear()
            st.sidebar.success("Cache limpo!")
        
        return filtros
    
    def show_footer(self):
        """Exibir footer com informações"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📱 Como usar:**")
            st.markdown("1. Adicione o bot no Telegram")
            st.markdown("2. Use os comandos para registrar")
            st.markdown("3. Acompanhe pelo dashboard")
            st.markdown("4. Baixe backups em Excel")
        
        with col2:
            st.markdown("**🔧 Tecnologias:**")
            st.markdown("• Python + Telegram Bot API")
            st.markdown("• Excel/Pandas para storage")
            st.markdown("• Streamlit Dashboard")
            st.markdown("• Logs estruturados")
        
        with col3:
            st.markdown("**📊 Storage:**")
            st.markdown(f"Arquivo: `{os.path.basename(self.excel_file)}`")
            if os.path.exists(self.excel_file):
                ultimo_update = datetime.fromtimestamp(os.path.getmtime(self.excel_file))
                st.markdown(f"Atualizado: {ultimo_update.strftime('%d/%m/%Y %H:%M')}")
            else:
                st.markdown("Arquivo não encontrado")
        
        st.markdown(
            """
            <div style='text-align: center; color: #666; margin-top: 2rem;'>
                💰 Controle Financeiro Pessoal v2.1 Excel Edition<br>
                📊 Dados salvos em planilha Excel • 🤖 Bot Telegram • 📈 Dashboard Web
            </div>
            """,
            unsafe_allow_html=True
        )

def main():
    try:
        # Inicializar dashboard
        dashboard = FinanceDashboard()
        
        # Título principal
        st.title(dashboard.config['dashboard']['title'])
        st.markdown("*Gerencie suas finanças pessoais através do Telegram • Dados salvos em Excel*")
        
        # Informações sobre o Excel
        dashboard.show_excel_info(pd.DataFrame())
        
        st.markdown("---")
        
        # Carregar dados
        with st.spinner("📊 Carregando dados do Excel..."):
            df = dashboard.get_data()
        
        # Sidebar com filtros
        filtros = dashboard.show_sidebar(df)
        
        # Métricas principais
        dashboard.show_metrics(df)
        
        st.markdown("---")
        
        # Gráficos
        dashboard.show_charts(df)
        
        st.markdown("---")
        
        # Tabela de transações
        dashboard.show_transactions_table(df, filtros)
        
        # Footer
        dashboard.show_footer()
        
        logger.info("Dashboard renderizado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro crítico no dashboard: {e}")
        st.error(f"❌ Erro crítico: {e}")
        st.info("Verifique os logs para mais detalhes")

if __name__ == "__main__":
    main()