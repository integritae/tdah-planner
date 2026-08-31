import streamlit as st
from supabase import create_client, Client
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Foco Neuroadaptativo",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONEXÃO COM SUPABASE ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY or "SUA_URL" in SUPABASE_URL:
    st.error("⚠️ **Credenciais do Supabase não configuradas no Streamlit Cloud!**")
    st.markdown("""
    Para ativar o banco de dados:
    1. No canto inferior direito do app, clique em **Manage app** (ou no menu superior `⋮` ➔ **Settings**).
    2. Acesse a aba **Secrets**.
    3. Cole as seguintes variáveis:
    ```toml
    SUPABASE_URL = "https://sqwgucoqgnmnasfiqqfa.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNxd2d1Y29xZ25tbmFzZmlxcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODQ3NTIsImV4cCI6MjEwMzc2MDc1Mn0.jsbz8BXagWcF7VBTzKBY0sG-ud5vedMsHq_EMcG84Cs"
    ```
    4. Clique em **Save**. O app recarregará automaticamente.
    """)
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()
hoje = datetime.date.today().isoformat()

# --- CSS MINIMALISTA PARA FOCO E MOBILE ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
    .stButton button { border-radius: 8px; width: 100%; height: 3em; font-weight: bold; }
    .criterio-box { background-color: #1e293b; color: #f8fafc; padding: 12px; border-radius: 8px; border-left: 5px solid #ef4444; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO GLOBAL & RESET SOS ---
col_head, col_sos = st.columns([3, 1])
with col_head:
    st.title("🎯 Modo Agora")
with col_sos:
    if st.button("⚡ SOS", help="Ativar Plano B (Isolar 1 tarefa crítica)"):
        # Protocolo Reset: Descarta OO/PCM do dia e mantém apenas a PSM prioritária
        supabase.table("tarefas").update({"status": "adiada"}).eq("data_alvo", hoje).neq("quadrante", "PSM").execute()
        supabase.table("registro_diario").upsert({"data": hoje, "sos_acionado": True}).execute()
        st.toast("Plano B ativado: Foque apenas na tarefa crítica.", icon="⚠️")
        st.rerun()

# --- ESTACIONAMENTO RÁPIDO (FAB SIMULADO NO TOPO) ---
with st.expander("🎙️ Estacionar Ideia Rápida (Não quebre o foco)", expanded=False):
    ideia = st.text_input("Captura rápida:", placeholder="Digite o pensamento intrusivo...", label_visibility="collapsed")
    if st.button("Guardar Ideia Silenciosamente") and ideia:
        supabase.table("estacionamento_ideias").insert({"conteudo": ideia, "tipo_captura": "texto"}).execute()
        st.success("Ideia guardada no estacionamento. Volte ao foco atual.")

# --- TABS PRINCIPAIS ---
tab_agora, tab_grid, tab_gaveta = st.tabs(["🎯 Agora", "📅 Grid do Dia", "📦 Gaveta"])

# ==========================================
# 1. TELA AGORA (Execução Única)
# ==========================================
with tab_agora:
    # Buscar tarefa ativa de maior prioridade
    res = supabase.table("tarefas").select("*").eq("data_alvo", hoje).neq("status", "concluida").order("ordem_prioridade").limit(1).execute()
    tarefas = res.data

    if tarefas:
        t_atual = tarefas[0]
        st.subheader(f"[{t_atual['quadrante']}] {t_atual['titulo']}")
        
        # Critério de Parada
        if t_atual.get('criterio_parada'):
            st.markdown(f"""
            <div class="criterio-box">
                <strong>🛑 CRITÉRIO DE PARADA:</strong><br>{t_atual['criterio_parada']}
            </div>
            """, unsafe_allow_html=True)

        # Micro-passos
        passos = t_atual.get('micro_passos', [])
        todos_concluidos = True
        
        if passos:
            st.write("**Micro-Passos (< 15 min):**")
            for idx, p in enumerate(passos):
                checked = st.checkbox(p.get('texto', f'Passo {idx+1}'), value=p.get('concluido', False), key=f"p_{t_atual['id']}_{idx}")
                p['concluido'] = checked
                if not checked:
                    todos_concluidos = False

        if st.button("✔️ Concluir Tarefa Completa"):
            supabase.table("tarefas").update({"status": "concluida"}).eq("id", t_atual["id"]).execute()
            st.balloons()
            st.rerun()
    else:
        st.info("Nenhuma tarefa pendente no momento. Bom trabalho ou defina o Foco do Dia no Grid.")

# ==========================================
# 2. TELA GRID DO DIA (Linha Circadiana)
# ==========================================
with tab_grid:
    st.subheader("Blocos Biológicos de Hoje")
    
    st.markdown("""
    * **🟡 08:00 - 12:00 (Janela Dourada):** Produção Sem Margem (PSM) / Foco Intenso
    * **🔴 13:00 - 15:00 (Crash 1):** Ocupações Obrigatórias (OO) / Burocracias
    * **🔵 15:00 - 18:30 (Platô / Clínica):** Atendimentos + Microtarefas de 5 min
    * **🔴 19:00 - 20:00 (Crash 2):** Descompressão Total (Proibido planejar)
    * **⛔ 22:00+ (Desaceleração):** Bloqueio de novas tarefas
    """)
    
    st.divider()
    
    with st.form("nova_tarefa_form"):
        st.write("**Adicionar Tarefa ao Grid**")
        titulo = st.text_input("Título da Tarefa")
        quadrante = st.selectbox("Classificação", ["PSM", "PCM", "OO", "OD"])
        criterio = st.text_input("Critério de Parada (Onde parar sem hiper-refinar)")
        p1 = st.text_input("Passo 1 (< 15 min)")
        p2 = st.text_input("Passo 2 (< 15 min)")
        p3 = st.text_input("Passo 3 (< 15 min)")
        
        if st.form_submit_button("Agendar Tarefa"):
            passos_json = [{"texto": p, "concluido": False} for p in [p1, p2, p3] if p]
            supabase.table("tarefas").insert({
                "data_alvo": hoje,
                "titulo": titulo,
                "quadrante": quadrante,
                "criterio_parada": criterio,
                "micro_passos": passos_json
            }).execute()
            st.success("Tarefa adicionada!")
            st.rerun()

# ==========================================
# 3. TELA GAVETA (Triagem de Segunda-Feira)
# ==========================================
with tab_gaveta:
    st.subheader("📦 Estacionamento de Ideias")
    ideias_res = supabase.table("estacionamento_ideias").select("*").eq("status", "nao_triado").order("criado_em", desc=True).execute()
    ideias = ideias_res.data

    if not ideias:
        st.write("Nenhuma ideia estacionada pendente de triagem.")
    else:
        for item in ideias:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.write(f"📌 {item['conteudo']}")
            with c2:
                if st.button("Converter", key=f"conv_{item['id']}"):
                    # Cria a tarefa no quadrante PCM por padrão
                    supabase.table("tarefas").insert({"titulo": item["conteudo"], "quadrante": "PCM"}).execute()
                    supabase.table("estacionamento_ideias").update({"status": "convertido"}).eq("id", item["id"]).execute()
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_{item['id']}"):
                    supabase.table("estacionamento_ideias").update({"status": "descartado"}).eq("id", item["id"]).execute()
                    st.rerun()