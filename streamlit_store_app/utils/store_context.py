"""Store context management utilities."""

import streamlit as st
from datetime import datetime
from utils.database import query
from utils.config import load_config

def init_store_context():
    """Initialize store context in session state."""
    # Load configuration
    config = st.session_state.config
    
    # Initialize store context
    if "store_id" not in st.session_state:
        st.session_state.store_id = None
    if "store_name" not in st.session_state:
        st.session_state.store_name = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "show_context_switcher" not in st.session_state:
        st.session_state.show_context_switcher = True
    if "store_details" not in st.session_state:
        st.session_state.store_details = None
    

def toggle_context_switcher():
    """Toggle the visibility of the context switcher."""
    st.session_state.show_context_switcher = not st.session_state.show_context_switcher

def check_permission(permission: str) -> bool:
    """Check if current user role has a specific permission."""
    if not st.session_state.user_role:
        return False
    return st.session_state.config["roles"][st.session_state.user_role].get(permission, False)

def format_store_details(store_details: dict) -> str:
    """Format store details for display."""
    current_day = datetime.now().strftime('%A').lower()
    hours = store_details['hours'][current_day]
    
    return (
        f"**Working as:** {st.session_state.user_role.replace('_', ' ').title()}\n\n"
        f"**Store:** {store_details['name']}\n"
        f"**Type:** {store_details['type'].title()}\n"
        f"**Address:** {store_details['address']}\n"
        f"**Location:** {store_details['city']}, {store_details['state']} {store_details['zip_code']}\n"
        f"**Hours Today:** {hours['open']} - {hours['close']}\n"
        f"**Size:** {store_details['size_sqft']:,} sq ft\n"
        f"**Rating:** {'⭐' * int(store_details['rating'])}"
    )

def show_context_selector():
    """Display the store context selector."""
    # Show context switcher panel if activated
    if st.session_state.show_context_switcher:
        with st.sidebar:
            st.markdown("### Store Context")
            
            # Get stores from config
            stores = [store for store in st.session_state.config["stores"].values()]
            store_names = [store["name"] for store in stores]
            roles = list(st.session_state.config["roles"].keys())
            
            # Store selection
            selected_store = st.selectbox(
                "Select Store:",
                options=store_names,
                index=None if not st.session_state.get("store_name") else 
                      store_names.index(st.session_state.store_name),
                placeholder="Choose a store..."
            )
            
            # Role selection
            selected_role = st.selectbox(
                "Select Role:",
                options=roles,
                index=None if not st.session_state.get("user_role") else 
                      roles.index(st.session_state.user_role),
                placeholder="Choose your role..."
            )
            
            # Apply button
            if st.button("Apply", type="primary"):
                if selected_store and selected_role:
                    # Find selected store in config
                    store = next(store for store in stores if store["name"] == selected_store)
                    st.session_state.store_id = store["id"]
                    st.session_state.store_name = store["name"]
                    st.session_state.user_role = selected_role
                    st.session_state.store_details = store
                    st.session_state.show_context_switcher = True  # Hide the switcher after applying
                    st.rerun()
                else:
                    st.warning("Please select both store and role")

    # Show current context
    if st.session_state.store_name and st.session_state.user_role:
        st.sidebar.success(format_store_details(st.session_state.store_details))
    else:
        st.sidebar.warning("Please select both store and role to continue") 