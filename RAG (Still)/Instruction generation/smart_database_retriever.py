#!/usr/bin/env python3
"""
Smart Database Retriever
Intelligent retrieval based on user requirements with multi-dimensional search
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from supabase import create_client, Client
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from config import SUPABASE_CONFIG, VECTOR_SEARCH_CONFIG

logger = logging.getLogger(__name__)

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

@dataclass
class SearchResult:
    """Structured search result with relevance scoring"""
    content: Dict[str, Any]
    relevance_score: float
    match_reasons: List[str]
    source_table: str
    search_type: str

class SmartDatabaseRetriever:
    """
    Intelligent database retriever that searches based on user requirements
    """
    
    def __init__(self):
        """Initialize Supabase client and search strategies"""
        self.supabase: Client = create_client(
            SUPABASE_CONFIG['url'], 
            SUPABASE_CONFIG['service_key']
        )
        
        # Search strategy weights
        self.search_weights = {
            'exact_pattern_match': 0.4,
            'component_match': 0.25,
            'system_integration_match': 0.2,
            'business_logic_match': 0.1,
            'semantic_similarity': 0.05
        }
        
        # Relevance thresholds
        self.relevance_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        logger.info("SmartDatabaseRetriever initialized")
    
    def fetch_targeted_content(self, user_intent: UserIntent) -> Dict[str, Any]:
        """
        Intelligent retrieval based on user requirements
        """
        logger.info(f"Starting targeted content retrieval for intent: {user_intent.integration_type}")
        
        try:
            # Multi-dimensional search strategy
            search_results = {
                'exact_matches': self._find_exact_pattern_matches(user_intent),
                'component_matches': self._find_required_components(user_intent.required_components),
                'system_matches': self._find_system_integrations(
                    user_intent.source_systems, user_intent.target_systems
                ),
                'business_logic_matches': self._find_business_logic_patterns(user_intent.business_logic),
                'similar_packages': self._find_similar_complete_packages(user_intent),
                'semantic_matches': self._find_semantic_matches(user_intent)
            }
            
            # Combine and rank all results
            combined_results = self._combine_and_rank_results(search_results, user_intent)
            
            # Select optimal content based on user needs
            optimal_content = self._select_optimal_components(combined_results, user_intent)
            
            logger.info(f"Retrieved {len(optimal_content.get('components', []))} components, "
                       f"{len(optimal_content.get('assets', []))} assets")
            
            return optimal_content
            
        except Exception as e:
            logger.error(f"Error in targeted content retrieval: {e}")
            return {'components': [], 'assets': [], 'flows': [], 'packages': []}
    
    def _find_exact_pattern_matches(self, user_intent: UserIntent) -> List[SearchResult]:
        """Find exact pattern matches for the integration type"""
        results = []
        
        try:
            # Search in iflow_packages for similar integration patterns
            package_query = self.supabase.table('iflow_packages').select(
                'id, package_name, description, iflw_xml, metadata'
            ).ilike('description', f'%{user_intent.integration_type}%')
            
            # Add system-specific filters
            for system in user_intent.source_systems + user_intent.target_systems:
                package_query = package_query.or_(f'description.ilike.%{system}%')
            
            package_result = package_query.limit(10).execute()
            
            if package_result.data:
                for package in package_result.data:
                    relevance = self._calculate_package_relevance(package, user_intent)
                    if relevance > self.relevance_thresholds['low']:
                        results.append(SearchResult(
                            content=package,
                            relevance_score=relevance,
                            match_reasons=[f"Integration type: {user_intent.integration_type}"],
                            source_table='iflow_packages',
                            search_type='exact_pattern'
                        ))
            
            logger.info(f"Found {len(results)} exact pattern matches")
            return results
            
        except Exception as e:
            logger.error(f"Error in exact pattern matching: {e}")
            return []
    
    def _find_required_components(self, required_components: List[str]) -> List[SearchResult]:
        """Find components that match user requirements"""
        results = []
        
        try:
            for component_type in required_components:
                # Search in iflow_components
                component_query = self.supabase.table('iflow_components').select(
                    'id, package_id, component_id, activity_type, description, '
                    'complete_bpmn_xml, properties, related_scripts'
                ).or_(
                    f'activity_type.ilike.%{component_type}%,'
                    f'description.ilike.%{component_type}%'
                ).limit(5).execute()
                
                if component_query.data:
                    for component in component_query.data:
                        relevance = self._calculate_component_relevance(component, component_type)
                        if relevance > self.relevance_thresholds['low']:
                            results.append(SearchResult(
                                content=component,
                                relevance_score=relevance,
                                match_reasons=[f"Component type: {component_type}"],
                                source_table='iflow_components',
                                search_type='component_match'
                            ))
            
            logger.info(f"Found {len(results)} component matches")
            return results
            
        except Exception as e:
            logger.error(f"Error in component matching: {e}")
            return []
    
    def _find_system_integrations(self, source_systems: List[str], 
                                 target_systems: List[str]) -> List[SearchResult]:
        """Find integrations between specific systems"""
        results = []
        all_systems = source_systems + target_systems
        
        try:
            for system in all_systems:
                # Search across all tables for system mentions
                tables_to_search = [
                    ('iflow_packages', 'description'),
                    ('iflow_components', 'description'),
                    ('iflow_assets', 'description'),
                    ('iflow_flows', 'description')
                ]
                
                for table_name, column_name in tables_to_search:
                    system_query = self.supabase.table(table_name).select('*').ilike(
                        column_name, f'%{system}%'
                    ).limit(5).execute()
                    
                    if system_query.data:
                        for item in system_query.data:
                            relevance = self._calculate_system_relevance(item, system)
                            if relevance > self.relevance_thresholds['low']:
                                results.append(SearchResult(
                                    content=item,
                                    relevance_score=relevance,
                                    match_reasons=[f"System integration: {system}"],
                                    source_table=table_name,
                                    search_type='system_match'
                                ))
            
            logger.info(f"Found {len(results)} system integration matches")
            return results
            
        except Exception as e:
            logger.error(f"Error in system integration matching: {e}")
            return []
    
    def _find_business_logic_patterns(self, business_logic: List[str]) -> List[SearchResult]:
        """Find components that implement specific business logic"""
        results = []
        
        try:
            for logic_type in business_logic:
                # Search in assets for scripts that implement this logic
                asset_query = self.supabase.table('iflow_assets').select(
                    'id, package_id, file_name, file_type, description, content'
                ).or_(
                    f'description.ilike.%{logic_type}%,'
                    f'content.ilike.%{logic_type}%'
                ).eq('file_type', 'groovy').limit(5).execute()
                
                if asset_query.data:
                    for asset in asset_query.data:
                        relevance = self._calculate_logic_relevance(asset, logic_type)
                        if relevance > self.relevance_thresholds['low']:
                            results.append(SearchResult(
                                content=asset,
                                relevance_score=relevance,
                                match_reasons=[f"Business logic: {logic_type}"],
                                source_table='iflow_assets',
                                search_type='business_logic'
                            ))
            
            logger.info(f"Found {len(results)} business logic matches")
            return results
            
        except Exception as e:
            logger.error(f"Error in business logic matching: {e}")
            return []
    
    def _find_similar_complete_packages(self, user_intent: UserIntent) -> List[SearchResult]:
        """Find complete packages similar to user requirements"""
        results = []
        
        try:
            # Search for packages with similar complexity and integration type
            package_query = self.supabase.table('iflow_packages').select(
                'id, package_name, description, iflw_xml, metadata'
            )
            
            # Add filters based on user intent
            if user_intent.integration_type:
                package_query = package_query.ilike('description', f'%{user_intent.integration_type}%')
            
            package_result = package_query.limit(10).execute()
            
            if package_result.data:
                for package in package_result.data:
                    relevance = self._calculate_package_similarity(package, user_intent)
                    if relevance > self.relevance_thresholds['medium']:
                        results.append(SearchResult(
                            content=package,
                            relevance_score=relevance,
                            match_reasons=["Similar complete package"],
                            source_table='iflow_packages',
                            search_type='similar_package'
                        ))
            
            logger.info(f"Found {len(results)} similar complete packages")
            return results
            
        except Exception as e:
            logger.error(f"Error in finding similar packages: {e}")
            return []
    
    def _find_semantic_matches(self, user_intent: UserIntent) -> List[SearchResult]:
        """Find semantic matches using description keywords"""
        results = []
        
        try:
            # Use description keywords for broader semantic search
            for keyword in user_intent.description_keywords[:5]:  # Limit to top 5 keywords
                if len(keyword) > 3:  # Skip short words
                    # Search across descriptions in all tables
                    tables = ['iflow_packages', 'iflow_components', 'iflow_assets', 'iflow_flows']
                    
                    for table in tables:
                        semantic_query = self.supabase.table(table).select('*').ilike(
                            'description', f'%{keyword}%'
                        ).limit(3).execute()
                        
                        if semantic_query.data:
                            for item in semantic_query.data:
                                relevance = self._calculate_semantic_relevance(item, keyword)
                                if relevance > self.relevance_thresholds['low']:
                                    results.append(SearchResult(
                                        content=item,
                                        relevance_score=relevance,
                                        match_reasons=[f"Semantic match: {keyword}"],
                                        source_table=table,
                                        search_type='semantic'
                                    ))
            
            logger.info(f"Found {len(results)} semantic matches")
            return results

        except Exception as e:
            logger.error(f"Error in semantic matching: {e}")
            return []

    def _combine_and_rank_results(self, search_results: Dict[str, List[SearchResult]],
                                 user_intent: UserIntent) -> List[SearchResult]:
        """Combine all search results and rank by relevance"""
        all_results = []

        # Combine all results with weighted scores
        for search_type, results in search_results.items():
            weight = self.search_weights.get(search_type, 0.1)
            for result in results:
                # Apply weight to relevance score
                result.relevance_score *= weight
                all_results.append(result)

        # Remove duplicates based on content ID
        unique_results = self._remove_duplicate_results(all_results)

        # Sort by relevance score
        ranked_results = sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)

        logger.info(f"Combined and ranked {len(ranked_results)} unique results")
        return ranked_results

    def _select_optimal_components(self, ranked_results: List[SearchResult],
                                  user_intent: UserIntent) -> Dict[str, Any]:
        """Select optimal components based on user needs"""
        selected_content = {
            'components': [],
            'assets': [],
            'flows': [],
            'packages': []
        }

        # Group results by table
        results_by_table = {}
        for result in ranked_results:
            if result.source_table not in results_by_table:
                results_by_table[result.source_table] = []
            results_by_table[result.source_table].append(result)

        # Select best results from each table
        for table_name, results in results_by_table.items():
            if table_name == 'iflow_components':
                selected_content['components'] = self._select_best_components(
                    results, user_intent.required_components
                )
            elif table_name == 'iflow_assets':
                selected_content['assets'] = self._select_best_assets(
                    results, user_intent.asset_keywords
                )
            elif table_name == 'iflow_flows':
                selected_content['flows'] = self._select_best_flows(
                    results, user_intent.flow_keywords
                )
            elif table_name == 'iflow_packages':
                selected_content['packages'] = self._select_best_packages(
                    results, user_intent.integration_type
                )

        return selected_content

    def _select_best_components(self, component_results: List[SearchResult],
                               required_components: List[str]) -> List[Dict[str, Any]]:
        """Select the best components for user requirements"""
        selected = []
        component_types_found = set()

        for result in component_results:
            if len(selected) >= 10:  # Limit to top 10 components
                break

            component = result.content
            activity_type = component.get('activity_type', '').lower()

            # Prioritize components that match required types
            is_required = any(req_type.lower() in activity_type for req_type in required_components)

            # Avoid duplicates of the same type unless it's a required type
            if activity_type not in component_types_found or is_required:
                selected.append({
                    **component,
                    'relevance_score': result.relevance_score,
                    'match_reasons': result.match_reasons,
                    'is_required': is_required
                })
                component_types_found.add(activity_type)

        return selected

    def _select_best_assets(self, asset_results: List[SearchResult],
                           asset_keywords: List[str]) -> List[Dict[str, Any]]:
        """Select the best assets for user requirements"""
        selected = []
        asset_types_found = set()

        for result in asset_results:
            if len(selected) >= 8:  # Limit to top 8 assets
                break

            asset = result.content
            file_type = asset.get('file_type', '').lower()

            # Prioritize diverse asset types
            if file_type not in asset_types_found or result.relevance_score > 0.7:
                selected.append({
                    **asset,
                    'relevance_score': result.relevance_score,
                    'match_reasons': result.match_reasons
                })
                asset_types_found.add(file_type)

        return selected

    def _select_best_flows(self, flow_results: List[SearchResult],
                          flow_keywords: List[str]) -> List[Dict[str, Any]]:
        """Select the best flows for user requirements"""
        selected = []

        for result in flow_results:
            if len(selected) >= 5:  # Limit to top 5 flows
                break

            selected.append({
                **result.content,
                'relevance_score': result.relevance_score,
                'match_reasons': result.match_reasons
            })

        return selected

    def _select_best_packages(self, package_results: List[SearchResult],
                             integration_type: str) -> List[Dict[str, Any]]:
        """Select the best packages for reference"""
        selected = []

        for result in package_results:
            if len(selected) >= 3:  # Limit to top 3 packages
                break

            selected.append({
                **result.content,
                'relevance_score': result.relevance_score,
                'match_reasons': result.match_reasons
            })

        return selected

    # Relevance calculation methods
    def _calculate_package_relevance(self, package: Dict[str, Any], user_intent: UserIntent) -> float:
        """Calculate relevance score for a package"""
        score = 0.0
        description = package.get('description', '').lower()

        # Integration type match
        if user_intent.integration_type.lower() in description:
            score += 0.4

        # System matches
        for system in user_intent.source_systems + user_intent.target_systems:
            if system.lower() in description:
                score += 0.2

        # Data type matches
        for data_type in user_intent.data_types:
            if data_type.lower() in description:
                score += 0.1

        return min(score, 1.0)

    def _calculate_component_relevance(self, component: Dict[str, Any], component_type: str) -> float:
        """Calculate relevance score for a component"""
        score = 0.0
        activity_type = component.get('activity_type', '').lower()
        description = component.get('description', '').lower()

        # Exact activity type match
        if component_type.lower() in activity_type:
            score += 0.6

        # Description match
        if component_type.lower() in description:
            score += 0.3

        # Has BPMN XML (more valuable)
        if component.get('complete_bpmn_xml'):
            score += 0.1

        return min(score, 1.0)

    def _calculate_system_relevance(self, item: Dict[str, Any], system: str) -> float:
        """Calculate relevance score for system integration"""
        score = 0.0
        description = item.get('description', '').lower()

        # System name match
        if system.lower() in description:
            score += 0.5

        # Additional context
        if any(keyword in description for keyword in ['integration', 'sync', 'api']):
            score += 0.2

        return min(score, 1.0)

    def _calculate_logic_relevance(self, asset: Dict[str, Any], logic_type: str) -> float:
        """Calculate relevance score for business logic"""
        score = 0.0
        description = asset.get('description', '').lower()
        content = asset.get('content', '').lower()

        # Logic type in description
        if logic_type.lower() in description:
            score += 0.4

        # Logic type in content
        if logic_type.lower() in content:
            score += 0.3

        # Is Groovy script (more valuable for logic)
        if asset.get('file_type', '').lower() == 'groovy':
            score += 0.2

        return min(score, 1.0)

    def _calculate_package_similarity(self, package: Dict[str, Any], user_intent: UserIntent) -> float:
        """Calculate similarity score for complete packages"""
        return self._calculate_package_relevance(package, user_intent)

    def _calculate_semantic_relevance(self, item: Dict[str, Any], keyword: str) -> float:
        """Calculate semantic relevance score"""
        score = 0.0
        description = item.get('description', '').lower()

        if keyword.lower() in description:
            score += 0.3

        return min(score, 1.0)

    def _remove_duplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content ID"""
        seen_ids = set()
        unique_results = []

        for result in results:
            content_id = result.content.get('id')
            if content_id and content_id not in seen_ids:
                seen_ids.add(content_id)
                unique_results.append(result)
            elif not content_id:  # Handle items without ID
                unique_results.append(result)

        return unique_results
