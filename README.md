# CloudCostAI: Multi-Cloud Cost Optimization & Forecasting System

A modular FinOps dashboard and automation suite that helps organizations optimize cloud costs across AWS, GCP, and Azure.

![CloudCostAI Dashboard](https://img.shields.io/badge/CloudCostAI-Dashboard-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Multi-Cloud Billing Integration**: Pull and normalize cost data from AWS, GCP, and Azure
- **Idle Resource Detection**: Identify underutilized resources across cloud platforms
- **AI-Powered Forecasting**: Predict future cloud spend using machine learning
- **Cost Optimization Recommendations**: Get actionable insights to reduce cloud costs
- **Interactive Dashboard**: Visualize spending patterns and optimization opportunities

## Tech Stack

- **Cloud Billing APIs**: Boto3 (AWS), google-cloud-billing, azure-mgmt-costmanagement
- **Data Processing**: Python, Pandas, NumPy, SQLAlchemy
- **AI Forecasting**: Facebook Prophet, Scikit-learn
- **Visualization**: Streamlit, Plotly
- **Automation**: GitHub Actions
- **Storage**: SQLite (for PoC)

## Screenshots

![Dashboard Preview](https://via.placeholder.com/800x450.png?text=CloudCostAI+Dashboard)

## Getting Started

### Prerequisites

- Python 3.8+
- AWS, GCP, and/or Azure accounts with billing access
- Appropriate API credentials configured

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cloudcostai-finops-dashboard.git
cd cloudcostai-finops-dashboard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file and edit it with your credentials:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your cloud provider credentials:
   ```
   # AWS Configuration
   AWS_PROFILE=default
   AWS_REGION=us-east-1

   # GCP Configuration
   GCP_PROJECT_ID=your-gcp-project-id
   GCP_BILLING_ACCOUNT=your-billing-account-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

   # Azure Configuration
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   ```

### Running the Application

#### Using Python directly:

```bash
# Run the dashboard
python app.py dashboard

# Collect cost data
python app.py collect --aws --gcp --azure

# Analyze and find idle resources
python app.py analyze --idle --report
```

#### Using Docker:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the dashboard at http://localhost:8501
```

## Project Structure

```
cloudcostai-finops-dashboard/
├── data/                      # Sample and processed data
├── notebooks/                 # Jupyter notebooks for analysis and model development
├── src/                       # Source code
│   ├── collectors/            # Cloud billing data collectors
│   ├── analyzers/             # Cost analysis and forecasting modules
│   ├── dashboards/            # Streamlit dashboard code
│   └── utils/                 # Helper functions and utilities
├── reports/                   # Generated cost reports
├── .github/workflows/         # GitHub Actions for automation
├── app.py                     # Main application entry point
├── config.py                  # Configuration settings
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Deployment Options

### Local Development

```bash
streamlit run src/dashboards/streamlit_app.py
```

### Docker Deployment

```bash
docker-compose up -d
```

### Cloud Deployment

The application can be deployed to various cloud platforms:

- **AWS**: Use AWS App Runner or ECS
- **GCP**: Use Cloud Run or GKE
- **Azure**: Use Azure Container Instances or AKS

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.# FinOpsAI-Platform
