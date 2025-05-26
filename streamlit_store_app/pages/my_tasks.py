"""My Tasks page for store associates."""

import streamlit as st
from datetime import datetime, timedelta
from components.styles import load_css

def main():
    """Main tasks page."""
    # Load CSS
    load_css()
    
    # Page header
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("📋 My Tasks")
        st.markdown("**Manage your daily assignments and priorities**")
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
    
    # Task filters
    col1, col2, col3 = st.columns(3)
    with col1:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    with col2:
        type_filter = st.selectbox("Type", ["All", "BOPIS", "Restocking", "Customer Service", "Visual Merchandising"])
    with col3:
        status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed"])
    
    # Mock tasks data focused on retail/fashion
    tasks = [
        {
            "id": 1, "type": "BOPIS", "title": "Order #B2024-0156", 
            "customer": "Sarah Johnson", "items": ["Designer Handbag", "Silk Scarf", "Sunglasses"], 
            "priority": "high", "due": "10:30 AM", "status": "pending",
            "location": "Customer Service Desk", "notes": "VIP customer - handle with care"
        },
        {
            "id": 2, "type": "BOPIS", "title": "Order #B2024-0157", 
            "customer": "Michael Chen", "items": ["Wireless Headphones"], 
            "priority": "medium", "due": "11:15 AM", "status": "pending",
            "location": "Electronics Section", "notes": "Gift wrapping requested"
        },
        {
            "id": 3, "type": "Restocking", "title": "Women's Designer Section", 
            "location": "Floor 2 - Designer", "items": ["Fall Jackets", "Evening Dresses", "Accessories"], 
            "priority": "high", "due": "12:00 PM", "status": "in_progress",
            "notes": "New collection display setup required"
        },
        {
            "id": 4, "type": "Customer Service", "title": "Personal Shopping Appointment", 
            "customer": "Emma Rodriguez", "location": "Private Styling Room", 
            "priority": "high", "due": "2:00 PM", "status": "pending",
            "notes": "Wedding guest outfit consultation - budget $500-800"
        },
        {
            "id": 5, "type": "Visual Merchandising", "title": "Electronics Display Update", 
            "location": "Electronics Section", "items": ["iPhone 15 Cases", "Smart Watches", "Headphones"], 
            "priority": "medium", "due": "3:00 PM", "status": "pending",
            "notes": "Highlight new arrivals and promotions"
        },
        {
            "id": 6, "type": "Restocking", "title": "Men's Footwear", 
            "location": "Men's Department", "items": ["Dress Shoes", "Sneakers", "Boots"], 
            "priority": "low", "due": "4:00 PM", "status": "pending",
            "notes": "Check sizes and arrange by style"
        }
    ]
    
    # Filter tasks
    filtered_tasks = tasks
    if priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["priority"].title() == priority_filter]
    if type_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["type"] == type_filter]
    if status_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["status"].replace("_", " ").title() == status_filter]
    
    # Group tasks by type
    bopis_tasks = [t for t in filtered_tasks if t["type"] == "BOPIS"]
    restock_tasks = [t for t in filtered_tasks if t["type"] == "Restocking"]
    service_tasks = [t for t in filtered_tasks if t["type"] == "Customer Service"]
    visual_tasks = [t for t in filtered_tasks if t["type"] == "Visual Merchandising"]
    
    # Display tasks in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🛒 BOPIS Orders", "📦 Restocking", "🤝 Customer Service", "🎨 Visual Merchandising"])
    
    with tab1:
        st.markdown("### BOPIS Orders")
        if bopis_tasks:
            for task in bopis_tasks:
                show_task_card(task, "bopis")
        else:
            st.info("No BOPIS orders matching your filters.")
    
    with tab2:
        st.markdown("### Restocking Tasks")
        if restock_tasks:
            for task in restock_tasks:
                show_task_card(task, "restock")
        else:
            st.info("No restocking tasks matching your filters.")
    
    with tab3:
        st.markdown("### Customer Service")
        if service_tasks:
            for task in service_tasks:
                show_task_card(task, "service")
        else:
            st.info("No customer service tasks matching your filters.")
    
    with tab4:
        st.markdown("### Visual Merchandising")
        if visual_tasks:
            for task in visual_tasks:
                show_task_card(task, "visual")
        else:
            st.info("No visual merchandising tasks matching your filters.")

def show_task_card(task, task_type):
    """Display a detailed task card with actions."""
    priority_colors = {"high": "#dc3545", "medium": "#ffc107", "low": "#28a745"}
    status_colors = {"pending": "#6c757d", "in_progress": "#007bff", "completed": "#28a745"}
    
    with st.container():
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            # Build HTML content step by step to avoid f-string issues
            html_content = f"""
                <div class="task-detail-card {task_type}">
                    <div class="task-header">
                        <span class="task-title">{task["title"]}</span>
                        <span class="task-priority" style="background-color: {priority_colors[task['priority']]}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">
                            {task["priority"].upper()}
                        </span>
                    </div>
                    <div class="task-details">
                        <div><strong>Due:</strong> {task["due"]}</div>
                        <div><strong>Location:</strong> {task["location"]}</div>
            """
            
            # Add customer info if present
            if "customer" in task:
                html_content += f'<div><strong>Customer:</strong> {task["customer"]}</div>'
            
            # Add items info if present
            if "items" in task:
                items_str = ", ".join(task["items"])
                html_content += f'<div><strong>Items:</strong> {items_str}</div>'
            
            # Add notes and close the HTML
            html_content += f"""
                        <div><strong>Notes:</strong> {task["notes"]}</div>
                    </div>
                </div>
            """
            
            st.markdown(html_content, unsafe_allow_html=True)
        
        with col2:
            status_options = ["pending", "in_progress", "completed"]
            current_status = task["status"]
            new_status = st.selectbox(
                "Status", 
                status_options, 
                index=status_options.index(current_status),
                key=f"status_{task['id']}"
            )
            
            if new_status != current_status:
                st.success(f"Status updated to {new_status.replace('_', ' ').title()}")
        
        with col3:
            if task["type"] == "BOPIS":
                if st.button("Start Picking", key=f"action_{task['id']}", use_container_width=True):
                    st.success("Started picking order!")
            elif task["type"] == "Restocking":
                if st.button("Begin Restock", key=f"action_{task['id']}", use_container_width=True):
                    st.success("Restocking task started!")
            elif task["type"] == "Customer Service":
                if st.button("Start Service", key=f"action_{task['id']}", use_container_width=True):
                    st.success("Customer service initiated!")
            elif task["type"] == "Visual Merchandising":
                if st.button("Start Setup", key=f"action_{task['id']}", use_container_width=True):
                    st.success("Visual merchandising started!")
        
        st.markdown("---")

# Add custom CSS for task cards
st.markdown("""
    <style>
    .task-detail-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid;
    }
    
    .task-detail-card.bopis {
        border-left-color: #007bff;
    }
    
    .task-detail-card.restock {
        border-left-color: #28a745;
    }
    
    .task-detail-card.service {
        border-left-color: #6f42c1;
    }
    
    .task-detail-card.visual {
        border-left-color: #fd7e14;
    }
    
    .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    
    .task-title {
        font-weight: 600;
        font-size: 1.1rem;
        color: #212529;
    }
    
    .task-details {
        color: #495057;
        line-height: 1.5;
    }
    
    .task-details div {
        margin-bottom: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 