#!/usr/bin/env python3
"""
Knowledge Graph Connector for RAG Prime
Integrates Neo4j knowledge graph for enhanced component selection and flow optimization
"""

import logging
import sys
import os
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
from collections import defaultdict, Counter

# Note: Emojis removed for Windows compatibility

# Neo4j Configuration
NEO4J_CONFIG = {
    'uri': 'neo4j+s://a09ee8ee.databases.neo4j.io',
    'username': 'neo4j',
    'password': 'X1hAOjlDuAPAMLE3cA7inKb5RQL6JHKeJeV57hKQ_YY',
    'database': 'neo4j'
}

logger = logging.getLogger(__name__)

@dataclass
class ComponentRelationship:
    """Represents a relationship between components"""
    source_type: str
    target_type: str
    relationship_type: str
    frequency: int
    confidence: float

@dataclass
class FlowPattern:
    """Represents a flow pattern in the knowledge graph"""
    pattern: List[str]
    frequency: int
    confidence: float
    relationships: List[str]

@dataclass
class ComponentRecommendation:
    """Component recommendation based on knowledge graph analysis"""
    component_type: str
    confidence: float
    reasoning: str
    next_components: List[str]
    usage_context: str

class KnowledgeGraphConnector:
    """
    Connector for integrating Neo4j knowledge graph with RAG Prime system
    """
    
    def __init__(self):
        """Initialize Neo4j connection and load knowledge graph insights"""
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG['uri'],
            auth=(NEO4J_CONFIG['username'], NEO4J_CONFIG['password'])
        )
        
        # Load knowledge graph insights
        self.component_relationships = self._load_component_relationships()
        self.flow_patterns = self._load_flow_patterns()
        self.component_frequencies = self._load_component_frequencies()
        
        logger.info("Knowledge Graph Connector initialized with insights")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def _load_component_relationships(self) -> Dict[str, List[ComponentRelationship]]:
        """Load component relationships from knowledge graph"""
        logger.info("Loading component relationships from knowledge graph...")
        
        with self.driver.session() as session:
            query = """
            MATCH (source:Component)-[r]->(target:Component)
            RETURN 
                source.type as source_type,
                type(r) as relationship_type,
                target.type as target_type,
                count(r) as frequency
            ORDER BY frequency DESC
            """
            
            results = session.run(query).data()
            
            relationships = defaultdict(list)
            total_relationships = sum(r['frequency'] for r in results)
            
            for result in results:
                confidence = result['frequency'] / total_relationships
                rel = ComponentRelationship(
                    source_type=result['source_type'],
                    target_type=result['target_type'],
                    relationship_type=result['relationship_type'],
                    frequency=result['frequency'],
                    confidence=confidence
                )
                relationships[result['source_type']].append(rel)
            
            logger.info(f"Loaded {len(relationships)} component relationship types")
            return dict(relationships)
    
    def _load_flow_patterns(self) -> List[FlowPattern]:
        """Load common flow patterns from knowledge graph"""
        logger.info("Loading flow patterns from knowledge graph...")
        
        with self.driver.session() as session:
            # Get 2-step patterns
            query_2 = """
            MATCH (a:Component)-[r1]->(b:Component)-[r2]->(c:Component)
            RETURN 
                [a.type, b.type, c.type] as pattern,
                [type(r1), type(r2)] as relationships,
                count(*) as frequency
            ORDER BY frequency DESC
            LIMIT 50
            """
            
            results_2 = session.run(query_2).data()
            
            # Get 3-step patterns
            query_3 = """
            MATCH (a:Component)-[r1]->(b:Component)-[r2]->(c:Component)-[r3]->(d:Component)
            RETURN 
                [a.type, b.type, c.type, d.type] as pattern,
                [type(r1), type(r2), type(r3)] as relationships,
                count(*) as frequency
            ORDER BY frequency DESC
            LIMIT 30
            """
            
            results_3 = session.run(query_3).data()
            
            patterns = []
            total_patterns = sum(r['frequency'] for r in results_2 + results_3)
            
            for result in results_2 + results_3:
                confidence = result['frequency'] / total_patterns
                pattern = FlowPattern(
                    pattern=result['pattern'],
                    frequency=result['frequency'],
                    confidence=confidence,
                    relationships=result['relationships']
                )
                patterns.append(pattern)
            
            logger.info(f"Loaded {len(patterns)} flow patterns")
            return patterns
    
    def _load_component_frequencies(self) -> Dict[str, int]:
        """Load component type frequencies"""
        logger.info("Loading component frequencies...")
        
        with self.driver.session() as session:
            query = """
            MATCH (c:Component)
            RETURN c.type as component_type, count(c) as frequency
            ORDER BY frequency DESC
            """
            
            results = session.run(query).data()
            frequencies = {r['component_type']: r['frequency'] for r in results}
            
            logger.info(f"Loaded frequencies for {len(frequencies)} component types")
            return frequencies
    
    def get_component_recommendations(self, current_components: List[str], 
                                    integration_type: str = "sync") -> List[ComponentRecommendation]:
        """Get component recommendations based on current components and integration type"""
        logger.info(f"Getting component recommendations for {current_components}")
        
        recommendations = []
        
        # If no components yet, recommend starting components
        if not current_components:
            start_recommendations = self._get_start_component_recommendations(integration_type)
            recommendations.extend(start_recommendations)
        else:
            # Get next component recommendations based on current components
            for component in current_components:
                next_recommendations = self._get_next_component_recommendations(component)
                recommendations.extend(next_recommendations)
        
        # Remove duplicates and sort by confidence
        unique_recommendations = {}
        for rec in recommendations:
            if rec.component_type not in unique_recommendations:
                unique_recommendations[rec.component_type] = rec
            elif rec.confidence > unique_recommendations[rec.component_type].confidence:
                unique_recommendations[rec.component_type] = rec
        
        sorted_recommendations = sorted(
            unique_recommendations.values(),
            key=lambda x: x.confidence,
            reverse=True
        )
        
        return sorted_recommendations[:10]  # Return top 10 recommendations
    
    def _get_start_component_recommendations(self, integration_type: str) -> List[ComponentRecommendation]:
        """Get recommendations for starting components based on integration type"""
        recommendations = []
        
        # Based on knowledge graph analysis, StartEvent is the most common starting point
        if integration_type in ["sync", "batch", "event_driven", "api_gateway"]:
            recommendations.append(ComponentRecommendation(
                component_type="StartEvent",
                confidence=0.95,
                reasoning="Most common starting component in knowledge graph",
                next_components=["CallActivity", "ExclusiveGateway"],
                usage_context="Integration entry point"
            ))
        
        return recommendations
    
    def _get_next_component_recommendations(self, current_component: str) -> List[ComponentRecommendation]:
        """Get next component recommendations based on current component"""
        recommendations = []
        
        if current_component in self.component_relationships:
            relationships = self.component_relationships[current_component]
            
            for rel in relationships[:5]:  # Top 5 relationships
                confidence = rel.confidence
                reasoning = f"Common pattern: {current_component} -> {rel.target_type} ({rel.frequency} times)"
                
                # Get next components for the target
                next_components = []
                if rel.target_type in self.component_relationships:
                    next_components = [r.target_type for r in self.component_relationships[rel.target_type][:3]]
                
                recommendations.append(ComponentRecommendation(
                    component_type=rel.target_type,
                    confidence=confidence,
                    reasoning=reasoning,
                    next_components=next_components,
                    usage_context=f"Follows {current_component} in {rel.frequency} flows"
                ))
        
        return recommendations
    
    def find_optimal_flow_path(self, start_component: str, end_component: str, 
                              max_length: int = 4) -> List[List[str]]:
        """Find optimal flow paths between components using knowledge graph"""
        logger.info(f"Finding optimal flow path: {start_component} -> {end_component}")
        
        with self.driver.session() as session:
            # Fix Neo4j query syntax - use string formatting for variable length paths
            query = f"""
            MATCH path = (start:Component {{type: $start_type}})-[*1..{max_length}]->(end:Component {{type: $end_type}})
            RETURN 
                [node in nodes(path) | node.type] as component_sequence,
                length(path) as path_length
            ORDER BY path_length
            LIMIT 10
            """
            
            results = session.run(query, 
                                start_type=start_component, 
                                end_type=end_component).data()
            
            paths = [result['component_sequence'] for result in results]
            
            logger.info(f"Found {len(paths)} optimal paths")
            return paths
    
    def get_flow_pattern_suggestions(self, current_flow: List[str]) -> List[FlowPattern]:
        """Get flow pattern suggestions based on current flow"""
        logger.info(f"Getting flow pattern suggestions for: {current_flow}")
        
        suggestions = []
        current_length = len(current_flow)
        
        # Find patterns that start with current flow
        for pattern in self.flow_patterns:
            if len(pattern.pattern) > current_length:
                # Check if current flow matches the beginning of the pattern
                if pattern.pattern[:current_length] == current_flow:
                    suggestions.append(pattern)
        
        # Sort by confidence and frequency
        suggestions.sort(key=lambda x: (x.confidence, x.frequency), reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def analyze_component_compatibility(self, components: List[str]) -> Dict[str, Any]:
        """Analyze compatibility between components based on knowledge graph"""
        logger.info(f"Analyzing compatibility for components: {components}")
        
        compatibility_score = 0.0
        compatibility_issues = []
        strengths = []
        
        # Check if components form a valid flow pattern
        for i in range(len(components) - 1):
            current = components[i]
            next_comp = components[i + 1]
            
            # Check if this transition exists in knowledge graph
            if current in self.component_relationships:
                relationships = self.component_relationships[current]
                found_relationship = False
                
                for rel in relationships:
                    if rel.target_type == next_comp:
                        compatibility_score += rel.confidence
                        strengths.append(f"{current} -> {next_comp} (confidence: {rel.confidence:.2f})")
                        found_relationship = True
                        break
                
                if not found_relationship:
                    compatibility_issues.append(f"No direct relationship found: {current} -> {next_comp}")
        
        # Normalize score
        if len(components) > 1:
            compatibility_score = compatibility_score / (len(components) - 1)
        
        return {
            'compatibility_score': compatibility_score,
            'compatibility_issues': compatibility_issues,
            'strengths': strengths,
            'recommendation': 'Good flow' if compatibility_score > 0.5 else 'Consider alternative flow'
        }
    
    def get_integration_pattern_insights(self, integration_type: str) -> Dict[str, Any]:
        """Get insights for specific integration patterns"""
        logger.info(f"Getting insights for integration pattern: {integration_type}")
        
        # This would be enhanced with more sophisticated pattern matching
        # For now, return basic insights based on knowledge graph analysis
        
        insights = {
            'recommended_start': "StartEvent",
            'common_components': ["CallActivity", "ExclusiveGateway", "ServiceTask"],
            'typical_flow_length': 3,
            'common_patterns': [
                ["StartEvent", "CallActivity", "EndEvent"],
                ["StartEvent", "ExclusiveGateway", "CallActivity", "EndEvent"],
                ["StartEvent", "CallActivity", "ServiceTask", "EndEvent"]
            ]
        }
        
        return insights
    
    def enhance_component_selection(self, retrieved_components: List[Dict[str, Any]], 
                                  user_intent: Any) -> List[Dict[str, Any]]:
        """Enhance component selection using knowledge graph insights"""
        logger.info("Enhancing component selection with knowledge graph insights")
        
        enhanced_components = []
        
        for component in retrieved_components:
            component_type = component.get('activity_type', '').lower()
            
            # Add knowledge graph insights
            kg_insights = {
                'kg_frequency': self.component_frequencies.get(component_type, 0),
                'kg_confidence': self._calculate_kg_confidence(component_type),
                'kg_recommendations': self._get_kg_recommendations(component_type),
                'kg_usage_context': self._get_kg_usage_context(component_type)
            }
            
            # Enhance component with KG insights
            enhanced_component = component.copy()
            enhanced_component['kg_insights'] = kg_insights
            
            # Boost relevance score based on KG insights
            original_score = component.get('relevance_score', 0.5)
            kg_boost = kg_insights['kg_confidence'] * 0.2  # 20% boost from KG
            enhanced_component['relevance_score'] = min(original_score + kg_boost, 1.0)
            
            enhanced_components.append(enhanced_component)
        
        # Sort by enhanced relevance score
        enhanced_components.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return enhanced_components
    
    def _calculate_kg_confidence(self, component_type: str) -> float:
        """Calculate confidence score based on knowledge graph frequency"""
        if component_type not in self.component_frequencies:
            return 0.1
        
        max_frequency = max(self.component_frequencies.values())
        return self.component_frequencies[component_type] / max_frequency
    
    def _get_kg_recommendations(self, component_type: str) -> List[str]:
        """Get KG-based recommendations for component"""
        if component_type in self.component_relationships:
            relationships = self.component_relationships[component_type]
            return [rel.target_type for rel in relationships[:3]]
        return []
    
    def _get_kg_usage_context(self, component_type: str) -> str:
        """Get usage context for component based on KG"""
        if component_type in self.component_relationships:
            relationships = self.component_relationships[component_type]
            if relationships:
                most_common = relationships[0]
                return f"Commonly flows to {most_common.target_type} ({most_common.frequency} times)"
        return "Standard component usage"
    
    def generate_flow_optimization(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate flow optimization suggestions using knowledge graph"""
        logger.info("Generating flow optimization suggestions")
        
        component_types = [comp.get('activity_type', '') for comp in components]
        
        # Analyze current flow
        compatibility = self.analyze_component_compatibility(component_types)
        
        # Get flow pattern suggestions
        pattern_suggestions = self.get_flow_pattern_suggestions(component_types)
        
        # Generate optimization recommendations
        optimizations = {
            'current_flow_analysis': compatibility,
            'pattern_suggestions': [
                {
                    'pattern': pattern.pattern,
                    'confidence': pattern.confidence,
                    'frequency': pattern.frequency
                }
                for pattern in pattern_suggestions
            ],
            'optimization_score': compatibility['compatibility_score'],
            'recommendations': self._generate_optimization_recommendations(compatibility, pattern_suggestions)
        }
        
        return optimizations
    
    def _generate_optimization_recommendations(self, compatibility: Dict[str, Any], 
                                             pattern_suggestions: List[FlowPattern]) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        if compatibility['compatibility_score'] < 0.5:
            recommendations.append("Consider alternative component sequence based on knowledge graph patterns")
        
        if pattern_suggestions:
            best_pattern = pattern_suggestions[0]
            recommendations.append(f"Consider following pattern: {' -> '.join(best_pattern.pattern)}")
        
        if compatibility['compatibility_issues']:
            recommendations.append("Address compatibility issues in component flow")
        
        return recommendations

def main():
    """Test the Knowledge Graph Connector"""
    print("🚀 Testing Knowledge Graph Connector")
    print("=" * 50)
    
    kg_connector = KnowledgeGraphConnector()
    
    try:
        # Test component recommendations
        print("\n💡 Testing Component Recommendations...")
        recommendations = kg_connector.get_component_recommendations([], "sync")
        print(f"Start recommendations: {len(recommendations)}")
        for rec in recommendations[:3]:
            print(f"   {rec.component_type}: {rec.confidence:.2f} - {rec.reasoning}")
        
        # Test flow path finding
        print("\n🎯 Testing Flow Path Finding...")
        paths = kg_connector.find_optimal_flow_path("StartEvent", "EndEvent")
        print(f"Found {len(paths)} paths from StartEvent to EndEvent")
        for i, path in enumerate(paths[:3], 1):
            print(f"   Path {i}: {' -> '.join(path)}")
        
        # Test flow optimization
        print("\n🔧 Testing Flow Optimization...")
        test_components = [
            {"activity_type": "StartEvent"},
            {"activity_type": "CallActivity"},
            {"activity_type": "EndEvent"}
        ]
        optimization = kg_connector.generate_flow_optimization(test_components)
        print(f"Optimization score: {optimization['optimization_score']:.2f}")
        print(f"Recommendations: {optimization['recommendations']}")
        
        print("\n✅ Knowledge Graph Connector test completed!")
        
    except Exception as e:
        print(f"❌ Error testing Knowledge Graph Connector: {e}")
        logger.error(f"Error testing Knowledge Graph Connector: {e}")
    
    finally:
        kg_connector.close()

if __name__ == "__main__":
    main()
