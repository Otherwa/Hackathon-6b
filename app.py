import streamlit as st
from ftplib import FTP, error_perm
import os
import tempfile
import pandas as pd

# FTP credentials
FTP_HOST = "ftpupload.net"
FTP_USER = "epiz_31577921"
FTP_PASS = "v2nNu6o2HTRmT"
ROOT_DIR = "/files"

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

    # Extract folder names from lines that begin with 'd'
    folders = []
    for line in items:
        if line.startswith("d"):
            # Folder name is everything after the last space in permissions block
            parts = line.split(maxsplit=8)  # 9 fields: permissions, links, owner, group, size, month, day, time/year, name
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

# === Streamlit UI ===
st.set_page_config(page_title="FTP File Viewer", layout="wide")
st.title("📂 FTP Folder & File Viewer")

try:
    ftp = connect_ftp()
    folders = list_folders(ftp, ROOT_DIR)

    if not folders:
        st.warning("No folders found inside /files.")
    else:
        selected_folder = st.selectbox("📁 Select a folder:", folders[1:])

        if selected_folder:
            folder_path = os.path.join(ROOT_DIR, selected_folder).replace("\\", "/")
            files = list_files(ftp, folder_path)

            txt_files = [f for f in files if f.endswith(".txt")]
            csv_files = [f for f in files if f.endswith(".csv")]

            st.subheader("📄 Text Files")
            if txt_files:
                for file in txt_files:
                    remote_file_path = f"{folder_path}/{file}"
                    local_path = download_ftp_file(ftp, remote_file_path)
                    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                        st.text_area(file, f.read(), height=200)
                    with open(local_path, "rb") as download_file:
                        st.download_button(f"⬇️ Download {file}", download_file.read(), file_name=file)
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
                        with open(local_path, "rb") as download_file:
                            st.download_button(f"⬇️ Download {file}", download_file.read(), file_name=file)
                    except Exception as e:
                        st.error(f"❌ Failed to load {file}: {e}")
            else:
                st.write("No .csv files found.")

    ftp.quit()

except Exception as e:
    st.error(f"🚫 FTP connection failed:\n{e}")
