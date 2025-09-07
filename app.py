import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, APIError

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

def get_client():
    sa_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_spreadsheet():
    gc = get_client()

    sheets_conf = st.secrets.get("sheets", {})
    sheet_id = sheets_conf.get("spreadsheet_id")          # opcional (recomendado)
    sheet_name = sheets_conf.get("spreadsheet_name")      # fallback

    try:
        if sheet_id:
            # Método mais seguro: não depende de nome
            return gc.open_by_key(sheet_id)
        elif sheet_name:
            return gc.open(sheet_name)
        else:
            st.error(
                "Configuração ausente: define em secrets.toml o campo "
                "`[sheets] spreadsheet_id = \"...\"` ou `spreadsheet_name = \"...\"`."
            )
            st.stop()

    except SpreadsheetNotFound:
        if sheet_id:
            st.error(
                f"Planilha com ID **{sheet_id}** não encontrada ou sem acesso.\n\n"
                "➡️ Verifica se o ID está correto (o trecho entre `/d/` e `/edit` na URL)\n"
                "➡️ Partilha a planilha com o e-mail da conta de serviço **Editor**."
            )
        else:
            st.error(
                f"A planilha com nome **'{sheet_name}'** não foi encontrada.\n\n"
                "➡️ Confirma o nome exatamente igual\n"
                "➡️ Partilha a planilha com o e-mail da conta de serviço **Editor**."
            )
        st.stop()

    except APIError as e:
        # Tentar mensagem mais clara (p.ex., 403 - Forbidden / 404 - Not Found)
        msg = getattr(e, "response", None)
        status = getattr(msg, "status_code", None)
        if status == 403:
            st.error(
                "Acesso negado (403).\n\n"
                "➡️ Garante que a planilha foi **partilhada** com o e-mail da conta de serviço, com permissão **Editor**.\n"
                "➡️ No Google Cloud, garante que as APIs **Google Sheets API** e **Google Drive API** estão ativadas."
            )
        elif status == 404:
            st.error(
                "Recurso não encontrado (404).\n\n"
                "➡️ Confere o **ID**/nome e a partilha com a conta de serviço."
            )
        else:
            st.error(f"Erro da API do Google Sheets: {e}")
        st.stop()

# --- Exemplo de uso na tua app ---
spread = get_spreadsheet()
st.success("Conexão com a planilha estabelecida ✅")
