"""
Intelligent Query Processing with GPT-4 Analysis
Uses GPT-4 for deep understanding of user requirements and intelligent component analysis
"""
import logging
import re
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from config import (
    OPENAI_CONFIG, SYSTEM_KEYWORDS, DATA_TYPE_KEYWORDS,
    OPERATION_KEYWORDS, INTEGRATION_PATTERNS
)

logger = logging.getLogger(__name__)

class IntelligentQueryProcessor:
    """
    Intelligent query processor using GPT-4 for deep understanding
    Analyzes user requirements and provides intelligent component recommendations
    """

    def __init__(self):
        """Initialize OpenAI client for both analysis and embeddings"""
        self.openai_client = OpenAI(api_key=OPENAI_CONFIG['api_key'])
        logger.info("IntelligentQueryProcessor initialized with GPT-4 analysis capabilities")
    
    def process_query_intelligently(self, user_query: str) -> Dict[str, Any]:
        """
        Intelligently process user query using GPT-4 for deep understanding

        Args:
            user_query: Natural language query from user

        Returns:
            Dict containing intelligent analysis, component recommendations, and embedding
        """
        logger.info(f"Intelligently processing query: {user_query[:100]}...")

        try:
            # Step 1: GPT-4 powered deep analysis of user requirements
            intelligent_analysis = self._analyze_requirements_with_gpt(user_query)

            # Step 2: Generate embedding for vector search
            embedding = self.generate_query_embedding(user_query)

            # Step 3: Extract intelligent keywords and search terms
            search_terms = self._extract_intelligent_search_terms(intelligent_analysis)

            # Step 4: Generate component selection criteria
            component_criteria = self._generate_component_criteria(intelligent_analysis)

            return {
                'original_query': user_query,
                'intelligent_analysis': intelligent_analysis,
                'embedding': embedding,
                'search_terms': search_terms,
                'component_criteria': component_criteria,
                'processing_metadata': {
                    'analysis_model': OPENAI_CONFIG['analysis_model'],
                    'confidence_level': intelligent_analysis.get('confidence_level', 0.8),
                    'complexity_assessment': intelligent_analysis.get('complexity_level', 'medium')
                }
            }

        except Exception as e:
            logger.error(f"Error in intelligent query processing: {e}")
            return self._create_fallback_analysis(user_query)

    def _analyze_requirements_with_gpt(self, user_query: str) -> Dict[str, Any]:
        """Use GPT-5 to deeply analyze user requirements and provide intelligent insights"""

        analysis_prompt = f"""
You are an expert SAP Integration Suite architect with deep knowledge of iFlow components, BPMN processes, and enterprise integration patterns.

Analyze this integration requirement and provide a comprehensive analysis:

USER QUERY: "{user_query}"

Please provide a detailed JSON analysis with the following structure:

{{
    "integration_type": "sync|batch|event_driven|api_gateway",
    "business_objective": "Clear description of what the user wants to achieve",
    "source_systems": ["list of source systems identified"],
    "target_systems": ["list of target systems identified"],
    "data_entities": ["list of data types/entities being processed"],
    "required_operations": ["list of operations like validation, transformation, routing, etc."],
    "technical_requirements": {{
        "security_needs": ["authentication", "encryption", etc.],
        "performance_needs": ["throughput", "latency", etc.],
        "reliability_needs": ["error_handling", "retry", "monitoring", etc.]
    }},
    "recommended_components": [
        {{
            "component_type": "ContentModifier|Script|RequestReply|ExclusiveGateway|MessageMapping|SFTP|Filter|etc.",
            "purpose": "Why this component is needed",
            "priority": "high|medium|low",
            "configuration_hints": "Key configuration aspects"
        }}
    ],
    "integration_flow_logic": {{
        "flow_pattern": "Description of the logical flow",
        "decision_points": ["Where conditional logic is needed"],
        "error_scenarios": ["Potential error conditions to handle"],
        "connection_logic": "How components should be connected"
    }},
    "complexity_level": "simple|medium|complex",
    "confidence_level": 0.0-1.0,
    "additional_considerations": ["Any other important aspects"]
}}

Focus on:
1. Understanding the true business intent
2. Identifying all systems and data involved
3. Recommending the most appropriate iFlow components
4. Suggesting intelligent connection patterns
5. Considering error handling and edge cases

Provide only the JSON response, no additional text.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=OPENAI_CONFIG['analysis_model'],
                messages=[
                    {"role": "system", "content": "You are an expert SAP Integration Suite architect. Provide detailed, accurate analysis in JSON format only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_completion_tokens=2000
            )

            analysis_text = response.choices[0].message.content.strip()

            # Parse JSON response
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()

            analysis = json.loads(analysis_text)
            logger.info(f"GPT-5 analysis completed with confidence: {analysis.get('confidence_level', 'unknown')}")

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT analysis JSON: {e}")
            return self._create_basic_analysis(user_query)
        except Exception as e:
            logger.error(f"Error in GPT analysis: {e}")
            return self._create_basic_analysis(user_query)

    def _extract_intelligent_search_terms(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract intelligent search terms from GPT analysis"""
        search_terms = {
            'component_terms': [],
            'system_terms': [],
            'operation_terms': [],
            'data_terms': [],
            'technical_terms': []
        }

        # Extract from recommended components
        for component in analysis.get('recommended_components', []):
            search_terms['component_terms'].append(component.get('component_type', '').lower())
            search_terms['operation_terms'].extend(component.get('purpose', '').lower().split())

        # Extract system terms
        search_terms['system_terms'].extend(analysis.get('source_systems', []))
        search_terms['system_terms'].extend(analysis.get('target_systems', []))

        # Extract data terms
        search_terms['data_terms'].extend(analysis.get('data_entities', []))

        # Extract operation terms
        search_terms['operation_terms'].extend(analysis.get('required_operations', []))

        # Extract technical terms
        tech_reqs = analysis.get('technical_requirements', {})
        for req_type, requirements in tech_reqs.items():
            search_terms['technical_terms'].extend(requirements)

        return search_terms

    def _generate_component_criteria(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent component selection criteria"""
        return {
            'required_components': [comp['component_type'] for comp in analysis.get('recommended_components', [])
                                  if comp.get('priority') == 'high'],
            'optional_components': [comp['component_type'] for comp in analysis.get('recommended_components', [])
                                  if comp.get('priority') in ['medium', 'low']],
            'integration_pattern': analysis.get('integration_type', 'sync'),
            'complexity_level': analysis.get('complexity_level', 'medium'),
            'flow_logic': analysis.get('integration_flow_logic', {}),
            'selection_weights': {
                'functionality_match': 0.4,
                'system_compatibility': 0.3,
                'performance_requirements': 0.2,
                'complexity_appropriateness': 0.1
            }
        }

    def _create_basic_analysis(self, user_query: str) -> Dict[str, Any]:
        """Create basic analysis when GPT analysis fails"""
        return {
            'integration_type': 'sync',
            'business_objective': f'Integration based on: {user_query}',
            'source_systems': [],
            'target_systems': [],
            'data_entities': [],
            'required_operations': ['transformation'],
            'technical_requirements': {
                'security_needs': [],
                'performance_needs': [],
                'reliability_needs': ['error_handling']
            },
            'recommended_components': [
                {
                    'component_type': 'ContentModifier',
                    'purpose': 'Set context and properties',
                    'priority': 'high',
                    'configuration_hints': 'Basic property setting'
                },
                {
                    'component_type': 'Script',
                    'purpose': 'Process and validate data',
                    'priority': 'high',
                    'configuration_hints': 'Groovy script for processing'
                }
            ],
            'integration_flow_logic': {
                'flow_pattern': 'Linear processing flow',
                'decision_points': [],
                'error_scenarios': ['validation_failure'],
                'connection_logic': 'Sequential component execution'
            },
            'complexity_level': 'medium',
            'confidence_level': 0.5,
            'additional_considerations': ['Basic integration pattern']
        }

    def _create_fallback_analysis(self, user_query: str) -> Dict[str, Any]:
        """Create fallback analysis when all else fails"""
        return {
            'original_query': user_query,
            'intelligent_analysis': self._create_basic_analysis(user_query),
            'embedding': [0.0] * OPENAI_CONFIG['embedding_dimensions'],
            'search_terms': {
                'component_terms': ['contentmodifier', 'script'],
                'system_terms': [],
                'operation_terms': ['transformation'],
                'data_terms': [],
                'technical_terms': []
            },
            'component_criteria': {
                'required_components': ['ContentModifier', 'Script'],
                'optional_components': [],
                'integration_pattern': 'sync',
                'complexity_level': 'medium',
                'flow_logic': {},
                'selection_weights': {
                    'functionality_match': 0.4,
                    'system_compatibility': 0.3,
                    'performance_requirements': 0.2,
                    'complexity_appropriateness': 0.1
                }
            },
            'processing_metadata': {
                'analysis_model': 'fallback',
                'confidence_level': 0.3,
                'complexity_assessment': 'medium'
            }
        }
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding using OpenAI text-embedding-3-small
        
        Args:
            query: Text to embed
            
        Returns:
            1536-dimensional embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model=OPENAI_CONFIG['embedding_model'],
                input=query,
                dimensions=OPENAI_CONFIG['embedding_dimensions']
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * OPENAI_CONFIG['embedding_dimensions']
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for better processing
        """
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Expand common abbreviations
        abbreviations = {
            's4hana': 'sap s4hana',
            's/4hana': 'sap s4hana',
            'sf': 'successfactors',
            'api': 'api call',
            'sync': 'synchronize',
            'xform': 'transform',
            'val': 'validate'
        }
        
        for abbrev, full in abbreviations.items():
            normalized = normalized.replace(abbrev, full)
        
        return normalized
    
    def _extract_intent(self, normalized_query: str) -> Dict[str, Any]:
        """
        Extract user intent using rule-based pattern matching
        """
        intent = {
            'operation_type': 'sync',  # default
            'source_system': None,
            'target_system': None,
            'data_type': None,
            'integration_pattern': 'sync',
            'operations': [],
            'systems': [],
            'confidence_scores': {}
        }
        
        # Extract operation type
        intent['operation_type'] = self._identify_operation_type(normalized_query)
        
        # Extract systems
        systems = self._identify_systems(normalized_query)
        intent['systems'] = systems
        if len(systems) >= 2:
            intent['source_system'] = systems[0]
            intent['target_system'] = systems[1]
        elif len(systems) == 1:
            intent['source_system'] = systems[0]
        
        # Extract data type
        intent['data_type'] = self._identify_data_type(normalized_query)
        
        # Extract integration pattern
        intent['integration_pattern'] = self._identify_integration_pattern(normalized_query)
        
        # Extract operations
        intent['operations'] = self._identify_operations(normalized_query)
        
        return intent
    
    def _identify_operation_type(self, query: str) -> str:
        """
        Identify the main operation type from query
        """
        operation_scores = {}
        
        for op_type, keywords in OPERATION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                operation_scores[op_type] = score
        
        if operation_scores:
            return max(operation_scores, key=operation_scores.get)
        
        return 'sync'  # default
    
    def _identify_systems(self, query: str) -> List[str]:
        """
        Identify systems mentioned in the query
        """
        identified_systems = []
        
        for system, keywords in SYSTEM_KEYWORDS.items():
            if any(keyword in query for keyword in keywords):
                identified_systems.append(system)
        
        return identified_systems
    
    def _identify_data_type(self, query: str) -> Optional[str]:
        """
        Identify the data type being processed
        """
        data_type_scores = {}
        
        for data_type, keywords in DATA_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                data_type_scores[data_type] = score
        
        if data_type_scores:
            return max(data_type_scores, key=data_type_scores.get)
        
        return None
    
    def _identify_integration_pattern(self, query: str) -> str:
        """
        Identify the integration pattern from query
        """
        pattern_scores = {}
        
        for pattern, config in INTEGRATION_PATTERNS.items():
            score = sum(1 for keyword in config['keywords'] if keyword in query)
            if score > 0:
                pattern_scores[pattern] = score
        
        if pattern_scores:
            return max(pattern_scores, key=pattern_scores.get)
        
        return 'sync'  # default
    
    def _identify_operations(self, query: str) -> List[str]:
        """
        Identify all operations mentioned in the query
        """
        operations = []
        
        for op_type, keywords in OPERATION_KEYWORDS.items():
            if any(keyword in query for keyword in keywords):
                operations.append(op_type)
        
        return operations
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract relevant keywords for hybrid search
        """
        keywords = []
        
        # Extract system keywords
        for system, system_keywords in SYSTEM_KEYWORDS.items():
            for keyword in system_keywords:
                if keyword in query:
                    keywords.append(keyword)
        
        # Extract data type keywords
        for data_type, type_keywords in DATA_TYPE_KEYWORDS.items():
            for keyword in type_keywords:
                if keyword in query:
                    keywords.append(keyword)
        
        # Extract operation keywords
        for op_type, op_keywords in OPERATION_KEYWORDS.items():
            for keyword in op_keywords:
                if keyword in query:
                    keywords.append(keyword)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _calculate_confidence(self, intent: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the extracted intent
        """
        confidence_factors = []
        
        # Operation type confidence
        if intent.get('operation_type'):
            confidence_factors.append(0.8)
        
        # System identification confidence
        systems = intent.get('systems', [])
        if len(systems) >= 2:
            confidence_factors.append(0.9)
        elif len(systems) == 1:
            confidence_factors.append(0.6)
        
        # Data type confidence
        if intent.get('data_type'):
            confidence_factors.append(0.7)
        
        # Integration pattern confidence
        if intent.get('integration_pattern'):
            confidence_factors.append(0.6)
        
        # Operations confidence
        operations = intent.get('operations', [])
        if operations:
            confidence_factors.append(min(0.8, len(operations) * 0.2))
        
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        
        return 0.3  # low confidence for unclear queries
    
    def _default_intent(self) -> Dict[str, Any]:
        """
        Return default intent for failed processing
        """
        return {
            'operation_type': 'sync',
            'source_system': None,
            'target_system': None,
            'data_type': None,
            'integration_pattern': 'sync',
            'operations': ['sync'],
            'systems': [],
            'confidence_scores': {}
        }
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity to determine processing approach
        """
        complexity_indicators = {
            'word_count': len(query.split()),
            'system_count': len(self._identify_systems(query.lower())),
            'operation_count': len(self._identify_operations(query.lower())),
            'has_conditions': any(word in query.lower() for word in ['if', 'when', 'condition', 'based on']),
            'has_multiple_steps': any(word in query.lower() for word in ['then', 'after', 'next', 'followed by']),
            'has_error_handling': any(word in query.lower() for word in ['error', 'fail', 'exception', 'retry'])
        }
        
        # Calculate complexity score
        complexity_score = 0
        complexity_score += min(complexity_indicators['word_count'] / 20, 1.0) * 0.2
        complexity_score += min(complexity_indicators['system_count'] / 3, 1.0) * 0.3
        complexity_score += min(complexity_indicators['operation_count'] / 4, 1.0) * 0.2
        complexity_score += complexity_indicators['has_conditions'] * 0.1
        complexity_score += complexity_indicators['has_multiple_steps'] * 0.1
        complexity_score += complexity_indicators['has_error_handling'] * 0.1
        
        complexity_level = 'simple'
        if complexity_score > 0.7:
            complexity_level = 'complex'
        elif complexity_score > 0.4:
            complexity_level = 'medium'
        
        return {
            'indicators': complexity_indicators,
            'score': complexity_score,
            'level': complexity_level
        }
