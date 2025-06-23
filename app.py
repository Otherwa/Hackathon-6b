import streamlit as st
from ftplib import FTP
import os
import tempfile
import pandas as pd
import time

# === FTP Credentials ===
FTP_HOST = "ftpupload.net"
FTP_USER = "epiz_31577921"
FTP_PASS = "v2nNu6o2HTRmT"
ROOT_DIR = "/files"

# === FTP Functions ===
def connect_ftp():
    ftp = FTP()
    ftp.set_pasv(True)
    ftp.connect(FTP_HOST, 21)
    ftp.login(FTP_USER, FTP_PASS)
    return ftp

def list_folders(ftp, base_path):
    ftp.cwd(base_path)
    items = []
    ftp.retrlines("LIST", items.append)
    folders = []
    for line in items:
        if line.startswith("d"):
            parts = line.split(maxsplit=8)
            if len(parts) >= 9:
                folders.append(parts[8])
    return folders

def list_files(ftp, folder_path, extensions=(".txt", ".csv")):
    ftp.cwd(folder_path)
    files = ftp.nlst()
    return [f for f in files if f.lower().endswith(extensions)]

def download_ftp_file(ftp, remote_path):
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(tmp_file.name, "wb") as f:
        ftp.retrbinary("RETR " + remote_path, f.write)
    return tmp_file.name

def stream_text_lines(text):
    for line in text.splitlines():
        yield line + "\n"
        time.sleep(0.02)

# === Streamlit Setup ===
st.image('https://imgs.search.brave.com/zsgwZRnan-oN5BLVpTeXzQLV4fo-PrClNbBqXFaMyFM/rs:fit:500:0:0:0/g:ce/aHR0cHM6Ly91cGxv/YWQud2lraW1lZGlh/Lm9yZy93aWtpcGVk/aWEvZW4vdGh1bWIv/ZS9lMi9Bc2lhbl9w/YWludHNfbG9nby5z/dmcvNTEycHgtQXNp/YW5fcGFpbnRzX2xv/Z28uc3ZnLnBuZw', width=168)

st.set_page_config(page_title="Tendor Document Analysis", layout="wide")
st.title("📑 Tender Document Analysis")

if st.button("🔄 Refresh FTP"):
    st.session_state.pop("ftp_folders", None)

try:
    ftp = connect_ftp()

    if "ftp_folders" not in st.session_state:
        st.session_state.ftp_folders = list_folders(ftp, ROOT_DIR)

    folders = st.session_state.ftp_folders

    if not folders:
        st.warning("No folders found inside /files.")
    else:
        selected_folder = st.selectbox("📁 Select a folder:", folders[2:])

        if selected_folder:
            folder_path = os.path.join(ROOT_DIR, selected_folder).replace("\\", "/")
            files = list_files(ftp, folder_path)

            txt_files = [f for f in files if f.lower().endswith(".txt")]
            csv_files = [f for f in files if f.lower().endswith(".csv")]

            cols = st.columns(2)

            with cols[0]:
                st.subheader("📄 Text Files")
                if txt_files:
                    for file in txt_files:
                        remote_file_path = f"{folder_path}/{file}"
                        local_path = download_ftp_file(ftp, remote_file_path)
    
                        with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                            full_text = f.read()
    
                        keyword = "unstructured data"
                        idx = full_text.lower().find(keyword)
                        content = full_text[idx + len(keyword):].strip() if idx != -1 else full_text
                        
                        st.write_stream(stream_text_lines(content))
    
                        with open(local_path, "rb") as dl:
                            st.download_button(f"⬇️ Download", dl.read(), file_name=file)
                else:
                    st.info("No .txt files found.")

            with cols[1]:
                st.subheader("📊 CSV Files")
                if csv_files:
                    for file in csv_files:
                        remote_file_path = f"{folder_path}/{file}"
                        local_path = download_ftp_file(ftp, remote_file_path)
                        try:
                            df = pd.read_csv(local_path)
                            file = file.replace("_"," ")
                            file = file.replace(".csv","")
                            file = file.capitalize()
                            st.write(f"**{file}**")
                            st.dataframe(df, use_container_width=True)
                            with open(local_path, "rb") as dl:
                                st.download_button(f"⬇️ Download", dl.read(), file_name=file)
                        except Exception as e:
                            st.error(f"❌ Could not read {file}: {e}")
                else:
                    st.info("No .csv files found.")

    ftp.quit()

except Exception as e:
    st.error(f"🚫 FTP connection failed:\n{e}")
