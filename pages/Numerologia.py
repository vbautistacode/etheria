# pages/Numerologia.py
st.sidebar.header("Entrada do Consulente")
# --- Sidebar (exemplo) ---
def _sync_sidebar_to_tab():
    # copia o valor do sidebar para a key usada na aba
    st.session_state["num_full_name"] = st.session_state.get("full_name", "")

# widget no sidebar (key "full_name")
full_name = st.sidebar.text_input(
    "Nome completo",
    value=st.session_state.get("full_name", ""),
    key="full_name",
    on_change=_sync_sidebar_to_tab
)

# data de nascimento no sidebar (mesma ideia)
def _sync_sidebar_dob_to_tab():
    st.session_state["num_dob"] = st.session_state.get("dob", st.session_state.get("num_dob", date(1990,4,25)))

dob = st.sidebar.date_input(
    "Data de nascimento",
    value=st.session_state.get("dob", date(1990,4,25)),
    key="dob",
    on_change=_sync_sidebar_dob_to_tab,
    min_value=date(1900, 1, 1),
    max_value=date(2100, 12, 31)
)

# inicializa antes de criar o widget
st.session_state.setdefault("birth_time_influences", "07:55")

# cria o widget uma única vez (sempre)
birth_time = st.sidebar.text_input(
    "Hora de nascimento (HH:MM)",
    value=st.session_state["birth_time_influences"],
    key="birth_time_influences"
)

generate_btn = st.sidebar.button("Gerar leitura")
