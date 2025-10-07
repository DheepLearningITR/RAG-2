#!/usr/bin/env python3
"""
Enhanced Knowledge Graph Blueprint Generator
Integrates Neo4j knowledge graph for superior component selection and flow optimization
"""

import logging
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Note: Emojis removed for Windows compatibility

# Add current directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from query_processor import IntelligentQueryProcessor
from smart_database_retriever import SmartDatabaseRetriever, UserIntent
from intelligent_content_selector import GPTPoweredContentSelector
from intelligent_flow_engine import IntelligentFlowEngine
from knowledge_graph_connector import KnowledgeGraphConnector
from config import KG_INTEGRATION_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class EnhancedBlueprintMetadata:
    """Enhanced metadata about the generated blueprint with KG insights"""
    generation_timestamp: str
    processing_time_seconds: float
    query_confidence: float
    selection_confidence: float
    kg_optimization_score: float
    total_components: int
    total_assets: int
    integration_pattern: str
    complexity_level: str
    kg_insights: Dict[str, Any]

class EnhancedKGBlueprintGenerator:
    """
    Enhanced blueprint generator with Knowledge Graph integration
    Creates superior JSON blueprints using KG insights and optimal flow patterns
    """
    
    def __init__(self):
        """Initialize the enhanced KG generator"""
        logger.info("Initializing Enhanced Knowledge Graph Blueprint Generator")
        
        try:
            self.query_processor = IntelligentQueryProcessor()
            self.smart_retriever = SmartDatabaseRetriever()
            self.content_selector = GPTPoweredContentSelector()
            self.flow_engine = IntelligentFlowEngine()
            
            # Initialize Knowledge Graph Connector
            self.kg_connector = None
            if KG_INTEGRATION_CONFIG.get('enabled', False):
                try:
                    self.kg_connector = KnowledgeGraphConnector()
                    logger.info("Knowledge Graph Connector initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Knowledge Graph Connector: {e}")
                    self.kg_connector = None
            
            # Blueprint templates for different integration patterns
            self.blueprint_templates = {
                'sync': self._get_sync_template(),
                'batch': self._get_batch_template(),
                'event_driven': self._get_event_driven_template(),
                'api_gateway': self._get_api_gateway_template()
            }
            
            logger.info("Enhanced KG Blueprint Generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Enhanced KG Blueprint Generator: {e}")
            raise
    
    def generate_perfect_blueprint(self, user_query: str) -> Dict[str, Any]:
        """
        Generate perfect JSON blueprint with Knowledge Graph integration
        
        Args:
            user_query: Natural language query describing integration requirements
            
        Returns:
            Perfect JSON blueprint with KG insights ready for iFlow synthesis
        """
        logger.info(f"Generating perfect blueprint with KG integration for: {user_query[:100]}...")
        start_time = time.time()
        
        try:
            # Step 1: Deep query analysis to understand user intent
            logger.info("Step 1: Analyzing user intent")
            user_intent = self._analyze_user_intent_deeply(user_query)
            logger.info(f"Intent analysis complete. Type: {user_intent.integration_type}, "
                       f"Confidence: {user_intent.confidence_score:.2f}")
            
            # Step 2: Intelligent database retrieval based on requirements
            logger.info("Step 2: Retrieving targeted content from database")
            retrieved_content = self.smart_retriever.fetch_targeted_content(user_intent)
            logger.info(f"Retrieved {len(retrieved_content.get('components', []))} components, "
                       f"{len(retrieved_content.get('assets', []))} assets")
            
            # Step 3: Smart content selection with KG enhancement
            logger.info("Step 3: Selecting optimal components with KG insights")
            selected_content = self.content_selector.select_optimal_components(
                retrieved_content, user_intent
            )
            logger.info(f"Selected {len(selected_content['core_components'])} core components, "
                       f"{len(selected_content['supporting_assets'])} assets")
            
            # Step 4: Knowledge Graph flow optimization
            kg_optimization = None
            if self.kg_connector:
                logger.info("Step 4: Applying Knowledge Graph flow optimization")
                kg_optimization = self._apply_kg_flow_optimization(
                    selected_content, user_intent
                )
                logger.info(f"KG optimization complete. Score: {kg_optimization.get('optimization_score', 0):.2f}")
            
            # Step 5: Generate intelligent blueprint structure
            logger.info("Step 5: Generating intelligent blueprint with KG insights")
            blueprint = self._generate_intelligent_blueprint(
                selected_content, user_intent, start_time, kg_optimization
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Perfect blueprint with KG integration generated in {processing_time:.2f} seconds")
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error generating perfect blueprint with KG: {e}")
            return self._create_fallback_blueprint(user_query, str(e))
    
    def _apply_kg_flow_optimization(self, selected_content: Dict[str, Any], 
                                   user_intent: UserIntent) -> Dict[str, Any]:
        """Apply Knowledge Graph flow optimization"""
        try:
            components = selected_content.get('core_components', [])
            
            # Get KG flow optimization
            kg_optimization = self.kg_connector.generate_flow_optimization(components)
            
            # Get component recommendations from KG
            component_types = [comp.get('activity_type', '') for comp in components]
            kg_recommendations = self.kg_connector.get_component_recommendations(
                component_types, user_intent.integration_type
            )
            
            # Get integration pattern insights
            pattern_insights = self.kg_connector.get_integration_pattern_insights(
                user_intent.integration_type
            )
            
            return {
                'flow_optimization': kg_optimization,
                'component_recommendations': kg_recommendations,
                'pattern_insights': pattern_insights,
                'optimization_score': kg_optimization.get('optimization_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error applying KG flow optimization: {e}")
            return {'optimization_score': 0.0, 'error': str(e)}
    
    def _analyze_user_intent_deeply(self, user_query: str) -> UserIntent:
        """Analyze user intent using enhanced query processor"""
        try:
            # Use intelligent query processor for GPT-powered analysis
            query_result = self.query_processor.process_query_intelligently(user_query)
            
            # Extract intelligent analysis from GPT-powered query processor
            intelligent_analysis = query_result.get('intelligent_analysis', {})
            search_terms = query_result.get('search_terms', {})

            # Create UserIntent object with GPT-enhanced analysis
            user_intent = UserIntent(
                integration_type=intelligent_analysis.get('integration_type', 'sync'),
                source_systems=intelligent_analysis.get('source_systems', []),
                target_systems=intelligent_analysis.get('target_systems', []),
                data_types=intelligent_analysis.get('data_entities', []),
                required_components=[comp.get('component_type', '') for comp in
                                   intelligent_analysis.get('recommended_components', [])],
                business_logic=intelligent_analysis.get('required_operations', []),
                error_handling=intelligent_analysis.get('technical_requirements', {}).get('reliability_needs', []),
                complexity_level=intelligent_analysis.get('complexity_level', 'medium'),
                description_keywords=search_terms.get('operation_terms', []),
                component_keywords=search_terms.get('component_terms', []),
                asset_keywords=search_terms.get('technical_terms', []),
                flow_keywords=search_terms.get('operation_terms', []),
                package_keywords=search_terms.get('system_terms', []),
                confidence_score=intelligent_analysis.get('confidence_level', 0.8),
                original_query=user_query
            )
            
            return user_intent
            
        except Exception as e:
            logger.error(f"Error in deep intent analysis: {e}")
            return self._create_fallback_intent(user_query)
    
    def _generate_intelligent_blueprint(self, selected_content: Dict[str, Any],
                                       user_intent: UserIntent, start_time: float,
                                       kg_optimization: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate intelligent blueprint with KG insights"""
        try:
            # Get the appropriate template
            template = self.blueprint_templates.get(user_intent.integration_type,
                                                   self.blueprint_templates['sync'])

            # Generate package info
            package_info = self._generate_package_info(user_intent)

            # Generate iFlow definition with KG-enhanced components
            iflow_definition = self._generate_kg_enhanced_iflow_definition(
                selected_content, user_intent, kg_optimization
            )

            # Generate package assets
            package_assets = self._generate_package_assets(selected_content)

            # Generate enhanced metadata with KG insights
            generation_metadata = self._generate_enhanced_blueprint_metadata(
                selected_content, user_intent, start_time, kg_optimization
            )

            # Assemble final blueprint
            blueprint = {
                'package_info': package_info,
                'iflow_definition': iflow_definition,
                'package_assets': package_assets,
                'generation_metadata': generation_metadata,
                'user_query': user_intent.original_query,
                'blueprint_version': '3.0',
                'generator_type': 'enhanced_kg_intelligent',
                'kg_integration': {
                    'enabled': self.kg_connector is not None,
                    'optimization_score': kg_optimization.get('optimization_score', 0.0) if kg_optimization else 0.0,
                    'insights': kg_optimization if kg_optimization else {}
                }
            }

            return blueprint

        except Exception as e:
            logger.error(f"Error generating intelligent blueprint with KG: {e}")
            return self._create_fallback_blueprint(user_intent.original_query, str(e))
    
    def _generate_kg_enhanced_iflow_definition(self, selected_content: Dict[str, Any],
                                              user_intent: UserIntent,
                                              kg_optimization: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate iFlow definition with KG-enhanced flow optimization"""
        iflow_id = f"iflow_{uuid.uuid4().hex[:8]}_main"
        iflow_name = self._generate_package_name(user_intent)

        # Use intelligent flow engine to design optimal flow
        intelligent_analysis = selected_content.get('selection_metadata', {}).get('gpt_analysis', {})
        flow_design = self.flow_engine.design_intelligent_flow(
            selected_content['core_components'],
            user_intent.__dict__,
            intelligent_analysis
        )

        # Generate BPMN structure from intelligent flow design
        bpmn_structure = self.flow_engine.generate_bpmn_structure(
            flow_design, selected_content['core_components']
        )

        # Enhance with KG flow sequence if available
        flow_sequence = [step.get('component_id', '') for step in flow_design.get('flow_sequence', [])]
        
        # Use KG-optimized flow sequence if available
        if kg_optimization and 'flow_optimization' in kg_optimization:
            kg_flow = kg_optimization['flow_optimization']
            if 'pattern_suggestions' in kg_flow and kg_flow['pattern_suggestions']:
                # Use the best pattern suggestion
                best_pattern = kg_flow['pattern_suggestions'][0]
                if 'pattern' in best_pattern:
                    kg_flow_sequence = best_pattern['pattern']
                    flow_sequence = kg_flow_sequence
                    logger.info(f"Using KG-optimized flow sequence: {kg_flow_sequence}")

        return {
            'iflow_id': iflow_id,
            'iflow_name': iflow_name,
            'description': user_intent.original_query,
            'bpmn_structure': bpmn_structure,
            'flow_sequence': flow_sequence,
            'integration_pattern': user_intent.integration_type,
            'complexity_assessment': user_intent.complexity_level,
            'kg_enhanced': True,
            'kg_flow_optimization': kg_optimization.get('flow_optimization', {}) if kg_optimization else {}
        }
    
    def _generate_package_info(self, user_intent: UserIntent) -> Dict[str, Any]:
        """Generate package information"""
        package_id = f"iflow_{uuid.uuid4().hex[:8]}"

        # Generate meaningful package name
        package_name = self._generate_package_name(user_intent)

        # Generate description
        description = self._generate_package_description(user_intent)

        return {
            'package_id': package_id,
            'package_name': package_name,
            'description': description,
            'version': '1.0.0',
            'generated_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'integration_type': user_intent.integration_type,
            'complexity_level': user_intent.complexity_level,
            'source_systems': user_intent.source_systems,
            'target_systems': user_intent.target_systems,
            'data_types': user_intent.data_types,
            'kg_enhanced': True
        }
    
    def _generate_package_name(self, user_intent: UserIntent) -> str:
        """Generate meaningful package name"""
        # Base name from integration type
        base_name = user_intent.integration_type

        # Add system information
        if user_intent.source_systems:
            base_name += f"_{user_intent.source_systems[0]}"

        # Add data type
        if user_intent.data_types:
            base_name += f"_{user_intent.data_types[0]}"

        # Add operation
        if user_intent.business_logic:
            base_name += f"_{user_intent.business_logic[0]}"

        return base_name.replace(' ', '_').lower()
    
    def _generate_package_description(self, user_intent: UserIntent) -> str:
        """Generate meaningful package description"""
        description_parts = []

        # Integration type
        description_parts.append(f"{user_intent.integration_type.title()} integration")

        # Systems
        if user_intent.source_systems and user_intent.target_systems:
            source = ', '.join(user_intent.source_systems)
            target = ', '.join(user_intent.target_systems)
            description_parts.append(f"from {source} to {target}")
        elif user_intent.source_systems:
            source = ', '.join(user_intent.source_systems)
            description_parts.append(f"involving {source}")

        # Data types
        if user_intent.data_types:
            data = ', '.join(user_intent.data_types)
            description_parts.append(f"for {data} data")

        # Business logic
        if user_intent.business_logic:
            logic = ', '.join(user_intent.business_logic)
            description_parts.append(f"with {logic}")

        description = ' '.join(description_parts)
        description += ". Generated from real iFlow components and assets using intelligent analysis and Knowledge Graph optimization."

        return description
    
    def _generate_package_assets(self, selected_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate package assets from GPT-selected content"""
        assets = {
            'bpmn_files': [],
            'groovy_scripts': [],
            'message_mappings': [],
            'wsdl_files': [],
            'configuration_files': [],
            'other_resources': []
        }

        # Process GPT-selected supporting assets
        for asset in selected_content.get('supporting_assets', []):
            file_type = asset.get('file_type', '').lower()

            asset_info = {
                'file_name': asset.get('file_name', 'unknown'),
                'description': asset.get('description', ''),
                'content': asset.get('content', ''),
                'relevance_score': asset.get('relevance_score', 0.0),
                'source': 'gpt_intelligent_selection',
                'gpt_selection_reason': asset.get('gpt_selection_reason', ''),
                'gpt_usage_context': asset.get('gpt_usage_context', ''),
                'gpt_priority': asset.get('gpt_priority', 'medium'),
                'kg_enhanced': True
            }

            # Categorize assets with GPT insights
            if file_type in ['groovy', 'gsh']:
                asset_info['script_type'] = 'processing'
                asset_info['gpt_script_purpose'] = asset.get('gpt_usage_context', 'Data processing')
                assets['groovy_scripts'].append(asset_info)
            elif file_type == 'mmap':
                asset_info['gpt_mapping_purpose'] = asset.get('gpt_usage_context', 'Data transformation')
                assets['message_mappings'].append(asset_info)
            elif file_type == 'wsdl':
                asset_info['gpt_service_purpose'] = asset.get('gpt_usage_context', 'Service definition')
                assets['wsdl_files'].append(asset_info)
            elif file_type in ['properties', 'prop']:
                asset_info['config_type'] = 'parameters'
                asset_info['gpt_config_purpose'] = asset.get('gpt_usage_context', 'Configuration')
                assets['configuration_files'].append(asset_info)
            else:
                assets['other_resources'].append(asset_info)

        # Add GPT analysis metadata
        assets['gpt_selection_metadata'] = {
            'total_assets_analyzed': len(selected_content.get('supporting_assets', [])),
            'gpt_confidence': selected_content.get('selection_metadata', {}).get('selection_confidence', 0.8),
            'selection_reasoning': selected_content.get('selection_metadata', {}).get('selection_reasoning', ''),
            'asset_coverage_analysis': selected_content.get('selection_metadata', {}).get('coverage_analysis', {}),
            'kg_enhanced': True
        }

        return assets
    
    def _generate_enhanced_blueprint_metadata(self, selected_content: Dict[str, Any],
                                            user_intent: UserIntent, start_time: float,
                                            kg_optimization: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive metadata about the blueprint with KG insights"""
        processing_time = time.time() - start_time

        # Extract KG insights
        kg_insights = {}
        kg_optimization_score = 0.0
        
        if kg_optimization:
            kg_optimization_score = kg_optimization.get('optimization_score', 0.0)
            kg_insights = {
                'flow_optimization': kg_optimization.get('flow_optimization', {}),
                'component_recommendations': len(kg_optimization.get('component_recommendations', [])),
                'pattern_insights': kg_optimization.get('pattern_insights', {}),
                'kg_enhanced': True
            }

        return {
            'generation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'processing_time_seconds': round(processing_time, 2),
            'query_confidence': user_intent.confidence_score,
            'selection_confidence': selected_content.get('selection_metadata', {}).get('selection_confidence', 0.0),
            'kg_optimization_score': kg_optimization_score,
            'total_components': len(selected_content.get('core_components', [])),
            'total_assets': len(selected_content.get('supporting_assets', [])),
            'integration_pattern': user_intent.integration_type,
            'complexity_level': user_intent.complexity_level,
            'essential_components': sum(1 for comp in selected_content.get('core_components', [])
                                      if comp.get('is_essential', False)),
            'component_types_covered': list(set(comp.get('activity_type', 'unknown')
                                              for comp in selected_content.get('core_components', []))),
            'asset_types_covered': list(set(asset.get('file_type', 'unknown')
                                          for asset in selected_content.get('supporting_assets', []))),
            'requirement_coverage': selected_content.get('selection_metadata', {}).get('coverage_analysis', {}),
            'source_packages': [pkg.get('id') for pkg in selected_content.get('reference_packages', [])],
            'generator_version': '3.0',
            'intelligence_level': 'enhanced_kg',
            'kg_insights': kg_insights
        }
    
    def _create_fallback_intent(self, user_query: str) -> UserIntent:
        """Create fallback intent when analysis fails"""
        return UserIntent(
            integration_type='sync',
            source_systems=[],
            target_systems=[],
            data_types=[],
            required_components=['enricher', 'script'],
            business_logic=[],
            error_handling=[],
            complexity_level='simple',
            description_keywords=user_query.lower().split(),
            component_keywords=[],
            asset_keywords=[],
            flow_keywords=[],
            package_keywords=[],
            confidence_score=0.1,
            original_query=user_query
        )

    def _create_fallback_blueprint(self, user_query: str, error_message: str) -> Dict[str, Any]:
        """Create fallback blueprint when generation fails"""
        package_id = f"fallback_{uuid.uuid4().hex[:8]}"

        return {
            'package_info': {
                'package_id': package_id,
                'package_name': 'fallback_integration',
                'description': f"Fallback blueprint for: {user_query}",
                'version': '1.0.0',
                'generated_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'integration_type': 'sync',
                'complexity_level': 'simple',
                'kg_enhanced': False
            },
            'iflow_definition': {
                'iflow_id': f"{package_id}_main",
                'iflow_name': 'fallback_integration',
                'description': user_query,
                'bpmn_structure': {
                    'start_events': [],
                    'activities': [],
                    'gateways': [],
                    'end_events': [],
                    'total_components': 0
                },
                'flow_sequence': ['StartEvent_1', 'EndEvent_1'],
                'integration_pattern': 'sync',
                'complexity_assessment': 'simple',
                'kg_enhanced': False
            },
            'package_assets': {
                'bpmn_files': [],
                'groovy_scripts': [],
                'message_mappings': [],
                'wsdl_files': [],
                'configuration_files': [],
                'other_resources': []
            },
            'generation_metadata': {
                'generation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'processing_time_seconds': 0.0,
                'query_confidence': 0.1,
                'selection_confidence': 0.0,
                'kg_optimization_score': 0.0,
                'total_components': 0,
                'total_assets': 0,
                'integration_pattern': 'sync',
                'complexity_level': 'simple',
                'error_message': error_message,
                'is_fallback': True,
                'kg_enhanced': False
            },
            'user_query': user_query,
            'blueprint_version': '3.0',
            'generator_type': 'enhanced_kg_intelligent_fallback',
            'kg_integration': {
                'enabled': False,
                'optimization_score': 0.0,
                'insights': {}
            }
        }

    # Template methods for different integration patterns
    def _get_sync_template(self) -> Dict[str, Any]:
        """Get template for synchronous integration"""
        return {
            'pattern': 'sync',
            'required_components': ['enricher', 'script', 'request_reply'],
            'optional_components': ['filter', 'message_mapping'],
            'flow_type': 'linear',
            'error_handling': 'basic'
        }

    def _get_batch_template(self) -> Dict[str, Any]:
        """Get template for batch integration"""
        return {
            'pattern': 'batch',
            'required_components': ['enricher', 'script', 'sftp'],
            'optional_components': ['filter', 'message_mapping', 'aggregator'],
            'flow_type': 'batch_processing',
            'error_handling': 'retry_mechanism'
        }

    def _get_event_driven_template(self) -> Dict[str, Any]:
        """Get template for event-driven integration"""
        return {
            'pattern': 'event_driven',
            'required_components': ['enricher', 'gateway', 'script'],
            'optional_components': ['filter', 'request_reply'],
            'flow_type': 'conditional',
            'error_handling': 'notification'
        }

    def _get_api_gateway_template(self) -> Dict[str, Any]:
        """Get template for API gateway integration"""
        return {
            'pattern': 'api_gateway',
            'required_components': ['enricher', 'gateway', 'request_reply'],
            'optional_components': ['script', 'filter'],
            'flow_type': 'routing',
            'error_handling': 'exception_handling'
        }

def main():
    """Test the Enhanced KG Blueprint Generator"""
    print("🚀 Testing Enhanced Knowledge Graph Blueprint Generator")
    print("=" * 60)
    
    generator = EnhancedKGBlueprintGenerator()
    
    try:
        # Test with a sample query
        test_query = "Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling"
        
        print(f"📝 Test Query: {test_query}")
        print("-" * 60)
        
        # Generate blueprint
        blueprint = generator.generate_perfect_blueprint(test_query)
        
        # Print summary
        print("\n📊 Blueprint Summary:")
        print("-" * 30)
        
        # Package info
        package_info = blueprint.get('package_info', {})
        print(f"📋 Package Name: {package_info.get('package_name', 'Unknown')}")
        print(f"🔄 Integration Type: {package_info.get('integration_type', 'Unknown')}")
        print(f"🧠 KG Enhanced: {package_info.get('kg_enhanced', False)}")
        
        # Metadata
        metadata = blueprint.get('generation_metadata', {})
        print(f"📊 Components: {metadata.get('total_components', 0)}")
        print(f"📁 Assets: {metadata.get('total_assets', 0)}")
        print(f"⏱️  Processing Time: {metadata.get('processing_time_seconds', 0):.2f}s")
        print(f"🎯 Query Confidence: {metadata.get('query_confidence', 0):.2f}")
        print(f"🧠 KG Optimization Score: {metadata.get('kg_optimization_score', 0):.2f}")
        print(f"🔧 Generator Version: {metadata.get('generator_version', 'Unknown')}")
        print(f"🧠 Intelligence Level: {metadata.get('intelligence_level', 'Unknown')}")
        
        # KG Integration info
        kg_integration = blueprint.get('kg_integration', {})
        print(f"🔗 KG Integration Enabled: {kg_integration.get('enabled', False)}")
        print(f"📈 KG Optimization Score: {kg_integration.get('optimization_score', 0):.2f}")
        
        print("\n✅ Enhanced KG Blueprint Generator test completed!")
        
    except Exception as e:
        print(f"❌ Error testing Enhanced KG Blueprint Generator: {e}")
        logger.error(f"Error testing Enhanced KG Blueprint Generator: {e}")
    
    finally:
        if generator.kg_connector:
            generator.kg_connector.close()

if __name__ == "__main__":
    main()
