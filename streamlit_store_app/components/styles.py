"""CSS styles for the Streamlit Store App."""

import streamlit as st

def load_css():
    """Load custom CSS styles for the application."""
    st.markdown("""
        <style>
        /* Global Styles */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background-color: #f8fafc;
        }
        
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Enhanced Typography with larger fonts */
        h1 {
            color: #1e293b;
            font-weight: 800;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        h2 {
            color: #334155;
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 0.75rem;
        }
        
        h3 {
            color: #334155;
            font-weight: 700;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        h4 {
            color: #475569;
            font-weight: 600;
            font-size: 1.25rem;
            margin-bottom: 0.75rem;
        }
        
        .stMarkdown p {
            font-size: 1rem;
            line-height: 1.6;
            color: #64748b;
        }
        
        /* Enhanced KPI Summary Cards */
        .kpi-summary-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            text-align: center;
            border: 1px solid rgba(226, 232, 240, 0.6);
        }
        
        .kpi-summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .kpi-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .kpi-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .kpi-label {
            font-size: 1.25rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .kpi-change {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
        }
        
        .kpi-change.positive {
            color: #10b981;
            font-weight: 600;
        }
        
        /* Enhanced Inventory Summary Cards */
        .inventory-summary-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            text-align: center;
            border: 1px solid rgba(226, 232, 240, 0.6);
        }
        
        .inventory-summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .inventory-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .inventory-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .inventory-label {
            font-size: 1.25rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .inventory-detail {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
        }
        
        /* Enhanced Summary Cards for Navigation */
        .summary-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            border: 1px solid rgba(226, 232, 240, 0.6);
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .summary-card.team {
            border-left-color: #10b981;
        }
        
        .summary-card.inventory {
            border-left-color: #8b5cf6;
        }
        
        .summary-card.tasks {
            border-left-color: #ef4444;
        }
        
        .summary-card.schedule {
            border-left-color: #f59e0b;
        }
        
        .summary-card.products {
            border-left-color: #06b6d4;
        }
        
        .summary-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1.25rem;
            gap: 1rem;
        }
        
        .stat-item {
            text-align: center;
            flex: 1;
            padding: 0.75rem;
            background: rgba(248, 250, 252, 0.8);
            border-radius: 8px;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            display: block;
            margin-bottom: 0.25rem;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .summary-preview {
            font-size: 1rem;
            color: #475569;
            line-height: 1.6;
            border-top: 2px solid #f1f5f9;
            padding-top: 0.75rem;
        }
        
        /* Enhanced Notification Modal Styles */
        .notification-item {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            border-left: 4px solid;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .notification-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        
        .notification-item.urgent {
            border-left-color: #ef4444;
        }
        
        .notification-item.important {
            border-left-color: #f59e0b;
        }
        
        .notification-message {
            font-size: 1rem;
            color: #334155;
            font-weight: 500;
            line-height: 1.5;
            margin-bottom: 0.5rem;
        }
        
        .notification-time {
            font-size: 0.875rem;
            color: #64748b;
            font-weight: 500;
        }
        
        /* Homepage Tab Content Styling */
        .quick-status-bar {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .status-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            border-left: 4px solid;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        
        .status-card.shift {
            border-left-color: #10b981;
        }
        
        .status-card.tasks {
            border-left-color: #3b82f6;
        }
        
        .status-card.inventory {
            border-left-color: #f59e0b;
        }
        
        .status-card.notifications {
            border-left-color: #ef4444;
        }
        
        .status-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .status-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.25rem;
            display: block;
        }
        
        .status-label {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
        }
        
        /* Task and Work Item Styling */
        .task-card, .work-item-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #3b82f6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .task-card:hover, .work-item-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .task-header, .work-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f1f5f9;
        }
        
        .task-title, .work-item-title {
            font-weight: 700;
            font-size: 1.25rem;
            color: #1e293b;
            line-height: 1.3;
        }
        
        .task-priority, .work-item-status {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .task-details, .work-item-details {
            color: #475569;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        .task-details div, .work-item-details div {
            margin-bottom: 0.5rem;
            padding: 0.25rem 0;
        }
        
        .task-details strong, .work-item-details strong {
            color: #334155;
            font-weight: 600;
        }
        
        /* Enhanced Team Member Cards */
        .team-member-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            border-left: 4px solid #10b981;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .team-member-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        
        .member-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #f1f5f9;
        }
        
        .member-name {
            font-weight: 700;
            font-size: 1.125rem;
            color: #1e293b;
        }
        
        .member-status {
            font-weight: 600;
            font-size: 1rem;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            background: rgba(255,255,255,0.9);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .member-details {
            color: #64748b;
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Enhanced Analytics and Metrics Cards */
        .team-metrics-card, .analytics-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #8b5cf6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            margin-bottom: 1rem;
        }
        
        .team-metric, .analytics-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f1f5f9;
        }
        
        .team-metric:last-child, .analytics-metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #64748b;
            font-weight: 600;
            font-size: 1rem;
        }
        
        .metric-value {
            font-weight: 700;
            color: #1e293b;
            font-size: 1.125rem;
        }
        
        .metric-value.positive {
            color: #10b981;
        }
        
        /* Enhanced Inventory Category Cards */
        .inventory-category-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            border-left: 4px solid;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .inventory-category-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        
        .category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        
        .category-name {
            font-weight: 700;
            font-size: 1.125rem;
            color: #1e293b;
        }
        
        .category-count {
            font-weight: 700;
            font-size: 1.25rem;
            color: #3b82f6;
        }
        
        .category-items {
            color: #64748b;
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Button Styles */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }
        
        /* Existing Metric Card Styles (for backward compatibility) */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .metric-card h3 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: bold;
        }
        
        .metric-card p {
            margin: 0.5rem 0 0 0;
            font-size: 1rem;
            opacity: 0.9;
        }
        
        /* Alert Styles */
        .alert-item {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            color: #0c5460;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }
        
        /* Legacy KPI Dashboard Styles */
        .kpi-card {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            border-left: 4px solid;
        }
        
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .kpi-card.sales {
            border-left-color: #28a745;
        }
        
        .kpi-card.orders {
            border-left-color: #007bff;
        }
        
        .kpi-card.staff {
            border-left-color: #6f42c1;
        }
        
        .kpi-card.inventory {
            border-left-color: #fd7e14;
        }
        
        .kpi-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .kpi-title {
            font-weight: 600;
            color: #495057;
            font-size: 0.9rem;
        }
        
        /* Chat Widget Styles */
        .chat-widget-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #007bff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
            z-index: 1000;
            transition: all 0.3s ease;
        }
        
        .chat-widget-container:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0,123,255,0.4);
        }
        
        .chat-icon {
            color: white;
            font-size: 24px;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .kpi-value, .inventory-value {
                font-size: 1.5rem;
            }
            
            .stat-value {
                font-size: 1rem;
            }
            
            .summary-card, .kpi-summary-card, .inventory-summary-card {
                margin-bottom: 0.75rem;
            }
            
            .main .block-container {
                padding-top: 0.5rem;
            }
        }
        
        /* Hide Streamlit elements for cleaner look */
        .stDeployButton {
            display: none;
        }
        
        header[data-testid="stHeader"] {
            display: none;
        }
        
        .stMainBlockContainer {
            padding-top: 1rem;
        }
        
        /* Quick status cards for associate homepage */
        .quick-status-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            text-align: center;
            border: 1px solid rgba(226, 232, 240, 0.6);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .quick-status-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .quick-status-card .status-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .quick-status-card .status-text {
            font-size: 2.25rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            display: block;
            line-height: 1.2;
        }
        
        .quick-status-card .status-detail {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Priority task preview cards */
        .priority-task-preview {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .task-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .task-preview-title {
            font-weight: 600;
            color: #212529;
            font-size: 1rem;
        }
        
        .task-preview-type {
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .task-preview-details {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Current assignment card */
        .current-assignment-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #6f42c1;
        }
        
        .assignment-department {
            font-weight: 600;
            color: #212529;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .assignment-details {
            color: #6c757d;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .assignment-details div {
            margin-bottom: 0.25rem;
        }
        
        /* Shift detail card */
        .shift-detail-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .shift-time-info {
            margin-bottom: 1rem;
        }
        
        .shift-current-time {
            font-size: 2rem;
            font-weight: bold;
            color: #212529;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .shift-progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            margin-bottom: 0.5rem;
            overflow: hidden;
        }
        
        .shift-progress-fill {
            background: linear-gradient(90deg, #007bff, #28a745);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .shift-progress-text {
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .shift-details {
            color: #495057;
            line-height: 1.5;
        }
        
        .shift-details div {
            margin-bottom: 0.25rem;
        }
        
        /* Week overview card */
        .week-overview-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
        }
        
        .week-stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .week-stat {
            text-align: center;
        }
        
        .week-stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #212529;
            display: block;
            margin-bottom: 0.25rem;
        }
        
        .week-stat-label {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Promotion preview cards */
        .promo-preview-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #dc3545;
        }
        
        .promo-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .promo-preview-name {
            font-weight: 600;
            color: #212529;
        }
        
        .promo-preview-discount {
            background: #dc3545;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .promo-preview-ends {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* New item preview */
        .new-item-preview {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-left: 3px solid #28a745;
        }
        
        .new-item-name {
            font-weight: 600;
            color: #212529;
            margin-bottom: 0.25rem;
        }
        
        .new-item-details {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Performance overview card */
        .performance-overview-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #6f42c1;
        }
        
        .performance-score {
            text-align: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .performance-score-value {
            font-size: 3rem;
            font-weight: bold;
            color: #6f42c1;
            display: block;
            margin-bottom: 0.25rem;
        }
        
        .performance-score-label {
            color: #6c757d;
            font-size: 1rem;
        }
        
        .performance-metrics {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .performance-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #f8f9fa;
        }
        
        .performance-metric:last-child {
            border-bottom: none;
        }
        
        /* Goals card */
        .goals-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #ffc107;
        }
        
        .goal-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f8f9fa;
        }
        
        .goal-item:last-child {
            border-bottom: none;
        }
        
        .goal-item.completed .goal-icon {
            color: #28a745;
        }
        
        .goal-item.in-progress .goal-icon {
            color: #007bff;
        }
        
        .goal-item.pending .goal-icon {
            color: #6c757d;
        }
        
        .goal-text {
            color: #495057;
            font-weight: 500;
        }
        
        .goal-item.completed .goal-text {
            text-decoration: line-through;
            color: #6c757d;
        }
        
        /* Enhanced Manager Status Cards - Clean styling without colored borders */
        .manager-status-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            text-align: center;
            border: 1px solid rgba(226, 232, 240, 0.6);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .manager-status-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .manager-status-card .status-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .manager-status-card .status-text {
            font-size: 2.25rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            display: block;
            line-height: 1.2;
        }
        
        .manager-status-card .status-detail {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Manager dashboard cards */
        .manager-dashboard-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .dashboard-metrics {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .dashboard-metric {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f8f9fa;
        }
        
        .dashboard-metric:last-child {
            border-bottom: none;
        }
        
        .metric-trend.positive {
            color: #28a745;
            font-weight: 500;
        }
        
        /* Priority alert cards */
        .priority-alert-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }
        
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .alert-type {
            font-weight: 600;
            color: #212529;
        }
        
        .alert-severity {
            font-size: 0.8rem;
            font-weight: 500;
            color: #6c757d;
        }
        
        .alert-message {
            color: #495057;
            margin-bottom: 0.5rem;
        }
        
        .alert-action {
            color: #007bff;
            font-weight: 500;
            font-style: italic;
        }
        
        /* Operation preview cards */
        .operation-preview-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #6f42c1;
        }
        
        .operation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .operation-task {
            font-weight: 600;
            color: #212529;
        }
        
        .operation-time {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .operation-details {
            color: #495057;
            font-size: 0.9rem;
        }
        
        /* Store hours card */
        .store-hours-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
        }
        
        .hours-today {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        
        .hours-label {
            font-weight: 600;
            color: #212529;
        }
        
        .hours-time {
            color: #495057;
        }
        
        .hours-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-open {
            font-weight: 500;
            color: #28a745;
        }
        
        .hours-remaining {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Inventory value card */
        .inventory-value-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #6f42c1;
        }
        
        .value-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f8f9fa;
        }
        
        .value-metric:last-child {
            border-bottom: none;
        }
        
        .value-label {
            color: #6c757d;
            font-weight: 500;
        }
        
        .value-amount {
            font-weight: 600;
            color: #212529;
        }
        
        /* Department stock bars */
        .department-stock-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .dept-name {
            min-width: 120px;
            font-weight: 500;
            color: #495057;
        }
        
        .stock-bar {
            flex: 1;
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        }
        
        .stock-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .stock-percentage {
            min-width: 40px;
            text-align: right;
            font-weight: 500;
            color: #495057;
        }
        
        /* Goal progress cards */
        .goal-progress-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .goal-name {
            font-weight: 600;
            color: #212529;
            margin-bottom: 0.75rem;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            margin-bottom: 0.5rem;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .goal-details {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Insight cards */
        .insight-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #20c997;
        }
        
        .insight-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .insight-icon {
            font-size: 1.2rem;
        }
        
        .insight-title {
            font-weight: 600;
            color: #212529;
            flex: 1;
        }
        
        .insight-impact {
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .insight-text {
            color: #495057;
            line-height: 1.4;
        }
        
        /* Enhanced Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            background-color: transparent;
            border-radius: 8px;
            color: #64748b;
            font-weight: 600;
            font-size: 1rem;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white;
            color: #1e293b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Enhanced Selectbox Styling */
        .stSelectbox > div > div {
            background-color: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        /* Enhanced Success/Info Messages */
        .stSuccess, .stInfo, .stWarning, .stError {
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            padding: 1rem;
        }
        
        /* Enhanced Column Styling */
        .stColumns > div {
            padding: 0.5rem;
        }
        
        /* Additional Homepage Component Styling */
        
        /* Enhanced Quick Status Cards - Clean styling without colored borders */
        .quick-status-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            text-align: center;
            border: 1px solid rgba(226, 232, 240, 0.6);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .quick-status-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .quick-status-card .status-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .quick-status-card .status-text {
            font-size: 2.25rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            display: block;
            line-height: 1.2;
        }
        
        .quick-status-card .status-detail {
            font-size: 1rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Enhanced Priority Task Preview Cards - Matching daily_operations styling */
        .priority-task-preview {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #3b82f6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .priority-task-preview:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .priority-task-preview .task-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f1f5f9;
        }
        
        .priority-task-preview .task-preview-title {
            font-weight: 700;
            color: #1e293b;
            font-size: 1.25rem;
            line-height: 1.3;
        }
        
        .priority-task-preview .task-preview-type {
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .priority-task-preview .task-preview-details {
            color: #475569;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        /* Enhanced Current Assignment Card - Matching daily_operations styling */
        .current-assignment-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #8b5cf6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .current-assignment-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .current-assignment-card .assignment-department {
            font-weight: 700;
            color: #1e293b;
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f1f5f9;
            line-height: 1.3;
        }
        
        .current-assignment-card .assignment-details {
            color: #475569;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        .current-assignment-card .assignment-details div {
            margin-bottom: 0.5rem;
            padding: 0.25rem 0;
        }
        
        .current-assignment-card .assignment-details strong {
            color: #334155;
            font-weight: 600;
        }
        
        /* Enhanced Shift Detail Card - Matching daily_operations styling */
        .shift-detail-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #3b82f6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .shift-detail-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .shift-detail-card .shift-time-info {
            margin-bottom: 1.5rem;
        }
        
        .shift-detail-card .shift-current-time {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin-bottom: 1rem;
            line-height: 1.2;
        }
        
        .shift-detail-card .shift-progress-bar {
            background: #e2e8f0;
            border-radius: 12px;
            height: 12px;
            margin-bottom: 0.75rem;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .shift-detail-card .shift-progress-fill {
            background: linear-gradient(90deg, #3b82f6, #10b981);
            height: 100%;
            border-radius: 12px;
            transition: width 0.3s ease;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        
        .shift-detail-card .shift-progress-text {
            text-align: center;
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
        }
        
        .shift-detail-card .shift-details {
            color: #475569;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        .shift-detail-card .shift-details div {
            margin-bottom: 0.5rem;
            padding: 0.25rem 0;
        }
        
        .shift-detail-card .shift-details strong {
            color: #334155;
            font-weight: 600;
        }
        
        /* Enhanced Week Overview Card - Matching daily_operations styling */
        .week-overview-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #10b981;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .week-overview-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .week-overview-card .week-stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        
        .week-overview-card .week-stat {
            text-align: center;
            padding: 1rem;
            background: rgba(248, 250, 252, 0.8);
            border-radius: 12px;
            border: 1px solid rgba(226, 232, 240, 0.6);
        }
        
        .week-overview-card .week-stat-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: #1e293b;
            display: block;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .week-overview-card .week-stat-label {
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Enhanced Promotion Preview Cards - Matching daily_operations styling */
        .promo-preview-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #ef4444;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .promo-preview-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .promo-preview-card .promo-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f1f5f9;
        }
        
        .promo-preview-card .promo-preview-name {
            font-weight: 700;
            color: #1e293b;
            font-size: 1.25rem;
            line-height: 1.3;
        }
        
        .promo-preview-card .promo-preview-discount {
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
        }
        
        .promo-preview-card .promo-preview-ends {
            color: #475569;
            font-size: 1rem;
            font-weight: 500;
            line-height: 1.6;
        }
        
        /* Enhanced New Item Preview - Matching daily_operations styling */
        .new-item-preview {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 0.75rem;
            border-left: 4px solid #10b981;
            border: 1px solid rgba(226, 232, 240, 0.6);
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }
        
        .new-item-preview:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        
        .new-item-preview .new-item-name {
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
            font-size: 1.125rem;
            line-height: 1.3;
        }
        
        .new-item-preview .new-item-details {
            color: #475569;
            font-size: 1rem;
            font-weight: 500;
            line-height: 1.6;
        }
        
        /* Enhanced Performance Overview Card - Matching daily_operations styling */
        .performance-overview-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #8b5cf6;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .performance-overview-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .performance-overview-card .performance-score {
            text-align: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f1f5f9;
        }
        
        .performance-overview-card .performance-score-value {
            font-size: 3.5rem;
            font-weight: 700;
            color: #8b5cf6;
            display: block;
            margin-bottom: 0.5rem;
            line-height: 1.1;
        }
        
        .performance-overview-card .performance-score-label {
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .performance-overview-card .performance-metrics {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .performance-overview-card .performance-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .performance-overview-card .performance-metric:last-child {
            border-bottom: none;
        }
        
        .performance-overview-card .performance-metric .metric-label {
            color: #64748b;
            font-weight: 600;
            font-size: 1rem;
        }
        
        .performance-overview-card .performance-metric .metric-value {
            font-weight: 700;
            color: #1e293b;
            font-size: 1.125rem;
        }
        
        /* Enhanced Goals Card - Matching daily_operations styling */
        .goals-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            border-left: 5px solid #f59e0b;
            border: 1px solid rgba(226, 232, 240, 0.6);
            transition: all 0.3s ease;
        }
        
        .goals-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }
        
        .goals-card .goal-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .goals-card .goal-item:last-child {
            border-bottom: none;
        }
        
        .goals-card .goal-item.completed .goal-icon {
            color: #10b981;
            font-size: 1.25rem;
        }
        
        .goals-card .goal-item.in-progress .goal-icon {
            color: #3b82f6;
            font-size: 1.25rem;
        }
        
        .goals-card .goal-item.pending .goal-icon {
            color: #64748b;
            font-size: 1.25rem;
        }
        
        .goals-card .goal-text {
            color: #475569;
            font-weight: 500;
            font-size: 1rem;
            line-height: 1.6;
        }
        
        .goals-card .goal-item.completed .goal-text {
            text-decoration: line-through;
            color: #64748b;
        }
        </style>
    """, unsafe_allow_html=True) 