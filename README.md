# Retail AI Agent

A conversational AI system for retail operations built on Databricks, providing intelligent product recommendations, inventory management, and customer service through specialized AI agents.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Databricks workspace with Unity Catalog
- Access to LLM and embedding model endpoints

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/retail-ai.git
cd retail-ai

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Configure your environment
cp model_config.yaml.template model_config.yaml
# Edit model_config.yaml with your Databricks settings
```

### Run the System

```bash
# 1. Set up data and vector search
python 01_ingest-and-transform.py
python 02_provision-vector-search.py

# 2. Develop and deploy the model
python 05_agent_as_code_driver.py
python 06_evaluate_agent.py
python 07_deploy_agent.py

# 3. Run the Streamlit store app
cd streamlit_store_app
streamlit run app.py
```

## 🤖 What It Does

The Retail AI system provides:

- **Product Recommendations**: AI-powered product suggestions based on customer preferences
- **Inventory Management**: Real-time stock tracking and automated reordering
- **Customer Service**: Natural language interface for customer inquiries
- **Store Operations**: Streamlit app for store associates and managers
- **Multi-Agent Architecture**: Specialized agents for different retail functions

## 🏗️ Architecture

The system uses a multi-agent architecture with:
- **Router Agent**: Routes queries to specialized agents
- **Product Agent**: Handles product information and recommendations
- **Inventory Agent**: Manages stock levels and availability
- **Orders Agent**: Processes order-related inquiries
- **DIY Agent**: Provides project guidance and tutorials

Built with LangGraph, LangChain, MLflow, and Databricks platform services.

## 📚 Documentation

**Complete documentation is available at: [https://your-org.github.io/retail-ai](https://your-org.github.io/retail-ai)**

### Key Resources
- [📖 Quick Start Guide](https://your-org.github.io/retail-ai/getting-started/quick-start/) - Detailed setup instructions
- [🏗️ Architecture Overview](https://your-org.github.io/retail-ai/architecture/overview/) - System design and components
- [🔧 Tools Reference](https://your-org.github.io/retail-ai/tools/overview/) - Complete tools documentation
- [🚀 Deployment Guide](https://your-org.github.io/retail-ai/deployment/production/) - Production deployment
- [🤝 Contributing](https://your-org.github.io/retail-ai/development/contributing/) - Development guidelines

### Local Documentation
```bash
# Install docs dependencies
make docs-install

# Serve docs locally
make docs-serve
# Visit http://localhost:8000
```

## 🛠️ Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy retail_ai/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

For detailed information, troubleshooting, and advanced usage, please refer to the [complete documentation](https://your-org.github.io/retail-ai).


