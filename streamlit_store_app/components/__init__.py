"""Components package for the retail store app."""

from .metrics import display_metric_card, display_alert
from .styles import load_css
from .chat import show_chat_widget
from .navigation import show_nav
from .homepage import (
    show_homepage,
    show_kpi_summary, 
    show_inventory_summary,
    show_notifications_modal,
    show_manager_summary_cards,
    show_associate_homepage,
    show_persistent_chat
)

__all__ = [
    'display_metric_card',
    'display_alert', 
    'load_css',
    'show_chat_widget',
    'show_nav',
    'show_homepage',
    'show_kpi_summary',
    'show_inventory_summary', 
    'show_notifications_modal',
    'show_manager_summary_cards',
    'show_associate_homepage',
    'show_persistent_chat'
] 