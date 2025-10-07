#!/usr/bin/env python3
"""
GPT-5 Powered Intelligent Content Selector
Uses GPT-5 for smart component selection and intelligent flow design
"""

import logging
import json
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI

# Add current directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
from config import OPENAI_CONFIG, KG_INTEGRATION_CONFIG
from knowledge_graph_connector import KnowledgeGraphConnector

logger = logging.getLogger(__name__)

@dataclass
class ComponentScore:
    """Component with calculated relevance score"""
    component: Dict[str, Any]
    relevance_score: float
    match_reasons: List[str]
    priority_level: str  # high, medium, low
    component_type: str
    is_essential: bool

@dataclass
class UserIntent:
    """User intent structure"""
    integration_type: str
    source_systems: List[str]
    target_systems: List[str]
    data_types: List[str]
    required_components: List[str]
    business_logic: List[str]
    error_handling: List[str]
    complexity_level: str
    description_keywords: List[str]
    component_keywords: List[str]
    asset_keywords: List[str]
    flow_keywords: List[str]
    package_keywords: List[str]
    confidence_score: float
    original_query: str

class GPTPoweredContentSelector:
    """
    GPT-5 powered intelligent content selector for optimal component selection
    """

    def __init__(self):
        """Initialize the GPT-powered content selector"""
        self.openai_client = OpenAI(api_key=OPENAI_CONFIG['api_key'])
        
        # Initialize Knowledge Graph Connector if enabled
        self.kg_connector = None
        if KG_INTEGRATION_CONFIG.get('enabled', False):
            try:
                self.kg_connector = KnowledgeGraphConnector()
                logger.info("Knowledge Graph Connector initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Knowledge Graph Connector: {e}")
                self.kg_connector = None

        # Component priority mapping based on integration patterns
        self.component_priorities = {
            'sync': {
                'essential': ['enricher', 'script', 'request_reply'],
                'recommended': ['filter', 'message_mapping'],
                'optional': ['gateway', 'aggregator']
            },
            'batch': {
                'essential': ['enricher', 'script', 'sftp'],
                'recommended': ['filter', 'message_mapping', 'aggregator'],
                'optional': ['gateway', 'splitter']
            },
            'event_driven': {
                'essential': ['enricher', 'gateway', 'script'],
                'recommended': ['filter', 'request_reply'],
                'optional': ['message_mapping', 'aggregator']
            },
            'api_gateway': {
                'essential': ['enricher', 'gateway', 'request_reply'],
                'recommended': ['script', 'filter'],
                'optional': ['message_mapping']
            }
        }
        
        # Component type scoring weights
        self.component_weights = {
            'activity_type_match': 0.4,
            'description_relevance': 0.25,
            'bpmn_xml_quality': 0.15,
            'system_integration': 0.1,
            'business_logic_match': 0.1
        }
        
        # Asset type priorities
        self.asset_priorities = {
            'groovy': 0.4,  # Scripts are highly valuable
            'mmap': 0.3,    # Message mappings
            'wsdl': 0.2,    # Service definitions
            'xsd': 0.1      # Schemas
        }
        
        logger.info("GPT-Powered Content Selector initialized")

    def select_optimal_components(self, retrieved_content: Dict[str, Any],
                                 user_intent: UserIntent) -> Dict[str, Any]:
        """
        GPT-5 powered intelligent selection of optimal components
        """
        logger.info(f"GPT-5 selecting optimal components for {user_intent.integration_type} integration")

        try:
            # Use GPT-5 to intelligently analyze and select components
            intelligent_selection = self._gpt_analyze_and_select_components(
                retrieved_content, user_intent
            )

            # Apply GPT recommendations to actual component selection
            selected_components = self._apply_gpt_component_selection(
                retrieved_content.get('components', []),
                intelligent_selection.get('component_recommendations', [])
            )
            
            # Enhance with Knowledge Graph insights if available
            if self.kg_connector and KG_INTEGRATION_CONFIG.get('enabled', False):
                selected_components = self.kg_connector.enhance_component_selection(
                    selected_components, user_intent
                )
                logger.info("Enhanced component selection with Knowledge Graph insights")

            # Apply GPT recommendations to asset selection
            selected_assets = self._apply_gpt_asset_selection(
                retrieved_content.get('assets', []),
                intelligent_selection.get('asset_recommendations', [])
            )

            # Generate intelligent flow connections using GPT-5
            connection_flows = self._generate_intelligent_flows(
                selected_components, intelligent_selection.get('flow_design', {})
            )

            # Select reference packages
            selected_packages = self._select_reference_packages(
                retrieved_content.get('packages', []), user_intent
            )

            selected_content = {
                'core_components': selected_components,
                'supporting_assets': selected_assets,
                'connection_flows': connection_flows,
                'reference_packages': selected_packages,
                'selection_metadata': {
                    'gpt_analysis': intelligent_selection,
                    'selection_confidence': intelligent_selection.get('confidence_score', 0.8),
                    'selection_reasoning': intelligent_selection.get('selection_reasoning', ''),
                    'flow_logic': intelligent_selection.get('flow_design', {}),
                    'coverage_analysis': self._analyze_requirement_coverage(
                        selected_components, selected_assets
                    )
                }
            }

            logger.info(f"GPT-5 selected {len(selected_components)} components, "
                       f"{len(selected_assets)} assets with confidence: "
                       f"{intelligent_selection.get('confidence_score', 0.8):.2f}")

            return selected_content

        except Exception as e:
            logger.error(f"Error in GPT-powered content selection: {e}")
            return self._create_fallback_selection(retrieved_content, user_intent)

    def _gpt_analyze_and_select_components(self, retrieved_content: Dict[str, Any],
                                          user_intent: UserIntent) -> Dict[str, Any]:
        """Use GPT-5 to intelligently analyze retrieved components and make optimal selections"""

        # Prepare component summaries for GPT analysis
        component_summaries = []
        for i, component in enumerate(retrieved_content.get('components', [])[:20]):  # Limit to top 20
            summary = {
                'index': i,
                'id': component.get('component_id', f'comp_{i}'),
                'activity_type': component.get('activity_type', 'unknown'),
                'description': component.get('description', '')[:200],  # Truncate for token efficiency
                'properties': component.get('properties', {}),
                'has_bpmn_xml': bool(component.get('complete_bpmn_xml')),
                'related_scripts': len(component.get('related_scripts', []))
            }
            component_summaries.append(summary)

        # Prepare asset summaries
        asset_summaries = []
        for i, asset in enumerate(retrieved_content.get('assets', [])[:15]):  # Limit to top 15
            summary = {
                'index': i,
                'file_name': asset.get('file_name', f'asset_{i}'),
                'file_type': asset.get('file_type', 'unknown'),
                'description': asset.get('description', '')[:150],
                'has_content': bool(asset.get('content')),
                'content_preview': asset.get('content', '')[:100] if asset.get('content') else ''
            }
            asset_summaries.append(summary)

        analysis_prompt = f"""
You are an expert SAP Integration Suite architect with deep knowledge of iFlow design patterns and component relationships.

TASK: Analyze the retrieved components and assets, then provide intelligent recommendations for optimal selection and flow design.

USER REQUIREMENTS:
- Integration Type: {user_intent.integration_type}
- Source Systems: {user_intent.source_systems}
- Target Systems: {user_intent.target_systems}
- Data Types: {user_intent.data_types}
- Required Operations: {user_intent.business_logic}
- Original Query: "{user_intent.original_query}"

AVAILABLE COMPONENTS:
{json.dumps(component_summaries, indent=2)}

AVAILABLE ASSETS:
{json.dumps(asset_summaries, indent=2)}

Please provide a comprehensive analysis and recommendations in JSON format:

{{
    "component_recommendations": [
        {{
            "component_index": 0,
            "selection_reason": "Why this component is essential/recommended",
            "priority": "essential|high|medium|low",
            "role_in_flow": "What role this component plays",
            "configuration_notes": "Key configuration considerations"
        }}
    ],
    "asset_recommendations": [
        {{
            "asset_index": 0,
            "selection_reason": "Why this asset is needed",
            "priority": "essential|high|medium|low",
            "usage_context": "How this asset will be used"
        }}
    ],
    "flow_design": {{
        "flow_pattern": "Description of the optimal flow pattern",
        "component_sequence": ["List of component IDs in execution order"],
        "connection_logic": {{
            "linear_connections": [["source_id", "target_id"]],
            "conditional_connections": [
                {{
                    "source_id": "gateway_id",
                    "conditions": [
                        {{"condition": "success", "target_id": "next_component"}},
                        {{"condition": "error", "target_id": "error_handler"}}
                    ]
                }}
            ]
        }},
        "error_handling_strategy": "How errors should be handled",
        "performance_considerations": "Performance optimization notes"
    }},
    "selection_reasoning": "Overall reasoning for the selections made",
    "confidence_score": 0.0-1.0,
    "integration_completeness": "Assessment of how well the selection meets requirements",
    "potential_gaps": ["Any missing components or capabilities"],
    "optimization_suggestions": ["Ways to improve the integration"]
}}

Focus on:
1. Selecting components that work well together
2. Ensuring proper data flow and transformation
3. Including appropriate error handling
4. Optimizing for the specific integration pattern
5. Considering system compatibility and performance

Provide only the JSON response, no additional text.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=OPENAI_CONFIG['component_selection_model'],
                messages=[
                    {"role": "system", "content": "You are an expert SAP Integration Suite architect. Provide detailed, accurate analysis in JSON format only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_completion_tokens=3000
            )

            analysis_text = response.choices[0].message.content.strip()

            # Parse JSON response
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()

            analysis = json.loads(analysis_text)
            logger.info(f"GPT-5 component analysis completed with confidence: {analysis.get('confidence_score', 'unknown')}")

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT component analysis JSON: {e}")
            return self._create_basic_component_analysis(user_intent)
        except Exception as e:
            logger.error(f"Error in GPT component analysis: {e}")
            return self._create_basic_component_analysis(user_intent)

    def _apply_gpt_component_selection(self, components: List[Dict[str, Any]],
                                      recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply GPT recommendations to select actual components"""
        selected_components = []

        for rec in recommendations:
            component_index = rec.get('component_index', -1)
            if 0 <= component_index < len(components):
                component = components[component_index].copy()

                # Enhance component with GPT insights
                component['gpt_selection_reason'] = rec.get('selection_reason', '')
                component['gpt_priority'] = rec.get('priority', 'medium')
                component['gpt_role_in_flow'] = rec.get('role_in_flow', '')
                component['gpt_config_notes'] = rec.get('configuration_notes', '')
                component['is_essential'] = rec.get('priority') in ['essential', 'high']
                component['relevance_score'] = self._priority_to_score(rec.get('priority', 'medium'))

                selected_components.append(component)

        return selected_components

    def _apply_gpt_asset_selection(self, assets: List[Dict[str, Any]],
                                  recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply GPT recommendations to select actual assets"""
        selected_assets = []

        for rec in recommendations:
            asset_index = rec.get('asset_index', -1)
            if 0 <= asset_index < len(assets):
                asset = assets[asset_index].copy()

                # Enhance asset with GPT insights
                asset['gpt_selection_reason'] = rec.get('selection_reason', '')
                asset['gpt_priority'] = rec.get('priority', 'medium')
                asset['gpt_usage_context'] = rec.get('usage_context', '')
                asset['relevance_score'] = self._priority_to_score(rec.get('priority', 'medium'))

                selected_assets.append(asset)

        return selected_assets

    def _generate_intelligent_flows(self, components: List[Dict[str, Any]],
                                   flow_design: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent flow connections based on GPT recommendations"""
        flows = []

        # Linear connections
        linear_connections = flow_design.get('connection_logic', {}).get('linear_connections', [])
        for source_id, target_id in linear_connections:
            flows.append({
                'source_component_id': source_id,
                'target_component_id': target_id,
                'flow_type': 'sequence',
                'connection_logic': 'linear',
                'gpt_reasoning': 'Sequential flow connection'
            })

        # Conditional connections
        conditional_connections = flow_design.get('connection_logic', {}).get('conditional_connections', [])
        for conn in conditional_connections:
            source_id = conn.get('source_id')
            for condition in conn.get('conditions', []):
                flows.append({
                    'source_component_id': source_id,
                    'target_component_id': condition.get('target_id'),
                    'flow_type': 'conditional',
                    'condition': condition.get('condition'),
                    'connection_logic': 'conditional',
                    'gpt_reasoning': f"Conditional flow for: {condition.get('condition')}"
                })

        return flows

    def _priority_to_score(self, priority: str) -> float:
        """Convert priority to numerical score"""
        priority_scores = {
            'essential': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        return priority_scores.get(priority.lower(), 0.6)

    def _create_basic_component_analysis(self, user_intent: UserIntent) -> Dict[str, Any]:
        """Create basic analysis when GPT analysis fails"""
        return {
            'component_recommendations': [
                {
                    'component_index': 0,
                    'selection_reason': 'Basic component for integration',
                    'priority': 'high',
                    'role_in_flow': 'Processing',
                    'configuration_notes': 'Standard configuration'
                }
            ],
            'asset_recommendations': [],
            'flow_design': {
                'flow_pattern': 'Linear processing',
                'component_sequence': [],
                'connection_logic': {
                    'linear_connections': [],
                    'conditional_connections': []
                },
                'error_handling_strategy': 'Basic error handling',
                'performance_considerations': 'Standard performance'
            },
            'selection_reasoning': 'Fallback selection due to analysis failure',
            'confidence_score': 0.5,
            'integration_completeness': 'Basic coverage',
            'potential_gaps': ['Limited analysis available'],
            'optimization_suggestions': ['Consider manual review']
        }

    def _analyze_requirement_coverage(self, selected_components: List[Dict[str, Any]],
                                    selected_assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well the selected components and assets cover the requirements"""
        return {
            'component_coverage': len(selected_components) / max(1, len(selected_components)),
            'asset_coverage': len(selected_assets) / max(1, len(selected_assets)),
            'overall_coverage': 0.8,
            'coverage_gaps': [],
            'coverage_strengths': ['Basic component selection', 'Asset inclusion']
        }

    def _create_fallback_selection(self, retrieved_content: Dict[str, Any],
                                  user_intent: UserIntent) -> Dict[str, Any]:
        """Create fallback selection when GPT analysis fails"""
        # Select first few components as fallback
        components = retrieved_content.get('components', [])[:3]
        assets = retrieved_content.get('assets', [])[:2]

        # Create a basic analysis - handle case where user_intent might be wrong type
        try:
            if hasattr(user_intent, 'original_query'):
                basic_analysis = self._create_basic_component_analysis(user_intent)
            else:
                # Create a dummy UserIntent if we got the wrong type
                from smart_database_retriever import UserIntent
                dummy_intent = UserIntent(
                    integration_type='sync',
                    source_systems=[],
                    target_systems=[],
                    data_types=[],
                    required_components=[],
                    business_logic=[],
                    error_handling=[],
                    complexity_level='medium',
                    description_keywords=[],
                    component_keywords=[],
                    asset_keywords=[],
                    flow_keywords=[],
                    package_keywords=[],
                    confidence_score=0.5,
                    original_query='fallback query'
                )
                basic_analysis = self._create_basic_component_analysis(dummy_intent)
        except Exception as e:
            logger.error(f"Error creating basic analysis: {e}")
            basic_analysis = {
                'component_recommendations': [],
                'asset_recommendations': [],
                'flow_design': {},
                'selection_reasoning': 'Fallback analysis due to error',
                'confidence_score': 0.3
            }

        return {
            'core_components': components,
            'supporting_assets': assets,
            'connection_flows': [],
            'reference_packages': [],
            'selection_metadata': {
                'gpt_analysis': basic_analysis,
                'selection_confidence': 0.5,
                'selection_reasoning': 'Fallback selection due to GPT analysis failure',
                'flow_logic': {},
                'coverage_analysis': self._analyze_requirement_coverage(components, assets)
            }
        }
    
    def _score_all_components(self, components: List[Dict[str, Any]], 
                             user_intent: UserIntent) -> List[ComponentScore]:
        """Score all components based on user requirements"""
        scored_components = []
        
        for component in components:
            score = self._calculate_component_score(component, user_intent)
            
            if score.relevance_score > 0.3:  # Only include relevant components
                scored_components.append(score)
        
        # Sort by relevance score
        scored_components.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Scored {len(scored_components)} relevant components")
        return scored_components
    
    def _calculate_component_score(self, component: Dict[str, Any], 
                                  user_intent: UserIntent) -> ComponentScore:
        """Calculate detailed score for a component"""
        activity_type = component.get('activity_type', '').lower()
        description = component.get('description', '').lower()
        bpmn_xml = component.get('complete_bpmn_xml', '')
        
        # Initialize scoring
        total_score = 0.0
        match_reasons = []
        
        # 1. Activity type match (40% weight)
        required_components = getattr(user_intent, 'required_components', []) if hasattr(user_intent, 'required_components') else []
        activity_score = self._score_activity_type_match(activity_type, required_components)
        total_score += activity_score * self.component_weights['activity_type_match']
        if activity_score > 0.5:
            match_reasons.append(f"Activity type match: {activity_type}")
        
        # 2. Description relevance (25% weight)
        desc_score = self._score_description_relevance(description, user_intent)
        total_score += desc_score * self.component_weights['description_relevance']
        if desc_score > 0.5:
            match_reasons.append("Description relevance")
        
        # 3. BPMN XML quality (15% weight)
        xml_score = self._score_bpmn_xml_quality(bpmn_xml)
        total_score += xml_score * self.component_weights['bpmn_xml_quality']
        if xml_score > 0.7:
            match_reasons.append("High-quality BPMN XML")
        
        # 4. System integration relevance (10% weight)
        system_score = self._score_system_integration(component, user_intent)
        total_score += system_score * self.component_weights['system_integration']
        if system_score > 0.5:
            match_reasons.append("System integration match")
        
        # 5. Business logic match (10% weight)
        logic_score = self._score_business_logic_match(component, user_intent.business_logic)
        total_score += logic_score * self.component_weights['business_logic_match']
        if logic_score > 0.5:
            match_reasons.append("Business logic match")
        
        # Determine priority level and essentiality
        integration_type = getattr(user_intent, 'integration_type', 'sync') if hasattr(user_intent, 'integration_type') else 'sync'
        required_components = getattr(user_intent, 'required_components', []) if hasattr(user_intent, 'required_components') else []
        priority_level, is_essential = self._determine_component_priority(
            activity_type, integration_type, required_components
        )
        
        return ComponentScore(
            component=component,
            relevance_score=min(total_score, 1.0),
            match_reasons=match_reasons,
            priority_level=priority_level,
            component_type=activity_type,
            is_essential=is_essential
        )
    
    def _score_activity_type_match(self, activity_type: str, required_components: List[str]) -> float:
        """Score how well activity type matches requirements"""
        if not required_components:
            return 0.5  # Neutral score if no specific requirements
        
        # Direct match
        for req_comp in required_components:
            if req_comp.lower() in activity_type or activity_type in req_comp.lower():
                return 1.0
        
        # Partial match
        activity_keywords = activity_type.split()
        for keyword in activity_keywords:
            for req_comp in required_components:
                if keyword in req_comp.lower() or req_comp.lower() in keyword:
                    return 0.7
        
        return 0.2  # Low score for no match
    
    def _score_description_relevance(self, description: str, user_intent: UserIntent) -> float:
        """Score description relevance to user intent"""
        if not description:
            return 0.1
        
        score = 0.0
        
        # Check for integration type keywords
        if user_intent.integration_type.lower() in description:
            score += 0.3
        
        # Check for system keywords
        all_systems = user_intent.source_systems + user_intent.target_systems
        for system in all_systems:
            if system.lower() in description:
                score += 0.2
                break
        
        # Check for data type keywords
        for data_type in user_intent.data_types:
            if data_type.lower() in description:
                score += 0.2
                break
        
        # Check for business logic keywords
        for logic in user_intent.business_logic:
            if logic.lower() in description:
                score += 0.1
        
        # Check for general description keywords
        keyword_matches = sum(1 for keyword in user_intent.description_keywords 
                             if keyword.lower() in description and len(keyword) > 3)
        if keyword_matches > 0:
            score += min(keyword_matches * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _score_bpmn_xml_quality(self, bpmn_xml: str) -> float:
        """Score the quality and completeness of BPMN XML"""
        if not bpmn_xml:
            return 0.0
        
        score = 0.3  # Base score for having XML
        
        # Check for essential BPMN elements
        quality_indicators = [
            'extensionElements',  # Has configuration
            'property',          # Has properties
            'incoming',          # Has connections
            'outgoing',          # Has connections
            'BPMNShape',         # Has visual elements
            'BPMNEdge'           # Has flow connections
        ]
        
        for indicator in quality_indicators:
            if indicator in bpmn_xml:
                score += 0.1
        
        # Bonus for longer, more detailed XML
        if len(bpmn_xml) > 1000:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_system_integration(self, component: Dict[str, Any], user_intent: UserIntent) -> float:
        """Score system integration relevance"""
        score = 0.0
        
        # Check component description and properties for system mentions
        text_fields = [
            component.get('description', ''),
            str(component.get('properties', {})),
            component.get('complete_bpmn_xml', '')
        ]
        
        combined_text = ' '.join(text_fields).lower()
        
        all_systems = user_intent.source_systems + user_intent.target_systems
        for system in all_systems:
            if system.lower() in combined_text:
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def _score_business_logic_match(self, component: Dict[str, Any], business_logic: List[str]) -> float:
        """Score business logic implementation match"""
        if not business_logic:
            return 0.5
        
        score = 0.0
        
        # Check component for business logic keywords
        text_fields = [
            component.get('description', ''),
            component.get('activity_type', ''),
            str(component.get('properties', {}))
        ]
        
        combined_text = ' '.join(text_fields).lower()
        
        for logic in business_logic:
            if logic.lower() in combined_text:
                score += 0.3
        
        return min(score, 1.0)
    
    def _determine_component_priority(self, activity_type: str, integration_type: str, 
                                    required_components: List[str]) -> Tuple[str, bool]:
        """Determine component priority level and essentiality"""
        priorities = self.component_priorities.get(integration_type, {})
        
        # Check if component is in essential list
        essential_components = priorities.get('essential', [])
        for essential in essential_components:
            if essential.lower() in activity_type or activity_type in essential.lower():
                return 'high', True
        
        # Check if component is in recommended list
        recommended_components = priorities.get('recommended', [])
        for recommended in recommended_components:
            if recommended.lower() in activity_type or activity_type in recommended.lower():
                return 'medium', False
        
        # Check if explicitly required by user
        for req_comp in required_components:
            if req_comp.lower() in activity_type or activity_type in req_comp.lower():
                return 'high', True
        
        return 'low', False

    def _score_all_assets(self, assets: List[Dict[str, Any]],
                         user_intent: UserIntent) -> List[Dict[str, Any]]:
        """Score all assets based on user requirements"""
        scored_assets = []

        for asset in assets:
            score = self._calculate_asset_score(asset, user_intent)
            if score > 0.3:  # Only include relevant assets
                scored_assets.append({
                    **asset,
                    'relevance_score': score,
                    'asset_priority': self._get_asset_priority(asset)
                })

        # Sort by relevance score
        scored_assets.sort(key=lambda x: x['relevance_score'], reverse=True)

        return scored_assets

    def _calculate_asset_score(self, asset: Dict[str, Any], user_intent: UserIntent) -> float:
        """Calculate relevance score for an asset"""
        file_type = asset.get('file_type', '').lower()
        description = asset.get('description', '').lower()
        content = asset.get('content', '').lower()

        score = 0.0

        # File type priority
        type_priority = self.asset_priorities.get(file_type, 0.1)
        score += type_priority

        # Description relevance
        for keyword in user_intent.asset_keywords:
            if keyword.lower() in description:
                score += 0.2

        # Content relevance (for scripts)
        if file_type == 'groovy':
            for logic in user_intent.business_logic:
                if logic.lower() in content:
                    score += 0.2

        # System integration relevance
        all_systems = user_intent.source_systems + user_intent.target_systems
        for system in all_systems:
            if system.lower() in description or system.lower() in content:
                score += 0.1

        return min(score, 1.0)

    def _get_asset_priority(self, asset: Dict[str, Any]) -> str:
        """Get priority level for an asset"""
        file_type = asset.get('file_type', '').lower()

        if file_type in ['groovy', 'gsh']:
            return 'high'  # Scripts are high priority
        elif file_type in ['mmap', 'wsdl']:
            return 'medium'  # Mappings and services are medium
        else:
            return 'low'

    def _select_best_components(self, scored_components: List[ComponentScore],
                               user_intent: UserIntent) -> List[Dict[str, Any]]:
        """Select the best components based on requirements"""
        selected = []
        component_types_covered = set()

        # First, select all essential components
        for comp_score in scored_components:
            if comp_score.is_essential and len(selected) < 15:
                selected.append({
                    **comp_score.component,
                    'relevance_score': comp_score.relevance_score,
                    'match_reasons': comp_score.match_reasons,
                    'priority_level': comp_score.priority_level,
                    'is_essential': True,
                    'selection_reason': 'Essential for integration pattern'
                })
                component_types_covered.add(comp_score.component_type)

        # Then, select high-priority components
        for comp_score in scored_components:
            if (comp_score.priority_level == 'high' and
                not comp_score.is_essential and
                len(selected) < 15):

                selected.append({
                    **comp_score.component,
                    'relevance_score': comp_score.relevance_score,
                    'match_reasons': comp_score.match_reasons,
                    'priority_level': comp_score.priority_level,
                    'is_essential': False,
                    'selection_reason': 'High priority match'
                })
                component_types_covered.add(comp_score.component_type)

        # Finally, fill with medium-priority components for diversity
        for comp_score in scored_components:
            if (comp_score.priority_level == 'medium' and
                comp_score.component_type not in component_types_covered and
                len(selected) < 12):

                selected.append({
                    **comp_score.component,
                    'relevance_score': comp_score.relevance_score,
                    'match_reasons': comp_score.match_reasons,
                    'priority_level': comp_score.priority_level,
                    'is_essential': False,
                    'selection_reason': 'Diversity and completeness'
                })
                component_types_covered.add(comp_score.component_type)

        logger.info(f"Selected {len(selected)} components covering {len(component_types_covered)} types")
        return selected

    def _select_supporting_assets(self, scored_assets: List[Dict[str, Any]],
                                 user_intent: UserIntent) -> List[Dict[str, Any]]:
        """Select supporting assets"""
        selected = []
        asset_types_covered = set()

        # Prioritize high-value asset types
        priority_order = ['groovy', 'mmap', 'wsdl', 'xsd', 'properties']

        for asset_type in priority_order:
            type_assets = [asset for asset in scored_assets
                          if asset.get('file_type', '').lower() == asset_type]

            # Select top assets of this type
            for asset in type_assets[:2]:  # Max 2 per type
                if len(selected) < 10:
                    selected.append({
                        **asset,
                        'selection_reason': f'Top {asset_type} asset'
                    })
                    asset_types_covered.add(asset_type)

        logger.info(f"Selected {len(selected)} assets covering {len(asset_types_covered)} types")
        return selected

    def _select_relevant_flows(self, flows: List[Dict[str, Any]],
                              user_intent: UserIntent) -> List[Dict[str, Any]]:
        """Select relevant connection flows"""
        selected = []

        for flow in flows[:5]:  # Limit to top 5 flows
            # Score flow relevance
            description = flow.get('description', '').lower()
            flow_score = 0.0

            # Check for integration type relevance
            if user_intent.integration_type.lower() in description:
                flow_score += 0.4

            # Check for system relevance
            all_systems = user_intent.source_systems + user_intent.target_systems
            for system in all_systems:
                if system.lower() in description:
                    flow_score += 0.2
                    break

            if flow_score > 0.3:
                selected.append({
                    **flow,
                    'relevance_score': flow_score,
                    'selection_reason': 'Relevant flow pattern'
                })

        return selected

    def _select_reference_packages(self, packages: List[Dict[str, Any]],
                                  user_intent: UserIntent) -> List[Dict[str, Any]]:
        """Select reference packages for context"""
        selected = []

        for package in packages[:3]:  # Limit to top 3 packages
            selected.append({
                **package,
                'selection_reason': 'Reference package for pattern'
            })

        return selected

    def _generate_selection_metadata(self, selected_components: List[Dict[str, Any]],
                                   selected_assets: List[Dict[str, Any]],
                                   user_intent: UserIntent) -> Dict[str, Any]:
        """Generate metadata about the selection process"""
        component_types = [comp.get('activity_type', 'unknown') for comp in selected_components]
        asset_types = [asset.get('file_type', 'unknown') for asset in selected_assets]

        essential_count = sum(1 for comp in selected_components if comp.get('is_essential', False))

        return {
            'total_components_selected': len(selected_components),
            'total_assets_selected': len(selected_assets),
            'essential_components_count': essential_count,
            'component_types_covered': list(set(component_types)),
            'asset_types_covered': list(set(asset_types)),
            'integration_type': user_intent.integration_type,
            'complexity_level': user_intent.complexity_level,
            'selection_confidence': self._calculate_selection_confidence(
                selected_components, user_intent
            ),
            'coverage_analysis': self._analyze_requirement_coverage(
                selected_components, user_intent
            )
        }

    def _calculate_selection_confidence(self, selected_components: List[Dict[str, Any]],
                                      user_intent: UserIntent) -> float:
        """Calculate confidence in the selection"""
        if not selected_components:
            return 0.0

        # Base confidence from component relevance scores
        avg_relevance = sum(comp.get('relevance_score', 0) for comp in selected_components) / len(selected_components)

        # Bonus for having essential components
        essential_count = sum(1 for comp in selected_components if comp.get('is_essential', False))
        essential_bonus = min(essential_count * 0.1, 0.3)

        # Bonus for requirement coverage
        required_components = getattr(user_intent, 'required_components', []) if hasattr(user_intent, 'required_components') else []
        required_types = set(required_components)
        covered_types = set(comp.get('activity_type', '').lower() for comp in selected_components)
        coverage_ratio = len(required_types.intersection(covered_types)) / max(len(required_types), 1)
        coverage_bonus = coverage_ratio * 0.2

        total_confidence = avg_relevance + essential_bonus + coverage_bonus
        return min(total_confidence, 1.0)

    def _analyze_requirement_coverage(self, selected_components: List[Dict[str, Any]],
                                    user_intent: UserIntent) -> Dict[str, Any]:
        """Analyze how well the selection covers user requirements"""
        covered_components = set()
        missing_components = set()

        # Check component coverage
        selected_types = [comp.get('activity_type', '').lower() for comp in selected_components]

        required_components = getattr(user_intent, 'required_components', []) if hasattr(user_intent, 'required_components') else []
        for req_comp in required_components:
            is_covered = any(req_comp.lower() in sel_type or sel_type in req_comp.lower()
                           for sel_type in selected_types)
            if is_covered:
                covered_components.add(req_comp)
            else:
                missing_components.add(req_comp)

        return {
            'covered_components': list(covered_components),
            'missing_components': list(missing_components),
            'coverage_percentage': len(covered_components) / max(len(required_components), 1) * 100,
            'has_essential_components': any(comp.get('is_essential', False) for comp in selected_components),
            'component_diversity': len(set(selected_types))
        }
