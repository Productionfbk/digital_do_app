import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# Konfigurasi PDF - pastikan path betul untuk Windows
PDF_CONFIG = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

# ========== Login Section ==========
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.image("fbkm_logo.png", width=200)  # Logo syarikat
    st.title("Login Leader")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "leader" and password == "fbkm123":
            st.session_state.authenticated = True
            st.success("Login berjaya!")
        else:
            st.error("Username atau password salah.")
    st.stop()

# ========== Main App ==========
st.set_page_config(page_title="Digital DO Form - FBKM", layout="wide")

# Auto-generate DO Number
def generate_do_number():
    folder = "do_data"
    if not os.path.exists(folder):
        os.makedirs(folder)
    today_str = date.today().strftime("%Y-%m-%d")
    csv_path = os.path.join(folder, today_str, "do_data.csv")
    if os.path.exists(csv_path):
        try:
            df_existing = pd.read_csv(csv_path)
            if not df_existing.empty and "DO Number" in df_existing.columns:
                last_do = df_existing["DO Number"].iloc[-1]
                last_num = int(last_do.split("-")[1])
                return f"DO-{last_num + 1:04d}"
        except:
            return "DO-0001"
    return "DO-0001"

# Initial states
if "do_number" not in st.session_state:
    st.session_state.do_number = generate_do_number()
if "do_date" not in st.session_state:
    st.session_state.do_date = date.today()
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "item_df" not in st.session_state:
    st.session_state.item_df = pd.DataFrame({
        "No.": list(range(1, 6)),
        "Item": [""] * 5,
        "MI Number": [""] * 5,
        "C/P No.": [""] * 5,
        "Set": [0] * 5,
        "Ctn": [0] * 5,
        "Quantity": [0] * 5
    })

st.title("🚚 Digital Delivery Order (DO) FBKM")

with st.form("do_form"):
    st.subheader("📄 Maklumat Delivery Order")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("DO Number", value=st.session_state.do_number, disabled=True)
    with col2:
        do_date = st.date_input("DO Date", value=st.session_state.do_date)

    customer_name = st.text_input("Customer Name", value=st.session_state.customer_name)

    st.markdown("---")
    st.subheader("📦 Item Details (maksimum 5 baris)")

    edited_df = st.data_editor(
        st.session_state.item_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="item_editor"
    )

    submitted = st.form_submit_button("🚀 Submit DO")

    if submitted:
        # Validasi: Semua ruangan wajib diisi
        if customer_name.strip() == "":
            st.warning("⚠️ Sila isi 'Customer Name'")
        elif edited_df["Item"].str.strip().eq("").all():
            st.warning("⚠️ Sila isi sekurang-kurangnya satu item.")
        elif edited_df["Quantity"].sum() <= 0:
            st.warning("⚠️ Jumlah Quantity mesti lebih dari 0.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today_str = date.today().strftime("%Y-%m-%d")
            save_dir = os.path.join("do_data", today_str)
            os.makedirs(save_dir, exist_ok=True)
            csv_path = os.path.join(save_dir, "do_data.csv")

            rows_to_save = []
            for _, row in edited_df.iterrows():
                if str(row["Item"]).strip() != "" and row["Quantity"] > 0:
                    record = {
                        "Timestamp": timestamp,
                        "DO Number": st.session_state.do_number,
                        "DO Date": do_date.strftime("%Y-%m-%d"),
                        "Customer Name": customer_name,
                        "No.": int(row["No."]),
                        "Item": row["Item"],
                        "MI Number": row["MI Number"],
                        "C/P No.": row["C/P No."],
                        "Set": int(row["Set"]),
                        "Ctn": int(row["Ctn"]),
                        "Quantity": int(row["Quantity"])
                    }
                    rows_to_save.append(record)

            df_to_save = pd.DataFrame(rows_to_save)
            df_to_save.to_csv(csv_path, mode="a", header=not os.path.exists(csv_path), index=False)

            # Simpan PDF
            pdf_html = f"""
                <h2>Delivery Order: {st.session_state.do_number}</h2>
                <p>Date: {do_date.strftime('%Y-%m-%d')}</p>
                <p>Customer: {customer_name}</p>
                {df_to_save.to_html(index=False)}
            """
            pdf_path = os.path.join(save_dir, f"{st.session_state.do_number}.pdf")
            pdfkit.from_string(pdf_html, pdf_path, configuration=PDF_CONFIG)

            st.success("✅ DO submitted, CSV & PDF saved successfully!")

            st.markdown("### 📄 DO Summary:")
            st.write(f"**DO Number:** {st.session_state.do_number}")
            st.write(f"**DO Date:** {do_date.strftime('%Y-%m-%d')}")
            st.write(f"**Customer Name:** {customer_name}")
            st.dataframe(df_to_save, use_container_width=True)

            # Reset for next entry
            st.session_state.do_number = generate_do_number()
            st.session_state.customer_name = ""
            st.session_state.item_df = pd.DataFrame({
                "No.": list(range(1, 6)),
                "Item": [""] * 5,
                "MI Number": [""] * 5,
                "C/P No.": [""] * 5,
                "Set": [0] * 5,
                "Ctn": [0] * 5,
                "Quantity": [0] * 5
            })

# Paparan DO dihantar hari ini
st.markdown("---")
st.subheader("📋 DO Dihantar Hari Ini")
today_folder = os.path.join("do_data", date.today().strftime("%Y-%m-%d"))
csv_today_path = os.path.join(today_folder, "do_data.csv")
if os.path.exists(csv_today_path):
    df_today = pd.read_csv(csv_today_path)
    if not df_today.empty:
        st.dataframe(df_today, use_container_width=True)
    else:
        st.info("Tiada DO dihantar hari ini.")
else:
    st.info("Tiada DO dihantar hari ini.")
