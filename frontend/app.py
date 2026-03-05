# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import io  # For CSV download
from st_bridge import bridge, html as st_html
from styles import inject_all_styles, render_section_label, render_main_title, render_sidebar_group_label
import plotly.graph_objects as go

# =============================================================================
# PAGE CONFIG — Must be the first Streamlit call in the script
# =============================================================================
st.set_page_config(page_title="Inventory Management System", layout="wide")
inject_all_styles()
render_main_title()
st.divider()

# =============================================================================
# CONSTANTS
# =============================================================================
API_BASE = "http://127.0.0.1:8000"  # FastAPI backend base URL

# =============================================================================
# API HELPER FUNCTIONS
# These functions talk to the FastAPI backend.
# They store results directly in st.session_state so the UI stays in sync.
# =============================================================================

def fetch_products():
    """Fetch all products from backend and store in session state."""
    try:
        response = requests.get(f"{API_BASE}/products")
        response.raise_for_status()
        st.session_state.products = response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch products: {e}")


def fetch_filtered_products(category=None, search=None, min_price=None, max_price=None, sort=None, max_items=50, skip=0):
    """Fetch products with optional filters, sorting, and pagination."""
    try:
        # Build params dict — skip None and empty string values
        params = {k: v for k, v in {
            "category": category,
            "search": search,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
            "max_items": max_items,
            "skip": skip
        }.items() if v is not None and v != ""}

        response = requests.get(f"{API_BASE}/products", params=params)
        response.raise_for_status()
        st.session_state.products = response.json()
    except requests.RequestException as e:
        st.error(f"Filter request failed: {e}")


def fetch_category_stats():
    """Fetch aggregated category stats (total qty, total value) from backend."""
    try:
        response = requests.get(f"{API_BASE}/stats/categories-summary")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch category stats: {e}")
        return None


def get_low_stock_products(threshold=5):
    """Return products whose quantity is at or below the given threshold."""
    try:
        response = requests.get(f"{API_BASE}/products/low_stock", params={"threshold": threshold})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch low stock products: {e}")
        return []

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def convert_df_to_csv(df):
    """Convert a DataFrame to a UTF-8 encoded CSV bytes object for download."""
    return df.to_csv(index=False).encode('utf-8')

# =============================================================================
# UI COMPONENT FUNCTIONS
# Each function renders one self-contained piece of the UI.
# =============================================================================

def display_table():
    """
    Renders the AG Grid product table.
    - Reads from st.session_state.products
    - On row selection → updates st.session_state.selected_product and reruns
    - On deselection → clears st.session_state.selected_product and reruns
    """
    if not st.session_state.products:
        st.warning("No products found. Click 'Refresh Table' to load data.")
        return

    df = pd.DataFrame(st.session_state.products)
    df = df[["sku", "name", "category", "description", "price", "quantity"]]

    # Build AG Grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="single")
    gb.configure_column("sku", width=150)
    gb.configure_column("name", width=200)
    gb.configure_column("category", width=150)
    gb.configure_column("description", width=350)
    gb.configure_column("price", width=100)
    gb.configure_column("quantity", width=100)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

    # Render the grid — update_mode triggers rerun when selection changes
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=300,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True
    )

    selected_rows = grid_response.get("selected_rows", [])

    # AgGrid sometimes returns a DataFrame instead of a list — normalize it
    if isinstance(selected_rows, pd.DataFrame):
        selected_rows = selected_rows.to_dict("records")

    if selected_rows and len(selected_rows) > 0:
        new_selection = selected_rows[0]
        # Only rerun if the selection actually changed (avoids infinite rerun loop)
        if new_selection != st.session_state.selected_product:
            st.session_state.selected_product = new_selection
            st.rerun()
    else:
        # Row was deselected — clear the stored selection
        if st.session_state.selected_product is not None:
            st.session_state.selected_product = None
            st.rerun()


def delete_selected_product(product):
    """
    Deletes a product via the API.
    Also removes it from session_state.products immediately so the table updates
    without needing a full refresh.
    """
    sku = product.get("sku")
    if not sku:
        st.error("Cannot determine SKU for deletion.")
        return

    try:
        response = requests.delete(f"{API_BASE}/products/{sku}")
        response.raise_for_status()
        st.success(f"Product '{product['name']}' deleted successfully!")
        # Optimistic local update — remove from session state immediately
        st.session_state.products = [p for p in st.session_state.products if p["sku"] != sku]
        st.session_state.selected_product = None
    except requests.RequestException as e:
        st.error(f"Failed to delete product: {e}")


def render_chat_widget():
    """
    Renders the AI chat assistant inside a sidebar expander.
    - Maintains full chat history in st.session_state.chat_history
    - Streams responses from the backend /ai/chat endpoint
    - Uses st.write_stream() for typewriter effect
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.sidebar.expander("🤖 Inventory AI", expanded=False):
        render_section_label("Ask Your Inventory")
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        .chat-header-title {
            font-family: 'Share Tech Mono', monospace;
            color: #b2f0d9; font-size: 14px;
            letter-spacing: 2px; text-shadow: 0 0 8px #2cb86d;
        }
        .chat-header-dot {
            display: inline-block; width: 8px; height: 8px;
            border-radius: 50%; background: #2cb86d;
            box-shadow: 0 0 6px #2cb86d; margin-right: 8px;
            animation: blink 1.4s ease-in-out infinite;
        }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.2; } }
        </style>
        <div>
            <span class="chat-header-dot"></span>
            <span class="chat-header-title">INVENTORY AI</span>
        </div>
        """, unsafe_allow_html=True)

        # Scrollable container for message history
        msg_container = st.container(height=350)

        with msg_container:
            if not st.session_state.chat_history:
                with st.chat_message("assistant"):
                    st.write("Hey. Ask me anything about your inventory — low stock, totals, categories, price ranges.")
            else:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        # Chat input is always rendered so the expander never closes mid-conversation
        user_input = st.chat_input("Ask about your inventory...", key="sidebar_chat_input")

        if user_input and user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

            # Re-render all messages including the new user message
            with msg_container:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Stream the AI response — write_stream renders each chunk as it arrives
            with msg_container:
                with st.chat_message("assistant"):
                    try:
                        with requests.post(
                            f"{API_BASE}/ai/chat",
                            params={"question": user_input.strip()},
                            stream=True,
                            timeout=30
                        ) as response:
                            response.raise_for_status()
                            answer = st.write_stream(
                                chunk for chunk in response.iter_content(chunk_size=None, decode_unicode=True) if chunk
                            )
                    except requests.exceptions.Timeout:
                        answer = "⚠️ Request timed out."
                        st.error(answer)
                    except requests.RequestException as e:
                        answer = f"⚠️ Backend error: {e}"
                        st.error(answer)

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

# =============================================================================
# SESSION STATE INITIALIZATION
# Must run before any widget or UI element that reads from session state.
# Streamlit re-runs the entire script on every interaction — these guards
# (using "not in") prevent resetting state on every rerun.
# =============================================================================
if "products" not in st.session_state:
    st.session_state.products = []
    fetch_products()  # Initial data load on first run only

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# =============================================================================
# MAIN PAGE — INVENTORY SUMMARY STATS BOX
# Fetched on every rerun so totals always reflect current DB state.
# =============================================================================
stats_data = fetch_category_stats()

if stats_data:
    grand_totals = stats_data["grand_totals"]

    with st.container():
        st.markdown("""
        <style>
        .stats-box {
            background: linear-gradient(145deg, #2cb86d  20%,  #03361b 80%);
            padding: 40px;
            border-radius: 40px;
            border: 1px solid #0f5731;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(19, 122, 99, 0.4), inset 0 0 15px rgba(19, 122, 99, 0.2);
        }
        .stats-title {
            font-size: 18px;
            font-weight: bold;
            color: #b2f0d9;
            margin-bottom: 15px;
            text-shadow: 0 0 10px #137a63, 0 0 20px rgba(19, 122, 99, 0.6);
            letter-spacing: 1px;
        }
        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .stats-label {
            font-weight: bold;
            color: #8fdfdf;
            font-size: 14px;
            text-shadow: 0 0 8px #137a63;
            letter-spacing: 0.5px;
        }
        .stats-value {
            font-size: 28px;
            font-weight: 800;
            color: #ffffff;
            text-shadow: 0 0 15px #137a63, 0 0 30px rgba(19, 122, 99, 0.8);
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stats-box">
            <div class="stats-title">🌿 INVENTORY SUMMARY</div>
            <div class="stats-row">
                <div>
                    <div class="stats-label">📦 TOTAL QUANTITY</div>
                    <div class="stats-value">{grand_totals['total_quantity']:,.0f}</div>
                </div>
                <div>
                    <div class="stats-label">💰 TOTAL VALUE</div>
                    <div class="stats-value">${grand_totals['total_price']:,.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Loading inventory statistics...")

st.divider()

# =============================================================================
# SIDEBAR — SEARCH & FILTER
# Sends filter params to backend and updates session_state.products
# =============================================================================
render_sidebar_group_label("Search & Filter")

with st.sidebar.expander("🔍 Search Products", expanded=False):
    render_section_label("Filter Options")
    search_query = st.text_input("Search (Name)", key="search_key")

    category_options = ["electronics", "fruits", "vegetables", "confectionaries"]
    category = st.selectbox(
        "Category",
        options=[""] + category_options,
        index=category_options.index(st.session_state.get("category_key", "")) if st.session_state.get("category_key") in category_options else 0,
        key="category_key"
    )

    min_price = st.number_input("Min Price", min_value=0.0, value=st.session_state.get("min_price_key", 0.0), key="min_price_key")
    max_price = st.number_input("Max Price", min_value=0.0, value=st.session_state.get("max_price_key", 0.0), key="max_price_key")

    sort_option = st.selectbox(
        "Sort By",
        ["None", "price_asc", "price_desc", "name_asc", "name_desc"],
        index=["None", "price_asc", "price_desc", "name_asc", "name_desc"].index(st.session_state.get("sort_key", "None")),
        key="sort_key"
    )

    max_items = st.number_input("Max Items", min_value=1, value=st.session_state.get("max_items_key", 50), key="max_items_key")
    skip = st.number_input("Skip", min_value=0, value=st.session_state.get("skip_key", 0), key="skip_key")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Apply Filters"):
            fetch_filtered_products(
                category=category if category else None,
                search=search_query if search_query else None,
                min_price=min_price if min_price > 0 else None,
                max_price=max_price if max_price > 0 else None,
                sort=sort_option if sort_option != "None" else None,
                max_items=max_items,
                skip=skip
            )
    with col2:
        if st.button("Clear Filters"):
            # Deleting widget-bound keys resets them to defaults on next rerun
            for key in ["search_key", "category_key", "min_price_key", "max_price_key", "sort_key", "max_items_key", "skip_key"]:
                st.session_state.pop(key, None)
            fetch_products()

# =============================================================================
# SIDEBAR — MANAGE INVENTORY (Create / Delete / Update)
# =============================================================================
render_sidebar_group_label("Manage Inventory")

# ── CREATE PRODUCT ──────────────────────────────────────────────────────────
with st.sidebar.expander("➕ Create Product", expanded=False):
    render_section_label("New Product Details")

    # Initialize state keys only if they don't exist yet
    # (Guards prevent overwriting values user is currently typing)
    if "new_category" not in st.session_state:
        st.session_state.new_category = ""
    if "new_sku" not in st.session_state:
        st.session_state.new_sku = ""
    if "new_name" not in st.session_state:
        st.session_state.new_name = ""
    if "new_description" not in st.session_state:
        st.session_state.new_description = ""
    if "new_price" not in st.session_state:
        st.session_state.new_price = 0.01
    if "new_quantity" not in st.session_state:
        st.session_state.new_quantity = 0

    category_options = ["electronics", "fruits", "vegetables", "confectionaries"]
    category = st.selectbox(
        "Category",
        options=[""] + category_options,
        index=category_options.index(st.session_state.new_category) if st.session_state.new_category in category_options else 0,
        key="new_category"
    )
    sku = st.text_input("SKU", value=st.session_state.new_sku, key="new_sku")
    name = st.text_input("Name", value=st.session_state.new_name, key="new_name")
    description = st.text_area("Description", value=st.session_state.new_description, key="new_description")
    price = st.number_input("Price", min_value=0.01, value=st.session_state.new_price, key="new_price")
    quantity = st.number_input("Quantity", min_value=0, value=st.session_state.new_quantity, key="new_quantity")

    if st.button("Create Product"):
        if not all([category, sku, name, description, price > 0, quantity >= 0]):
            st.error("Please fill all fields correctly.")
        else:
            payload = {
                "category": category,
                "sku": sku,
                "name": name,
                "description": description,
                "price": price,
                "quantity": quantity
            }
            try:
                response = requests.post(f"{API_BASE}/products", json=payload)
                response.raise_for_status()
                created_product = response.json()

                # Optimistic local update — append to session state immediately
                st.session_state.products.append(created_product)
                st.success(f"Product '{name}' created successfully!")

                # ✅ KEY RULE: Never assign directly to a widget-bound key after instantiation.
                # Instead, DELETE the key — Streamlit will reinitialize it from defaults on next rerun.
                for key in ["new_sku", "new_name", "new_description", "new_price", "new_quantity", "new_category"]:
                    st.session_state.pop(key, None)

                st.rerun()

            except requests.RequestException as e:
                st.error(f"Failed to create product: {e}")
            except Exception as ex:
                st.error(f"Unexpected error: {ex}")

# ── DELETE PRODUCT ───────────────────────────────────────────────────────────
with st.sidebar.expander("🗑️ Delete Selected Product", expanded=False):
    render_section_label("Remove From Inventory")
    selected_product = st.session_state.get("selected_product")

    # Shows which product is currently selected in the AG Grid table
    if selected_product:
        st.info(f"Product Selected: **{selected_product.get('name')}**")
    else:
        st.warning("No product selected.")

    if st.button("Delete Product"):
        if not selected_product:
            st.warning("Please select a row to delete first.")
        else:
            sku_to_delete = selected_product.get("sku")
            try:
                response = requests.delete(f"{API_BASE}/products/{sku_to_delete}")
                response.raise_for_status()
                st.success(f"Product '{selected_product['name']}' deleted successfully!")
                # Remove from local state so table updates instantly
                st.session_state.products = [
                    p for p in st.session_state.products if p.get("sku") != sku_to_delete
                ]
                st.session_state.selected_product = None
            except requests.RequestException as e:
                st.error(f"Failed to delete product: {e}")

# ── UPDATE PRODUCT ───────────────────────────────────────────────────────────
with st.sidebar.expander("✏️ Update Product", expanded=False):
    render_section_label("Edit Product Details")
    selected = st.session_state.get("selected_product")

    if not selected:
        st.info("Select a row in the table to update.")
    else:
        # Populate fields from selected product, but only when the selection changes.
        # upd_source tracks which SKU was last loaded — prevents overwriting edits mid-form.
        if "upd_sku" not in st.session_state or st.session_state.get("upd_source") != selected.get("sku"):
            st.session_state.upd_category = selected.get("category", "")
            st.session_state.upd_sku = selected.get("sku", "")
            st.session_state.upd_name = selected.get("name", "")
            st.session_state.upd_description = selected.get("description", "")
            st.session_state.upd_price = float(selected.get("price", 0.01))
            st.session_state.upd_quantity = int(selected.get("quantity", 0))
            st.session_state.upd_source = selected.get("sku")  # Mark which product is loaded

        category_options = ["electronics", "fruits", "vegetables", "confectionaries"]
        upd_category = st.selectbox(
            "Category",
            options=[""] + category_options,
            index=category_options.index(st.session_state.upd_category) if st.session_state.upd_category in category_options else 0,
            key="upd_category"
        )
        upd_sku = st.text_input("SKU", value=st.session_state.upd_sku, key="upd_sku")
        upd_name = st.text_input("Name", value=st.session_state.upd_name, key="upd_name")
        upd_description = st.text_area("Description", value=st.session_state.upd_description, key="upd_description")
        upd_price = st.number_input(
            "Price",
            min_value=0.01,
            value=max(st.session_state.upd_price, 0.01),  # Clamp to avoid Streamlit min_value error
            key="upd_price"
        )
        upd_quantity = st.number_input(
            "Quantity",
            min_value=0,
            value=max(st.session_state.upd_quantity, 0),  # Clamp to avoid negative value error
            key="upd_quantity"
        )

        if st.button("Update Product"):
            if not all([upd_category, upd_sku, upd_name, upd_description, upd_price > 0, upd_quantity >= 0]):
                st.error("Please fill all fields correctly. Price must be > 0, quantity >= 0.")
            else:
                payload = {
                    "category": upd_category,
                    "sku": upd_sku,
                    "name": upd_name,
                    "description": upd_description,
                    "price": upd_price,
                    "quantity": upd_quantity
                }
                try:
                    response = requests.put(f"{API_BASE}/products/{upd_sku}", json=payload)
                    response.raise_for_status()
                    st.success(f"Product '{upd_name}' updated successfully!")
                    fetch_products()  # Full refresh — update reflects in table immediately
                    st.session_state.selected_product = None
                    st.rerun()
                except requests.RequestException as e:
                    st.error(f"Failed to update product: {e}")
                except Exception as ex:
                    st.error(f"Unexpected error: {ex}")

# =============================================================================
# SIDEBAR — LOW STOCK MONITORING
# Runs on every rerun so the alert count stays live.
# Auto-opens if any low stock products are detected.
# =============================================================================
if "low_stock_threshold" not in st.session_state:
    st.session_state.low_stock_threshold = 5
if "low_stock_products" not in st.session_state:
    st.session_state.low_stock_products = []

# Re-check low stock on every rerun (products or threshold may have changed)
if st.session_state.products:
    st.session_state.low_stock_products = get_low_stock_products(st.session_state.low_stock_threshold)

auto_open = len(st.session_state.low_stock_products) > 0  # Auto-expand if alerts exist
render_sidebar_group_label("Monitoring")

with st.sidebar.expander("⚠️ Low Stock Alert", expanded=auto_open):
    render_section_label("Stock Threshold Monitor")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_threshold = st.number_input(
            "Alert when quantity ≤",
            min_value=1,
            max_value=100,
            value=st.session_state.low_stock_threshold,
            key="low_stock_input"
        )
    with col2:
        st.metric("Products", len(st.session_state.low_stock_products))

    # Threshold changed — update state and rerun to refresh the alert list
    if new_threshold != st.session_state.low_stock_threshold:
        st.session_state.low_stock_threshold = new_threshold
        st.rerun()

    if st.session_state.low_stock_products:
        st.error(f"🚨 **{len(st.session_state.low_stock_products)} products need attention!**")

        for i, product in enumerate(st.session_state.low_stock_products):
            with st.container():
                if i > 0:
                    st.markdown("---")
                st.markdown(f"""
                **📦 {product['name']}**  
                🔹 **SKU:** `{product['sku']}`  
                🔹 **Quantity:** **:{product['quantity']}** units  
                🔹 **Category:** {product['category']}
                """)
    else:
        st.success(f"✅ All products have quantity > {st.session_state.low_stock_threshold}")

        # Show the 3 lowest-stock items as a heads-up even when no alerts are triggered
        if st.session_state.products:
            df = pd.DataFrame(st.session_state.products)
            lowest_stock = df.nsmallest(3, 'quantity')[['name', 'quantity']]
            if not lowest_stock.empty:
                st.caption("Current lowest stock levels:")
                for _, row in lowest_stock.iterrows():
                    st.markdown(f"- **{row['name']}**: {row['quantity']} units")

# =============================================================================
# MAIN PAGE — PRODUCT TABLE
# Refresh button re-fetches from backend.
# display_table() reads from session_state.products.
# =============================================================================
render_section_label("Product Inventory")

if st.button("Refresh Table"):
    fetch_products()

display_table()

# =============================================================================
# MAIN PAGE — CATEGORY CHARTS
# Only rendered if stats_data was successfully fetched above.
# =============================================================================
if stats_data and stats_data["per_category_summary"]:
    st.markdown("---")

    st.markdown("""
    <div style="
        font-family: 'Share Tech Mono', monospace;
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2cb86d, #b2f0d9, #2cb86d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 3px;
        text-transform: uppercase;
        filter: drop-shadow(0 0 8px rgba(44,184,109,0.7));
        margin-bottom: 12px;
    ">📊 Category-wise Inventory Analysis</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
        background: linear-gradient(145deg, #2cb86d 20%, #03361b 80%);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #137a63;
        box-shadow: 0 0 20px rgba(19, 122, 99, 0.3);
        margin-bottom: 20px;
    }
    [data-testid="column"] {
        background: rgba(10, 20, 15, 0.6);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2cb86d;
        backdrop-filter: blur(5px);
    }
    .stCaption {
        color: #b2f0d9 !important;
        text-shadow: 0 0 8px #137a63;
        font-weight: bold;
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build chart data from stats_data
    categories, total_quantities, total_values = [], [], []
    for category, data in stats_data["per_category_summary"].items():
        categories.append(category.capitalize())
        total_quantities.append(data["total_quantity"])
        total_values.append(data["total_price"])

    chart_df = pd.DataFrame({
        "Category": categories,
        "Total Quantity (units)": total_quantities,
        "Total Value ($)": total_values
    })

    # ── Chart 1: Total Quantity by Category ──────────────────────────────────
    st.caption("**📦 TOTAL QUANTITY BY CATEGORY**")
    fig1 = go.Figure(go.Bar(
        x=chart_df["Category"],
        y=chart_df["Total Quantity (units)"],
        marker=dict(
            color=chart_df["Total Quantity (units)"],
            colorscale=[[0, "#03361b"], [0.5, "#2cb86d"], [1, "#b2f0d9"]],
            line=dict(color="#2cb86d", width=1),
        ),
        text=chart_df["Total Quantity (units)"].apply(lambda x: f"{x:,.0f}"),
        textposition="outside",
        textfont=dict(color="#b2f0d9", family="Share Tech Mono", size=12),
    ))
    fig1.update_layout(
        paper_bgcolor="#061209", plot_bgcolor="#0d1f14",
        font=dict(family="Share Tech Mono", color="#b2f0d9"),
        height=400, margin=dict(t=30, b=20, l=20, r=20),
        xaxis=dict(gridcolor="rgba(44,184,109,0.13)", tickfont=dict(color="#4dba80", size=11), linecolor="rgba(44,184,109,0.2)"),
        yaxis=dict(gridcolor="rgba(44,184,109,0.13)", tickfont=dict(color="#4dba80", size=11), linecolor="rgba(44,184,109,0.2)"),
        bargap=0.3,
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ── Chart 2: Total Value by Category ─────────────────────────────────────
    st.caption("**💰 TOTAL VALUE BY CATEGORY**")
    fig2 = go.Figure(go.Bar(
        x=chart_df["Category"],
        y=chart_df["Total Value ($)"],
        marker=dict(
            color=chart_df["Total Value ($)"],
            colorscale=[[0, "#03361b"], [0.5, "#137a63"], [1, "#2cb86d"]],
            line=dict(color="#2cb86d", width=1),
        ),
        text=chart_df["Total Value ($)"].apply(lambda x: f"${x:,.2f}"),
        textposition="outside",
        textfont=dict(color="#b2f0d9", family="Share Tech Mono", size=12),
    ))
    fig2.update_layout(
        paper_bgcolor="#061209", plot_bgcolor="#0d1f14",
        font=dict(family="Share Tech Mono", color="#b2f0d9"),
        height=400, margin=dict(t=30, b=20, l=20, r=20),
        xaxis=dict(gridcolor="rgba(44,184,109,0.13)", tickfont=dict(color="#4dba80", size=11), linecolor="rgba(44,184,109,0.2)"),
        yaxis=dict(gridcolor="rgba(44,184,109,0.13)", tickfont=dict(color="#4dba80", size=11), linecolor="rgba(44,184,109,0.2)"),
        bargap=0.3,
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.divider()

    # ── Detailed Stats Table ──────────────────────────────────────────────────
    with st.expander("📋 View Category Details"):
        st.markdown("""
        <style>
        [data-testid="stExpander"] details summary p {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 12px !important;
            letter-spacing: 2px !important;
            color: #b2f0d9 !important;
            text-shadow: 0 0 6px #2cb86d;
            text-transform: uppercase;
        }
        [data-testid="stExpander"] details {
            border: 1px solid #2cb86d55 !important;
            border-radius: 10px !important;
            background: rgba(44,184,109,0.03) !important;
        }
        [data-testid="stExpander"] details[open] {
            border: 1px solid #2cb86d88 !important;
            box-shadow: 0 0 12px rgba(44,184,109,0.15) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        total_qty = grand_totals['total_quantity']
        total_val = grand_totals['total_price']

        detailed_df = chart_df.copy()
        detailed_df["Total Value ($)"] = detailed_df["Total Value ($)"].apply(lambda x: f"${x:,.2f}")
        detailed_df["Total Quantity (units)"] = detailed_df["Total Quantity (units)"].apply(lambda x: f"{x:,.0f} units")
        detailed_df["Quantity %"] = (chart_df["Total Quantity (units)"] / total_qty * 100).round(1).apply(lambda x: f"{x}%")
        detailed_df["Value %"] = (chart_df["Total Value ($)"] / total_val * 100).round(1).apply(lambda x: f"{x}%")
        detailed_df["Avg Price/Unit"] = (chart_df["Total Value ($)"] / chart_df["Total Quantity (units)"]).round(2).apply(lambda x: f"${x:,.2f}")
        detailed_df = detailed_df[["Category", "Total Quantity (units)", "Quantity %", "Total Value ($)", "Value %", "Avg Price/Unit"]]

        st.dataframe(detailed_df.set_index("Category"), use_container_width=True)
        st.markdown("---")
        st.caption("📈 **Summary Insights:**")

        max_qty_cat = chart_df.loc[chart_df["Total Quantity (units)"].idxmax(), "Category"]
        max_qty = chart_df["Total Quantity (units)"].max()
        max_val_cat = chart_df.loc[chart_df["Total Value ($)"].idxmax(), "Category"]
        max_val = chart_df["Total Value ($)"].max()
        avg_prices = chart_df["Total Value ($)"] / chart_df["Total Quantity (units)"]
        max_avg_cat = chart_df.loc[avg_prices.idxmax(), "Category"]
        max_avg = avg_prices.max()

        st.markdown(f"""
        - 🏆 **Most Units:** {max_qty_cat} ({max_qty:,.0f} units)
        - 💰 **Highest Value:** {max_val_cat} (${max_val:,.2f})
        - 💎 **Highest Avg Price:** {max_avg_cat} (${max_avg:,.2f} per unit)
        """)

st.divider()

# =============================================================================
# MAIN PAGE — CSV EXPORT
# Only shown when products exist in session state.
# =============================================================================
if st.session_state.products:
    df = pd.DataFrame(st.session_state.products)
    csv = convert_df_to_csv(df)
    st.download_button(
        label="📥 Download Inventory CSV",
        data=csv,
        file_name=f"inventory_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# =============================================================================
# SIDEBAR — AI CHAT ASSISTANT
# Rendered last so it doesn't interfere with session state setup above.
# =============================================================================
render_sidebar_group_label("AI Assistant")
render_chat_widget()