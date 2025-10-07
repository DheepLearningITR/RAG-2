#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Explorer
Explores the knowledge graph structure to understand component relationships
"""

import logging
import sys
import os
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import json

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Neo4j Configuration
NEO4J_CONFIG = {
    'uri': 'neo4j+s://a09ee8ee.databases.neo4j.io',
    'username': 'neo4j',
    'password': 'X1hAOjlDuAPAMLE3cA7inKb5RQL6JHKeJeV57hKQ_YY',
    'database': 'neo4j'
}

logger = logging.getLogger(__name__)

class Neo4jKnowledgeGraphExplorer:
    """
    Explorer for understanding the knowledge graph structure and relationships
    """
    
    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(
            NEO4J_CONFIG['uri'],
            auth=(NEO4J_CONFIG['username'], NEO4J_CONFIG['password'])
        )
        logger.info("Neo4j Knowledge Graph Explorer initialized")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def explore_graph_structure(self) -> Dict[str, Any]:
        """Explore the overall structure of the knowledge graph"""
        print("🔍 Exploring Knowledge Graph Structure...")
        
        with self.driver.session() as session:
            # Get all node labels
            node_labels = session.run("CALL db.labels()").data()
            print(f"📊 Node Labels: {[label['label'] for label in node_labels]}")
            
            # Get all relationship types
            rel_types = session.run("CALL db.relationshipTypes()").data()
            print(f"🔗 Relationship Types: {[rel['relationshipType'] for rel in rel_types]}")
            
            # Get node counts by label
            node_counts = {}
            for label in node_labels:
                count = session.run(f"MATCH (n:{label['label']}) RETURN count(n) as count").single()['count']
                node_counts[label['label']] = count
                print(f"   {label['label']}: {count} nodes")
            
            # Get relationship counts
            rel_counts = {}
            for rel_type in rel_types:
                count = session.run(f"MATCH ()-[r:{rel_type['relationshipType']}]->() RETURN count(r) as count").single()['count']
                rel_counts[rel_type['relationshipType']] = count
                print(f"   {rel_type['relationshipType']}: {count} relationships")
            
            return {
                'node_labels': [label['label'] for label in node_labels],
                'relationship_types': [rel['relationshipType'] for rel in rel_types],
                'node_counts': node_counts,
                'relationship_counts': rel_counts
            }
    
    def explore_component_relationships(self) -> Dict[str, Any]:
        """Explore component-specific relationships and patterns"""
        print("\n🔧 Exploring Component Relationships...")
        
        with self.driver.session() as session:
            # Find component-related nodes
            component_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label CONTAINS 'Component' OR label CONTAINS 'Activity' OR label CONTAINS 'Flow')
            RETURN DISTINCT labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            component_nodes = session.run(component_query).data()
            print("Component-related nodes:")
            for node in component_nodes:
                print(f"   {node['labels']}: {node['count']} nodes")
            
            # Find integration patterns
            pattern_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label CONTAINS 'Pattern' OR label CONTAINS 'Integration' OR label CONTAINS 'Flow')
            RETURN DISTINCT labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            pattern_nodes = session.run(pattern_query).data()
            print("\nIntegration pattern nodes:")
            for node in pattern_nodes:
                print(f"   {node['labels']}: {node['count']} nodes")
            
            # Find system-related nodes
            system_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label CONTAINS 'System' OR label CONTAINS 'SAP' OR label CONTAINS 'SuccessFactors')
            RETURN DISTINCT labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            system_nodes = session.run(system_query).data()
            print("\nSystem-related nodes:")
            for node in system_nodes:
                print(f"   {node['labels']}: {node['count']} nodes")
            
            return {
                'component_nodes': component_nodes,
                'pattern_nodes': pattern_nodes,
                'system_nodes': system_nodes
            }
    
    def explore_flow_patterns(self) -> Dict[str, Any]:
        """Explore flow patterns and component connections"""
        print("\n🌊 Exploring Flow Patterns...")
        
        with self.driver.session() as session:
            # Find flow relationships
            flow_query = """
            MATCH (source)-[r]->(target)
            WHERE any(rel_type in ['FLOWS_TO', 'CONNECTS_TO', 'SEQUENCE', 'NEXT', 'FOLLOWS'] 
                     WHERE type(r) = rel_type)
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
            
            flow_relationships = session.run(flow_query).data()
            print("Flow relationships:")
            for rel in flow_relationships:
                print(f"   {rel['relationship_type']}: {rel['count']} relationships")
            
            # Find component sequences
            sequence_query = """
            MATCH path = (start)-[r*1..3]->(end)
            WHERE any(rel_type in ['FLOWS_TO', 'CONNECTS_TO', 'SEQUENCE', 'NEXT', 'FOLLOWS'] 
                     WHERE any(rel in relationships(path) WHERE type(rel) = rel_type))
            RETURN length(path) as path_length, count(path) as count
            ORDER BY path_length, count DESC
            """
            
            sequences = session.run(sequence_query).data()
            print("\nComponent sequences:")
            for seq in sequences:
                print(f"   Path length {seq['path_length']}: {seq['count']} sequences")
            
            return {
                'flow_relationships': flow_relationships,
                'sequences': sequences
            }
    
    def get_sample_components(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample components with their properties"""
        print(f"\n📋 Getting Sample Components (limit: {limit})...")
        
        with self.driver.session() as session:
            # Get sample components
            sample_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label CONTAINS 'Component' OR label CONTAINS 'Activity')
            RETURN n, labels(n) as node_labels
            LIMIT $limit
            """
            
            components = session.run(sample_query, limit=limit).data()
            
            print("Sample components:")
            for i, comp in enumerate(components, 1):
                node = comp['n']
                labels = comp['node_labels']
                print(f"   {i}. Labels: {labels}")
                print(f"      Properties: {dict(node)}")
                print()
            
            return components
    
    def find_component_relationships(self, component_type: str = None) -> Dict[str, Any]:
        """Find relationships for specific component types"""
        print(f"\n🔍 Finding Component Relationships for: {component_type or 'All'}")
        
        with self.driver.session() as session:
            if component_type:
                # Find relationships for specific component type
                rel_query = """
                MATCH (source)-[r]->(target)
                WHERE any(label in labels(source) WHERE label CONTAINS $component_type)
                   OR any(label in labels(target) WHERE label CONTAINS $component_type)
                RETURN 
                    labels(source) as source_labels,
                    type(r) as relationship_type,
                    labels(target) as target_labels,
                    count(r) as count
                ORDER BY count DESC
                LIMIT 20
                """
                
                relationships = session.run(rel_query, component_type=component_type).data()
            else:
                # Find all component relationships
                rel_query = """
                MATCH (source)-[r]->(target)
                WHERE any(label in labels(source) WHERE label CONTAINS 'Component' OR label CONTAINS 'Activity')
                   OR any(label in labels(target) WHERE label CONTAINS 'Component' OR label CONTAINS 'Activity')
                RETURN 
                    labels(source) as source_labels,
                    type(r) as relationship_type,
                    labels(target) as target_labels,
                    count(r) as count
                ORDER BY count DESC
                LIMIT 20
                """
                
                relationships = session.run(rel_query).data()
            
            print("Component relationships:")
            for rel in relationships:
                print(f"   {rel['source_labels']} --[{rel['relationship_type']}]--> {rel['target_labels']} ({rel['count']} times)")
            
            return relationships
    
    def analyze_integration_patterns(self) -> Dict[str, Any]:
        """Analyze integration patterns in the knowledge graph"""
        print("\n🎯 Analyzing Integration Patterns...")
        
        with self.driver.session() as session:
            # Find pattern nodes and their relationships
            pattern_query = """
            MATCH (pattern)
            WHERE any(label in labels(pattern) WHERE label CONTAINS 'Pattern' OR label CONTAINS 'Integration')
            OPTIONAL MATCH (pattern)-[r]->(related)
            RETURN 
                pattern,
                labels(pattern) as pattern_labels,
                collect({
                    relationship: type(r),
                    target: labels(related),
                    target_props: properties(related)
                }) as relationships
            """
            
            patterns = session.run(pattern_query).data()
            
            print("Integration patterns found:")
            for pattern in patterns:
                node = pattern['pattern']
                labels = pattern['pattern_labels']
                relationships = pattern['relationships']
                
                print(f"   Pattern: {labels}")
                print(f"      Properties: {dict(node)}")
                print(f"      Relationships: {len(relationships)}")
                for rel in relationships[:3]:  # Show first 3 relationships
                    if rel['relationship']:
                        print(f"         --[{rel['relationship']}]--> {rel['target']}")
                print()
            
            return patterns
    
    def generate_graph_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive summary of the knowledge graph"""
        print("\n📊 Generating Knowledge Graph Summary...")
        
        summary = {
            'structure': self.explore_graph_structure(),
            'components': self.explore_component_relationships(),
            'flows': self.explore_flow_patterns(),
            'sample_components': self.get_sample_components(5),
            'patterns': self.analyze_integration_patterns()
        }
        
        # Save summary to file
        with open('kg_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("✅ Knowledge Graph summary saved to kg_summary.json")
        return summary

def main():
    """Main function to explore the knowledge graph"""
    print("🚀 Neo4j Knowledge Graph Explorer")
    print("=" * 50)
    
    explorer = Neo4jKnowledgeGraphExplorer()
    
    try:
        # Generate comprehensive summary
        summary = explorer.generate_graph_summary()
        
        print("\n🎉 Knowledge Graph exploration completed!")
        print("📁 Summary saved to: kg_summary.json")
        
    except Exception as e:
        print(f"❌ Error exploring knowledge graph: {e}")
        logger.error(f"Error exploring knowledge graph: {e}")
    
    finally:
        explorer.close()

if __name__ == "__main__":
    main()
