"""Chat widget component for the Streamlit Store App."""

import logging
import streamlit as st
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

def show_chat_widget(config):
    """Display the AI chat widget."""
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Load model configuration
    model_config = st.session_state.config.get("model", {})
    
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

    # Chat container
    with st.container():
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input(
            placeholder=config.get("placeholder", "How can I help you today?")
        ):
            # Add user message
            st.chat_message("user").write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get AI response
            with st.chat_message("assistant"):
                try:
                    # Get endpoint name
                    endpoint = get_serving_endpoint()
                    
                    # Query the model with configuration from config.yaml
                    messages, request_id = query_endpoint(
                        endpoint_name=endpoint,
                        messages=st.session_state.messages,
                        **optional_params
                    )
                    
                    # Get the last message from the response
                    if messages and len(messages) > 0:
                        response = messages[-1].get("content", "")
                        st.write(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.error("Received empty response from the model.")
                except Exception as e:
                    logger.exception("Failed to get AI response")
                    st.error("Sorry, I couldn't process your request. Please try again.")