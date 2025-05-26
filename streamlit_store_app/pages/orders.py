"""Orders page for the Streamlit Store App."""

import streamlit as st
from components import display_metric_card, display_alert, show_nav
from utils.database import query
from components.styles import load_css

def main():
    """Main orders page."""
    # Load CSS
    load_css()
    
    # Show navigation
    show_nav()

    # Verify store context
    if not st.session_state.get("store_id") or not st.session_state.get("user_role"):
        st.warning("Please select a store and role from the sidebar to continue")
        st.stop()

    # Check permissions
    if not st.session_state.get("user_role") in ["store_associate", "store_manager"]:
        st.error("You don't have permission to view this page")
        st.stop()

    # Initialize order processing state
    if "processing_orders" not in st.session_state:
        st.session_state.processing_orders = set()

    if "completed_orders" not in st.session_state:
        st.session_state.completed_orders = set()

    # Page header
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title(f"📦 Orders - {st.session_state.store_name}")
        st.markdown("**Manage customer orders and fulfillment**")
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

    # Orders Overview with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="kpi-summary-card orders">
                <div class="kpi-icon">⏳</div>
                <div class="kpi-value">8</div>
                <div class="kpi-label">Pending Orders</div>
                <div class="kpi-change">+2 from yesterday</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="kpi-summary-card sales">
                <div class="kpi-icon">🔄</div>
                <div class="kpi-value">5</div>
                <div class="kpi-label">Processing</div>
                <div class="kpi-change">Currently active</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="kpi-summary-card conversion">
                <div class="kpi-icon">✅</div>
                <div class="kpi-value">23</div>
                <div class="kpi-label">Completed Today</div>
                <div class="kpi-change positive">+15% vs yesterday</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="kpi-summary-card traffic">
                <div class="kpi-icon">💰</div>
                <div class="kpi-value">$4.2K</div>
                <div class="kpi-label">Today's Revenue</div>
                <div class="kpi-change positive">+8.5%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Active Orders", "🛒 BOPIS Orders", "📊 Order Analytics", "⚠️ Priority Orders"])
    
    with tab1:
        show_active_orders()
    
    with tab2:
        show_bopis_orders()
    
    with tab3:
        show_order_analytics()
    
    with tab4:
        show_priority_orders()

def handle_order_action(order_id: int, action: str):
    """Handle order processing actions."""
    if action == "process":
        st.session_state.processing_orders.add(order_id)
    elif action == "complete":
        st.session_state.completed_orders.add(order_id)
        if order_id in st.session_state.processing_orders:
            st.session_state.processing_orders.remove(order_id)

def show_active_orders():
    """Display active orders with enhanced styling."""
    st.markdown("### 📋 Active Orders")
    
    # Mock orders data focused on retail/fashion
    orders = [
        {
            "id": "ORD-2024-0156",
            "customer": "Sarah Johnson",
            "items": ["Designer Handbag", "Silk Scarf"],
            "amount": 389.98,
            "status": "pending",
            "priority": "high",
            "created": "2024-01-15 10:30 AM",
            "type": "online"
        },
        {
            "id": "ORD-2024-0157",
            "customer": "Michael Chen",
            "items": ["Wireless Headphones", "iPhone Case"],
            "amount": 249.98,
            "status": "processing",
            "priority": "medium",
            "created": "2024-01-15 11:15 AM",
            "type": "bopis"
        },
        {
            "id": "ORD-2024-0158",
            "customer": "Emma Rodriguez",
            "items": ["Evening Dress", "Jewelry Set"],
            "amount": 299.99,
            "status": "pending",
            "priority": "medium",
            "created": "2024-01-15 12:00 PM",
            "type": "online"
        }
    ]
    
    for order in orders:
        show_order_card(order)

def show_order_card(order):
    """Display an enhanced order card."""
    status_colors = {"pending": "#f59e0b", "processing": "#3b82f6", "completed": "#10b981"}
    priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"}
    type_colors = {"online": "#8b5cf6", "bopis": "#06b6d4"}
    
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col1:
        html_content = f"""
            <div class="order-card">
                <div class="order-header">
                    <span class="order-id">{order['id']}</span>
                    <div class="order-badges">
                        <span class="order-status" style="background-color: {status_colors[order['status']]}">
                            {order['status'].upper()}
                        </span>
                        <span class="order-priority" style="background-color: {priority_colors[order['priority']]}">
                            {order['priority'].upper()}
                        </span>
                        <span class="order-type" style="background-color: {type_colors[order['type']]}">
                            {order['type'].upper()}
                        </span>
                    </div>
                </div>
                <div class="order-details">
                    <div><strong>Customer:</strong> {order['customer']}</div>
                    <div><strong>Items:</strong> {', '.join(order['items'])}</div>
                    <div><strong>Amount:</strong> ${order['amount']}</div>
                    <div><strong>Created:</strong> {order['created']}</div>
                </div>
            </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    with col2:
        if order['status'] == 'pending':
            if st.button("Start Processing", key=f"process_{order['id']}", use_container_width=True):
                st.success(f"Order {order['id']} processing started!")
        elif order['status'] == 'processing':
            if st.button("Mark Complete", key=f"complete_{order['id']}", use_container_width=True, type="primary"):
                st.success(f"Order {order['id']} completed!")
    
    with col3:
        if st.button("View Details", key=f"details_{order['id']}", use_container_width=True):
            st.info(f"Detailed view for {order['id']} would open here")
    
    st.markdown("---")

def show_bopis_orders():
    """Display BOPIS (Buy Online, Pick up In Store) orders."""
    st.markdown("### 🛒 BOPIS Orders")
    
    bopis_orders = [
        {
            "id": "BOPIS-2024-0045",
            "customer": "Jennifer Smith",
            "items": ["Smart Watch", "Wireless Charger"],
            "amount": 339.98,
            "pickup_time": "2:00 PM - 4:00 PM",
            "status": "ready",
            "location": "Customer Service Desk"
        },
        {
            "id": "BOPIS-2024-0046",
            "customer": "David Park",
            "items": ["Fall Jacket"],
            "amount": 149.99,
            "pickup_time": "3:00 PM - 5:00 PM",
            "status": "preparing",
            "location": "Women's Fashion"
        }
    ]
    
    for order in bopis_orders:
        show_bopis_card(order)

def show_bopis_card(order):
    """Display a BOPIS order card."""
    status_colors = {"ready": "#10b981", "preparing": "#f59e0b", "picked_up": "#64748b"}
    
    html_content = f"""
        <div class="bopis-card">
            <div class="bopis-header">
                <span class="bopis-id">{order['id']}</span>
                <span class="bopis-status" style="background-color: {status_colors[order['status']]}">
                    {order['status'].upper()}
                </span>
            </div>
            <div class="bopis-details">
                <div><strong>Customer:</strong> {order['customer']}</div>
                <div><strong>Items:</strong> {', '.join(order['items'])}</div>
                <div><strong>Pickup Window:</strong> {order['pickup_time']}</div>
                <div><strong>Location:</strong> {order['location']}</div>
                <div><strong>Amount:</strong> ${order['amount']}</div>
            </div>
        </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def show_order_analytics():
    """Display order analytics."""
    st.markdown("### 📊 Order Analytics")
    st.info("Order analytics and trends would be displayed here with charts and metrics.")

def show_priority_orders():
    """Display priority orders."""
    st.markdown("### ⚠️ Priority Orders")
    st.info("High-priority and urgent orders would be displayed here.")

# Add custom CSS for order components
st.markdown("""
    <style>
    .order-card, .bopis-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border: 1px solid rgba(226, 232, 240, 0.6);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .order-card:hover, .bopis-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.12);
    }
    
    .order-header, .bopis-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .order-id, .bopis-id {
        font-weight: 700;
        font-size: 1.25rem;
        color: #1e293b;
        line-height: 1.3;
    }
    
    .order-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    
    .order-status, .order-priority, .order-type, .bopis-status {
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    
    .order-details, .bopis-details {
        color: #475569;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .order-details div, .bopis-details div {
        margin-bottom: 0.5rem;
        padding: 0.25rem 0;
    }
    
    .order-details strong, .bopis-details strong {
        color: #334155;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 