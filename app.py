import streamlit as st
from ftplib import FTP
import os
import tempfile
import pandas as pd

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

# === Streamlit Setup ===
st.set_page_config(page_title="Tendor Document Analysis", layout="wide")
st.title("📑 Tendor Document Analysis")

# Refresh button logic
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

            st.subheader("📄 Text Files")
            if txt_files:
                for file in txt_files:
                    remote_file_path = f"{folder_path}/{file}"
                    local_path = download_ftp_file(ftp, remote_file_path)
                    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()

                        def stream_text(text):
                            for line in text.splitlines():
                                yield line + "\n"
                                time.sleep(0.01)  # adjust for desired speed
                        
                        with st.chat_message("assistant"):
                            st.write_stream(lambda: stream_text(txt))


                    with open(local_path, "rb") as dl:
                        st.download_button(f"⬇️ Download {file}", dl.read(), file_name=file)
            else:
                st.write("No .txt files found.")

            st.subheader("📊 CSV Files")
            if csv_files:
                for file in csv_files:
                    remote_file_path = f"{folder_path}/{file}"
                    local_path = download_ftp_file(ftp, remote_file_path)
                    try:
                        df = pd.read_csv(local_path)
                        st.write(f"**{file}**")
                        st.dataframe(df, use_container_width=True)
                        with open(local_path, "rb") as dl:
                            st.download_button(f"⬇️ Download {file}", dl.read(), file_name=file)
                    except Exception as e:
                        st.error(f"❌ Could not read {file}: {e}")
            else:
                st.write("No .csv files found.")

    ftp.quit()

except Exception as e:
    st.error(f"🚫 FTP connection failed:\n{e}")
