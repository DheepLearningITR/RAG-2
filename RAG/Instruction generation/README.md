# Enhanced Intelligent RAG Blueprint Generator

An **intelligent, query-driven system** for generating perfect JSON blueprints from natural language queries using advanced Retrieval-Augmented Generation (RAG) with real SAP iFlow components.

## Overview

This enhanced system takes natural language queries describing integration requirements and generates **perfect, structured JSON blueprints** ready for SAP Integration Suite iFlow package synthesis. It uses **intelligent analysis** and **smart content selection** to understand exactly what users want and retrieve the optimal components from Supabase.

## Enhanced Architecture

```
User Query → Intelligent Intent Analysis → Smart Database Retrieval → Optimal Content Selection → Perfect JSON Blueprint
```

### Core Enhanced Components

1. **QueryProcessor** - Processes natural language queries and generates embeddings (only LLM usage)
2. **SmartDatabaseRetriever** - Intelligent multi-dimensional search across all database columns and descriptions
3. **IntelligentContentSelector** - Smart selection of optimal components based on user requirements with scoring
4. **EnhancedBlueprintGenerator** - Generates perfect JSON blueprints with real components and comprehensive metadata

## Enhanced Features

- 🎯 **Intelligent Query Understanding** - Deep analysis of user intent and requirements
- 🔍 **Smart Database Search** - Multi-dimensional search across all columns and descriptions
- ⚡ **Optimal Component Selection** - AI-driven selection with relevance scoring and priority ranking
- 🏗️ **Perfect JSON Generation** - Comprehensive blueprints with real components and metadata
- 📊 **Confidence Scoring** - Quality metrics and requirement coverage analysis
- 🎨 **Template-Based Patterns** - Support for sync, batch, event-driven, and API gateway patterns
- ✅ **Comprehensive Testing** - Advanced validation and testing framework

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
   - Update `config.py` with your Supabase and OpenAI credentials
   - Ensure your Supabase database has the required schema (see below)

## Database Schema

The system expects the following Supabase tables:

```sql
-- iFlow packages
CREATE TABLE iflow_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name TEXT NOT NULL,
    version TEXT,
    description TEXT,
    iflw_xml TEXT,
    description_embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- iFlow components
CREATE TABLE iflow_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID REFERENCES iflow_packages(id) ON DELETE CASCADE,
    component_id TEXT NOT NULL,
    activity_type TEXT,
    description TEXT,
    complete_bpmn_xml TEXT,
    properties JSONB,
    related_scripts JSONB,
    code_embedding VECTOR(1536),
    description_embedding VECTOR(1536),
    activity_type_embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- iFlow assets (scripts, mappings, etc.)
CREATE TABLE iflow_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID REFERENCES iflow_packages(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT,
    description TEXT,
    content TEXT,
    content_embedding VECTOR(1536),
    description_embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- iFlow flows (connections)
CREATE TABLE iflow_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID REFERENCES iflow_packages(id) ON DELETE CASCADE,
    source_component_id TEXT NOT NULL,
    target_component_id TEXT NOT NULL,
    flow_type TEXT CHECK (flow_type IN ('sequence', 'message')),
    content TEXT,
    connections JSONB,
    flow_embedding VECTOR(1536),
    description TEXT,
    description_embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## Usage

### Command Line Testing

```bash
# Test the enhanced generator with comprehensive validation
python test_enhanced_generator.py
```

### Python API

```python
from enhanced_blueprint_generator import EnhancedBlueprintGenerator

# Initialize enhanced generator
generator = EnhancedBlueprintGenerator()

# Generate perfect blueprint
blueprint = generator.generate_perfect_blueprint(
    "Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling"
)

# The blueprint contains:
# - Intelligent package information
# - Real BPMN components with XML
# - Supporting assets (scripts, mappings, WSDLs)
# - Comprehensive metadata and confidence scores
```

### Key Improvements

- **Intelligent Intent Analysis**: Understands exactly what user wants to build
- **Smart Component Selection**: Chooses optimal components with relevance scoring
- **Perfect JSON Structure**: Generates comprehensive blueprints ready for synthesis
- **Real Component Integration**: Uses actual BPMN XML, scripts, and mappings from database

## Perfect Blueprint Example

See `sample_perfect_blueprint.json` for a complete example of the enhanced system output.

**Key Features of Generated Blueprints:**

```json
{
  "package_info": {
    "package_id": "iflow_a1b2c3d4",
    "package_name": "sync_sap_s4hana_employee_validation",
    "description": "Sync integration from sap_s4hana to successfactors for employee data with validation, transformation. Generated from real iFlow components and assets using intelligent analysis.",
    "integration_type": "sync",
    "source_systems": ["sap_s4hana"],
    "target_systems": ["successfactors"],
    "data_types": ["employee"]
  },
  "iflow_definition": {
    "bpmn_structure": {
      "activities": [
        {
          "id": "ContentModifier_1",
          "name": "Set Employee Context",
          "bpmn_xml": "<callActivity id=\"ContentModifier_1\" name=\"Set Employee Context\">...",
          "relevance_score": 0.95,
          "match_reasons": ["Activity type match: enricher", "Description relevance"],
          "is_essential": true
        }
      ]
    }
  },
  "package_assets": {
    "groovy_scripts": [
      {
        "file_name": "employee_validation.groovy",
        "content": "import com.sap.gateway.ip.core.customdev.util.Message;...",
        "relevance_score": 0.93
      }
    ]
  },
  "generation_metadata": {
    "query_confidence": 0.87,
    "selection_confidence": 0.91,
    "total_components": 5,
    "total_assets": 4,
    "intelligence_level": "enhanced"
  }
}
```

## Testing

Run the enhanced test suite:

```bash
python test_enhanced_generator.py
```

This comprehensive test validates:
- Intelligent query analysis and intent extraction
- Smart database retrieval with multi-dimensional search
- Optimal component selection with relevance scoring
- Perfect JSON blueprint generation with real components
- Comprehensive metadata and confidence scoring

## Configuration

Key configuration options in `config.py`:

- **SUPABASE_CONFIG**: Database connection settings
- **OPENAI_CONFIG**: OpenAI API settings (for embeddings only)
- **COMPONENT_RULES**: Rules for component type detection
- **INTEGRATION_PATTERNS**: Integration pattern definitions
- **VECTOR_SEARCH_CONFIG**: Vector search parameters

## Enhanced Component Intelligence

The system intelligently selects from various component types:

- **ContentModifier/Enricher**: Context setting, property management, header manipulation
- **Script**: Groovy processing, validation logic, business rules, data transformation
- **RequestReply**: API calls, external system integration, service invocation
- **ExclusiveGateway**: Conditional routing, decision logic, error handling paths
- **MessageMapping**: Data transformation, format conversion, field mapping
- **SFTP**: File transfer operations, batch processing
- **Filter**: Data filtering, XPath operations, content selection

## Intelligent Integration Patterns

- **sync**: Real-time synchronization with validation and error handling
- **batch**: Scheduled batch processing with file operations and aggregation
- **event_driven**: Event-based processing with conditional routing and notifications
- **api_gateway**: API proxy with intelligent routing and transformation

## Logging

The system provides comprehensive logging:
- Console output for real-time monitoring
- File logging to `rag_blueprint_generator.log`
- Configurable log levels

## Error Handling

- Graceful degradation with fallback blueprints
- Comprehensive error logging
- Validation warnings and suggestions
- Recovery mechanisms for failed components

## Future Enhancements

- [ ] Support for more component types
- [ ] Enhanced pattern recognition
- [ ] Custom template support
- [ ] Integration with iFlow synthesizer
- [ ] Web interface
- [ ] Performance optimizations

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Ensure rule-based approach (no LLM for generation)

## License

This project is part of the RAG Pipeline system for SAP Integration Suite automation.
