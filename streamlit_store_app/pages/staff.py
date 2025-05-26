"""Staff page for the Streamlit Store App."""

import streamlit as st
from components import display_metric_card, display_alert
from utils.database import query
from components.navigation import show_nav
from components.styles import load_css

def main():
    """Main staff page."""
    # Load CSS
    load_css()
    
    # Show navigation
    show_nav()

    # Page header
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("👥 Staff Management")
        st.markdown("**Manage team schedules and staff information**")
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

    # Staff Overview with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="kpi-summary-card sales">
                <div class="kpi-icon">👥</div>
                <div class="kpi-value">12</div>
                <div class="kpi-label">Active Staff</div>
                <div class="kpi-change">Currently working</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="kpi-summary-card traffic">
                <div class="kpi-icon">🏖️</div>
                <div class="kpi-value">3</div>
                <div class="kpi-label">On Leave</div>
                <div class="kpi-change">Planned absences</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="kpi-summary-card orders">
                <div class="kpi-icon">📅</div>
                <div class="kpi-value">15</div>
                <div class="kpi-label">Scheduled Today</div>
                <div class="kpi-change">All departments</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="kpi-summary-card conversion">
                <div class="kpi-icon">⏰</div>
                <div class="kpi-value">98%</div>
                <div class="kpi-label">Attendance Rate</div>
                <div class="kpi-change positive">+2% this week</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Today's Schedule", "👤 Staff Directory", "📊 Performance", "⚠️ Alerts"])
    
    with tab1:
        show_todays_schedule()
    
    with tab2:
        show_staff_directory()
    
    with tab3:
        show_staff_performance()
    
    with tab4:
        show_staff_alerts()

def show_todays_schedule():
    """Display today's staff schedule."""
    st.markdown("### 📅 Today's Schedule")
    
    # Mock staff schedule data
    schedule = [
        {
            "name": "Sarah Chen",
            "role": "Store Associate",
            "department": "Women's Fashion",
            "shift": "8:00 AM - 4:00 PM",
            "break": "12:00 - 12:30 PM",
            "status": "present",
            "hours_worked": "4h 23m"
        },
        {
            "name": "Mike Rodriguez",
            "role": "Store Associate", 
            "department": "Electronics",
            "shift": "8:00 AM - 4:00 PM",
            "break": "12:30 - 1:00 PM",
            "status": "present",
            "hours_worked": "4h 15m"
        },
        {
            "name": "Emma Wilson",
            "role": "Customer Service Rep",
            "department": "Customer Service",
            "shift": "10:00 AM - 6:00 PM",
            "break": "2:00 - 2:30 PM",
            "status": "present",
            "hours_worked": "2h 45m"
        },
        {
            "name": "James Park",
            "role": "Visual Merchandiser",
            "department": "All Floors",
            "shift": "9:00 AM - 5:00 PM",
            "break": "1:00 - 1:30 PM",
            "status": "break",
            "hours_worked": "3h 30m"
        },
        {
            "name": "Lisa Thompson",
            "role": "Store Associate",
            "department": "Men's Fashion",
            "shift": "12:00 PM - 8:00 PM",
            "break": "4:00 - 4:30 PM",
            "status": "scheduled",
            "hours_worked": "0h 0m"
        }
    ]
    
    for staff in schedule:
        show_staff_schedule_card(staff)

def show_staff_schedule_card(staff):
    """Display a staff schedule card."""
    status_colors = {"present": "#10b981", "break": "#f59e0b", "scheduled": "#64748b", "absent": "#ef4444"}
    status_icons = {"present": "✅", "break": "☕", "scheduled": "📅", "absent": "❌"}
    
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col1:
        html_content = f"""
            <div class="staff-schedule-card">
                <div class="staff-header">
                    <span class="staff-name">{staff['name']}</span>
                    <span class="staff-status" style="color: {status_colors[staff['status']]}">
                        {status_icons[staff['status']]} {staff['status'].upper()}
                    </span>
                </div>
                <div class="staff-details">
                    <div><strong>Role:</strong> {staff['role']}</div>
                    <div><strong>Department:</strong> {staff['department']}</div>
                    <div><strong>Shift:</strong> {staff['shift']}</div>
                    <div><strong>Break:</strong> {staff['break']}</div>
                    <div><strong>Hours Worked:</strong> {staff['hours_worked']}</div>
                </div>
            </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
    with col2:
        if staff['status'] == 'scheduled':
            if st.button("Mark Present", key=f"present_{staff['name']}", use_container_width=True):
                st.success(f"{staff['name']} marked as present!")
        elif staff['status'] == 'present':
            if st.button("Start Break", key=f"break_{staff['name']}", use_container_width=True):
                st.info(f"{staff['name']} is now on break")
    
    with col3:
        if st.button("View Details", key=f"details_{staff['name']}", use_container_width=True):
            st.info(f"Detailed view for {staff['name']} would open here")
    
    st.markdown("---")

def show_staff_directory():
    """Display staff directory."""
    st.markdown("### 👤 Staff Directory")
    st.info("Staff directory with contact information and roles would be displayed here.")

def show_staff_performance():
    """Display staff performance metrics."""
    st.markdown("### 📊 Performance Metrics")
    st.info("Staff performance analytics and metrics would be displayed here.")

def show_staff_alerts():
    """Display staff-related alerts."""
    st.markdown("### ⚠️ Staff Alerts")
    
    alerts = [
        {"type": "Late Arrival", "staff": "John Smith", "time": "15 minutes", "severity": "medium"},
        {"type": "Overtime Alert", "staff": "Sarah Chen", "hours": "42/40", "severity": "low"},
        {"type": "Break Overdue", "staff": "Mike Rodriguez", "overdue": "30 minutes", "severity": "high"}
    ]
    
    for alert in alerts:
        show_staff_alert_card(alert)

def show_staff_alert_card(alert):
    """Display a staff alert card."""
    severity_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"}
    
    html_content = f"""
        <div class="alert-card" style="border-left-color: {severity_colors[alert['severity']]}">
            <div class="alert-type">{alert['type']} - {alert['staff']}</div>
            <div class="alert-details">
                {alert.get('time', alert.get('hours', alert.get('overdue', '')))}
            </div>
        </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

# Add custom CSS for staff components
st.markdown("""
    <style>
    .staff-schedule-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-left: 5px solid #3b82f6;
        margin-bottom: 1rem;
        border: 1px solid rgba(226, 232, 240, 0.6);
        transition: all 0.3s ease;
    }
    
    .staff-schedule-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.12);
    }
    
    .staff-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .staff-name {
        font-weight: 700;
        font-size: 1.25rem;
        color: #1e293b;
        line-height: 1.3;
    }
    
    .staff-status {
        font-weight: 600;
        font-size: 1rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        background: rgba(255,255,255,0.9);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .staff-details {
        color: #475569;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .staff-details div {
        margin-bottom: 0.5rem;
        padding: 0.25rem 0;
    }
    
    .staff-details strong {
        color: #334155;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 