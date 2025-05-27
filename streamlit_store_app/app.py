"""Streamlit Store Companion App."""

import os
from dotenv import load_dotenv
import streamlit as st
from components import display_metric_card, display_alert, load_css, show_chat_widget, show_nav
from components.homepage import show_homepage
from utils.config import load_config, validate_env
from utils.database import query
from utils.store_context import init_store_context, show_context_selector, check_permission
from datetime import datetime

# Define available roles and their permissions
ROLES = {
    "store_associate": {
        "can_view_orders": True,
        "can_process_orders": True,
        "can_view_inventory": True,
        "can_reorder_inventory": False,
        "can_view_staff_schedule": True,
        "can_modify_staff_schedule": False,
        "can_view_sales_data": False,
    },
    "store_manager": {
        "can_view_orders": True,
        "can_process_orders": True,
        "can_view_inventory": True,
        "can_reorder_inventory": True,
        "can_view_staff_schedule": True,
        "can_modify_staff_schedule": True,
        "can_view_sales_data": True,
    }
}

def init_session_state():
    """Initialize session state variables."""
    # User and Store Context
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "store_id" not in st.session_state:
        st.session_state.store_id = None
    if "store_name" not in st.session_state:
        st.session_state.store_name = None
    
    # App State
    if "order_history" not in st.session_state:
        st.session_state.order_history = []
    if "selected_items" not in st.session_state:
        st.session_state.selected_items = set()


def check_permission(permission):
    """Check if current user role has a specific permission."""
    if not st.session_state.user_role:
        return False
    return ROLES[st.session_state.user_role].get(permission, False)



def init_app():
    """Initialize the application."""
    # Load environment variables
    load_dotenv()
    
    # Validate environment and load config
    validate_env()
    config = load_config()
    
    # Store the config in session state for easy access
    if "config" not in st.session_state:
        st.session_state.config = config
    
    # Load custom CSS
    load_css()
    
    return config

def show_home():
    """Display the modular card-based home page."""
    if not st.session_state.store_id or not st.session_state.user_role:
        st.warning("Please select a store and role from the sidebar to continue")
        return

    # Get employee name from config
    employee_name = st.session_state.config.get('employees', {}).get(st.session_state.user_role, st.session_state.user_role.replace('_', ' ').title())

    # Page header
    st.title(f"🏪 {st.session_state.store_name}")
    st.markdown(f"**Welcome back, {employee_name}!**")
    
    # Show the centralized homepage content
    show_homepage()

def main():
    """Main application entry point."""
    try:
        # Set page config (must be the first Streamlit command)
        st.set_page_config(
            page_title="BrickMate",
            page_icon="🏪",
            layout="wide"
        )

        # Initialize the app
        init_app()
        
        # Initialize store context and show selector
        init_store_context()

        # Show context selector
        show_context_selector()
        
        # Show home page content
        show_home()
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if os.getenv("DEBUG", "false").lower() == "true":
            st.exception(e)

if __name__ == "__main__":
    main()
