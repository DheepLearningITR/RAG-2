# 🚀 RAG Prime Blueprint Generator - Quick Start Guide

## 📋 What You Need to Run

**Main File to Execute:** `generate_blueprint.py`

**Output Location:** All JSON files are automatically saved in `Output json/` subfolder

## 🎯 How to Run

### 1. Interactive Mode (Recommended)
```bash
python generate_blueprint.py
```
- Enter your integration requirements when prompted
- Type 'quit', 'exit', or 'q' to stop
- Each blueprint is automatically saved with timestamp

### 2. Single Query Mode
```bash
python generate_blueprint.py "Create a sync integration from SAP to SuccessFactors"
```

### 3. Run Example Queries
```bash
python generate_blueprint.py -e
```

### 4. Show Help
```bash
python generate_blueprint.py -h
```

## 💡 Example Integration Queries

Try these sample queries:

1. **Simple Sync Integration:**
   ```
   Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation
   ```

2. **Complex Batch Processing:**
   ```
   Build a batch integration that processes orders from multiple e-commerce systems, validates inventory in SAP ERP, transforms data formats, handles errors with retry logic, and sends confirmations back to source systems
   ```

3. **API Gateway Pattern:**
   ```
   Create an API gateway integration that routes customer requests to different backend systems based on customer type and region
   ```

4. **File Transfer with Validation:**
   ```
   Set up a daily SFTP file upload process with data transformation and validation
   ```

## 📁 Output Structure

Generated files are saved in:
```
RAG Prime/Instruction generation/Output json/
├── blueprint_20250929_171706.json
├── blueprint_20250929_172345.json
└── example_1_blueprint.json
```

## 🎉 System Features

- **🧠 GPT-4o Intelligence**: Advanced AI-powered analysis
- **🎯 Smart Component Selection**: Optimal component matching
- **🔗 Intelligent Flow Design**: Logical component connections
- **📊 Quality Analysis**: Comprehensive validation and scoring
- **⚡ Fast Processing**: 50-85 seconds per blueprint
- **📁 Organized Output**: Automatic file organization

## 🔧 System Requirements

- Python 3.8+
- OpenAI API access (GPT-4o models)
- Supabase database connection
- Internet connection for API calls

## 📊 What You Get

Each generated JSON blueprint contains:
- **Package Information**: Metadata, systems, data types
- **iFlow Definition**: BPMN structure, components, flows
- **Package Assets**: Scripts, mappings, configurations  
- **Generation Metadata**: Processing time, confidence scores, quality analysis

## 🚨 Important Notes

- **No test scripts needed** - All test files have been removed
- **Main entry point**: Always use `generate_blueprint.py`
- **Automatic organization**: Files are saved in `Output json/` folder
- **GPT-4o powered**: Uses latest AI models for superior intelligence
- **Quality assured**: Built-in validation and error handling

## 🎯 Quick Test

Run this command to test the system:
```bash
python generate_blueprint.py "Create a simple integration between two systems"
```

The system will generate a JSON blueprint and save it in `Output json/` folder automatically!
