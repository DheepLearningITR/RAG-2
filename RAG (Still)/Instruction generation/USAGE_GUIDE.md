# RAG Prime Instruction Generation - Usage Guide

## Overview
The RAG Prime Instruction Generation system creates intelligent JSON blueprints for SAP iFlow packages from natural language queries. It uses advanced RAG techniques to retrieve relevant components from your Supabase database and generates comprehensive integration blueprints.

## Prerequisites

### 1. Python Dependencies
Install the required Python packages:

```bash
pip install openai supabase python-dotenv
```

### 2. Database Setup
Ensure your Supabase database has the required schema with these tables:
- `iflow_packages` - iFlow package information
- `iflow_components` - BPMN components with embeddings
- `iflow_assets` - Scripts, mappings, and other assets
- `iflow_flows` - Flow connections and sequences

### 3. Configuration
The system uses credentials in `config.py`. Make sure you have:
- Valid Supabase URL and service key
- OpenAI API key for embeddings
- Proper database permissions

## How to Run

### Method 1: Using the Test Suite (Recommended for First Time)

```bash
cd "e:\A RAG Pipeline\RAG\RAG Prime\Instruction generation"
python test_enhanced_generator.py
```

This will:
- Run 5 different test scenarios
- Generate JSON blueprints for each
- Save them as separate files
- Validate the results
- Show comprehensive output

### Method 2: Direct API Usage

Create a Python script:

```python
#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

# Add the instruction generation directory to path
sys.path.append(r"e:\A RAG Pipeline\RAG\RAG Prime\Instruction generation")

from enhanced_blueprint_generator import EnhancedBlueprintGenerator

def generate_blueprint(query: str, output_file: str = None):
    """Generate a JSON blueprint from a natural language query"""
    
    try:
        # Initialize the generator
        print("🚀 Initializing Enhanced Blueprint Generator...")
        generator = EnhancedBlueprintGenerator()
        
        # Generate blueprint
        print(f"🔍 Processing query: {query}")
        blueprint = generator.generate_perfect_blueprint(query)
        
        # Save to file
        if not output_file:
            output_file = "generated_blueprint.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Blueprint generated successfully!")
        print(f"📁 Saved to: {Path(output_file).absolute()}")
        
        # Print summary
        package_info = blueprint.get('package_info', {})
        metadata = blueprint.get('generation_metadata', {})
        
        print(f"\n📋 Package: {package_info.get('package_name', 'Unknown')}")
        print(f"🔄 Type: {package_info.get('integration_type', 'Unknown')}")
        print(f"📊 Components: {metadata.get('total_components', 0)}")
        print(f"📁 Assets: {metadata.get('total_assets', 0)}")
        print(f"🎯 Confidence: {metadata.get('query_confidence', 0):.2f}")
        
        return blueprint
        
    except Exception as e:
        print(f"❌ Error generating blueprint: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    query = "Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling"
    generate_blueprint(query, "my_integration_blueprint.json")
```

### Method 3: Interactive Usage

```python
#!/usr/bin/env python3
import sys
sys.path.append(r"e:\A RAG Pipeline\RAG\RAG Prime\Instruction generation")

from enhanced_blueprint_generator import EnhancedBlueprintGenerator
import json

# Initialize generator
generator = EnhancedBlueprintGenerator()

# Interactive loop
while True:
    print("\n" + "="*60)
    print("🚀 RAG Prime Blueprint Generator")
    print("="*60)
    
    query = input("\n📝 Enter your integration requirement (or 'quit' to exit): ")
    
    if query.lower() in ['quit', 'exit', 'q']:
        break
    
    if query.strip():
        try:
            blueprint = generator.generate_perfect_blueprint(query)
            
            # Save with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blueprint_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Blueprint saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⚠️ Please enter a valid query")

print("👋 Goodbye!")
```

## Example Queries

Here are some example queries you can use:

### 1. Employee Sync Integration
```
Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling
```

### 2. Batch File Processing
```
Set up a daily batch process to upload order files via SFTP, validate them, and send to database with transformation
```

### 3. Event-Driven Integration
```
Build an event-driven integration that triggers notifications when invoice status changes, with conditional routing
```

### 4. API Gateway
```
Create an API gateway that routes customer requests to different backend systems based on customer type
```

### 5. Simple Data Mapping
```
Simple integration to map and transform product data between two systems
```

## Output Structure

The generated JSON blueprint contains:

```json
{
  "package_info": {
    "package_id": "unique_id",
    "package_name": "descriptive_name",
    "description": "detailed_description",
    "integration_type": "sync|batch|event_driven|api_gateway",
    "source_systems": ["system1"],
    "target_systems": ["system2"],
    "data_types": ["employee", "order", etc.]
  },
  "iflow_definition": {
    "bpmn_structure": {
      "activities": [/* BPMN components with real XML */],
      "flows": [/* Connection flows */]
    }
  },
  "package_assets": {
    "groovy_scripts": [/* Scripts with actual code */],
    "message_mappings": [/* Mapping definitions */],
    "wsdl_files": [/* Service definitions */]
  },
  "generation_metadata": {
    "query_confidence": 0.85,
    "total_components": 5,
    "total_assets": 3,
    "processing_time_seconds": 2.34
  }
}
```

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure you're in the correct directory and all dependencies are installed
2. **Database Connection**: Verify Supabase credentials in `config.py`
3. **OpenAI API**: Check your OpenAI API key and quota
4. **Empty Results**: Ensure your database has relevant iFlow data

### Debug Mode:
Add logging to see detailed processing:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Next Steps

After generating a blueprint:
1. Review the generated JSON structure
2. Validate components and assets
3. Use the blueprint with your iFlow synthesis system
4. Customize components as needed for your specific requirements

The system is designed to be intelligent and adaptive, learning from your database content to provide the most relevant components for your integration needs.
