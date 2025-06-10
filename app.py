import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from fpdf import FPDF

# ------------------------------
# Konfigurasi halaman & tema
# ------------------------------
st.set_page_config(page_title="Digital DO Form - FBKM", layout="wide")
st.markdown("""
    <style>
        .stButton > button {
            background-color: #1a73e8;
            color: white !important;
            border-radius: 6px;
            padding: 0.6em 1.2em;
            font-weight: 600;
            font-size: 16px;
            border: none;
        }

        .stButton > button:hover {
            background-color: #155ab6;
            color: white !important;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚚 Digital Delivery Order (DO) FBKM")

# ------------------------------
# Fungsi jana DO Number ikut tarikh
# ------------------------------
def generate_do_number_by_date():
    today_str = date.today().strftime("%Y%m%d")
    prefix = f"DO-{today_str}"
    master_csv = "do_master.csv"
    if os.path.exists(master_csv):
        try:
            df_existing = pd.read_csv(master_csv)
            df_today = df_existing[df_existing["DO Number"].str.startswith(prefix)]
            next_num = len(df_today) + 1
            return f"{prefix}-{next_num:03d}"
        except:
            return f"{prefix}-001"
    else:
        return f"{prefix}-001"

# ------------------------------
# Fungsi jana PDF rasmi
# ------------------------------
def generate_pdf(do_number, do_date, customer_name, item_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Delivery Order (DO)", ln=True, align='C')
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"DO Number: {do_number}", ln=True)
    pdf.cell(200, 10, txt=f"DO Date: {do_date}", ln=True)
    pdf.cell(200, 10, txt=f"Customer Name: {customer_name}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(10, 8, "No", border=1)
    pdf.cell(40, 8, "Item", border=1)
    pdf.cell(35, 8, "MI Number", border=1)
    pdf.cell(30, 8, "C/P No.", border=1)
    pdf.cell(15, 8, "Set", border=1, align='C')
    pdf.cell(15, 8, "Ctn", border=1, align='C')
    pdf.cell(25, 8, "Quantity", border=1, align='C')
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    for i, row in item_df.iterrows():
        pdf.cell(10, 8, str(row["No."]), border=1)
        pdf.cell(40, 8, str(row["Item"]), border=1)
        pdf.cell(35, 8, str(row["MI Number"]), border=1)
        pdf.cell(30, 8, str(row["C/P No."]), border=1)
        pdf.cell(15, 8, str(row["Set"]), border=1, align='C')
        pdf.cell(15, 8, str(row["Ctn"]), border=1, align='C')
        pdf.cell(25, 8, str(row["Quantity"]), border=1, align='C')
        pdf.ln()

    folder_name = f"do_data/{do_date}"
    os.makedirs(folder_name, exist_ok=True)
    pdf_path = f"{folder_name}/{do_number}.pdf"
    pdf.output(pdf_path)
    return pdf_path

# ------------------------------
# Borang DO
# ------------------------------
do_number = generate_do_number_by_date()

with st.form("do_form"):
    st.subheader("📄 Maklumat Delivery Order")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("DO Number", value=do_number, disabled=True)
    with col2:
        do_date = st.date_input("DO Date", value=date.today())

    customer_name = st.text_input("Customer Name")

    st.markdown("---")
    st.subheader("📦 Item Details (maksimum 20 baris)")

    default_items = {
        "No.": list(range(1, 21)),
        "Item": [""] * 20,
        "MI Number": [""] * 20,
        "C/P No.": [""] * 20,
        "Set": [0] * 20,
        "Ctn": [0] * 20,
    }
    item_df = pd.DataFrame(default_items)
    edited_df = st.data_editor(
        item_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True
    )

    edited_df["Quantity"] = edited_df["Set"] * edited_df["Ctn"]

    submitted = st.form_submit_button("🚀 Submit DO")

    if submitted:
        if not customer_name.strip():
            st.warning("⚠️ Sila isi nama pelanggan.")
        elif edited_df[["Item", "Quantity"]].replace("", 0).Quantity.sum() == 0:
            st.warning("⚠️ Sila isi sekurang-kurangnya satu item dengan kuantiti lebih daripada 0.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows_to_save = []
            for _, row in edited_df.iterrows():
                if str(row["Item"]).strip() != "" and row["Quantity"] > 0:
                    rows_to_save.append({
                        "Timestamp": timestamp,
                        "DO Number": do_number,
                        "DO Date": do_date.strftime("%Y-%m-%d"),
                        "Customer Name": customer_name,
                        "No.": row["No."],
                        "Item": row["Item"],
                        "MI Number": row["MI Number"],
                        "C/P No.": row["C/P No."],
                        "Set": row["Set"],
                        "Ctn": row["Ctn"],
                        "Quantity": row["Quantity"]
                    })

            df_to_save = pd.DataFrame(rows_to_save)
            folder_path = f"do_data/{do_date.strftime('%Y-%m-%d')}"
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, f"{do_number}.csv")
            df_to_save.to_csv(file_path, index=False)

            # Simpan juga ke master log
            master_path = "do_master.csv"
            df_to_save.to_csv(master_path, mode="a", header=not os.path.exists(master_path), index=False)

            # Jana PDF
            pdf_path = generate_pdf(do_number, do_date.strftime("%Y-%m-%d"), customer_name, df_to_save)

            st.success("✅ DO submitted, saved & PDF generated!")
            st.markdown(f"📄 [Klik untuk muat turun PDF DO]({pdf_path})")
            st.markdown("### 📄 DO Summary:")
            st.write(f"**DO Number:** {do_number}")
            st.write(f"**DO Date:** {do_date.strftime('%Y-%m-%d')}")
            st.write(f"**Customer Name:** {customer_name}")
            st.dataframe(df_to_save, use_container_width=True)

# ------------------------------
# Papar semua rekod
# ------------------------------
st.markdown("---")
st.subheader("📋 Semua Rekod DO (master log)")
if os.path.exists("do_master.csv"):
    try:
        df_all = pd.read_csv("do_master.csv")
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True)
        else:
            st.info("Tiada DO dihantar lagi.")
    except:
        st.error("❌ Ralat membaca master CSV.")
else:
    st.info("Tiada DO dihantar lagi.")
