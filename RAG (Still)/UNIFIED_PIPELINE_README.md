# Unified RAG Pipeline - Complete iFlow Generation

This unified pipeline combines the **Instruction Generation** and **Package Generation** systems to provide a complete end-to-end solution for generating SAP CPI iFlow packages from natural language queries.

## 🚀 Features

- **Natural Language Processing**: Input your integration requirements in plain English
- **Knowledge Graph Integration**: Uses Neo4j knowledge graph for optimal component selection
- **Intelligent Blueprint Generation**: Creates detailed JSON blueprints with GPT-5 analysis
- **Complete Package Generation**: Generates ready-to-deploy SAP CPI packages
- **Multiple Output Formats**: JSON blueprints and zip packages
- **Interactive Mode**: User-friendly command-line interface

## 📁 Output Structure

```
RAG Prime/
├── Instruction generation/
│   └── Output json/           # Generated JSON blueprints
│       └── blueprint_YYYYMMDD_HHMMSS.json
├── package generation/
│   └── output/               # Generated SAP CPI packages
│       └── iflow_package_YYYYMMDD_HHMMSS.zip
└── unified_rag_pipeline.py   # Main pipeline script
```

## 🛠️ Setup and Usage

### Environment Setup

1. **Copy Environment Template**:
```bash
cd "RAG (Still)"
cp env.example .env
```

2. **Configure Environment Variables**:
Edit the `.env` file with your actual values:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# Neo4j Knowledge Graph Configuration
NEO4J_URI=your_neo4j_uri_here
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
NEO4J_DATABASE=neo4j
```

3. **Install Dependencies**:
```bash
pip install -r "Instruction generation/requirements.txt"
```

### Quick Start

```bash
# Navigate to RAG (Still) directory
cd "RAG (Still)"

# Run interactive mode
python run_pipeline.py

# Or run the main pipeline directly
python unified_rag_pipeline.py
```

### Command Line Options

```bash
# Interactive mode (default)
python run_pipeline.py
python run_pipeline.py -i

# Run example queries
python run_pipeline.py -e

# Single query
python run_pipeline.py "Create a sync integration between SAP and SuccessFactors"

# Show help
python run_pipeline.py -h
```

### Advanced Usage

```bash
# Using the main pipeline script directly
python unified_rag_pipeline.py --interactive
python unified_rag_pipeline.py --examples
python unified_rag_pipeline.py --cleanup 7  # Clean files older than 7 days
```

## 📝 Example Queries

The system can handle various types of integration requirements:

### Sync Integrations
```
"Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling"
```

### Batch Processing
```
"Set up a daily batch process to upload order files via SFTP, validate them, and send to database with transformation"
```

### Event-Driven Integrations
```
"Build an event-driven integration that triggers notifications when invoice status changes, with conditional routing"
```

### API Gateway
```
"Create an API gateway that routes customer requests to different backend systems based on customer type"
```

### Simple Integrations
```
"Simple integration to map and transform product data between two systems"
```

## 🔄 Pipeline Flow

1. **Query Analysis**: Natural language query is analyzed using GPT-5
2. **Knowledge Graph Enhancement**: Neo4j knowledge graph provides component relationship insights
3. **Component Selection**: Optimal components are selected based on requirements
4. **Blueprint Generation**: Detailed JSON blueprint is created
5. **Package Creation**: SAP CPI package structure is generated
6. **Zip Packaging**: Final deployable zip file is created

## 📊 Output Information

### JSON Blueprint Contains:
- Package information and metadata
- iFlow definition with BPMN structure
- Component configurations
- Asset files (scripts, mappings, etc.)
- Knowledge Graph optimization insights
- Generation metadata and confidence scores

### Zip Package Contains:
- Complete SAP CPI package structure
- BPMN process definition
- Component configurations
- Asset files (Groovy scripts, message mappings, etc.)
- META-INF files for deployment

## 🧠 Knowledge Graph Integration

The system leverages Neo4j knowledge graph for:
- **Component Relationship Analysis**: Understanding how components typically connect
- **Flow Pattern Recognition**: Identifying optimal flow sequences
- **Integration Pattern Insights**: Best practices for different integration types
- **Optimization Recommendations**: Suggestions for improved component selection

## 📈 Performance Metrics

The system provides detailed metrics:
- **Query Confidence**: How well the system understood your requirements
- **KG Optimization Score**: Knowledge Graph enhancement score
- **Component Coverage**: Number and types of components selected
- **Asset Coverage**: Supporting files and resources included
- **Processing Time**: Total time for blueprint and package generation

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r "Instruction generation/requirements.txt"
   ```

2. **Neo4j Connection Issues**: Check Neo4j credentials in `config.py`

3. **File Permission Errors**: Ensure write permissions for output directories

4. **Memory Issues**: For large queries, consider processing in smaller batches

### Logging

The system provides detailed logging:
- INFO level: General progress and status
- WARNING level: Non-critical issues
- ERROR level: Critical failures

## 🔧 Configuration

### Environment Variables
The system now uses environment variables for all sensitive configuration. Set these in your `.env` file:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here
NEO4J_URI=your_neo4j_uri_here
NEO4J_PASSWORD=your_neo4j_password_here

# Optional Configuration
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
```

### Knowledge Graph Integration
The system automatically loads configuration from environment variables. No manual editing of `config.py` is required for basic setup.

## 📚 Related Documentation

- [Instruction Generation README](Instruction%20generation/README.md)
- [Package Generation README](package%20generation/README_BLUEPRINT_TO_PACKAGE.md)
- [Knowledge Graph Integration](Instruction%20generation/KNOWLEDGE_GRAPH_INTEGRATION.md)
- [Usage Guide](Instruction%20generation/USAGE_GUIDE.md)

## 🤝 Contributing

To extend or modify the pipeline:

1. **Add New Query Types**: Extend the query processor
2. **Enhance Knowledge Graph**: Add new relationship patterns
3. **Improve Package Generation**: Extend the blueprint to package converter
4. **Add New Output Formats**: Create additional export options

## 📄 License

This project is part of the RAG Prime system for SAP CPI integration development.

---

**Ready to generate your first iFlow package?** Run `python run_pipeline.py` and start with a simple integration query!
