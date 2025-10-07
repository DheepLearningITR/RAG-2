# 🚀 iFlow Package Processor API for Cloud Foundry

A production-ready Flask API for processing SAP Integration Suite iFlow packages for RAG (Retrieval-Augmented Generation) applications, designed for SAP BTP Cloud Foundry deployment and n8n integration.

## ✨ Features

- **☁️ Cloud-Ready**: Optimized for SAP BTP Cloud Foundry deployment
- **🔗 n8n Integration**: RESTful API endpoints for workflow automation
- **📦 ZIP Package Processing**: Automatically extracts and processes iFlow ZIP packages
- **🧩 Component-Level Chunking**: Intelligent BPMN component extraction with relationships
- **🤖 AI-Enhanced Descriptions**: Uses GPT-4o-mini to generate detailed component descriptions
- **🔍 Vector Embeddings**: Creates 1536-dimensional embeddings using OpenAI text-embedding-3-small
- **🗄️ Supabase Integration**: Stores processed data in structured 4-table schema
- **📄 Asset Processing**: Handles Groovy scripts, XSLT, XSD, JSON, and other iFlow assets
- **🏥 Health Monitoring**: Built-in health check endpoints for Cloud Foundry
- **🛡️ Production Ready**: Comprehensive error handling and logging

## 🚀 Quick Deployment to SAP BTP Cloud Foundry

### Prerequisites
- SAP BTP Trial Account with Cloud Foundry enabled
- Cloud Foundry CLI installed
- OpenAI API key
- Supabase project with service role key

### Environment Setup

1. **Copy Environment Template**:
```bash
cd "Injection pipeline"
cp env.example .env
```

2. **Configure Environment Variables**:
Edit the `.env` file with your actual values:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
```

### Deployment Steps

1. **Install Cloud Foundry CLI**:
```bash
# Download from: https://github.com/cloudfoundry/cli/releases
cf --version  # Verify installation
```

2. **Login to SAP BTP**:
```bash
cf api https://api.cf.us10-001.hana.ondemand.com
cf login
cf target -o your_trial_org -s dev
```

3. **Set Environment Variables in Cloud Foundry**:
```bash
# Set your API keys as environment variables
cf set-env iflow-processor-api OPENAI_API_KEY "your_openai_api_key_here"
cf set-env iflow-processor-api SUPABASE_URL "your_supabase_url_here"
cf set-env iflow-processor-api SUPABASE_KEY "your_supabase_service_role_key_here"
```

4. **Deploy Application**:
```bash
cd "Injection pipeline"
cf push
```

Your API will be available at: `https://iflow-processor-api.cfapps.us10-001.hana.ondemand.com`

## 🔗 API Endpoints

### Available Endpoints

- `GET /` - Basic health check
- `GET /health` - Detailed health check with database connectivity
- `POST /process-iflow` - Process iFlow ZIP package (for n8n integration)
- `GET /status/<package_id>` - Get package processing status

### 🤖 n8n Integration

Use the `/process-iflow` endpoint in your n8n workflows:

**HTTP Request Node Configuration:**
- **Method**: POST
- **URL**: `https://your-app-url.cfapps.us10-001.hana.ondemand.com/process-iflow`
- **Body Type**: Form-Data
- **Form Fields**:
  - Key: `file`
  - Type: File
  - Value: Your ZIP file

### 🧪 Testing the API

**Health Check:**
```bash
curl https://your-app-url.cfapps.us10-001.hana.ondemand.com/health
```

**Process iFlow Package:**
```bash
curl -X POST -F 'file=@your_iflow.zip' \
  https://your-app-url.cfapps.us10-001.hana.ondemand.com/process-iflow
```

**Check Package Status:**
```bash
curl https://your-app-url.cfapps.us10-001.hana.ondemand.com/status/your-package-id
```

### 💻 Local Development

For local testing:

1. **Setup Environment**:
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your actual API keys
# OPENAI_API_KEY=your_actual_key_here
# SUPABASE_URL=your_actual_url_here
# SUPABASE_KEY=your_actual_key_here
```

2. **Install Dependencies and Run**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (will automatically load .env file)
python app.py

# Or process a single file
python app.py path/to/your/iflow.zip
```

**Note**: The application automatically loads environment variables from the `.env` file using python-dotenv.

## Architecture

### Core Components

1. **EnhancedIFlowChunker**: Processes iFlow packages and creates structured chunks
2. **EmbeddingGenerator**: Generates embeddings and enhanced descriptions
3. **SupabaseClient**: Handles database operations
4. **IFlowPackageProcessor**: Main orchestrator class

### Processing Pipeline

1. **ZIP Extraction**: Extract to temporary directory
2. **Enhanced Chunking**: Process BPMN components, flows, and assets
3. **Data Classification**: Classify chunks into 4 table types
4. **Embedding Generation**: Generate embeddings and descriptions
5. **Supabase Upload**: Insert into database with proper relationships
6. **Cleanup**: Remove temporary files

### Database Schema

The processor uploads data to 4 Supabase tables:

- **iflow_packages**: Package metadata and full XML
- **iflow_components**: Individual BPMN components
- **iflow_flows**: Flow connections (sequence + message flows)
- **iflow_assets**: Scripts, schemas, mappings, properties

## Output

Successful processing returns:
```json
{
  "status": "success",
  "package_id": "uuid-of-package",
  "total_chunks": 150,
  "coverage_report": {
    "total_files_discovered": 25,
    "total_files_processed": 25,
    "coverage_percentage": 100.0
  },
  "message": "Successfully processed 150 chunks"
}
```

## Error Handling

The processor includes comprehensive error handling:
- ZIP extraction errors
- BPMN parsing errors
- Embedding generation failures
- Database connection issues
- Temporary file cleanup

## Logging

All operations are logged to:
- Console output
- `iflow_processing.log` file

## Requirements

- Python 3.8+
- OpenAI API key
- Supabase project with proper schema
- Required Python packages (see requirements.txt)

## Notes

- Maximum file size: 100MB (configurable)
- Supports .iflw, .groovy, .xsd, .mmap, .wsdl, .properties, .xsl files
- Automatically handles BPMN namespaces and XML formatting
- Includes duplicate detection and cleanup mechanisms
