"""Test script for homepage components."""

import streamlit as st
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.homepage import (
    show_kpi_dashboard, show_daily_operations_brief, show_team_insights,
    show_assigned_tasks, show_personal_schedule, show_product_promotions,
    show_notifications, show_inventory_status
)
from components.styles import load_css

def main():
    """Test the homepage components."""
    st.set_page_config(
        page_title="Homepage Test",
        page_icon="🏪",
        layout="wide"
    )
    
    # Load CSS
    load_css()
    
    # Mock session state
    if "store_id" not in st.session_state:
        st.session_state.store_id = 101
    if "store_name" not in st.session_state:
        st.session_state.store_name = "Downtown Market"
    if "user_role" not in st.session_state:
        st.session_state.user_role = "store_manager"
    
    st.title("🧪 Homepage Components Test")
    
    # Test role selector
    role = st.selectbox("Test Role:", ["store_manager", "store_associate"])
    st.session_state.user_role = role
    
    st.markdown("---")
    
    if role == "store_manager":
        st.markdown("## Store Manager View")
        show_kpi_dashboard()
        
        col1, col2 = st.columns([3, 2])
        with col1:
            show_daily_operations_brief()
        with col2:
            show_team_insights()
    
    elif role == "store_associate":
        st.markdown("## Store Associate View")
        show_assigned_tasks()
        
        col1, col2 = st.columns([3, 2])
        with col1:
            show_personal_schedule()
        with col2:
            show_product_promotions()
    
    st.markdown("---")
    st.markdown("## Common Components")
    
    col1, col2 = st.columns(2)
    with col1:
        show_notifications()
    with col2:
        show_inventory_status()

if __name__ == "__main__":
    main() 