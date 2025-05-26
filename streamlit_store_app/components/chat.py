"""Chat message container component for the Streamlit Store App."""

import logging
import streamlit as st
import time
from utils.model_serving import (
    query_endpoint,
    get_serving_endpoint
)
from utils.config import load_config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_config():
    """Load model configuration from config.yaml."""
    
    config = load_config()
    return config.get('model', {})

def initialize_chat_state():
    """Initialize chat state in session."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_status" not in st.session_state:
        st.session_state.chat_status = "available"  # available, typing, processing, error
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()

def update_chat_status(status):
    """Update the chat status."""
    st.session_state.chat_status = status
    st.session_state.last_activity = time.time()

def get_status_indicator():
    """Get the status indicator based on current chat status."""
    status_indicators = {
        "available": {"icon": "🟢", "text": "AI Assistant is ready", "color": "#28a745"},
        "typing": {"icon": "💭", "text": "AI is thinking...", "color": "#007bff"},
        "processing": {"icon": "⚡", "text": "Processing your request...", "color": "#ffc107"},
        "error": {"icon": "🔴", "text": "Connection error", "color": "#dc3545"}
    }
    return status_indicators.get(st.session_state.chat_status, status_indicators["available"])

def show_chat_status():
    """Display the current chat status."""
    status = get_status_indicator()
    
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        padding: 0.5rem;
        background: rgba(0,0,0,0.05);
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    ">
        <span style="margin-right: 0.5rem; font-size: 1.1rem;">{status['icon']}</span>
        <span style="color: {status['color']}; font-weight: 500;">{status['text']}</span>
    </div>
    """, unsafe_allow_html=True)

def display_chat_message(message):
    """Display a single chat message."""
    with st.chat_message(message["role"]):
        st.write(message["content"])

def show_chat_messages():
    """Display all chat messages in the container."""
    for message in st.session_state.messages:
        display_chat_message(message)

def add_message_to_chat(role, content):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content})
    update_chat_status("available")

def show_typing_indicator():
    """Show a typing indicator while AI is processing."""
    with st.chat_message("assistant"):
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            color: #666;
            font-style: italic;
        ">
            <div style="
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #007bff;
                margin-right: 4px;
                animation: typing 1.4s infinite ease-in-out;
            "></div>
            <div style="
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #007bff;
                margin-right: 4px;
                animation: typing 1.4s infinite ease-in-out 0.2s;
            "></div>
            <div style="
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #007bff;
                margin-right: 8px;
                animation: typing 1.4s infinite ease-in-out 0.4s;
            "></div>
            AI is typing...
        </div>
        
        <style>
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.5;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }
        </style>
        """, unsafe_allow_html=True)

def get_model_response(messages, model_config):
    """Get response from the AI model."""
    # Prepare model parameters
    optional_params = {
        'temperature': model_config.get('temperature'),
        'max_tokens': model_config.get('max_tokens'),
        'stop': model_config.get('stop'),
        'n': model_config.get('n'),
        'stream': model_config.get('stream')
    }
    # Remove None values
    optional_params = {k: v for k, v in optional_params.items() if v is not None}
    
    try:
        # Update status to processing
        update_chat_status("processing")
        
        # Get endpoint name
        endpoint = get_serving_endpoint()
        
        # Query the model with configuration from config.yaml
        response_messages, request_id = query_endpoint(
            endpoint_name=endpoint,
            messages=messages,
            **optional_params
        )
        
        # Get the last message from the response
        if response_messages and len(response_messages) > 0:
            update_chat_status("available")
            return response_messages[-1].get("content", "")
        else:
            update_chat_status("error")
            return None
    except Exception as e:
        logger.exception("Failed to get AI response")
        update_chat_status("error")
        raise e

def show_chat_container(config):
    """Display the chat message container."""
    # Initialize chat state
    initialize_chat_state()
    
    # Load model configuration
    model_config = st.session_state.config.get("model", {})
    
    # Chat message container with fixed layout
    st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 500px;
        max-height: 500px;
    }
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e0e0e0;
        max-height: 400px;
    }
    .chat-input-area {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem 0 0 0;
        border-top: 1px solid #e0e0e0;
        z-index: 100;
    }
    /* Ensure chat input stays visible */
    .stChatInput {
        position: sticky !important;
        bottom: 0 !important;
        background: white !important;
        z-index: 101 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        # Show chat status
        show_chat_status()
        
        # Scrollable messages area
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        st.markdown("#### Chat History")
        
        # Display all existing messages
        if st.session_state.messages:
            for message in st.session_state.messages:
                display_chat_message(message)
        else:
            st.info("👋 Start a conversation! Ask me anything about the store.")
        
        # Handle pending AI response if there's an unprocessed user message
        if (len(st.session_state.messages) > 0 and 
            st.session_state.messages[-1]["role"] == "user" and
            st.session_state.get("waiting_for_response", False)):
            
            # Show typing indicator
            with st.chat_message("assistant"):
                with st.spinner("AI is thinking..."):
                    try:
                        # Get AI response
                        response = get_model_response(st.session_state.messages, model_config)
                        
                        if response:
                            # Show response
                            st.write(response)
                            # Add to history
                            add_message_to_chat("assistant", response)
                            # Clear waiting flag
                            st.session_state.waiting_for_response = False
                            # Rerun to refresh display
                            st.rerun()
                        else:
                            update_chat_status("error")
                            st.error("Received empty response from the model.")
                            st.session_state.waiting_for_response = False
                    except Exception as e:
                        update_chat_status("error")
                        st.error("Sorry, I couldn't process your request. Please try again.")
                        st.session_state.waiting_for_response = False
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fixed input area at bottom
        st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
        st.markdown("#### Ask a Question")
        placeholder_text = config.get("placeholder", "How can I help you today?")
        
        # Handle new user input
        user_input = st.chat_input(placeholder=placeholder_text)
        
        if user_input:
            # Update status to typing
            update_chat_status("typing")
            
            # Add user message to history immediately
            add_message_to_chat("user", user_input)
            
            # Set flag to indicate we're waiting for AI response
            st.session_state.waiting_for_response = True
            
            # Rerun to show the user message and trigger AI response
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Backward compatibility - alias for the old function name
def show_chat_widget(config):
    """Display the AI chat widget (deprecated - use show_chat_container instead)."""
    return show_chat_container(config)