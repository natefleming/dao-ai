"""Homepage components for the retail store employee iPad app."""

import streamlit as st
from datetime import datetime, timedelta
from utils.database import query
from utils.store_context import check_permission
from components.metrics import display_metric_card, display_alert

def show_notifications_modal():
    """Display notifications in an expandable modal."""
    # Initialize notification state
    if "show_notifications" not in st.session_state:
        st.session_state.show_notifications = False
    
    # Notification button with count badge
    notification_count = 4  # Mock count
    
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button(f"🔔 {notification_count}", key="notifications_toggle", help="View notifications"):
            st.session_state.show_notifications = not st.session_state.show_notifications
    
    # Show notifications modal if toggled
    if st.session_state.show_notifications:
        with st.expander("📢 Notifications", expanded=True):
            # Categorized notifications
            st.markdown("#### 🚨 Urgent")
            urgent_notifications = [
                {"message": "Security system maintenance in 30 minutes - Electronics section", "time": "5 min ago"},
                {"message": "VIP customer arriving at 2 PM - Personal shopping assistance needed", "time": "15 min ago"}
            ]
            
            for notif in urgent_notifications:
                st.markdown(f"""
                    <div class="notification-item urgent">
                        <div class="notification-message">{notif["message"]}</div>
                        <div class="notification-time">{notif["time"]}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("#### ⚠️ Important")
            important_notifications = [
                {"message": "New designer collection arriving tomorrow - Prepare display area", "time": "1 hour ago"},
                {"message": "Staff meeting moved to 3 PM in conference room", "time": "2 hours ago"}
            ]
            
            for notif in important_notifications:
                st.markdown(f"""
                    <div class="notification-item important">
                        <div class="notification-message">{notif["message"]}</div>
                        <div class="notification-time">{notif["time"]}</div>
                    </div>
                """, unsafe_allow_html=True)

def show_kpi_summary():
    """Display condensed KPI dashboard for store managers."""
    st.markdown("### 📊 Store Performance")
    
    # Mock retail data
    today_sales = 28750.00
    yesterday_sales = 24320.00
    sales_change = ((today_sales - yesterday_sales) / yesterday_sales) * 100
    
    pending_orders = 15
    completed_orders = 89
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="kpi-summary-card sales">
                <div class="kpi-icon">💰</div>
                <div class="kpi-value">${today_sales:,.0f}</div>
                <div class="kpi-label">Today's Sales</div>
                <div class="kpi-change positive">+{sales_change:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="kpi-summary-card orders">
                <div class="kpi-icon">📦</div>
                <div class="kpi-value">{completed_orders}</div>
                <div class="kpi-label">Orders Complete</div>
                <div class="kpi-change">{pending_orders} pending</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="kpi-summary-card traffic">
                <div class="kpi-icon">👥</div>
                <div class="kpi-value">247</div>
                <div class="kpi-label">Customers Today</div>
                <div class="kpi-change">Peak: 2-4 PM</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="kpi-summary-card conversion">
                <div class="kpi-icon">📈</div>
                <div class="kpi-value">68%</div>
                <div class="kpi-label">Conversion Rate</div>
                <div class="kpi-change positive">+5% vs avg</div>
            </div>
        """, unsafe_allow_html=True)

def show_inventory_summary():
    """Display condensed inventory status for all employees."""
    st.markdown("### 📊 Inventory Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="inventory-summary-card critical">
                <div class="inventory-icon">🚨</div>
                <div class="inventory-value">3</div>
                <div class="inventory-label">Critical Stock</div>
                <div class="inventory-detail">Designer Jeans, iPhone Cases</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="inventory-summary-card low">
                <div class="inventory-icon">⚠️</div>
                <div class="inventory-value">12</div>
                <div class="inventory-label">Low Stock</div>
                <div class="inventory-detail">Seasonal items</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="inventory-summary-card good">
                <div class="inventory-icon">✅</div>
                <div class="inventory-value">892</div>
                <div class="inventory-label">Well Stocked</div>
                <div class="inventory-detail">Core inventory</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="inventory-summary-card new">
                <div class="inventory-icon">🆕</div>
                <div class="inventory-value">24</div>
                <div class="inventory-label">New Arrivals</div>
                <div class="inventory-detail">Fall collection</div>
            </div>
        """, unsafe_allow_html=True)

def show_manager_summary_cards():
    """Display summary cards for store managers with navigation."""
    st.markdown("### 🎯 Quick Access")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Daily Operations", key="daily_ops", use_container_width=True):
            st.switch_page("pages/daily_operations.py")
        
        st.markdown("""
            <div class="summary-card operations">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">5/8</span>
                        <span class="stat-label">Tasks Complete</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">2</span>
                        <span class="stat-label">Urgent Items</span>
                    </div>
                </div>
                <div class="summary-preview">
                    • Morning inventory ✅<br>
                    • Vendor delivery 🔄<br>
                    • Staff meeting ⏳
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("👥 Team Insights", key="team_insights", use_container_width=True):
            st.switch_page("pages/team_insights.py")
        
        st.markdown("""
            <div class="summary-card team">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">12/15</span>
                        <span class="stat-label">Staff Present</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">94%</span>
                        <span class="stat-label">Avg Performance</span>
                    </div>
                </div>
                <div class="summary-preview">
                    🏆 Top: Sarah Chen (98%)<br>
                    ⚠️ Coverage gap: 3-4 PM<br>
                    📅 3 shift changes today
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("📊 Detailed Inventory", key="detailed_inventory", use_container_width=True):
            st.switch_page("pages/inventory.py")
        
        st.markdown("""
            <div class="summary-card inventory">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">$2.1M</span>
                        <span class="stat-label">Total Value</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">15</span>
                        <span class="stat-label">Reorder Needed</span>
                    </div>
                </div>
                <div class="summary-preview">
                    📱 Electronics: 95% stocked<br>
                    👗 Apparel: 87% stocked<br>
                    👟 Footwear: 92% stocked
                </div>
            </div>
        """, unsafe_allow_html=True)

def show_associate_homepage():
    """Display homepage content for store associates with improved tab-based layout."""
    # Quick status bar at top with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="quick-status-card active">
                <div class="status-icon">🟢</div>
                <div class="status-text">On Shift</div>
                <div class="status-detail">3h 37m left</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="quick-status-card tasks">
                <div class="status-icon">📋</div>
                <div class="status-text">7 Tasks</div>
                <div class="status-detail">3 high priority</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="quick-status-card inventory">
                <div class="status-icon">📦</div>
                <div class="status-text">Inventory</div>
                <div class="status-detail">3 critical items</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="quick-status-card notifications">
                <div class="status-icon">🔔</div>
                <div class="status-text">4 Alerts</div>
                <div class="status-detail">2 urgent</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main content in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 My Work", "📅 Schedule", "🏷️ Products", "📊 Performance"])
    
    with tab1:
        show_my_work_tab()
    
    with tab2:
        show_schedule_tab()
    
    with tab3:
        show_products_tab()
    
    with tab4:
        show_performance_tab()

def show_my_work_tab():
    """Display the My Work tab with tasks and immediate priorities."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🎯 Today's Priorities")
        
        # High priority tasks preview
        priority_tasks = [
            {"title": "BOPIS Order #B2024-0156", "customer": "Sarah Johnson", "due": "10:30 AM", "type": "BOPIS"},
            {"title": "Personal Shopping Appt", "customer": "Emma Rodriguez", "due": "2:00 PM", "type": "Service"},
            {"title": "Restock Designer Section", "location": "Floor 2", "due": "12:00 PM", "type": "Restock"}
        ]
        
        for task in priority_tasks:
            task_type_colors = {"BOPIS": "#007bff", "Service": "#6f42c1", "Restock": "#28a745"}
            st.markdown(f"""
                <div class="priority-task-preview">
                    <div class="task-preview-header">
                        <span class="task-preview-title">{task['title']}</span>
                        <span class="task-preview-type" style="background-color: {task_type_colors[task['type']]}">
                            {task['type']}
                        </span>
                    </div>
                    <div class="task-preview-details">
                        Due: {task['due']} • {task.get('customer', task.get('location', ''))}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("📋 View All Tasks", key="view_all_tasks", use_container_width=True):
            st.switch_page("pages/my_tasks.py")
    
    with col2:
        st.markdown("#### 🚨 Quick Actions")
        
        # Quick action buttons
        if st.button("🛒 Check BOPIS Orders", use_container_width=True):
            st.switch_page("pages/my_tasks.py")
        
        if st.button("📦 Report Low Stock", use_container_width=True):
            st.info("Stock reporting form would open")
        
        if st.button("🤝 Request Help", use_container_width=True):
            st.info("Help request sent to manager")
        
        if st.button("☕ Take Break", use_container_width=True):
            st.success("Break started - timer activated")
        
        st.markdown("#### 📍 Current Assignment")
        st.markdown("""
            <div class="current-assignment-card">
                <div class="assignment-department">Women's Fashion</div>
                <div class="assignment-details">
                    <div>Section: Designer Area</div>
                    <div>Focus: Customer Service</div>
                    <div>Coverage: Solo until 2 PM</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def show_schedule_tab():
    """Display the Schedule tab with shift info and time tracking."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⏰ Current Shift")
        
        st.markdown("""
            <div class="shift-detail-card">
                <div class="shift-time-info">
                    <div class="shift-current-time">12:23 PM</div>
                    <div class="shift-progress">
                        <div class="shift-progress-bar">
                            <div class="shift-progress-fill" style="width: 55%"></div>
                        </div>
                        <div class="shift-progress-text">4h 23m worked • 3h 37m remaining</div>
                    </div>
                </div>
                <div class="shift-details">
                    <div><strong>Shift:</strong> 8:00 AM - 4:00 PM</div>
                    <div><strong>Break:</strong> 12:00 - 12:30 PM (Due now!)</div>
                    <div><strong>Department:</strong> Women's Fashion</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📅 View Full Schedule", use_container_width=True):
            st.switch_page("pages/my_schedule.py")
    
    with col2:
        st.markdown("#### 📊 This Week")
        
        st.markdown("""
            <div class="week-overview-card">
                <div class="week-stats-grid">
                    <div class="week-stat">
                        <div class="week-stat-value">32/40</div>
                        <div class="week-stat-label">Hours</div>
                    </div>
                    <div class="week-stat">
                        <div class="week-stat-value">4/5</div>
                        <div class="week-stat-label">Days</div>
                    </div>
                    <div class="week-stat">
                        <div class="week-stat-value">94%</div>
                        <div class="week-stat-label">Performance</div>
                    </div>
                    <div class="week-stat">
                        <div class="week-stat-value">$2,847</div>
                        <div class="week-stat-label">Sales</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📝 Upcoming")
        upcoming_items = [
            {"day": "Tomorrow", "shift": "8 AM - 4 PM", "dept": "Electronics"},
            {"day": "Friday", "shift": "9 AM - 5 PM", "dept": "Women's Fashion"},
            {"day": "Saturday", "shift": "OFF", "dept": ""}
        ]
        
        for item in upcoming_items:
            if item["shift"] == "OFF":
                st.markdown(f"""
                    <div class="new-item-preview">
                        <div class="new-item-name">🏖️ {item['day']}</div>
                        <div class="new-item-details">Day Off</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="new-item-preview">
                        <div class="new-item-name">📅 {item['day']}</div>
                        <div class="new-item-details">{item['shift']} - {item['dept']}</div>
                    </div>
                """, unsafe_allow_html=True)

def show_products_tab():
    """Display the Products tab with promotions and product info."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 Active Promotions")
        
        promotions = [
            {"name": "Fall Fashion Sale", "discount": "40% off", "ends": "End of week"},
            {"name": "Designer Handbags", "discount": "25% off", "ends": "Tomorrow"},
            {"name": "Tech Accessories", "discount": "Buy 2 Get 1", "ends": "3 days"}
        ]
        
        for promo in promotions:
            st.markdown(f"""
                <div class="promo-preview-card">
                    <div class="promo-preview-header">
                        <span class="promo-preview-name">{promo['name']}</span>
                        <span class="promo-preview-discount">{promo['discount']}</span>
                    </div>
                    <div class="promo-preview-ends">Ends: {promo['ends']}</div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("🏷️ View All Promotions", use_container_width=True):
            st.switch_page("pages/products_promotions.py")
    
    with col2:
        st.markdown("#### 🆕 New This Week")
        
        new_items = [
            {"name": "iPhone 15 Pro Cases", "category": "Electronics", "location": "E3"},
            {"name": "Winter Coats", "category": "Women's Apparel", "location": "W2"},
            {"name": "Designer Sneakers", "category": "Footwear", "location": "F4"}
        ]
        
        for item in new_items:
            st.markdown(f"""
                <div class="new-item-preview">
                    <div class="new-item-name">{item['name']}</div>
                    <div class="new-item-details">{item['category']} • {item['location']}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### 🔥 Trending")
        trending_items = [
            {"name": "Wireless Earbuds Pro", "growth": "+45%", "icon": "🎧"},
            {"name": "Oversized Blazers", "growth": "+60%", "icon": "👗"},
            {"name": "Minimalist Watches", "growth": "+35%", "icon": "⌚"}
        ]
        
        for item in trending_items:
            st.markdown(f"""
                <div class="new-item-preview">
                    <div class="new-item-name">{item['icon']} {item['name']}</div>
                    <div class="new-item-details">Growth: {item['growth']}</div>
                </div>
            """, unsafe_allow_html=True)

def show_performance_tab():
    """Display the Performance tab with personal metrics and achievements."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Today's Performance")
        
        st.markdown("""
            <div class="performance-overview-card">
                <div class="performance-score">
                    <div class="performance-score-value">94%</div>
                    <div class="performance-score-label">Overall Score</div>
                </div>
                <div class="performance-metrics">
                    <div class="performance-metric">
                        <span class="metric-label">BOPIS Orders:</span>
                        <span class="metric-value">12 completed</span>
                    </div>
                    <div class="performance-metric">
                        <span class="metric-label">Customer Assists:</span>
                        <span class="metric-value">8 interactions</span>
                    </div>
                    <div class="performance-metric">
                        <span class="metric-label">Sales:</span>
                        <span class="metric-value">$2,450</span>
                    </div>
                    <div class="performance-metric">
                        <span class="metric-label">Customer Rating:</span>
                        <span class="metric-value">4.8/5 ⭐</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🎯 Goals & Achievements")
        
        st.markdown("""
            <div class="goals-card">
                <div class="goal-item completed">
                    <span class="goal-icon">✅</span>
                    <span class="goal-text">Complete 10 BOPIS orders</span>
                </div>
                <div class="goal-item in-progress">
                    <span class="goal-icon">🔄</span>
                    <span class="goal-text">Assist 15 customers (8/15)</span>
                </div>
                <div class="goal-item pending">
                    <span class="goal-icon">⏳</span>
                    <span class="goal-text">Achieve $3,000 in sales</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🏅 Recent Achievements")
        achievements = [
            {"name": "Customer Service Excellence", "icon": "🌟"},
            {"name": "Sales Target Exceeded", "icon": "💰"}, 
            {"name": "Speed Champion (BOPIS)", "icon": "⚡"}
        ]
        
        for achievement in achievements:
            st.markdown(f"""
                <div class="new-item-preview">
                    <div class="new-item-name">{achievement['icon']} {achievement['name']}</div>
                    <div class="new-item-details">Recently earned</div>
                </div>
            """, unsafe_allow_html=True)

def show_persistent_chat():
    """Display a persistent, easily accessible chat widget."""
    # Initialize chat state
    if "chat_expanded" not in st.session_state:
        st.session_state.chat_expanded = False
    
    # Create a floating chat button using columns for positioning
    col1, col2, col3 = st.columns([8, 1, 1])
    
    with col3:
        if st.button("💬", key="chat_toggle", help="AI Assistant"):
            st.session_state.chat_expanded = not st.session_state.chat_expanded
    
    # Show expanded chat if toggled
    if st.session_state.chat_expanded:
        with st.expander("🤖 AI Assistant", expanded=True):
            # Import and show the existing chat widget
            from components.chat import show_chat_widget
            show_chat_widget(st.session_state.config["chat"])

# Legacy functions for backward compatibility (simplified versions)
def show_kpi_dashboard():
    """Legacy function - redirects to summary."""
    show_kpi_summary()

def show_notifications():
    """Legacy function - redirects to modal."""
    show_notifications_modal()

def show_inventory_status():
    """Legacy function - redirects to summary."""
    show_inventory_summary()

def show_homepage():
    """Main homepage function that routes to appropriate view based on user role."""
    # Get user role from session state
    user_role = st.session_state.get("user_role", "store_associate")
    
    if user_role == "store_manager":
        # Show new tab-based manager homepage
        show_manager_homepage()
    else:
        # Show new tab-based associate homepage
        show_associate_homepage()
    
    # Show persistent chat for all users
    show_persistent_chat()

def show_manager_homepage():
    """Display tab-based homepage content for store managers."""
    # Quick executive dashboard at top with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="manager-status-card sales">
                <div class="status-icon">💰</div>
                <div class="status-text">$28,750</div>
                <div class="status-detail">Today's Sales (+18%)</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="manager-status-card team">
                <div class="status-icon">👥</div>
                <div class="status-text">12/15</div>
                <div class="status-detail">Staff Present (94% avg)</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="manager-status-card operations">
                <div class="status-icon">📋</div>
                <div class="status-text">5/8</div>
                <div class="status-detail">Tasks Complete (2 urgent)</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Notifications button
        if st.button("🔔 4 Alerts", key="manager_notifications", use_container_width=True):
            st.session_state.show_notifications = not st.session_state.get("show_notifications", False)
    
    # Show notifications if toggled
    if st.session_state.get("show_notifications", False):
        show_notifications_modal()
    
    st.markdown("---")
    
    # Main content in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🎯 Operations", "👥 Team", "📦 Inventory", "📈 Analytics"])
    
    with tab1:
        show_manager_dashboard_tab()
    
    with tab2:
        show_manager_operations_tab()
    
    with tab3:
        show_manager_team_tab()
    
    with tab4:
        show_manager_inventory_tab()
    
    with tab5:
        show_manager_analytics_tab()

def show_manager_dashboard_tab():
    """Display the Dashboard tab with key metrics and alerts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Today's Performance")
        
        st.markdown("""
            <div class="manager-dashboard-card">
                <div class="dashboard-metrics">
                    <div class="dashboard-metric">
                        <span class="metric-label">Sales Target:</span>
                        <span class="metric-value">96% ($28,750/$30,000)</span>
                        <span class="metric-trend positive">+18% vs yesterday</span>
                    </div>
                    <div class="dashboard-metric">
                        <span class="metric-label">Customer Traffic:</span>
                        <span class="metric-value">247 visitors</span>
                        <span class="metric-trend">Peak: 2-4 PM</span>
                    </div>
                    <div class="dashboard-metric">
                        <span class="metric-label">Conversion Rate:</span>
                        <span class="metric-value">68%</span>
                        <span class="metric-trend positive">+5% vs avg</span>
                    </div>
                    <div class="dashboard-metric">
                        <span class="metric-label">Avg Transaction:</span>
                        <span class="metric-value">$171.50</span>
                        <span class="metric-trend positive">+12% vs avg</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ⚠️ Priority Alerts")
        
        priority_alerts = [
            {"type": "Critical Stock", "message": "Designer Jeans - only 2 left", "severity": "high", "action": "Reorder now"},
            {"type": "Staff Coverage", "message": "Electronics understaffed 3-4 PM", "severity": "high", "action": "Find coverage"},
            {"type": "VIP Customer", "message": "Sarah Johnson arriving at 2 PM", "severity": "medium", "action": "Prep personal shopper"},
            {"type": "Delivery", "message": "Designer collection delayed to 4:30 PM", "severity": "medium", "action": "Update team"}
        ]
        
        for alert in priority_alerts:
            severity_colors = {"high": "#dc3545", "medium": "#ffc107", "low": "#28a745"}
            st.markdown(f"""
                <div class="priority-alert-card" style="border-left-color: {severity_colors[alert['severity']]}">
                    <div class="alert-header">
                        <span class="alert-type">{alert['type']}</span>
                        <span class="alert-severity">{alert['severity'].upper()}</span>
                    </div>
                    <div class="alert-message">{alert['message']}</div>
                    <div class="alert-action">→ {alert['action']}</div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("📋 View All Operations", use_container_width=True):
            st.switch_page("pages/daily_operations.py")

def show_manager_operations_tab():
    """Display the Operations tab with daily priorities and tasks."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🎯 Today's Priorities")
        
        operations = [
            {"task": "Morning inventory check", "status": "completed", "time": "08:00", "owner": "Sarah Chen"},
            {"task": "Staff meeting - Holiday prep", "status": "in_progress", "time": "09:30", "owner": "All Staff"},
            {"task": "Vendor delivery - Designer Collection", "status": "pending", "time": "11:00", "owner": "Mike Rodriguez"},
            {"task": "Weekly sales report review", "status": "pending", "time": "15:00", "owner": "Manager"},
            {"task": "Evening shift handover", "status": "pending", "time": "18:00", "owner": "Emma Wilson"}
        ]
        
        for op in operations:
            status_colors = {"completed": "#28a745", "in_progress": "#007bff", "pending": "#6c757d"}
            status_icons = {"completed": "✅", "in_progress": "🔄", "pending": "⏳"}
            
            st.markdown(f"""
                <div class="operation-preview-card">
                    <div class="operation-header">
                        <span class="operation-task">{op['task']}</span>
                        <span class="operation-time">{op['time']}</span>
                    </div>
                    <div class="operation-details">
                        <span style="color: {status_colors[op['status']]}">
                            {status_icons[op['status']]} {op['status'].replace('_', ' ').title()}
                        </span>
                        • Assigned to: {op['owner']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📅 Quick Actions")
        
        if st.button("➕ Add Task", use_container_width=True):
            st.info("Task creation form would open")
        
        if st.button("📞 Call Staff", use_container_width=True):
            st.info("Staff contact list would open")
        
        if st.button("🚚 Track Deliveries", use_container_width=True):
            st.info("Delivery tracking would open")
        
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generator would open")
        
        st.markdown("#### 🕐 Store Hours")
        st.markdown("""
            <div class="store-hours-card">
                <div class="hours-today">
                    <div class="hours-label">Today:</div>
                    <div class="hours-time">8:00 AM - 9:00 PM</div>
                </div>
                <div class="hours-status">
                    <div class="status-open">🟢 Open</div>
                    <div class="hours-remaining">5h 37m remaining</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def show_manager_team_tab():
    """Display the Team tab with staff overview and performance."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Team Status")
        
        team_members = [
            {"name": "Sarah Chen", "role": "Store Associate", "status": "active", "performance": 98, "location": "Women's Fashion"},
            {"name": "Mike Rodriguez", "role": "Store Associate", "status": "active", "performance": 95, "location": "Electronics"},
            {"name": "Emma Wilson", "role": "Store Associate", "status": "break", "performance": 92, "location": "Customer Service"},
            {"name": "James Park", "role": "Visual Merchandiser", "status": "active", "performance": 88, "location": "All Floors"},
            {"name": "Lisa Wong", "role": "Store Associate", "status": "off", "performance": 75, "location": "Men's Fashion"}
        ]
        
        for member in team_members:
            status_colors = {"active": "#28a745", "break": "#ffc107", "off": "#6c757d"}
            status_icons = {"active": "🟢", "break": "☕", "off": "🔴"}
            
            st.markdown(f"""
                <div class="team-member-card">
                    <div class="member-header">
                        <span class="member-name">{member['name']}</span>
                        <span class="member-status" style="color: {status_colors[member['status']]}">
                            {status_icons[member['status']]} {member['status'].title()}
                        </span>
                    </div>
                    <div class="member-details">
                        <div>{member['role']} • {member['location']}</div>
                        <div>Performance: {member['performance']}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("👥 View Team Insights", use_container_width=True):
            st.switch_page("pages/team_insights.py")
    
    with col2:
        st.markdown("#### 📊 Team Metrics")
        
        st.markdown("""
            <div class="team-metrics-card">
                <div class="team-metric">
                    <span class="metric-label">Average Performance:</span>
                    <span class="metric-value">94%</span>
                </div>
                <div class="team-metric">
                    <span class="metric-label">Customer Satisfaction:</span>
                    <span class="metric-value">4.6/5</span>
                </div>
                <div class="team-metric">
                    <span class="metric-label">Tasks Completed:</span>
                    <span class="metric-value">47/52</span>
                </div>
                <div class="team-metric">
                    <span class="metric-label">Schedule Adherence:</span>
                    <span class="metric-value">98%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### ⚠️ Team Alerts")
        team_alerts = [
            {"alert": "Coverage gap: 3-4 PM Electronics", "icon": "⚠️"},
            {"alert": "Sarah Chen: 42 hours this week", "icon": "⏰"},
            {"alert": "3 employees need safety training", "icon": "📚"}
        ]
        
        for alert in team_alerts:
            st.markdown(f"""
                <div class="new-item-preview">
                    <div class="new-item-name">{alert['icon']} Alert</div>
                    <div class="new-item-details">{alert['alert']}</div>
                </div>
            """, unsafe_allow_html=True)

def show_manager_inventory_tab():
    """Display the Inventory tab with stock levels and alerts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📦 Inventory Overview")
        
        # Use the existing inventory summary but in a more compact format
        inventory_categories = [
            {"name": "Critical Stock", "count": 3, "items": ["Designer Jeans", "iPhone Cases", "Silk Scarves"], "color": "#dc3545"},
            {"name": "Low Stock", "count": 12, "items": ["Fall Jackets", "Wireless Headphones", "Boots"], "color": "#ffc107"},
            {"name": "Well Stocked", "count": 892, "items": ["Core inventory items"], "color": "#28a745"},
            {"name": "New Arrivals", "count": 24, "items": ["Winter Collection", "Holiday Items"], "color": "#6f42c1"}
        ]
        
        for category in inventory_categories:
            st.markdown(f"""
                <div class="inventory-category-card" style="border-left-color: {category['color']}">
                    <div class="category-header">
                        <span class="category-name">{category['name']}</span>
                        <span class="category-count">{category['count']}</span>
                    </div>
                    <div class="category-items">{', '.join(category['items'][:3])}</div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("📊 Detailed Inventory", use_container_width=True):
            st.switch_page("pages/inventory.py")
    
    with col2:
        st.markdown("#### 💰 Inventory Value")
        
        st.markdown("""
            <div class="inventory-value-card">
                <div class="value-metric">
                    <span class="value-label">Total Inventory Value:</span>
                    <span class="value-amount">$2.1M</span>
                </div>
                <div class="value-metric">
                    <span class="value-label">Turnover Rate:</span>
                    <span class="value-amount">4.2x/year</span>
                </div>
                <div class="value-metric">
                    <span class="value-label">Reorder Needed:</span>
                    <span class="value-amount">15 items</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📈 Department Stock Levels")
        departments = [
            {"name": "Electronics", "level": 95, "color": "#28a745"},
            {"name": "Women's Fashion", "level": 87, "color": "#ffc107"},
            {"name": "Men's Fashion", "level": 92, "color": "#28a745"},
            {"name": "Footwear", "level": 78, "color": "#ffc107"}
        ]
        
        for dept in departments:
            st.markdown(f"""
                <div class="department-stock-bar">
                    <div class="dept-name">{dept['name']}</div>
                    <div class="stock-bar">
                        <div class="stock-fill" style="width: {dept['level']}%; background-color: {dept['color']}"></div>
                    </div>
                    <div class="stock-percentage">{dept['level']}%</div>
                </div>
            """, unsafe_allow_html=True)

def show_manager_analytics_tab():
    """Display the Analytics tab with trends and insights."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Sales Trends")
        
        st.markdown("""
            <div class="analytics-card">
                <div class="analytics-metric">
                    <span class="metric-label">Week-over-Week Growth:</span>
                    <span class="metric-value positive">+12.5%</span>
                </div>
                <div class="analytics-metric">
                    <span class="metric-label">Best Performing Category:</span>
                    <span class="metric-value">Electronics (+23%)</span>
                </div>
                <div class="analytics-metric">
                    <span class="metric-label">Peak Sales Hour:</span>
                    <span class="metric-value">2:00 - 4:00 PM</span>
                </div>
                <div class="analytics-metric">
                    <span class="metric-label">Return Rate:</span>
                    <span class="metric-value">2.8% (below target)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🎯 Goals Progress")
        goals = [
            {"name": "Monthly Sales Target", "progress": 78, "target": "$450K"},
            {"name": "Customer Satisfaction", "progress": 92, "target": "4.5/5"},
            {"name": "Inventory Turnover", "progress": 85, "target": "4.5x/year"}
        ]
        
        for goal in goals:
            color = "#28a745" if goal['progress'] >= 90 else "#ffc107" if goal['progress'] >= 70 else "#dc3545"
            st.markdown(f"""
                <div class="goal-progress-card">
                    <div class="goal-name">{goal['name']}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {goal['progress']}%; background-color: {color}"></div>
                    </div>
                    <div class="goal-details">{goal['progress']}% to {goal['target']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 💡 Insights & Recommendations")
        
        insights = [
            {"title": "Optimize Staffing", "insight": "Add 1 associate during 2-4 PM peak hours", "impact": "High", "icon": "👥"},
            {"title": "Inventory Alert", "insight": "Reorder designer jeans before weekend rush", "impact": "High", "icon": "📦"},
            {"title": "Promotion Opportunity", "insight": "Electronics trending +45% - extend promotion", "impact": "Medium", "icon": "📈"},
            {"title": "Training Need", "insight": "Customer service scores dipped in Men's Fashion", "impact": "Medium", "icon": "📚"}
        ]
        
        for insight in insights:
            impact_colors = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}
            st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-header">
                        <span class="insight-icon">{insight['icon']}</span>
                        <span class="insight-title">{insight['title']}</span>
                        <span class="insight-impact" style="background-color: {impact_colors[insight['impact']]}">
                            {insight['impact']}
                        </span>
                    </div>
                    <div class="insight-text">{insight['insight']}</div>
                </div>
            """, unsafe_allow_html=True) 