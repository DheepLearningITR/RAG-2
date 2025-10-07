#!/usr/bin/env python3
"""
Enhanced Blueprint Generator
Creates perfect JSON blueprints using intelligent query analysis and smart content selection
"""

import logging
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add current directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from query_processor import IntelligentQueryProcessor
from smart_database_retriever import SmartDatabaseRetriever, UserIntent
from intelligent_content_selector import GPTPoweredContentSelector
from intelligent_flow_engine import IntelligentFlowEngine

logger = logging.getLogger(__name__)

@dataclass
class BlueprintMetadata:
    """Metadata about the generated blueprint"""
    generation_timestamp: str
    processing_time_seconds: float
    query_confidence: float
    selection_confidence: float
    total_components: int
    total_assets: int
    integration_pattern: str
    complexity_level: str

class EnhancedBlueprintGenerator:
    """
    Enhanced blueprint generator that creates perfect JSON blueprints
    using intelligent analysis and smart content selection
    """
    
    def __init__(self):
        """Initialize the enhanced generator"""
        logger.info("Initializing Enhanced Blueprint Generator")
        
        try:
            self.query_processor = IntelligentQueryProcessor()
            self.smart_retriever = SmartDatabaseRetriever()
            self.content_selector = GPTPoweredContentSelector()
            self.flow_engine = IntelligentFlowEngine()
            
            # Blueprint templates for different integration patterns
            self.blueprint_templates = {
                'sync': self._get_sync_template(),
                'batch': self._get_batch_template(),
                'event_driven': self._get_event_driven_template(),
                'api_gateway': self._get_api_gateway_template()
            }
            
            logger.info("Enhanced Blueprint Generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Enhanced Blueprint Generator: {e}")
            raise
    
    def generate_perfect_blueprint(self, user_query: str) -> Dict[str, Any]:
        """
        Generate perfect JSON blueprint from user query
        
        Args:
            user_query: Natural language query describing integration requirements
            
        Returns:
            Perfect JSON blueprint ready for iFlow synthesis
        """
        logger.info(f"Generating perfect blueprint for: {user_query[:100]}...")
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
            
            # Step 3: Smart content selection based on user needs
            logger.info("Step 3: Selecting optimal components")
            selected_content = self.content_selector.select_optimal_components(
                retrieved_content, user_intent
            )
            logger.info(f"Selected {len(selected_content['core_components'])} core components, "
                       f"{len(selected_content['supporting_assets'])} assets")
            
            # Step 4: Generate intelligent blueprint structure
            logger.info("Step 4: Generating intelligent blueprint")
            blueprint = self._generate_intelligent_blueprint(
                selected_content, user_intent, start_time
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Perfect blueprint generated in {processing_time:.2f} seconds")
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error generating perfect blueprint: {e}")
            return self._create_fallback_blueprint(user_query, str(e))
    
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
    
    def _determine_integration_type(self, query_result: Dict[str, Any], user_query: str) -> str:
        """Determine integration type from query"""
        query_lower = user_query.lower()
        
        # Check for explicit patterns
        if any(word in query_lower for word in ['batch', 'daily', 'scheduled', 'bulk']):
            return 'batch'
        elif any(word in query_lower for word in ['real-time', 'realtime', 'immediate', 'sync']):
            return 'sync'
        elif any(word in query_lower for word in ['event', 'trigger', 'notification', 'webhook']):
            return 'event_driven'
        elif any(word in query_lower for word in ['api gateway', 'proxy', 'routing']):
            return 'api_gateway'
        else:
            return query_result.get('intent', {}).get('operation_type', 'sync')
    
    def _extract_source_systems(self, user_query: str) -> List[str]:
        """Extract source systems from query"""
        systems = []
        query_lower = user_query.lower()
        
        system_patterns = {
            'sap_s4hana': ['s4hana', 's/4hana', 'sap s4', 'erp'],
            'successfactors': ['successfactors', 'sf', 'success factors'],
            'concur': ['concur', 'expense'],
            'ariba': ['ariba', 'procurement'],
            'database': ['database', 'db', 'sql'],
            'api': ['api', 'rest', 'web service']
        }
        
        for system, keywords in system_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                systems.append(system)
        
        return systems
    
    def _extract_target_systems(self, user_query: str) -> List[str]:
        """Extract target systems from query"""
        # For now, use same logic as source systems
        # In future, could use NLP to distinguish "from X to Y"
        return self._extract_source_systems(user_query)
    
    def _extract_data_types(self, user_query: str) -> List[str]:
        """Extract data types from query"""
        data_types = []
        query_lower = user_query.lower()
        
        data_patterns = {
            'employee': ['employee', 'worker', 'person', 'staff'],
            'order': ['order', 'purchase', 'sales'],
            'invoice': ['invoice', 'billing', 'payment'],
            'customer': ['customer', 'client', 'account'],
            'product': ['product', 'item', 'material']
        }
        
        for data_type, keywords in data_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                data_types.append(data_type)
        
        return data_types
    
    def _extract_required_components(self, user_query: str) -> List[str]:
        """Extract required components from query"""
        components = []
        query_lower = user_query.lower()
        
        component_patterns = {
            'enricher': ['set properties', 'add headers', 'context', 'enrich'],
            'script': ['validation', 'transformation', 'processing', 'groovy'],
            'request_reply': ['api call', 'http', 'rest', 'service call'],
            'gateway': ['condition', 'branch', 'decision', 'route'],
            'message_mapping': ['mapping', 'transform', 'convert'],
            'sftp': ['sftp', 'file transfer', 'upload', 'download']
        }
        
        for component, keywords in component_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                components.append(component)
        
        # Add default components if none found
        if not components:
            components = ['enricher', 'script']
        
        return components
    
    def _extract_business_logic(self, user_query: str) -> List[str]:
        """Extract business logic requirements from query"""
        logic = []
        query_lower = user_query.lower()
        
        logic_patterns = {
            'validation': ['validate', 'check', 'verify'],
            'transformation': ['transform', 'convert', 'map'],
            'routing': ['route', 'direct', 'send to'],
            'notification': ['notify', 'alert', 'email']
        }
        
        for logic_type, keywords in logic_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                logic.append(logic_type)
        
        return logic
    
    def _extract_error_handling(self, user_query: str) -> List[str]:
        """Extract error handling requirements from query"""
        error_handling = []
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['error', 'exception', 'failure']):
            error_handling.append('exception_handling')
        if any(word in query_lower for word in ['retry', 'attempt']):
            error_handling.append('retry_mechanism')
        if any(word in query_lower for word in ['notify', 'alert']):
            error_handling.append('notification')
        
        return error_handling
    
    def _assess_complexity(self, user_query: str) -> str:
        """Assess complexity level of the integration"""
        query_lower = user_query.lower()
        
        # Simple indicators
        if any(word in query_lower for word in ['simple', 'basic', 'straightforward']):
            return 'simple'
        
        # Complex indicators
        complex_indicators = ['multiple', 'conditional', 'routing', 'transformation', 'validation']
        if sum(1 for indicator in complex_indicators if indicator in query_lower) >= 2:
            return 'complex'
        
        return 'medium'
    
    def _extract_component_keywords(self, user_query: str) -> List[str]:
        """Extract component-specific keywords"""
        keywords = []
        query_lower = user_query.lower()
        
        component_keywords = ['script', 'mapping', 'gateway', 'filter', 'enricher']
        for keyword in component_keywords:
            if keyword in query_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _extract_asset_keywords(self, user_query: str) -> List[str]:
        """Extract asset-specific keywords"""
        keywords = []
        query_lower = user_query.lower()
        
        asset_keywords = ['groovy', 'xml', 'wsdl', 'xsd', 'mapping']
        for keyword in asset_keywords:
            if keyword in query_lower:
                keywords.append(keyword)
        
        return keywords

    def _generate_intelligent_blueprint(self, selected_content: Dict[str, Any],
                                       user_intent: UserIntent, start_time: float) -> Dict[str, Any]:
        """Generate intelligent blueprint from selected content"""
        try:
            # Get the appropriate template
            template = self.blueprint_templates.get(user_intent.integration_type,
                                                   self.blueprint_templates['sync'])

            # Generate package info
            package_info = self._generate_package_info(user_intent)

            # Generate iFlow definition with real components
            iflow_definition = self._generate_iflow_definition(selected_content, user_intent)

            # Generate package assets
            package_assets = self._generate_package_assets(selected_content)

            # Generate metadata
            generation_metadata = self._generate_blueprint_metadata(
                selected_content, user_intent, start_time
            )

            # Assemble final blueprint
            blueprint = {
                'package_info': package_info,
                'iflow_definition': iflow_definition,
                'package_assets': package_assets,
                'generation_metadata': generation_metadata,
                'user_query': user_intent.original_query,
                'blueprint_version': '2.0',
                'generator_type': 'enhanced_intelligent'
            }

            return blueprint

        except Exception as e:
            logger.error(f"Error generating intelligent blueprint: {e}")
            return self._create_fallback_blueprint(user_intent.original_query, str(e))

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
            'data_types': user_intent.data_types
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
        description += ". Generated from real iFlow components and assets using intelligent analysis."

        return description

    def _generate_iflow_definition(self, selected_content: Dict[str, Any],
                                  user_intent: UserIntent) -> Dict[str, Any]:
        """Generate iFlow definition with real components"""
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

        # Generate intelligent flow sequence from GPT design
        flow_sequence = [step.get('component_id', '') for step in flow_design.get('flow_sequence', [])]

        return {
            'iflow_id': iflow_id,
            'iflow_name': iflow_name,
            'description': user_intent.original_query,
            'bpmn_structure': bpmn_structure,
            'flow_sequence': flow_sequence,
            'integration_pattern': user_intent.integration_type,
            'complexity_assessment': user_intent.complexity_level
        }

    def _build_bpmn_structure(self, core_components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build BPMN structure from selected components"""
        start_events = []
        activities = []
        gateways = []
        end_events = []

        for component in core_components:
            activity_type = component.get('activity_type', '').lower()

            # Categorize components
            if 'start' in activity_type or 'begin' in activity_type:
                start_events.append(self._format_component_for_bpmn(component))
            elif 'end' in activity_type or 'terminate' in activity_type:
                end_events.append(self._format_component_for_bpmn(component))
            elif 'gateway' in activity_type:
                gateways.append(self._format_component_for_bpmn(component))
            else:
                activities.append(self._format_component_for_bpmn(component))

        return {
            'start_events': start_events,
            'activities': activities,
            'gateways': gateways,
            'end_events': end_events,
            'total_components': len(core_components)
        }

    def _format_component_for_bpmn(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Format component for BPMN structure"""
        return {
            'id': component.get('component_id', f"Component_{uuid.uuid4().hex[:8]}"),
            'name': component.get('description', 'Component')[:50],  # Limit name length
            'type': component.get('activity_type', 'serviceTask').lower(),
            'properties': component.get('properties', {}),
            'bpmn_xml': component.get('complete_bpmn_xml', ''),
            'description': component.get('description', ''),
            'relevance_score': component.get('relevance_score', 0.0),
            'match_reasons': component.get('match_reasons', []),
            'is_essential': component.get('is_essential', False)
        }

    def _generate_flow_sequence(self, core_components: List[Dict[str, Any]],
                               user_intent: UserIntent) -> List[str]:
        """Generate logical flow sequence"""
        # Sort components by priority and relevance
        sorted_components = sorted(
            core_components,
            key=lambda x: (x.get('is_essential', False), x.get('relevance_score', 0)),
            reverse=True
        )

        # Create flow sequence
        flow_sequence = []

        # Add start event
        flow_sequence.append('StartEvent_1')

        # Add components in logical order
        for i, component in enumerate(sorted_components):
            component_id = component.get('component_id', f'Component_{i+1}')
            flow_sequence.append(component_id)

        # Add end event
        flow_sequence.append('EndEvent_1')

        return flow_sequence

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
                'gpt_priority': asset.get('gpt_priority', 'medium')
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
            'asset_coverage_analysis': selected_content.get('selection_metadata', {}).get('coverage_analysis', {})
        }

        return assets

    def _generate_blueprint_metadata(self, selected_content: Dict[str, Any],
                                   user_intent: UserIntent, start_time: float) -> Dict[str, Any]:
        """Generate comprehensive metadata about the blueprint"""
        processing_time = time.time() - start_time

        return {
            'generation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'processing_time_seconds': round(processing_time, 2),
            'query_confidence': user_intent.confidence_score,
            'selection_confidence': selected_content.get('selection_metadata', {}).get('selection_confidence', 0.0),
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
            'generator_version': '2.0',
            'intelligence_level': 'enhanced'
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
                'complexity_level': 'simple'
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
                'complexity_assessment': 'simple'
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
                'total_components': 0,
                'total_assets': 0,
                'integration_pattern': 'sync',
                'complexity_level': 'simple',
                'error_message': error_message,
                'is_fallback': True
            },
            'user_query': user_query,
            'blueprint_version': '2.0',
            'generator_type': 'enhanced_intelligent_fallback'
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
    
    def _extract_flow_keywords(self, user_query: str) -> List[str]:
        """Extract flow-specific keywords"""
        keywords = []
        query_lower = user_query.lower()
        
        flow_keywords = ['flow', 'connection', 'sequence', 'process']
        for keyword in flow_keywords:
            if keyword in query_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _extract_package_keywords(self, user_query: str) -> List[str]:
        """Extract package-specific keywords"""
        keywords = []
        query_lower = user_query.lower()
        
        package_keywords = ['package', 'integration', 'iflow', 'process']
        for keyword in package_keywords:
            if keyword in query_lower:
                keywords.append(keyword)
        
        return keywords
