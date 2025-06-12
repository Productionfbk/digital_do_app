import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# Set page config
st.set_page_config(page_title="Digital DO Form - FBKM", layout="wide")

# Auto-generate DO Number function
def generate_do_number():
    csv_path = "do_data.csv"
    if os.path.exists(csv_path):
        try:
            df_existing = pd.read_csv(csv_path)
            if not df_existing.empty and "DO Number" in df_existing.columns:
                last_do = df_existing["DO Number"].iloc[-1]
                try:
                    last_num = int(last_do.split("-")[1])
                    return f"DO-{last_num + 1:04d}"
                except:
                    return "DO-0001"
        except pd.errors.EmptyDataError:
            return "DO-0001"
        except Exception:
            return "DO-0001"
    return "DO-0001"

# Initialize session state variables once
if "do_number" not in st.session_state:
    st.session_state.do_number = generate_do_number()
if "do_date" not in st.session_state:
    st.session_state.do_date = date.today()
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "item_df" not in st.session_state:
    # 20 rows default item dataframe
    st.session_state.item_df = pd.DataFrame({
        "No.": list(range(1, 21)),
        "Item": [""] * 20,
        "MI Number": [""] * 20,
        "C/P No.": [""] * 20,
        "Set": [0] * 20,
        "Ctn": [0] * 20,
        "Quantity": [0] * 20
    })

# Page Title
st.title("🚚 Digital Delivery Order (DO) FBKM")

# Main Form
with st.form("do_form"):

    st.subheader("📄 Maklumat Delivery Order")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("DO Number", value=st.session_state.do_number, disabled=True)
    with col2:
        do_date = st.date_input("DO Date", value=st.session_state.do_date)

    customer_name = st.text_input("Customer Name", value=st.session_state.customer_name)

    st.markdown("---")
    st.subheader("📦 Item Details (maksimum 20 baris)")

    # Editable table with default from session_state.item_df
    edited_df = st.data_editor(
        st.session_state.item_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="item_editor"
    )

    # Submit & Clear buttons in the form
    col_submit, col_clear = st.columns(2)
    with col_submit:
        submitted = st.form_submit_button("🚀 Submit DO")
    with col_clear:
        cleared = st.form_submit_button("🔄 Clear Form")

    # Handle Clear
    if cleared:
        st.session_state.do_number = generate_do_number()
        st.session_state.do_date = date.today()
        st.session_state.customer_name = ""
        st.session_state.item_df = pd.DataFrame({
            "No.": list(range(1, 21)),
            "Item": [""] * 20,
            "MI Number": [""] * 20,
            "C/P No.": [""] * 20,
            "Set": [0] * 20,
            "Ctn": [0] * 20,
            "Quantity": [0] * 20
        })
        st.experimental_rerun()

    # Handle Submit
    if submitted:
        # Validate at least one item with Quantity > 0 and Item not empty
        valid_rows = []
        for _, row in edited_df.iterrows():
            if str(row["Item"]).strip() != "" and row["Quantity"] > 0:
                valid_rows.append(row)

        if len(valid_rows) == 0:
            st.warning("⚠️ Sila isi sekurang-kurangnya satu item dengan kuantiti lebih daripada 0.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows_to_save = []
            for row in valid_rows:
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
            csv_path = "do_data.csv"
            file_exists = os.path.exists(csv_path)
            df_to_save.to_csv(csv_path, mode="a", header=not file_exists, index=False)

            st.success("✅ DO submitted and saved successfully!")
            st.markdown("### 📄 DO Summary:")
            st.write(f"**DO Number:** {st.session_state.do_number}")
            st.write(f"**DO Date:** {do_date.strftime('%Y-%m-%d')}")
            st.write(f"**Customer Name:** {customer_name}")
            st.write("#### Items:")
            st.dataframe(df_to_save, use_container_width=True)

            # Update session_state with current values
            st.session_state.do_number = generate_do_number()
            st.session_state.do_date = date.today()
            st.session_state.customer_name = ""
            st.session_state.item_df = pd.DataFrame({
                "No.": list(range(1, 21)),
                "Item": [""] * 20,
                "MI Number": [""] * 20,
                "C/P No.": [""] * 20,
                "Set": [0] * 20,
                "Ctn": [0] * 20,
                "Quantity": [0] * 20
            })

# Divider
st.markdown("---")
st.subheader("📋 Semua Rekod DO")

# Show all saved DO records if any
csv_path = "do_data.csv"
if os.path.exists(csv_path):
    try:
        df_all = pd.read_csv(csv_path)
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True)
        else:
            st.info("Tiada DO dihantar lagi.")
    except pd.errors.EmptyDataError:
        st.info("Tiada DO dihantar lagi.")
    except Exception as e:
        st.error(f"❌ Ralat membaca fail CSV: {e}")
else:
    st.info("Tiada DO dihantar lagi.")
