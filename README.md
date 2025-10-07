# 🚀 SAP Integration Suite RAG Pipeline

A comprehensive Retrieval-Augmented Generation (RAG) pipeline for SAP Integration Suite iFlow processing, blueprint generation, and package creation.

## ✨ Features

- **🧠 Intelligent Blueprint Generation**: AI-powered creation of SAP CPI integration blueprints
- **📦 iFlow Package Processing**: Automated extraction and analysis of iFlow packages
- **🔍 Vector Search**: Semantic search across integration components and assets
- **🤖 Multi-AI Integration**: OpenAI GPT-4, Google Gemini, and custom models
- **🗄️ Knowledge Graph**: Neo4j-powered relationship mapping and optimization
- **☁️ Cloud Ready**: SAP BTP Cloud Foundry deployment support
- **🔗 n8n Integration**: RESTful API endpoints for workflow automation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  RAG Pipeline    │───▶│  Blueprint      │
│                 │    │                  │    │  Generation     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   iFlow Package │───▶│  Processing      │───▶│  Package        │
│   Upload        │    │  Pipeline        │    │  Generation     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Supabase        │
                       │  Vector Store    │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Supabase project
- Neo4j database (optional)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/DheepLearningITR/RAG-2.git
cd RAG-2
```

2. **Set up environment variables**:
```bash
cp env.example .env
# Edit .env with your API keys
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the pipeline**:
```bash
cd "RAG/Instruction generation"
python generate_blueprint.py "Create an employee sync integration"
```

## 📁 Project Structure

```
RAG-2/
├── 📁 RAG/
│   ├── 📁 Instruction generation/     # Blueprint generation
│   ├── 📁 package generation/         # Package creation
│   └── unified_rag_pipeline.py       # Main pipeline
├── 📁 Injection pipeline/             # iFlow processing API
├── 📁 Iflow Ingestion pipeline/       # N8N workflow
├── 📄 env.example                     # Environment template
└── 📄 README.md                       # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | ✅ |
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | ✅ |
| `NEO4J_URI` | Neo4j database URI | ❌ |
| `NEO4J_USERNAME` | Neo4j username | ❌ |
| `NEO4J_PASSWORD` | Neo4j password | ❌ |
| `GEMINI_API_KEY` | Google Gemini API key | ❌ |

### Database Schema

The pipeline uses a 4-table Supabase schema:

- **`iflow_packages`**: Package metadata and full XML
- **`iflow_components`**: Individual BPMN components
- **`iflow_flows`**: Flow connections (sequence + message flows)
- **`iflow_assets`**: Scripts, schemas, mappings, properties

## 🎯 Usage Examples

### Blueprint Generation

```python
from RAG.Instruction_generation.enhanced_blueprint_generator import EnhancedBlueprintGenerator

generator = EnhancedBlueprintGenerator()
blueprint = generator.generate_perfect_blueprint(
    "Create a real-time employee data synchronization between SAP S/4HANA and SuccessFactors"
)
```

### iFlow Processing

```python
from Injection_pipeline.app import IFlowPackageProcessor

processor = IFlowPackageProcessor()
result = processor.process_zip_package("path/to/iflow.zip")
```

### Package Generation

```python
from RAG.package_generation.complete_iflow_generator import CompleteIFlowGenerator

generator = CompleteIFlowGenerator()
solution = generator.generate_complete_solution(
    "Employee master data validation and sync"
)
```

## 🌐 API Endpoints

### Injection Pipeline API

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /process-iflow` - Process iFlow ZIP package
- `GET /status/<package_id>` - Get processing status

### Example Usage

```bash
# Process an iFlow package
curl -X POST -F 'file=@your_iflow.zip' \
  https://your-api-url.com/process-iflow

# Check processing status
curl https://your-api-url.com/status/package-id
```

## 🔒 Security

- **Environment Variables**: All sensitive data is stored in environment variables
- **API Key Protection**: No hardcoded secrets in the codebase
- **Input Validation**: Comprehensive validation for all inputs
- **Error Handling**: Secure error messages without information leakage

## 🚀 Deployment

### Local Development

```bash
# RAG Pipeline
cd "RAG/Instruction generation"
python generate_blueprint.py

# Injection Pipeline
cd "Injection pipeline"
python app.py
```

### Cloud Foundry (SAP BTP)

```bash
cd "Injection pipeline"
cf push
```

### Docker

```bash
docker build -t rag-pipeline .
docker run -p 5000:5000 --env-file .env rag-pipeline
```

## 📊 Performance

- **Processing Time**: 5-10 minutes for typical iFlow packages
- **Memory Usage**: 512MB-1GB depending on package size
- **Concurrent Requests**: Supports multiple simultaneous processing
- **Scalability**: Horizontal scaling with load balancers

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Security checks
bandit -r .
safety check

# Code quality
flake8 .
black .
```

## 📈 Monitoring

- **Health Checks**: Built-in health monitoring endpoints
- **Logging**: Comprehensive logging with structured output
- **Metrics**: Processing time and success rate tracking
- **Alerts**: Configurable alerts for failures and performance issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See individual module README files for detailed setup instructions
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Security**: Report security issues privately

## 🙏 Acknowledgments

- OpenAI for GPT models
- Supabase for database services
- Neo4j for graph database
- SAP for Integration Suite platform
- The open-source community for various libraries and tools

---

**⚠️ Important**: This project contains AI-generated code and should be thoroughly tested before use in production environments.
