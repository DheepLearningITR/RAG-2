"""
Configuration settings for RAG Blueprint Generator
"""
import os
from typing import Dict, Any

# Supabase Configuration
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL', 'your_supabase_url_here'),
    'anon_key': os.getenv('SUPABASE_ANON_KEY', 'your_supabase_anon_key_here'),
    'service_key': os.getenv('SUPABASE_SERVICE_KEY', 'your_supabase_service_key_here')
}

# OpenAI Configuration - Using Latest GPT-5 Models for Intelligence
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here'),
    'embedding_model': 'text-embedding-3-small',
    'embedding_dimensions': 1536,
    # Latest GPT models for intelligent analysis
    'analysis_model': 'gpt-4o-mini',  # Fast and cost-efficient for analysis
    'reasoning_model': 'gpt-4o',      # Best model for complex reasoning
    'component_selection_model': 'gpt-4o-mini',  # For component selection logic
    'flow_design_model': 'gpt-4o'     # For intelligent flow connections
}

# Component Type Detection Rules
COMPONENT_RULES = {
    'enricher': {
        'triggers': ['set properties', 'add headers', 'context', 'metadata', 'enrich', 'property'],
        'keywords': ['enricher', 'content modifier', 'set header', 'property'],
        'activity_types': ['ContentModifier', 'Enricher'],
        'template': 'enricher_template'
    },
    'script': {
        'triggers': ['validation', 'transformation', 'processing', 'groovy', 'script', 'validate', 'transform'],
        'keywords': ['script', 'groovy', 'validation', 'processing'],
        'activity_types': ['ScriptTask', 'Script'],
        'template': 'script_template'
    },
    'request_reply': {
        'triggers': ['api call', 'http', 'rest', 'service call', 'request', 'call', 'invoke'],
        'keywords': ['request reply', 'http', 'api', 'service'],
        'activity_types': ['RequestReply', 'ServiceTask'],
        'template': 'request_reply_template'
    },
    'gateway': {
        'triggers': ['condition', 'branch', 'decision', 'route', 'gateway', 'split'],
        'keywords': ['gateway', 'condition', 'branch', 'decision'],
        'activity_types': ['ExclusiveGateway', 'ParallelGateway', 'InclusiveGateway'],
        'template': 'gateway_template'
    },
    'odata': {
        'triggers': ['odata', 'sap', 'entity', 'query', 'odata call'],
        'keywords': ['odata', 'entity', 'sap'],
        'activity_types': ['ODataCall', 'OData'],
        'template': 'odata_template'
    },
    'sftp': {
        'triggers': ['sftp', 'file transfer', 'upload', 'download', 'ftp'],
        'keywords': ['sftp', 'file', 'transfer', 'upload'],
        'activity_types': ['SFTP', 'FileTransfer'],
        'template': 'sftp_template'
    },
    'message_mapping': {
        'triggers': ['mapping', 'transform', 'message mapping', 'data mapping'],
        'keywords': ['mapping', 'transform', 'message'],
        'activity_types': ['MessageMapping', 'Mapping'],
        'template': 'message_mapping_template'
    }
}

# Integration Pattern Rules
INTEGRATION_PATTERNS = {
    'sync': {
        'keywords': ['sync', 'synchronize', 'synchronization'],
        'flow_type': 'linear',
        'components': ['enricher', 'script', 'request_reply']
    },
    'batch': {
        'keywords': ['batch', 'daily', 'scheduled', 'bulk'],
        'flow_type': 'batch',
        'components': ['enricher', 'script', 'request_reply', 'sftp']
    },
    'real_time': {
        'keywords': ['real time', 'realtime', 'immediate', 'instant'],
        'flow_type': 'linear',
        'components': ['enricher', 'script', 'request_reply']
    },
    'event_driven': {
        'keywords': ['event', 'trigger', 'notification', 'alert'],
        'flow_type': 'conditional',
        'components': ['enricher', 'gateway', 'script', 'request_reply']
    },
    'api_gateway': {
        'keywords': ['api gateway', 'gateway', 'routing', 'proxy'],
        'flow_type': 'conditional',
        'components': ['enricher', 'script', 'gateway', 'request_reply']
    }
}

# System Keywords for Intent Recognition
SYSTEM_KEYWORDS = {
    'sap_s4hana': ['s4hana', 's/4hana', 'sap s4', 'erp'],
    'successfactors': ['successfactors', 'sf', 'success factors'],
    'concur': ['concur', 'expense'],
    'ariba': ['ariba', 'procurement'],
    'fieldglass': ['fieldglass', 'contingent workforce'],
    'commissions': ['commissions', 'commission'],
    'warehouse': ['warehouse', 'wms'],
    'field_service': ['field service', 'fsm']
}

# Data Type Keywords
DATA_TYPE_KEYWORDS = {
    'employee': ['employee', 'worker', 'person', 'staff', 'hr'],
    'order': ['order', 'purchase', 'sales'],
    'invoice': ['invoice', 'billing', 'payment'],
    'product': ['product', 'item', 'material'],
    'customer': ['customer', 'client', 'account'],
    'vendor': ['vendor', 'supplier', 'partner'],
    'title': ['title', 'position', 'job'],
    'commission': ['commission', 'incentive', 'bonus']
}

# Operation Type Keywords
OPERATION_KEYWORDS = {
    'create': ['create', 'add', 'insert', 'new'],
    'update': ['update', 'modify', 'change', 'edit'],
    'delete': ['delete', 'remove', 'cancel'],
    'sync': ['sync', 'synchronize', 'replicate'],
    'validate': ['validate', 'check', 'verify'],
    'transform': ['transform', 'convert', 'map'],
    'notify': ['notify', 'alert', 'send', 'email']
}

# Vector Search Configuration
VECTOR_SEARCH_CONFIG = {
    'similarity_threshold': 0.8,
    'max_components': 20,
    'max_assets': 15,
    'max_flows': 10,
    'max_packages': 5
}

# Component Templates Configuration
COMPONENT_TEMPLATES_DIR = "templates/components"
FLOW_TEMPLATES_DIR = "templates/flows"
ENDPOINT_TEMPLATES_DIR = "templates/endpoints"

# Neo4j Knowledge Graph Configuration
NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'your_neo4j_uri_here'),
    'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
    'password': os.getenv('NEO4J_PASSWORD', 'your_neo4j_password_here'),
    'database': os.getenv('NEO4J_DATABASE', 'neo4j')
}

# Knowledge Graph Integration Settings
KG_INTEGRATION_CONFIG = {
    'enabled': True,
    'confidence_boost': 0.2,  # 20% boost from KG insights
    'max_recommendations': 10,
    'flow_optimization_enabled': True,
    'pattern_matching_enabled': True
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'rag_blueprint_generator.log'
}
