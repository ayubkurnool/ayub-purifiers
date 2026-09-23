import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# --- DATABASE SETUP ---
DB_NAME = "ayub_database.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Inventory Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE,
            part_description TEXT,
            quantity INTEGER,
            unit_price REAL DEFAULT 0.0,
            date_received TEXT
        )
    """)

  # Sales/Transactions Table (Quotes and Invoices)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, -- 'Quotation' or 'Invoice'
            client_name TEXT,
            mobile_number TEXT,
            items_json TEXT,
            subtotal REAL,
            discount_type TEXT, -- 'percentage' or 'fixed'
            discount_value REAL,
            total_amount REAL,
            created_by TEXT,
            date TEXT
        )
    """)

  # Activity Log Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


# --- HELPER FUNCTIONS ---
def log_activity(username, action):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO activity_log (username, action, timestamp) VALUES (?, ?, ?)",
      (username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
  )
  conn.commit()
  conn.close()


# --- AUTHENTICATION CONFIGURATION ---
CREDENTIALS = {
    "User1": "223344",
    "User2": "445566",
    "User3": "556688",
    "User4": "668899",
    "Owner": "253614",  # Admin Account
}

st.set_page_config(
    page_title="Ayub Purifiers Management System", layout="wide"
)

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.is_admin = False

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
  st.title("💧 Value Delivers - Login Portal")
  st.markdown("Water Purifier Sales & Service Management System")

  with st.form("login_form"):
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    submit = st.form_submit_button("Login")

    if submit:
      if (
          username_input in CREDENTIALS
          and CREDENTIALS[username_input] == password_input
      ):
        st.session_state.logged_in = True
        st.session_state.username = username_input
        st.session_state.is_admin = username_input == "Owner"
        log_activity(username_input, "Logged into the system")
        st.rerun()
      else:
        st.error("Invalid Username or Password.")
  st.stop()

# --- MAIN APP INTERFACE ---
st.sidebar.title(f"Welcome, {st.session_state.username}")
role_badge = "Admin (Owner)" if st.session_state.is_admin else "Staff Member"
st.sidebar.markdown(f"**Role:** {role_badge}")

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Stock Receiving",
        "Price Management",
        "Create Quotation",
        "Create Invoice",
        "Reports",
    ],
)

if st.sidebar.button("Logout"):
  log_activity(st.session_state.username, "Logged out")
  st.session_state.logged_in = False
  st.rerun()

# --- 1. DASHBOARD MODULE (Updated: Excludes Quotations) ---
if menu == "Dashboard":
  st.title("📊 Business Dashboard")
  st.markdown("At-a-glance business insights (Invoices & Inventory focus).")

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT * FROM inventory", conn)
  trans_df = pd.read_sql("SELECT * FROM transactions", conn)
  activity_df = pd.read_sql(
      "SELECT * FROM activity_log ORDER BY id DESC LIMIT 10", conn
  )
  conn.close()

  # Filter transactions to look only at Invoices (ignoring quotations on dashboard)
  invoices_df = (
      trans_df[trans_df["type"] == "Invoice"]
      if not trans_df.empty
      else pd.DataFrame()
  )

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        "Total Inventory Items",
        len(inv_df) if not inv_df.empty else 0,
    )
  with col2:
    total_sales = (
        invoices_df["total_amount"].sum() if not invoices_df.empty else 0
    )
    st.metric("Total Invoiced Sales", f"Rs. {total_sales:,.2f}")
  with col3:
    total_invoices_count = (
        len(invoices_df) if not invoices_df.empty else 0
    )
    st.metric("Total Invoices Issued", total_invoices_count)
  with col4:
    low_stock = (
        len(inv_df[inv_df["quantity"] < 5]) if not inv_df.empty else 0
    )
    st.metric("Low Stock Alerts (<5)", low_stock, delta_color="inverse")

  st.markdown("---")
  c1, c2 = st.columns(2)
  with c1:
    st.subheader("Inventory Overview & Stock Levels")
    if not inv_df.empty:
      fig = px.bar(
          inv_df,
          x="part_description",
          y="quantity",
          title="Stock Levels per Item",
      )
      st.plotly_chart(fig, use_container_width=True)
    else:
      st.info("No inventory data found.")

  with c2:
    st.subheader("Recent User Activity")
    if not activity_df.empty:
      st.dataframe(
          activity_df[["username", "action", "timestamp"]],
          use_container_width=True,
      )
    else:
      st.info("No recent activity recorded.")

# --- 2. STOCK RECEIVING MODULE ---
elif menu == "Stock Receiving":
  st.title("📦 Record Incoming Stock")
  st.markdown("Log incoming stock components into inventory.")

  with st.form("stock_form"):
    part_number = st.text_input("Part Number (Unique Identifier)")
    part_description = st.text_input("Part Description (Item Name/Details)")
    quantity = st.number_input("Quantity Received", min_value=1, step=1)
    current_date = datetime.now().strftime("%Y-%m-%d")
    st.text(f"Stock Received Date (Auto-generated): {current_date}")

    submitted = st.form_submit_button("Save Stock Entry")
    if submitted:
      if part_number and part_description:
        try:
          conn = sqlite3.connect(DB_NAME)
          cursor = conn.cursor()
          cursor.execute(
              """INSERT INTO inventory (part_number, part_description, quantity, date_received) 
                             VALUES (?, ?, ?, ?)""",
              (part_number, part_description, quantity, current_date),
          )
          conn.commit()
          conn.close()
          log_activity(
              st.session_state.username,
              f"Received stock: {part_description} (Qty: {quantity})",
          )
          st.success("Stock recorded successfully!")
        except sqlite3.IntegrityError:
          st.error("Error: Part Number already exists in inventory.")
      else:
        st.warning("Please fill in all mandatory fields.")

# --- 3. PRICE MANAGEMENT MODULE ---
elif menu == "Price Management":
  st.title("💲 Inventory Price Management")
  if not st.session_state.is_admin:
    st.error(
        "Access Denied. Price Management is restricted to the Administrator"
        " (Owner)."
    )
  else:
    st.markdown("Select items and update unit pricing.")
    conn = sqlite3.connect(DB_NAME)
    inv_df = pd.read_sql("SELECT * FROM inventory", conn)
    conn.close()

    if not inv_df.empty:
      selected_part = st.selectbox(
          "Select Inventory Item", inv_df["part_description"].tolist()
      )
      item_row = inv_df[inv_df["part_description"] == selected_part].iloc[0]

      st.write(f"**Part Number:** {item_row['part_number']}")
      st.write(f"**Current Stock:** {item_row['quantity']}")
      st.write(f"**Current Unit Price:** Rs. {item_row['unit_price']}")

      new_price = st.number_input(
          "Enter New Unit Price",
          min_value=0.0,
          value=float(item_row["unit_price"]),
          step=1.0,
      )

      if st.button("Update Unit Price"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET unit_price = ? WHERE part_number = ?",
            (new_price, item_row["part_number"]),
        )
        conn.commit()
        conn.close()
        log_activity(
            st.session_state.username,
            f"Updated price for {selected_part} to {new_price}",
        )
        st.success(f"Price updated successfully for {selected_part}!")
        st.rerun()
    else:
      st.info("No items available in inventory to update pricing.")

# --- 4 & 5. CREATE QUOTATION & INVOICE MODULES (With Print Button) ---
elif menu in ["Create Quotation", "Create Invoice"]:
  doc_type = "Quotation" if menu == "Create Quotation" else "Invoice"
  st.title(f"📝 Create {doc_type}")
  st.markdown(f"Generate a professional itemized {doc_type.lower()} layout.")

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT * FROM inventory", conn)
  conn.close()

  if inv_df.empty:
    st.warning(
        "Inventory is empty. Please add items and prices before generating"
        " sales documents."
    )
  else:
    client_name = st.text_input("Client Name")
    mobile_number = st.text_input("Mobile Number")

    st.subheader("Select Items")
    selected_items = []
    subtotal = 0.0

    for index, row in inv_df.iterrows():
      col1, col2, col3 = st.columns([3, 2, 2])
      with col1:
        include = st.checkbox(
            f"{row['part_description']} (Avail: {row['quantity']})",
            key=f"chk_{row['id']}",
        )
      with col2:
        st.text(f"Price: Rs. {row['unit_price']}")
      with col3:
        qty = st.number_input(
            "Qty",
            min_value=1,
            max_value=max(1, int(row["quantity"])),
            value=1,
            key=f"qty_{row['id']}",
        )

      if include:
        item_total = row["unit_price"] * qty
        selected_items.append({
            "part_number": row["part_number"],
            "description": row["part_description"],
            "unit_price": row["unit_price"],
            "quantity": qty,
            "total": item_total,
        })
        subtotal += item_total

    st.markdown(f"### Subtotal: Rs. {subtotal:,.2f}")

    discount_type = "None"
    discount_value = 0.0
    if st.session_state.is_admin:
      st.markdown("---")
      st.subheader("Admin Discount Controls")
      discount_type = st.selectbox(
          "Discount Type", ["None", "Percentage (%)", "Fixed Amount (Rs.)"]
      )
      if discount_type == "Percentage (%)":
        discount_value = st.number_input(
            "Percentage Off (%)", min_value=0.0, max_value=100.0, value=0.0
        )
        discount_amount = subtotal * (discount_value / 100.0)
      elif discount_type == "Fixed Amount (Rs.)":
        discount_value = st.number_input(
            "Fixed Amount Off (Rs.)", min_value=0.0, max_value=subtotal, value=0.0
        )
        discount_amount = discount_value
      else:
        discount_amount = 0.0
    else:
      discount_amount = 0.0
      st.info(
          "Note: Only the Administrator (Owner) can apply discounts to"
          " quotations/invoices."
      )

    final_total = max(0.0, subtotal - discount_amount)
    st.markdown(f"## Final Total: Rs. {final_total:,.2f}")

    if st.button(f"Generate & Save {doc_type}"):
      if client_name and mobile_number and selected_items:
        import json

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions (type, client_name, mobile_number, items_json, subtotal, discount_type, discount_value, total_amount, created_by, date)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_type,
                client_name,
                mobile_number,
                json.dumps(selected_items),
                subtotal,
                discount_type,
                discount_value,
                final_total,
                st.session_state.username,
                datetime.now().strftime("%Y-%m-%d"),
            ),
        )
        conn.commit()
        conn.close()
        log_activity(
            st.session_state.username,
            f"Generated {doc_type} for Client: {client_name}",
        )
        st.success(f"Professional {doc_type} generated successfully!")

        # Professional Layout Output with Direct Print Button
        st.markdown("---")
        st.markdown(f"### 🖨️ AYUB PURIFIERS - OFFICIAL {doc_type.upper()}")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        st.write(
            f"**Client Name:** {client_name} | **Mobile:** {mobile_number}"
        )
        st.dataframe(pd.DataFrame(selected_items), use_container_width=True)
        st.write(f"**Subtotal:** Rs. {subtotal:,.2f}")
        if discount_amount > 0:
          st.write(f"**Discount Applied:** -Rs. {discount_amount:,.2f}")
        st.write(f"**Total Amount Payable:** Rs. {final_total:,.2f}")

        # Built-in direct browser print trigger button
        st.markdown(
            """
                <button onclick="window.print();" style="background-color: #2e7d32; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 10px;">
                    🖨️ Print this Document Now
                </button>
                """,
            unsafe_allow_html=True,
        )
      else:
        st.warning(
            "Please enter client name, mobile number, and select at least one"
            " item."
        )

# --- 6. REPORTING MODULE ---
elif menu == "Reports":
  st.title("📈 Reporting Module")
  st.markdown("Filter, view, and inspect system records and transactions.")

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT * FROM inventory", conn)
  trans_df = pd.read_sql("SELECT * FROM transactions", conn)
  conn.close()

  report_tab1, report_tab2 = st.tabs(
      ["Inventory & Stock Reports", "Sales Transactions"]
  )

  with report_tab1:
    st.subheader("Inventory Stock Filter View")
    if not inv_df.empty:
      search_term = st.text_input("Filter by Part Name/Description")
      price_sort = st.selectbox(
          "Sort by Unit Price", ["None", "Low to High", "High to Low"]
      )

      filtered_inv = inv_df.copy()
      if search_term:
        filtered_inv = filtered_inv[
            filtered_inv["part_description"]
            .str.contains(search_term, case=False, na=False)
        ]
      if price_sort == "Low to High":
        filtered_inv = filtered_inv.sort_values(by="unit_price", ascending=True)
      elif price_sort == "High to Low":
        filtered_inv = filtered_inv.sort_values(
            by="unit_price", ascending=False
        )

      st.dataframe(filtered_inv, use_container_width=True)
    else:
      st.info("No inventory records found.")

  with report_tab2:
    st.subheader("Quotes & Invoices Summary")
    if not trans_df.empty:
      doc_filter = st.selectbox(
          "Filter by Document Type", ["All", "Quotation", "Invoice"]
      )
      filtered_trans = trans_df.copy()
      if doc_filter != "All":
        filtered_trans = filtered_trans[filtered_trans["type"] == doc_filter]

      st.dataframe(
          filtered_trans[[
              "id",
              "type",
              "client_name",
              "mobile_number",
              "subtotal",
              "total_amount",
              "created_by",
              "date",
          ]],
          use_container_width=True,
      )
    else:
      st.info("No sales transactions logged yet.")
