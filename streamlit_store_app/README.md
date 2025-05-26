# Store Companion

A Streamlit-based retail store management application with AI assistance.

## Features

- Multi-store management system
- Role-based access control (Store Associate/Manager)
- Real-time inventory tracking
- Order management
- Staff management
- AI-powered chat assistance

## Project Structure

```
streamlit_store_app/
├── app.py                 # Main application entry point
├── config.yaml           # Centralized configuration
├── components/          # Reusable UI components
│   ├── chat.py         # AI chat widget
│   ├── metrics.py      # Store metrics display
│   ├── navigation.py   # Navigation components
│   └── styles.py       # UI styling utilities
├── pages/              # Application pages
│   ├── 1_📦_Orders.py
│   ├── 2_📊_Inventory.py
│   └── 3_👥_Staff.py
├── utils/              # Utility functions
│   ├── config.py       # Configuration management
│   ├── database.py     # Database operations
│   └── model_serving.py # AI model integration
└── tests/              # Test suite
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration

All configuration is centralized in `config.yaml`:

- Application settings
- Store information
- User roles
- Chat interface settings
- Model serving configuration
- Database settings

## Development

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

## Deployment

The application can be deployed using Docker:

```bash
docker build -t store-companion .
docker run -p 8501:8501 store-companion
```

## License

MIT License 