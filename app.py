from datetime import datetime
import json
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

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
            type TEXT,
            client_name TEXT,
            mobile_number TEXT,
            items_json TEXT,
            subtotal REAL,
            discount_type TEXT,
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
  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_log (username, action, timestamp) VALUES (?, ?,"
        " ?)",
        (username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass


# --- AUTHENTICATION CONFIGURATION ---
CREDENTIALS = {
    "User1": "223344",
    "User2": "445566",
    "User3": "556688",
    "User4": "668899",
    "Owner": "253614",  # Admin Account
}

st.set_page_config(
    page_title="Ayub Purifiers Management System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CLEAN PRINT CSS INJECTION (Hides sidebar & menus during print) ---
st.markdown(
    """
    <style>
    @media print {
        /* Hide everything by default on the page */
        body * {
            visibility: hidden !important;
        }
        /* Show only our clean bill container and its children */
        #clean-bill, #clean-bill * {
            visibility: visible !important;
        }
        #clean-bill {
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            border: none !important;
            padding: 0px !important;
        }
        /* Hide Streamlit UI Chrome */
        [data-testid="stSidebar"], header, footer, .stButton, div[data-testid="stHorizontalBlock"] {
            display: none !important;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.is_admin = False

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
  st.title("💧 Ayub Purifiers - Login Portal")
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

# --- 1. DASHBOARD MODULE ---
if menu == "Dashboard":
  st.markdown(
      """
        <div style="background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%); padding: 35px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 2.3rem; color: white; font-weight: 700;">📊 Ayub Purifiers Command Center</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.95;">Welcome back! Here is your real-time overview of inventory, sales, and business operations.</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT * FROM inventory", conn)
  trans_df = pd.read_sql("SELECT * FROM transactions", conn)
  activity_df = pd.read_sql(
      "SELECT * FROM activity_log ORDER BY id DESC LIMIT 10", conn
  )
  conn.close()

  invoices_df = (
      trans_df[trans_df["type"] == "Invoice"]
      if not trans_df.empty
      else pd.DataFrame()
  )

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    total_inv_count = len(inv_df) if not inv_df.empty else 0
    st.markdown(
        f"""
            <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #1976d2;">
                <p style="margin:0; color: #555; font-size: 14px; font-weight: bold;">TOTAL INVENTORY</p>
                <h2 style="margin: 5px 0 0 0; color: #0d47a1;">{total_inv_count}</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col2:
    total_sales = (
        invoices_df["total_amount"].sum() if not invoices_df.empty else 0
    )
    st.markdown(
        f"""
            <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32;">
                <p style="margin:0; color: #555; font-size: 14px; font-weight: bold;">TOTAL INVOICED SALES</p>
                <h2 style="margin: 5px 0 0 0; color: #1b5e20;">Rs. {total_sales:,.2f}</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col3:
    total_invoices_count = len(invoices_df) if not invoices_df.empty else 0
    st.markdown(
        f"""
            <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; border-left: 5px solid #f57c00;">
                <p style="margin:0; color: #555; font-size: 14px; font-weight: bold;">INVOICES ISSUED</p>
                <h2 style="margin: 5px 0 0 0; color: #e65100;">{total_invoices_count}</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col4:
    low_stock = (
        len(inv_df[inv_df["quantity"] < 5]) if not inv_df.empty else 0
    )
    st.markdown(
        f"""
            <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 5px solid #c62828;">
                <p style="margin:0; color: #555; font-size: 14px; font-weight: bold;">LOW STOCK ALERTS</p>
                <h2 style="margin: 5px 0 0 0; color: #b71c1c;">{low_stock}</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  c1, c2 = st.columns(2)
  with c1:
    st.subheader("📦 Inventory Overview & Stock Levels")
    if not inv_df.empty:
      fig = px.bar(
          inv_df,
          x="part_description",
          y="quantity",
          title="Stock Levels per Item",
          color="quantity",
          color_continuous_scale="blues",
      )
      st.plotly_chart(fig, use_container_width=True)
    else:
      st.info("No inventory data found.")

  with c2:
    st.subheader("🕒 Recent User Activity")
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

# --- 4 & 5. CREATE QUOTATION & INVOICE MODULES ---
elif menu in ["Create Quotation", "Create Invoice"]:
  doc_type = "Quotation" if menu == "Create Quotation" else "Invoice"
  st.title(f"📝 Create {doc_type}")

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT * FROM inventory", conn)
  conn.close()

  if inv_df.empty:
    st.warning(
        "Inventory is empty. Please add items and prices before generating"
        " sales documents."
    )
  else:
    if f"show_print_{doc_type}" not in st.session_state:
      st.session_state[f"show_print_{doc_type}"] = False

    if not st.session_state[f"show_print_{doc_type}"]:
      # --- FORM INPUT VIEW ---
      client_name = st.text_input("Client Name", key=f"cn_{doc_type}")
      mobile_number = st.text_input("Mobile Number", key=f"mb_{doc_type}")

      st.subheader("Select Items")
      selected_items = []
      subtotal = 0.0

      for index, row in inv_df.iterrows():
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
          include = st.checkbox(
              f"{row['part_description']} (Avail: {row['quantity']})",
              key=f"chk_{doc_type}_{row['id']}",
          )
        with col2:
          st.text(f"Price: Rs. {row['unit_price']}")
        with col3:
          qty = st.number_input(
              "Qty",
              min_value=1,
              max_value=max(1, int(row["quantity"])),
              value=1,
              key=f"qty_{doc_type}_{row['id']}",
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
            "Discount Type",
            ["None", "Percentage (%)", "Fixed Amount (Rs.)"],
            key=f"dt_{doc_type}",
        )
        if discount_type == "Percentage (%)":
          discount_value = st.number_input(
              "Percentage Off (%)",
              min_value=0.0,
              max_value=100.0,
              value=0.0,
              key=f"dv_p_{doc_type}",
          )
          discount_amount = subtotal * (discount_value / 100.0)
        elif discount_type == "Fixed Amount (Rs.)":
          discount_value = st.number_input(
              "Fixed Amount Off (Rs.)",
              min_value=0.0,
              max_value=subtotal,
              value=0.0,
              key=f"dv_f_{doc_type}",
          )
          discount_amount = discount_value
        else:
          discount_amount = 0.0
      else:
        discount_amount = 0.0

      final_total = max(0.0, subtotal - discount_amount)
      st.markdown(f"## Final Total: Rs. {final_total:,.2f}")

      if st.button(f"Generate & Save {doc_type}", key=f"btn_{doc_type}"):
        if client_name and mobile_number and selected_items:
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

          st.session_state[f"last_doc_{doc_type}"] = {
              "client_name": client_name,
              "mobile_number": mobile_number,
              "items": selected_items,
              "subtotal": subtotal,
              "discount_amount": discount_amount,
              "final_total": final_total,
              "date": datetime.now().strftime("%Y-%m-%d"),
          }
          st.session_state[f"show_print_{doc_type}"] = True
          st.rerun()
        else:
          st.warning(
              "Please enter client name, mobile number, and select at least one"
              " item."
          )
    else:
      # --- CLEAN DEDICATED PRINTABLE VIEW ---
      doc_data = st.session_state[f"last_doc_{doc_type}"]

      st.success(f"Professional {doc_type} generated and saved successfully!")

      # Build HTML table rows dynamically so they render perfectly in print
      table_rows_html = ""
      for item in doc_data["items"]:
        table_rows_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['description']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">Rs. {item['unit_price']:,.2f}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">Rs. {item['total']:,.2f}</td>
                </tr>
                """

      # Clean printable card container with embedded native HTML table
      st.markdown(
          f"""
            <div style="background-color: white; color: black; padding: 30px; border: 1px solid #ddd; border-radius: 8px;" id="clean-bill">
                <h2 style="color: #0d47a1; margin-bottom: 0px;">AYUB PURIFIERS</h2>
                <p style="color: gray; margin-top: 0px;">Water Purifiers Sales & Service Management</p>
                <hr style="border: 1px solid #0d47a1;">
                <h3>OFFICIAL {doc_type.upper()}</h3>
                <p><b>Date:</b> {doc_data['date']}</p>
                <p><b>Client Name:</b> {doc_data['client_name']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Mobile:</b> {doc_data['mobile_number']}</p>
                <br>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: #f1f1f1; text-align: left;">
                            <th style="padding: 10px; border-bottom: 2px solid #ccc;">Item Description</th>
                            <th style="padding: 10px; border-bottom: 2px solid #ccc; text-align: center;">Qty</th>
                            <th style="padding: 10px; border-bottom: 2px solid #ccc; text-align: right;">Unit Price</th>
                            <th style="padding: 10px; border-bottom: 2px solid #ccc; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
                <div style="text-align: right; margin-top: 20px;">
                    <p><b>Subtotal:</b> Rs. {doc_data['subtotal']:,.2f}</p>
                    {f"<p><b>Discount:</b> -Rs. {doc_data['discount_amount']:,.2f}</p>" if doc_data['discount_amount'] > 0 else ""}
                    <h3><b>Total Amount: Rs. {doc_data['final_total']:,.2f}</b></h3>
                </div>
                <hr style="border: 0.5px solid #ccc;">
                <p style="text-align: center; color: gray; font-size: 12px;">Thank you for your business with Ayub Purifiers!</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

      # --- WORKING HTML PRINT COMPONENT BUTTON ---
      print_component_code = """
      <div style="text-align: center; margin: 20px 0;">
          <button onclick="parent.window.print();" style="background-color: #2e7d32; color: white; padding: 14px 28px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
              🖨️ Click Here to Print Document
          </button>
      </div>
      """

      col_p1, col_p2 = st.columns([2, 1])
      with col_p1:
        components.html(print_component_code, height=80)
      with col_p2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Create Another Document", key=f"reset_{doc_type}"):
          st.session_state[f"show_print_{doc_type}"] = False
          st.rerun()

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
