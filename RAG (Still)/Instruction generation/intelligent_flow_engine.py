#!/usr/bin/env python3
"""
GPT-5 Powered Intelligent Flow Connection Engine
Creates intelligent component connections and flow sequences using GPT-5
"""

import logging
import json
import sys
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Add current directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
from config import OPENAI_CONFIG, KG_INTEGRATION_CONFIG
from knowledge_graph_connector import KnowledgeGraphConnector

logger = logging.getLogger(__name__)

class IntelligentFlowEngine:
    """
    GPT-5 powered engine for creating intelligent component flows and connections
    """
    
    def __init__(self):
        """Initialize the intelligent flow engine"""
        self.openai_client = OpenAI(api_key=OPENAI_CONFIG['api_key'])
        
        # Initialize Knowledge Graph Connector if enabled
        self.kg_connector = None
        if KG_INTEGRATION_CONFIG.get('enabled', False):
            try:
                self.kg_connector = KnowledgeGraphConnector()
                logger.info("Knowledge Graph Connector initialized for flow optimization")
            except Exception as e:
                logger.warning(f"Failed to initialize Knowledge Graph Connector: {e}")
                self.kg_connector = None
        
        logger.info("Intelligent Flow Engine initialized with GPT-5 and Knowledge Graph")
    
    def design_intelligent_flow(self, components: List[Dict[str, Any]], 
                               user_intent: Dict[str, Any],
                               gpt_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use GPT-5 to design intelligent component flow and connections
        """
        logger.info(f"Designing intelligent flow for {len(components)} components")
        
        try:
            # Prepare component information for GPT analysis
            component_info = []
            for i, comp in enumerate(components):
                info = {
                    'index': i,
                    'id': comp.get('component_id', f'comp_{i}'),
                    'name': comp.get('name', 'Unknown Component'),
                    'type': comp.get('activity_type', 'unknown'),
                    'description': comp.get('description', '')[:150],
                    'gpt_role': comp.get('gpt_role_in_flow', ''),
                    'gpt_priority': comp.get('gpt_priority', 'medium'),
                    'is_essential': comp.get('is_essential', False)
                }
                component_info.append(info)
            
            # Create GPT prompt for flow design
            flow_design_prompt = f"""
You are an expert SAP Integration Suite architect specializing in BPMN flow design and component orchestration.

TASK: Design an optimal flow sequence and connections for the given components based on the user requirements.

USER REQUIREMENTS:
- Integration Type: {user_intent.get('integration_type', 'sync')}
- Business Objective: {gpt_analysis.get('business_objective', 'Integration flow')}
- Source Systems: {user_intent.get('source_systems', [])}
- Target Systems: {user_intent.get('target_systems', [])}
- Data Types: {user_intent.get('data_types', [])}
- Required Operations: {user_intent.get('business_logic', [])}
- Original Query: "{user_intent.get('original_query', '')}"

AVAILABLE COMPONENTS:
{json.dumps(component_info, indent=2)}

EXISTING GPT ANALYSIS:
Flow Pattern: {gpt_analysis.get('flow_design', {}).get('flow_pattern', 'Not specified')}
Connection Logic: {gpt_analysis.get('flow_design', {}).get('connection_logic', {})}

Please design a comprehensive flow with the following JSON structure:

{{
    "flow_sequence": [
        {{
            "step": 1,
            "component_id": "component_id",
            "component_name": "readable_name",
            "purpose": "what this step accomplishes",
            "input_requirements": ["what data/conditions are needed"],
            "output_provides": ["what this step produces"],
            "error_scenarios": ["potential error conditions"]
        }}
    ],
    "connections": [
        {{
            "source_id": "source_component_id",
            "target_id": "target_component_id",
            "connection_type": "sequence|conditional|error|parallel",
            "condition": "condition for conditional connections",
            "reasoning": "why this connection is needed"
        }}
    ],
    "error_handling": {{
        "error_paths": [
            {{
                "error_source": "component_id",
                "error_type": "validation|system|network|business",
                "handler_component": "error_handler_id",
                "recovery_action": "retry|skip|abort|notify"
            }}
        ],
        "global_error_strategy": "overall error handling approach"
    }},
    "performance_optimization": {{
        "parallel_execution": [["comp1", "comp2"]],
        "bottleneck_components": ["component_ids"],
        "optimization_notes": "performance considerations"
    }},
    "data_flow": {{
        "data_transformations": [
            {{
                "at_component": "component_id",
                "transformation": "what data transformation occurs",
                "input_format": "expected input format",
                "output_format": "resulting output format"
            }}
        ],
        "data_validation_points": ["component_ids where validation occurs"]
    }},
    "integration_completeness": {{
        "requirements_coverage": "how well the flow meets requirements",
        "missing_elements": ["any missing components or logic"],
        "enhancement_suggestions": ["ways to improve the flow"]
    }},
    "flow_confidence": 0.0-1.0,
    "design_reasoning": "overall reasoning for the flow design"
}}

Focus on:
1. Logical sequence that makes business sense
2. Proper error handling and recovery
3. Data flow and transformation points
4. Performance optimization opportunities
5. Complete requirement coverage
6. Realistic component interactions

Provide only the JSON response, no additional text.
"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_CONFIG['flow_design_model'],
                messages=[
                    {"role": "system", "content": "You are an expert SAP Integration Suite architect specializing in BPMN flow design. Provide detailed, accurate flow design in JSON format only."},
                    {"role": "user", "content": flow_design_prompt}
                ],
                max_completion_tokens=4000
            )
            
            flow_design_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if flow_design_text.startswith('```json'):
                flow_design_text = flow_design_text.replace('```json', '').replace('```', '').strip()
            
            flow_design = json.loads(flow_design_text)
            logger.info(f"GPT-5 flow design completed with confidence: {flow_design.get('flow_confidence', 'unknown')}")
            
            # Enhance with Knowledge Graph insights if available
            if self.kg_connector and KG_INTEGRATION_CONFIG.get('enabled', False):
                flow_design = self._enhance_flow_with_kg_insights(flow_design, components, user_intent)
                logger.info("Enhanced flow design with Knowledge Graph insights")
            
            return flow_design
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT flow design JSON: {e}")
            return self._create_basic_flow_design(components, user_intent)
        except Exception as e:
            logger.error(f"Error in GPT flow design: {e}")
            return self._create_basic_flow_design(components, user_intent)
    
    def _create_basic_flow_design(self, components: List[Dict[str, Any]], 
                                 user_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic flow design when GPT analysis fails"""
        
        # Create simple sequential flow
        flow_sequence = []
        connections = []
        
        for i, comp in enumerate(components):
            flow_sequence.append({
                'step': i + 1,
                'component_id': comp.get('component_id', f'comp_{i}'),
                'component_name': comp.get('name', f'Component {i+1}'),
                'purpose': 'Process data',
                'input_requirements': ['Previous step output'],
                'output_provides': ['Processed data'],
                'error_scenarios': ['Processing failure']
            })
            
            # Create sequential connections
            if i > 0:
                connections.append({
                    'source_id': components[i-1].get('component_id', f'comp_{i-1}'),
                    'target_id': comp.get('component_id', f'comp_{i}'),
                    'connection_type': 'sequence',
                    'condition': None,
                    'reasoning': 'Sequential processing'
                })
        
        return {
            'flow_sequence': flow_sequence,
            'connections': connections,
            'error_handling': {
                'error_paths': [],
                'global_error_strategy': 'Basic error handling'
            },
            'performance_optimization': {
                'parallel_execution': [],
                'bottleneck_components': [],
                'optimization_notes': 'Sequential processing'
            },
            'data_flow': {
                'data_transformations': [],
                'data_validation_points': []
            },
            'integration_completeness': {
                'requirements_coverage': 'Basic coverage',
                'missing_elements': ['Advanced error handling'],
                'enhancement_suggestions': ['Add conditional logic', 'Improve error handling']
            },
            'flow_confidence': 0.6,
            'design_reasoning': 'Fallback sequential flow design'
        }
    
    def generate_bpmn_structure(self, flow_design: Dict[str, Any], 
                               components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate BPMN structure from intelligent flow design"""
        
        bpmn_structure = {
            'start_events': [{'id': 'StartEvent_1', 'name': 'Start'}],
            'activities': [],
            'gateways': [],
            'end_events': [{'id': 'EndEvent_1', 'name': 'End'}],
            'sequence_flows': [],
            'total_components': len(components)
        }
        
        # Add components as activities
        for comp in components:
            activity = {
                'id': comp.get('component_id', 'unknown'),
                'name': comp.get('name', 'Unknown Component'),
                'type': comp.get('activity_type', 'serviceTask').lower(),
                'properties': comp.get('properties', {}),
                'bpmn_xml': comp.get('complete_bpmn_xml', ''),
                'description': comp.get('description', ''),
                'relevance_score': comp.get('relevance_score', 0.8),
                'match_reasons': comp.get('match_reasons', []),
                'is_essential': comp.get('is_essential', False),
                'gpt_role_in_flow': comp.get('gpt_role_in_flow', ''),
                'gpt_selection_reason': comp.get('gpt_selection_reason', '')
            }
            bpmn_structure['activities'].append(activity)
        
        # Add sequence flows from connections
        for connection in flow_design.get('connections', []):
            sequence_flow = {
                'id': f"SequenceFlow_{connection['source_id']}_{connection['target_id']}",
                'source_ref': connection['source_id'],
                'target_ref': connection['target_id'],
                'connection_type': connection.get('connection_type', 'sequence'),
                'condition': connection.get('condition'),
                'gpt_reasoning': connection.get('reasoning', '')
            }
            bpmn_structure['sequence_flows'].append(sequence_flow)
        
        return bpmn_structure
    
    def _enhance_flow_with_kg_insights(self, flow_design: Dict[str, Any], 
                                     components: List[Dict[str, Any]], 
                                     user_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance flow design with knowledge graph insights"""
        try:
            # Get component types from the flow
            component_types = [comp.get('activity_type', '') for comp in components]
            
            # Get flow optimization from knowledge graph
            kg_optimization = self.kg_connector.generate_flow_optimization(components)
            
            # Get optimal flow paths if we have start and end components
            if len(component_types) >= 2:
                start_component = component_types[0]
                end_component = component_types[-1]
                optimal_paths = self.kg_connector.find_optimal_flow_path(start_component, end_component)
                
                # Add KG insights to flow design
                flow_design['kg_insights'] = {
                    'optimization_score': kg_optimization['optimization_score'],
                    'optimal_paths': optimal_paths[:3],  # Top 3 paths
                    'pattern_suggestions': kg_optimization['pattern_suggestions'],
                    'recommendations': kg_optimization['recommendations']
                }
                
                # Boost flow confidence based on KG optimization
                original_confidence = flow_design.get('flow_confidence', 0.5)
                kg_boost = kg_optimization['optimization_score'] * 0.1  # 10% boost
                flow_design['flow_confidence'] = min(original_confidence + kg_boost, 1.0)
                
                # Add KG-based flow sequence if available
                if optimal_paths:
                    best_path = optimal_paths[0]
                    flow_design['kg_flow_sequence'] = best_path
                    flow_design['kg_flow_reasoning'] = f"Based on knowledge graph analysis of {len(optimal_paths)} optimal paths"
            
            return flow_design
            
        except Exception as e:
            logger.error(f"Error enhancing flow with KG insights: {e}")
            return flow_design
