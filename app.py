
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Timesheet CCM", layout="centered")
TZ = pytz.timezone("Africa/Maputo")
def now_ts(): return datetime.now(TZ)
def today_str(): return now_ts().strftime("%Y-%m-%d")
def ts_str(dt): return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_client():
    sa_info = st.secrets["gcp_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    return gspread.authorize(creds)

def get_spreadsheet():
    gc = get_client()
    name = st.secrets["sheets"]["spreadsheet_name"]
    try: return gc.open(name)
    except gspread.SpreadsheetNotFound: return gc.create(name)

def ensure_worksheet(spread, emp_id: str, emp_name: str):
    title = emp_id.strip().upper()
    try: ws = spread.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spread.add_worksheet(title=title, rows=1000, cols=7)
        ws.update("A1:G1", [["Data","Dia da Semana","Projeto","Check-in","Check-out","Horas","Obs."]])
        ws.freeze(rows=1)
    header = ws.row_values(1)
    if header != ["Data","Dia da Semana","Projeto","Check-in","Check-out","Horas","Obs."]:
        ws.update("A1:G1", [["Data","Dia da Semana","Projeto","Check-in","Check-out","Horas","Obs."]])
    return ws

def get_today_row_index(ws, day_str):
    colA = ws.col_values(1)
    for i, v in enumerate(colA, start=1):
        if v == day_str: return i
    return None

def append_row(ws, row): ws.append_row(row, value_input_option="USER_ENTERED")
def update_row(ws, row_idx, values): ws.update(f"A{row_idx}:G{row_idx}", [values])
def load_df(ws): return pd.DataFrame(ws.get_all_records())

st.title("📒 Timesheet – Registro Automático (Cloud)")
st.caption("Entrada registrada ao acessar; saída por botão. Dados no Google Sheets, uma aba por ID.")

with st.form("auth"):
    emp_id = st.text_input("ID do funcionário (ex.: AM01)", max_chars=16)
    emp_name = st.text_input("Nome completo", max_chars=80)
    project = st.text_input("Projeto (opcional)", value="--")
    submitted = st.form_submit_button("Acessar / Registrar")

if submitted:
    if not emp_id.strip() or not emp_name.strip():
        st.error("Preencha ID e Nome."); st.stop()

    spread = get_spreadsheet()
    ws = ensure_worksheet(spread, emp_id.strip(), emp_name.strip())

    today = today_str()
    weekday = now_ts().strftime("%a")
    row_idx = get_today_row_index(ws, today)

    if row_idx is None:
        new = [today, weekday, project, ts_str(now_ts()), "", "", ""]
        append_row(ws, new)
        st.success(f"✅ Entrada registrada: {new[3]}")
    else:
        row = ws.row_values(row_idx); row += [""] * (7 - len(row))
        if not row[4]:
            if st.button("Registrar saída agora"):
                out = ts_str(now_ts()); cin = row[3]
                try: h = round((pd.to_datetime(out) - pd.to_datetime(cin)).total_seconds()/3600, 2)
                except Exception: h = ""
                update_row(ws, row_idx, [row[0],row[1],row[2],row[3],out,h,row[6]])
                st.success(f"✅ Saída registrada: {out}")
        else:
            st.info("Você já registrou entrada e saída hoje.")

    df = load_df(ws)
    if not df.empty:
        st.subheader("Últimos registros")
        st.dataframe(df.sort_values("Data", ascending=False).head(20), use_container_width=True)
    else:
        st.write("Sem registros.")

    st.link_button("Abrir Google Sheet", get_spreadsheet().url)
