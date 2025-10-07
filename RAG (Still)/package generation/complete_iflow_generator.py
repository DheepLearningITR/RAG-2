#!/usr/bin/env python3
"""
Complete SAP CPI iFlow Generator
Single script that does everything: Supabase search, AI analysis, component validation, and package generation
"""

import json
import os
import re
import sys
import zipfile
import shutil
import subprocess
import requests
import google.generativeai as genai
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyDBsNt50RXURHniFlrcXHo-EPkKgXR4Z8M"
genai.configure(api_key=GEMINI_API_KEY)

# Supabase Configuration
SUPABASE_URL = "https://jnoobtfelhtjfermohfx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impub29idGZlbGh0amZlcm1vaGZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2NzE0MjIsImV4cCI6MjA3MTI0NzQyMn0.idtnXt4-jxsy3f6QpaB8aOzFPmSqRONtnGcfJRhpfiQ"

class CompleteIFlowGenerator:
    def __init__(self):
        print("🚀 Complete SAP CPI iFlow Generator initialized!")
        
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        # Initialize Gemini model
        try:
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            self.gemini_enabled = True
            print("✅ Gemini AI enabled for intelligent component selection and validation!")
        except Exception as e:
            print(f"⚠️ Gemini AI not enabled: {e}")
            self.gemini_enabled = False
    
    def search_supabase_components(self, query: str) -> List[Dict[str, Any]]:
        """Search for components in Supabase database - FIXED to only select actual processing components"""
        print(f"🔍 Searching Supabase for: '{query}'")
        
        try:
            all_components = []
            
            # Get only actual processing components from Supabase
            url = f"{SUPABASE_URL}/rest/v1/iflow_components"
            params = {"select": "*", "limit": 50}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            components = response.json()
            
            # Filter out metadata files and only include actual processing components
            for comp in components:
                activity_type = comp.get('activity_type', '').lower()
                component_id = comp.get('component_id', '').lower()
                
                # Skip metadata files and non-processing components
                if any(skip in component_id for skip in ['manifest', 'properties', 'metainfo', 'mf']):
                    continue
                if any(skip in activity_type for skip in ['asset', 'file', 'metadata', 'manifest']):
                    continue
                    
                # Only include actual processing components
                if activity_type in ['script', 'service', 'enricher', 'gateway', 'request_reply', 'mapping', 'directcall', 'externalcall']:
                    all_components.append(comp)
            
            # Search in scripts table - only for actual script components
            url_scripts = f"{SUPABASE_URL}/rest/v1/scripts"
            response_scripts = requests.get(url_scripts, headers=self.headers, params={"select": "*", "limit": 50})
            if response_scripts.status_code == 200:
                scripts = response_scripts.json()
                for script in scripts:
                    # Only include scripts with actual content
                    if script.get('script_content') and len(script.get('script_content', '').strip()) > 10:
                        component = {
                            "component_id": f"script_{script.get('id', '')}",
                            "activity_type": "Script",
                            "description": script.get('description', ''),
                            "script_content": script.get('script_content', ''),
                            "complete_bpmn_xml": f"<bpmn2:scriptTask id=\"script_{script.get('id', '')}\" name=\"{script.get('name', 'Script Task')}\"/>",
                            "source": "scripts_table"
                        }
                        all_components.append(component)
            
            print(f"✅ Found {len(all_components)} valid processing components from Supabase")
            return all_components
            
        except Exception as e:
            print(f"❌ Supabase search failed: {e}")
            return self._get_mock_components(query)
    
    def _get_mock_components(self, query: str) -> List[Dict[str, Any]]:
        """Fallback mock components for testing"""
        print("🔄 Using mock data for testing...")
        
        mock_components = [
            {
                "component_id": "ScriptTask_OrderValidation",
                "activity_type": "Script",
                "description": "Order validation and processing script with comprehensive business logic",
                "script_content": """// Order Validation and Processing Script
def order = new JsonSlurper().parseText(message)

// Validate required fields
if (!order.customerId || !order.items || order.items.isEmpty()) {
    throw new Exception('Invalid order data: Missing customer ID or items')
}

// Validate item availability
order.items.each { item ->
    if (!item.sku || !item.quantity || item.quantity <= 0) {
        throw new Exception('Invalid item data: SKU or quantity missing')
    }
}

// Calculate total amount
def totalAmount = order.items.sum { item -> item.price * item.quantity }
order.totalAmount = totalAmount

// Set processing timestamp
order.processedAt = new Date().format('yyyy-MM-dd HH:mm:ss')

// Log processing
log.info("Order validated successfully: ${order.orderId}, Total: ${totalAmount}")

return new JsonBuilder(order).toString()""",
                "complete_bpmn_xml": "<bpmn2:scriptTask id=\"ScriptTask_OrderValidation\" name=\"Order Validation Script\"/>",
                "source": "mock_data"
            },
            {
                "component_id": "Enricher_Context", 
                "activity_type": "Enricher",
                "description": "Enrich message with order context and processing properties",
                "complete_bpmn_xml": "<bpmn2:serviceTask id=\"Enricher_Context\" name=\"Context Enricher\"/>",
                "enricher_config": {
                    "properties": "order_id={{uuid}},processing_timestamp=now(),channel={{order_channel}},priority={{order_priority}},batch_id={{batch_id}}",
                    "headers": "Content-Type=application/json,X-Process-ID={{uuid}},X-Source=OrderProcessing"
                },
                "source": "mock_data"
            },
            {
                "component_id": "MessageMapping_Transform",
                "activity_type": "MessageMapping",
                "description": "Transform order data for target system integration",
                "complete_bpmn_xml": "<bpmn2:serviceTask id=\"MessageMapping_Transform\" name=\"Data Transformation\"/>",
                "mapping_config": {
                    "mapping_file": "src/main/resources/mapping/OrderTransformation.mmap",
                    "source_message": "OrderRequest",
                    "target_message": "OrderResponse"
                },
                "source": "mock_data"
            },
            {
                "component_id": "ExternalCall_API",
                "activity_type": "ExternalCall",
                "description": "Call external API for order validation and processing",
                "complete_bpmn_xml": "<bpmn2:serviceTask id=\"ExternalCall_API\" name=\"API Validation\"/>",
                "external_call_config": {
                    "endpoint_path": "/api/orders/validate",
                    "method": "POST",
                    "url": "{{ORDER_VALIDATION_SERVICE_URL}}/api/orders/validate",
                    "headers": "Content-Type=application/json,Authorization=Bearer {{ORDER_VALIDATION_TOKEN}},X-Request-ID={{uuid}}"
                },
                "source": "mock_data"
            },
            {
                "component_id": "Gateway_Router",
                "activity_type": "Gateway",
                "description": "Route orders based on validation results and business rules",
                "complete_bpmn_xml": "<bpmn2:exclusiveGateway id=\"Gateway_Router\" name=\"Order Router\"/>",
                "gateway_config": {
                    "gateway_type": "exclusive",
                    "routing_conditions": [
                        {
                            "condition": "${message.validation_result == 'VALID'}",
                            "target": "process_order",
                            "description": "Route valid orders to processing"
                        },
                        {
                            "condition": "${message.validation_result == 'INVALID'}",
                            "target": "handle_invalid_order",
                            "description": "Route invalid orders to error handling"
                        }
                    ]
                },
                "source": "mock_data"
            },
            {
                "component_id": "ScriptTask_Response",
                "activity_type": "Script",
                "description": "Format response message for order processing completion",
                "script_content": """// Response Formatting Script
def response = new JsonSlurper().parseText(message)

// Add processing status
response.status = 'PROCESSED'
response.processedAt = new Date().format('yyyy-MM-dd HH:mm:ss')
response.correlationId = UUID.randomUUID().toString()

// Log completion
log.info("Order processing completed: ${response.orderId}")

return new JsonBuilder(response).toString()""",
                "complete_bpmn_xml": "<bpmn2:scriptTask id=\"ScriptTask_Response\" name=\"Response Formatter\"/>",
                "source": "mock_data"
            }
        ]
        
        return mock_components
    
    def calculate_similarity_scores(self, query: str, components: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Calculate enhanced similarity scores between query and components"""
        print("🔍 Calculating enhanced similarity scores...")
        
        if not components:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_components = []
        
        for comp in components:
            comp_text_parts = []
            
            # Component description
            description = comp.get('description', '').lower()
            if description:
                comp_text_parts.append(description)
            
            # Activity type
            activity_type = comp.get('activity_type', '').lower()
            if activity_type:
                comp_text_parts.append(activity_type)
            
            # Component ID
            component_id = comp.get('component_id', '').lower()
            if component_id:
                comp_text_parts.append(component_id)
            
            comp_text = ' '.join(comp_text_parts)
            comp_words = set(comp_text.split())
            
            # Calculate similarity
            exact_matches = len(query_words.intersection(comp_words))
            exact_score = min(exact_matches / len(query_words), 1.0) if query_words else 0.0
            
            # Activity type bonus
            activity_bonus = 0.0
            if any(keyword in query for keyword in ['script', 'groovy']) and 'script' in activity_type:
                activity_bonus += 0.3
            if any(keyword in query for keyword in ['enricher', 'enrich']) and 'enricher' in activity_type:
                activity_bonus += 0.3
            
            final_score = exact_score * 0.7 + activity_bonus
            scored_components.append((comp, min(max(final_score, 0.0), 1.0)))
        
        scored_components.sort(key=lambda x: x[1], reverse=True)
        print(f"✅ Calculated similarity scores for {len(components)} components")
        return scored_components
    
    def analyze_query_with_ai(self, query: str, scored_components: List[Tuple[Dict[str, Any], float]]) -> Dict[str, Any]:
        """Use Gemini AI to analyze query and select best components"""
        print("🧠 Analyzing query with Gemini AI...")
        
        if not self.gemini_enabled:
            return self._fallback_analysis(query, [comp for comp, score in scored_components])
        
        try:
            # Prepare component summary for AI
            component_summary = []
            for comp, score in scored_components[:10]:
                summary = {
                    "id": comp.get("component_id", ""),
                    "type": comp.get("activity_type", ""),
                    "description": comp.get("description", ""),
                    "similarity_score": round(score, 3),
                    "has_script": "script_content" in comp,
                    "has_config": any(key.endswith("_config") for key in comp.keys())
                }
                component_summary.append(summary)
            
            # Create AI prompt
            prompt = f"""
            Analyze this iFlow query and select the best components from the available options.
            
            Query: "{query}"
            
            Available Components (with similarity scores):
            {json.dumps(component_summary, indent=2)}
            
            IMPORTANT SELECTION RULES:
            - PRIORITIZE components with HIGH similarity scores (>0.3)
            - If the query mentions "script", prioritize Script components
            - If the query mentions "enricher", prioritize Enricher components  
            - If the query mentions "order" or "validation", prioritize Enricher + Script components
            - Always include StartEvent and EndEvent for complete flow
            - Select components that match the query intent exactly
            - For business processes, prefer: Enricher (set context) → Script (validation) → Gateway (routing)
            
            Please provide a JSON response with:
            1. intent: The main intent of the query
            2. scenario: The business scenario
            3. selected_components: Array of component IDs to use (max 6)
            4. execution_order: Array showing the order of execution
            5. reasoning: Brief explanation of the selection
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Clean up response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
            
            print(f"✅ AI Analysis: {analysis.get('intent', 'Unknown')}")
            print(f"   Scenario: {analysis.get('scenario', 'Unknown')}")
            print(f"   Selected: {len(analysis.get('selected_components', []))} components")
            
            return analysis
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            print("🔄 Using fallback analysis with comprehensive mock data...")
            return self._fallback_analysis(query, [comp for comp, score in scored_components])
    
    def _fallback_analysis(self, query: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback analysis without AI"""
        print("🔄 Using fallback analysis...")
        
        query_lower = query.lower()
        
        if "order" in query_lower:
            intent = "ecommerce_order_processing"
            scenario = "E-Commerce Order Processing"
            selected_components = ["ScriptTask_OrderValidation", "Enricher_Context", "MessageMapping_Transform", "ExternalCall_API", "Gateway_Router", "ScriptTask_Response"]
        elif "customer" in query_lower:
            intent = "customer_synchronization"
            scenario = "Customer Data Synchronization"
            selected_components = ["Enricher_Context", "ScriptTask_OrderValidation", "ExternalCall_API", "MessageMapping_Transform"]
        else:
            intent = "general_processing"
            scenario = "General Data Processing"
            selected_components = ["ScriptTask_OrderValidation", "Enricher_Context", "MessageMapping_Transform", "ExternalCall_API"]
        
        return {
            "intent": intent,
            "scenario": scenario,
            "selected_components": selected_components,
            "execution_order": selected_components,
            "reasoning": f"Fallback analysis for {scenario}"
        }
    
    def validate_component_config(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix component configuration"""
        comp_type = component.get("type", "").lower()
        config = component.get("config", {})
        
        issues = []
        corrected_config = config.copy()
        
        if comp_type == "script":
            # Validate script content
            script_content = config.get("script_content", "")
            if not script_content or len(script_content.strip()) < 10:
                issues.append("Script content is too short or empty")
                corrected_config["script_content"] = self._generate_default_script(component)
            
            # Check for proper Groovy syntax
            if "def " not in script_content and "return " not in script_content:
                issues.append("Script lacks proper Groovy structure")
                corrected_config["script_content"] = self._generate_default_script(component)
        
        elif comp_type == "enricher":
            # Validate enricher properties
            properties = config.get("properties", "")
            if not properties:
                issues.append("Enricher properties are empty")
                corrected_config["properties"] = "component.id={{uuid}},timestamp=now(),process.type=enricher"
            
            headers = config.get("headers", "")
            if not headers:
                issues.append("Enricher headers are empty")
                corrected_config["headers"] = "Content-Type=application/json,X-Process-ID={{uuid}}"
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "corrected_config": corrected_config
        }
    
    def _generate_default_script(self, component: Dict[str, Any]) -> str:
        """Generate a default valid script based on component context"""
        comp_name = component.get("name", "").lower()
        
        if "validation" in comp_name or "validate" in comp_name:
            return """// Data Validation Script
def inputData = new JsonSlurper().parseText(message)

// Validate required fields
if (!inputData) {
    throw new Exception('Invalid input data: Message is null or empty')
}

// Add validation timestamp
inputData.validationTimestamp = new Date().format('yyyy-MM-dd HH:mm:ss')
inputData.validationStatus = 'VALIDATED'

// Log validation
log.info("Data validation completed successfully")

return new JsonBuilder(inputData).toString()"""
        
        else:
            return """// Data Processing Script
def inputData = new JsonSlurper().parseText(message)

// Process the data
def processedData = [
    data: inputData,
    processedAt: new Date().format('yyyy-MM-dd HH:mm:ss'),
    processedBy: 'Script Component'
]

// Log processing
log.info("Data processing completed successfully")

return new JsonBuilder(processedData).toString()"""
    
    def create_dynamic_json_blueprint(self, components: List[Dict[str, Any]], iflow_name: str, query: str, ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create dynamic JSON blueprint from components"""
        print("📋 Creating dynamic JSON blueprint...")
        
        # Create rich endpoint with validated components
        endpoint_components = []
        
        for i, component in enumerate(components):
            # Create proper component ID and type
            activity_type = component.get("activity_type", "").lower()
            component_id = f"{activity_type}_{i+1}" if activity_type else f"component_{i+1}"
            
            # Map component types properly
            if activity_type in ["startevent", "start_event"]:
                component_type = "startevent"
            elif activity_type in ["endevent", "end_event"]:
                component_type = "endevent"
            elif activity_type in ["flow", "sequence", "messageflow", "message"]:
                # Skip flow components as they're handled separately
                continue
            elif activity_type == "messagemapping":
                component_type = "message_mappings"
            elif activity_type == "externalcall":
                component_type = "externalcall"
            elif activity_type == "gateway":
                component_type = "gateway"
            else:
                component_type = activity_type
            
            # Create proper component name (short and descriptive)
            component_name = self._create_proper_component_name(component, activity_type, i+1)
            
            # Create rich component configuration based on type
            config = self._create_component_config(component, component_type)
            
            # Validate component configuration
            validation = self.validate_component_config({
                "type": component_type,
                "config": config
            })
            
            # Use corrected config if validation found issues
            if not validation["is_valid"]:
                config = validation["corrected_config"]
                print(f"   🔧 Fixed {len(validation['issues'])} issues in {component_id}")
            
            rich_component = {
                "type": component_type,
                "name": component_name,
                "id": component_id,
                "config": config,
                "source": component.get("source", "supabase")
            }
            
            endpoint_components.append(rich_component)
        
        # Create flow sequence
        flow = [comp["id"] for comp in endpoint_components]
        
        # Create dynamic blueprint
        blueprint = {
            "process_name": ai_analysis.get("scenario", iflow_name),
            "description": f"Generated iFlow for: {query}",
            "endpoints": [
                {
                    "id": "main_processing",
                    "name": ai_analysis.get("scenario", "Main Processing"),
                    "method": "POST",
                    "path": f"/{iflow_name.lower().replace('_', '-')}/process",
                    "purpose": f"Process {query.lower()}",
                    "components": endpoint_components,
                    "flow": flow
                }
            ],
            "metadata": {
                "generated_by": "Complete iFlow Generator",
                "query": query,
                "scenario": ai_analysis.get("scenario", "Custom"),
                "component_count": len(components),
                "ai_analysis": ai_analysis,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        print("✅ Dynamic JSON blueprint created!")
        return blueprint
    
    def _create_proper_component_name(self, component: Dict[str, Any], activity_type: str, index: int) -> str:
        """Create proper component name (short and descriptive)"""
        description = component.get("description", "")
        
        # Create short, meaningful names based on component type and description
        if activity_type == "script":
            if "validation" in description.lower():
                return "Order Validation Script"
            elif "process" in description.lower():
                return "Data Processing Script"
            else:
                return f"Script {index}"
        
        elif activity_type == "enricher":
            if "mapping" in description.lower():
                return "Data Mapping Enricher"
            elif "context" in description.lower():
                return "Context Enricher"
            else:
                return f"Enricher {index}"
        
        elif activity_type == "message_mappings":
            return "Message Mapping"
        
        elif activity_type == "properties_files":
            return "Properties File"
        
        elif activity_type == "wsdl_files":
            return "WSDL File"
        
        elif activity_type == "jsontoxmlconverter":
            return "JSON to XML Converter"
        
        else:
            # Extract meaningful words from description
            words = description.lower().split()[:4]  # Take first 4 words
            meaningful_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'component', 'identified', 'bpmn']]
            if meaningful_words:
                return ' '.join(meaningful_words).title()
            else:
                # Try to extract from component_id
                comp_id = component.get("component_id", "")
                if comp_id:
                    # Extract meaningful parts from component_id
                    id_parts = comp_id.replace("_", " ").replace("-", " ").split()
                    meaningful_parts = [p for p in id_parts if len(p) > 2 and p.lower() not in ['component', 'id', 'asset', 'script']]
                    if meaningful_parts:
                        return ' '.join(meaningful_parts).title()
                
                return f"Component {index}"
    
    def _create_component_config(self, component: Dict[str, Any], component_type: str) -> Dict[str, Any]:
        """Create proper component configuration based on type"""
        if component_type == "script":
            script_content = component.get("script_content", "")
            if not script_content:
                script_content = self._generate_default_script(component)
            
            return {
                "script_content": script_content,
                "script_file": f"{component.get('component_id', 'script')}.groovy"
            }
        
        elif component_type == "enricher":
            # Use existing enricher config or create default
            if "enricher_config" in component:
                return component["enricher_config"]
            else:
                return {
                    "properties": "order_id={{uuid}},processing_timestamp=now(),channel=web,priority=normal,batch_id={{batch_id}},status=processing",
                    "headers": "Content-Type=application/json,X-Process-ID={{uuid}},X-Source=OrderProcessing,X-Version=1.0",
                    "bodyType": "expression",
                    "propertyTable": "{}",
                    "headerTable": "{}"
                }
        
        elif component_type == "message_mappings":
            return {
                "mapping_file": "src/main/resources/mapping/OrderTransformation.mmap",
                "source_message": "OrderRequest",
                "target_message": "OrderResponse",
                "mapping_type": "XML_to_JSON",
                "description": "Message mapping for order data transformation"
            }
        
        elif component_type == "properties_files":
            return {
                "properties_file": component.get("asset_path", "properties.prop"),
                "properties_content": component.get("asset_content", ""),
                "description": "Properties file for configuration"
            }
        
        elif component_type == "wsdl_files":
            return {
                "wsdl_file": component.get("asset_path", "service.wsdl"),
                "wsdl_content": component.get("asset_content", ""),
                "description": "WSDL file for service definition"
            }
        
        elif component_type == "externalcall":
            return {
                "endpoint_path": "/api/orders/validate",
                "method": "POST",
                "url": "{{ORDER_VALIDATION_SERVICE_URL}}/api/orders/validate",
                "headers": "Content-Type=application/json,Authorization=Bearer {{ORDER_VALIDATION_TOKEN}},X-Request-ID={{uuid}}",
                "timeout": 30000,
                "retry_count": 3,
                "description": "External API call for order validation"
            }
        
        elif component_type == "gateway":
            return {
                "gateway_type": "exclusive",
                "routing_conditions": [
                    {
                        "condition": "${message.validation_result == 'VALID'}",
                        "target": "process_order",
                        "description": "Route valid orders to processing"
                    },
                    {
                        "condition": "${message.validation_result == 'INVALID'}",
                        "target": "handle_invalid_order",
                        "description": "Route invalid orders to error handling"
                    }
                ],
                "description": "Gateway for order routing decisions"
            }
        
        elif component_type == "jsontoxmlconverter":
            return {
                "conversion_type": "JSON to XML",
                "description": "JSON to XML conversion"
            }
        
        else:
            return {
                "component_type": component_type,
                "description": component.get("description", "Default component"),
                "version": "1.0",
                "enabled": "true"
            }
    
    def create_sap_cpi_package(self, blueprint: Dict[str, Any], iflow_name: str, output_dir: str = "output") -> str:
        """Create complete SAP CPI package from blueprint"""
        print(f"🏗️ Creating SAP CPI package: {iflow_name}")
        
        # Create output directory
        output_path = Path(output_dir)
        iflow_dir = output_path / iflow_name
        iflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package structure
        self._create_package_structure(iflow_dir, iflow_name)
        
        # Generate BPMN XML
        bpmn_xml = self._generate_bpmn_xml(blueprint, iflow_name)
        
        # Write BPMN file
        iflow_file = iflow_dir / "src" / "main" / "resources" / "scenarioflows" / "integrationflow" / f"{iflow_name}.iflw"
        with open(iflow_file, "w", encoding="utf-8") as f:
            f.write(bpmn_xml)
        
        # Create script and mapping files
        self._create_asset_files(iflow_dir, blueprint)
        
        # Create zip package
        zip_path = output_path / f"{iflow_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in iflow_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(iflow_dir)
                    zipf.write(file_path, arcname)
        
        # Clean up temp directory
        shutil.rmtree(iflow_dir)
        
        print(f"✅ SAP CPI package created: {zip_path}")
        return str(zip_path)
    
    def _create_asset_files(self, iflow_dir: Path, blueprint: Dict[str, Any]):
        """Create script and mapping files referenced by components"""
        print("📝 Creating asset files (scripts and mappings)...")
        
        # Get components from blueprint
        endpoint = blueprint.get("endpoints", [{}])[0]
        components = endpoint.get("components", [])
        
        script_count = 0
        mapping_count = 0
        
        for component in components:
            comp_type = component.get("type", "")
            config = component.get("config", {})
            
            if comp_type == "script":
                # Create Groovy script file
                script_file = config.get("script_file", f"ScriptTask_{script_count + 1}.groovy")
                # Extract just the filename if full path is provided
                if "/" in script_file:
                    script_file = script_file.split("/")[-1]
                if "\\" in script_file:
                    script_file = script_file.split("\\")[-1]
                script_content = config.get("script_content", "// Default script content")
                
                script_path = iflow_dir / "src" / "main" / "resources" / "script" / script_file
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                print(f"   ✅ Created script: {script_file}")
                script_count += 1
                
            elif comp_type == "message_mappings":
                # Create mapping file
                mapping_file = config.get("mapping_file", f"Mapping_{mapping_count + 1}.mmap")
                # Extract just the filename if full path is provided
                if "/" in mapping_file:
                    mapping_file = mapping_file.split("/")[-1]
                if "\\" in mapping_file:
                    mapping_file = mapping_file.split("\\")[-1]
                
                # Create a realistic mapping file content
                mapping_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mapping>
    <description>Order transformation mapping for {component.get('name', 'Component')}</description>
    <source>
        <messageType>JSON</messageType>
        <structure>OrderRequest</structure>
    </source>
    <target>
        <messageType>JSON</messageType>
        <structure>OrderResponse</structure>
    </target>
    <mappingRules>
        <rule>
            <source>//orderId</source>
            <target>//order/orderId</target>
        </rule>
        <rule>
            <source>//customerId</source>
            <target>//order/customerId</target>
        </rule>
        <rule>
            <source>//items</source>
            <target>//order/items</target>
        </rule>
        <rule>
            <source>//totalAmount</source>
            <target>//order/totalAmount</target>
        </rule>
        <rule>
            <source>//processedAt</source>
            <target>//order/processedAt</target>
        </rule>
    </mappingRules>
</mapping>"""
                
                mapping_path = iflow_dir / "src" / "main" / "resources" / "mapping" / mapping_file
                with open(mapping_path, "w", encoding="utf-8") as f:
                    f.write(mapping_content)
                
                print(f"   ✅ Created mapping: {mapping_file}")
                mapping_count += 1
        
        print(f"📁 Created {script_count} script files and {mapping_count} mapping files")
    
    def _create_package_structure(self, iflow_dir: Path, iflow_name: str):
        """Create the complete SAP CPI package structure"""
        # Create directories
        (iflow_dir / "META-INF").mkdir(parents=True)
        (iflow_dir / "src" / "main" / "resources" / "scenarioflows" / "integrationflow").mkdir(parents=True)
        (iflow_dir / "src" / "main" / "resources" / "script").mkdir(parents=True)
        (iflow_dir / "src" / "main" / "resources" / "mapping").mkdir(parents=True)
        
        # Create manifest
        manifest_content = f"""Manifest-Version: 1.0
Bundle-SymbolicName: com.sap.ifl.{iflow_name};singleton:=true
Origin-Bundle-SymbolicName: com.sap.ifl.{iflow_name}
Bundle-ManifestVersion: 2
Origin-Bundle-Version: 1.0.0
Import-Package: com.sap.esb.application.services.cxf.interceptor,com.sap
 .esb.security,com.sap.it.op.agent.api,com.sap.it.op.agent.collector.cam
 el,com.sap.it.op.agent.collector.cxf,com.sap.it.op.agent.mpl,javax.jms,
 javax.jws,javax.wsdl,javax.xml.bind.annotation,javax.xml.namespace,java
 x.xml.ws,org.apache.camel,org.apache.camel.builder,org.apache.camel.com
 ponent.cxf,org.apache.camel.model,org.apache.camel.processor,org.apache
 .camel.processor.aggregate,org.apache.camel.spring.spi,org.apache.commo
 ns.logging,org.apache.cxf.binding,org.apache.cxf.binding.soap,org.apach
 e.cxf.binding.soap.spring,org.apache.cxf.bus,org.apache.cxf.bus.resourc
 e,org.apache.cxf.bus.spring,org.apache.cxf.buslifecycle,org.apache.cxf.
 catalog,org.apache.cxf.configuration.jsse,org.apache.cxf.configuration.
 spring,org.apache.cxf.endpoint,org.apache.cxf.headers,org.apache.cxf.in
 terceptor,org.apache.cxf.management.counters,org.apache.cxf.message,org
 .apache.cxf.phase,org.apache.cxf.resource,org.apache.cxf.service.factor
 y,org.apache.cxf.service.model,org.apache.cxf.transport,org.apache.cxf.
 transport.common.gzip,org.apache.cxf.transport.http,org.apache.cxf.tran
 sport.http.policy,org.apache.cxf.workqueue,org.apache.cxf.ws.rm.persist
 ence,org.apache.cxf.wsdl11,org.osgi.framework,org.slf4j,org.springframe
 work.beans.factory.config,com.sap.esb.camel.security.cms,org.apache.cam
 el.spi,com.sap.esb.webservice.audit.log,com.sap.esb.camel.endpoint.conf
 igurator.api,com.sap.esb.camel.jdbc.idempotency.reorg,javax.sql,org.apa
 che.camel.processor.idempotent.jdbc,org.osgi.service.blueprint
Origin-Bundle-Name: {iflow_name}
SAP-RuntimeProfile: iflmap
Bundle-Name: {iflow_name}
Bundle-Version: 1.0.0
SAP-NodeType: IFLMAP
Origin-ModifiedDate: {int(datetime.now().timestamp() * 1000)}
Import-Service: com.sap.esb.security.KeyManagerFactory;multiple:=false,c
 om.sap.esb.security.TrustManagerFactory;multiple:=false,javax.sql.DataS
 ource;multiple:=false;filter="(dataSourceName=default)",org.apache.cxf.
 ws.rm.persistence.RMStore;multiple:=false ,com.sap.esb.camel.security.c
 ms.SignatureSplitter;multiple:=false,com.sap.esb.webservice.audit.log.A
 uditLogger
SAP-BundleType: IntegrationFlow
"""
        
        with open(iflow_dir / "META-INF" / "MANIFEST.MF", "w", encoding="utf-8") as f:
            f.write(manifest_content)
        
        # Create .project file
        project_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
   <name>{iflow_name}</name>
   <comment/>
   <projects/>
   <buildSpec>
      <buildCommand>
         <name>org.eclipse.jdt.core.javabuilder</name>
         <arguments/>
      </buildCommand>
   </buildSpec>
   <natures>
      <nature>org.eclipse.jdt.core.javanature</nature>
      <nature>com.sap.ide.ifl.project.support.project.nature</nature>
      <nature>com.sap.ide.ifl.bsn</nature>
   </natures>
</projectDescription>"""
        
        with open(iflow_dir / ".project", "w", encoding="utf-8") as f:
            f.write(project_content)
        
        # Create metainfo.prop
        metainfo_content = f"""#Store metainfo properties
#{datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")}
description=SAP Integration Flow: {iflow_name}
"""
        
        with open(iflow_dir / "metainfo.prop", "w", encoding="utf-8") as f:
            f.write(metainfo_content)
        
        # Create parameters.prop
        parameters_content = f"""#{datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")}
"""
        
        with open(iflow_dir / "src" / "main" / "resources" / "parameters.prop", "w", encoding="utf-8") as f:
            f.write(parameters_content)
        
        # Create parameters.propdef
        propdef_content = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<parameters>
   <param_references/>
</parameters>"""
        
        with open(iflow_dir / "src" / "main" / "resources" / "parameters.propdef", "w", encoding="utf-8") as f:
            f.write(propdef_content)
    
    def _generate_bpmn_xml(self, blueprint: Dict[str, Any], iflow_name: str) -> str:
        """Generate BPMN XML from blueprint with corrected property placement"""
        print("📝 Generating BPMN XML with corrected structure...")

        endpoint = blueprint.get("endpoints", [{}])[0]
        components = endpoint.get("components", [])

        # Generate process elements and diagram elements as before
        process_elements = self._generate_process_elements(components)
        diagram_elements = self._generate_diagram_elements(components)

        # CORRECTED BPMN XML TEMPLATE
        bpmn_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn2:definitions xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:ifl="http:///com.sap.ifl.model/Ifl.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_1">
    <bpmn2:collaboration id="Collaboration_1" name="Default Collaboration">
        <bpmn2:extensionElements/>
        <bpmn2:participant id="Participant_Process_1" ifl:type="IntegrationProcess" name="Integration Process" processRef="Process_1">
            <bpmn2:extensionElements>
                <ifl:property><key>namespaceMapping</key><value></value></ifl:property>
                <ifl:property><key>httpSessionHandling</key><value>None</value></ifl:property>
                <ifl:property><key>returnExceptionToSender</key><value>false</value></ifl:property>
                <ifl:property><key>log</key><value>All events</value></ifl:property>
                <ifl:property><key>corsEnabled</key><value>false</value></ifl:property>
                <ifl:property><key>componentVersion</key><value>1.2</value></ifl:property>
                <ifl:property><key>ServerTrace</key><value>false</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::IFlowVariant/cname::IFlowConfiguration/version::1.2.4</value></ifl:property>
            </bpmn2:extensionElements>
        </bpmn2:participant>
    </bpmn2:collaboration>
    <bpmn2:process id="Process_1" name="Integration Process">
        <bpmn2:extensionElements>
            <ifl:property>
                <key>transactionTimeout</key>
                <value>30</value>
            </ifl:property>
            <ifl:property>
                <key>componentVersion</key>
                <value>1.2</value>
            </ifl:property>
            <ifl:property>
                <key>cmdVariantUri</key>
                <value>ctype::FlowElementVariant/cname::IntegrationProcess/version::1.2.1</value>
            </ifl:property>
            <ifl:property>
                <key>transactionalHandling</key>
                <value>Not Required</value>
            </ifl:property>
        </bpmn2:extensionElements>
{process_elements}
    </bpmn2:process>
{diagram_elements}
</bpmn2:definitions>'''

        return bpmn_xml
    
    def _generate_process_elements(self, components: List[Dict[str, Any]]) -> str:
        """Generate BPMN process elements with clean, proven structure"""
        elements = []
        flows = []
        
        # Filter out startevent and endevent components
        valid_components = [c for c in components if c.get("activity_type", "").lower() not in ["startevent", "endevent"]]
        
        # Start event
        start_event = '''    <bpmn2:startEvent id="StartEvent_2" name="Start">
        <bpmn2:extensionElements>
            <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
            <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::MessageStartEvent/version::1.0</value></ifl:property>
            <ifl:property><key>adapterType</key><value>HTTPS</value></ifl:property>
            <ifl:property><key>address</key><value>/orders/v1/process</value></ifl:property>
            <ifl:property><key>httpMethod</key><value>POST</value></ifl:property>
        </bpmn2:extensionElements>
        <bpmn2:outgoing>SequenceFlow_Start_Component_1</bpmn2:outgoing>
        <bpmn2:messageEventDefinition/>
    </bpmn2:startEvent>'''
        elements.append(start_event)
        
        # Add components
        for i, component in enumerate(valid_components):
            component_index = i + 1
            comp_id = f"Component_{component_index}"
            comp_name = component.get("name", f"Component {component_index}")
            
            # Clean up component name - remove metadata references
            comp_name = self._clean_component_name(comp_name)
            
            # Escape XML characters in name
            comp_name = comp_name.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            
            # Map activity_type to proper component type
            activity_type = component.get("activity_type", "").lower()
            comp_type = self._map_activity_type_to_component_type(activity_type)
            
            # Determine incoming and outgoing flows
            if component_index == 1:
                incoming = "SequenceFlow_Start_Component_1"
            else:
                incoming = f"SequenceFlow_Component_{component_index-1}_Component_{component_index}"
                
            if component_index == len(valid_components):
                outgoing = f"SequenceFlow_Component_{component_index}_End"
            else:
                outgoing = f"SequenceFlow_Component_{component_index}_Component_{component_index+1}"
            
            # Generate component element based on proper type
            comp_element = self._generate_component_bpmn_element(comp_id, comp_name, comp_type, component, incoming, outgoing)
            
            elements.append(comp_element)
        
        # End event
        end_event = f'''    <bpmn2:endEvent id="EndEvent_2" name="End">
        <bpmn2:extensionElements>
            <ifl:property><key>componentVersion</key><value>1.1</value></ifl:property>
            <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::MessageEndEvent/version::1.1.0</value></ifl:property>
        </bpmn2:extensionElements>
        <bpmn2:incoming>SequenceFlow_Component_{len(valid_components)}_End</bpmn2:incoming>
        <bpmn2:messageEventDefinition/>
    </bpmn2:endEvent>'''
        elements.append(end_event)
        
        # Generate sequence flows
        if valid_components:
            flows.append('    <bpmn2:sequenceFlow id="SequenceFlow_Start_Component_1" sourceRef="StartEvent_2" targetRef="Component_1"/>')
            
            for i in range(len(valid_components) - 1):
                current_comp = f"Component_{i+1}"
                next_comp = f"Component_{i+2}"
                flows.append(f'    <bpmn2:sequenceFlow id="SequenceFlow_{current_comp}_{next_comp}" sourceRef="{current_comp}" targetRef="{next_comp}"/>')
            
            flows.append(f'    <bpmn2:sequenceFlow id="SequenceFlow_Component_{len(valid_components)}_End" sourceRef="Component_{len(valid_components)}" targetRef="EndEvent_2"/>')
        else:
            flows.append('    <bpmn2:sequenceFlow id="SequenceFlow_Start_End" sourceRef="StartEvent_2" targetRef="EndEvent_2"/>')
        
        return '\n'.join(elements + flows)
    
    def _map_activity_type_to_component_type(self, activity_type: str) -> str:
        """Map Supabase activity_type to proper component type for BPMN generation"""
        mapping = {
            'script': 'script',
            'service': 'service',
            'enricher': 'enricher',
            'gateway': 'gateway',
            'request_reply': 'request_reply',
            'mapping': 'message_mappings',
            'directcall': 'externalcall',
            'externalcall': 'externalcall',
            'callactivity': 'enricher',  # Map CallActivity to Enricher
            'servicetask': 'service',    # Map ServiceTask to Service
            'scripttask': 'script',      # Map ScriptTask to Script
        }
        return mapping.get(activity_type, 'service')  # Default to service if unknown
    
    def _clean_component_name(self, name: str) -> str:
        """Clean component name by removing metadata references and making it human-readable"""
        if not name:
            return "Processing Step"
        
        # Remove common metadata prefixes
        name = re.sub(r'^(CallActivity_|ServiceTask_|ScriptTask_|Participant_|Process_|asset_|script_|flow_)', '', name)
        
        # Remove file extensions
        name = re.sub(r'\.(groovy|mmap|prop|xml|wsdl|mf)$', '', name)
        
        # Convert underscores to spaces and title case
        name = re.sub(r'_+', ' ', name)
        name = name.title()
        
        # Handle specific cases
        if 'manifest' in name.lower() or 'properties' in name.lower():
            return "Configuration"
        
        return name if name.strip() else "Processing Step"

    def _generate_component_bpmn_element(self, comp_id: str, comp_name: str, comp_type: str, component: Dict[str, Any], incoming: str, outgoing: str) -> str:
        """Generate proper BPMN element based on component type"""
        
        if comp_type == "script":
            # Get script configuration from component
            config = component.get("config", {})
            script_file = config.get("script_file", "script.groovy")
            script_content = config.get("script_content", "// Default script")
            
            return f'''        <bpmn2:scriptTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Script</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::GroovyScript/version::1.1.1</value>
                </ifl:property>
                <ifl:property>
                    <key>scriptFile</key>
                    <value>{script_file}</value>
                </ifl:property>
                <ifl:property>
                    <key>scriptContent</key>
                    <value><![CDATA[{script_content}]]></value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:scriptTask>'''
        
        elif comp_type == "enricher":
            # Get enricher configuration from component
            config = component.get("config", {})
            properties = config.get("properties", "order_id={{uuid}},processing_timestamp=now(),channel=web,priority=normal,batch_id={{batch_id}},status=processing")
            headers = config.get("headers", "Content-Type=application/json,X-Process-ID={{uuid}},X-Source=OrderProcessing,X-Version=1.0")
            
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Enricher</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::Enricher/version::1.5.1</value>
                </ifl:property>
                <ifl:property>
                    <key>properties</key>
                    <value>{properties}</value>
                </ifl:property>
                <ifl:property>
                    <key>headers</key>
                    <value>{headers}</value>
                </ifl:property>
                <ifl:property>
                    <key>bodyType</key>
                    <value>expression</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type == "message_mappings":
            # Get mapping configuration from component
            config = component.get("config", {})
            mapping_file = config.get("mapping_file", "src/main/resources/mapping/AutoMapping.mmap")
            
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Mapping</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::MessageMapping/version::1.3.0</value>
                </ifl:property>
                <ifl:property>
                    <key>mappingFile</key>
                    <value>{mapping_file}</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type == "gateway":
            # Get gateway configuration from component
            config = component.get("config", {})
            gateway_type = config.get("gateway_type", "exclusive")
            routing_conditions = config.get("routing_conditions", [])
            
            return f'''        <bpmn2:exclusiveGateway id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Gateway</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::Gateway/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>SequenceFlow_{comp_id}_Success</bpmn2:outgoing>
            <bpmn2:outgoing>SequenceFlow_{comp_id}_Error</bpmn2:outgoing>
        </bpmn2:exclusiveGateway>'''
        
        elif comp_type == "properties_files":
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Properties</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::Properties/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type == "wsdl_files":
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>WSDL</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::WSDL/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type == "jsontoxmlconverter":
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>JsonToXmlConverter</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::JsonToXmlConverter/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type == "externalcall":
            # Get external call configuration from component
            config = component.get("config", {})
            endpoint_path = config.get("endpoint_path", "/api/orders/validate")
            method = config.get("method", "POST")
            url = config.get("url", "{{API_BASE_URL}}/api/orders/validate")
            headers = config.get("headers", "Content-Type=application/json")
            
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Request-Reply</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::RequestReply/version::1.0.4</value>
                </ifl:property>
                <ifl:property>
                    <key>endpointPath</key>
                    <value>{endpoint_path}</value>
                </ifl:property>
                <ifl:property>
                    <key>method</key>
                    <value>{method}</value>
                </ifl:property>
                <ifl:property>
                    <key>url</key>
                    <value>{url}</value>
                </ifl:property>
                <ifl:property>
                    <key>headers</key>
                    <value>{headers}</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        else:
            # Default to a valid Content Modifier to prevent errors
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>ContentModifier</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::ContentModifier/version::1.1.2</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
    
    def _generate_diagram_elements(self, components: List[Dict[str, Any]]) -> str:
        """Generate BPMN diagram elements"""
        elements = []
        
        # Filter out startevent and endevent components
        valid_components = [c for c in components if c.get("type", "").lower() not in ["startevent", "endevent"]]
        
        # Start event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="StartEvent_2" id="BPMNShape_StartEvent_2">')
        elements.append('                <dc:Bounds height="32.0" width="32.0" x="292.0" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Component shapes (only for valid components)
        current_x = 400
        for i, component in enumerate(valid_components):
            comp_id = f"Component_{i+1}"
            elements.append(f'            <bpmndi:BPMNShape bpmnElement="{comp_id}" id="BPMNShape_{comp_id}">')
            elements.append(f'                <dc:Bounds height="56.0" width="100.0" x="{current_x}" y="130.0"/>')
            elements.append(f'            </bpmndi:BPMNShape>')
            current_x += 150
        
        # End event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="EndEvent_2" id="BPMNShape_EndEvent_2">')
        elements.append(f'                <dc:Bounds height="32.0" width="32.0" x="{current_x}" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Only add error handling shapes if there's a Gateway component
        has_gateway = any(comp.get("type", "").lower() == "gateway" for comp in components)
        
        if has_gateway:
            # Error content modifier shape
            elements.append('            <bpmndi:BPMNShape bpmnElement="ErrorContentModifier" id="BPMNShape_ErrorContentModifier">')
            elements.append(f'                <dc:Bounds height="56.0" width="100.0" x="{current_x - 150}" y="200.0"/>')
            elements.append('            </bpmndi:BPMNShape>')
            
            # Error end event shape
            elements.append('            <bpmndi:BPMNShape bpmnElement="ErrorEndEvent" id="BPMNShape_ErrorEndEvent">')
            elements.append(f'                <dc:Bounds height="32.0" width="32.0" x="{current_x}" y="200.0"/>')
            elements.append('            </bpmndi:BPMNShape>')
        
        # Participant shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="Participant_Process_1" id="BPMNShape_Participant_Process_1">')
        elements.append(f'                <dc:Bounds height="220.0" width="{current_x + 100}" x="250.0" y="60.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Sequence flow edges (only for valid components)
        if valid_components:
            # Start to first component
            elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Start_Component_1" id="BPMNEdge_SequenceFlow_Start_Component_1" sourceElement="BPMNShape_StartEvent_2" targetElement="BPMNShape_Component_1">')
            elements.append('                <di:waypoint x="324.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('                <di:waypoint x="400.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
            
            # Component to component edges
            for i in range(len(valid_components) - 1):
                source_x = 400 + i * 150
                target_x = 400 + (i + 1) * 150
                elements.append(f'            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Component_{i+1}_Component_{i+2}" id="BPMNEdge_SequenceFlow_Component_{i+1}_Component_{i+2}" sourceElement="BPMNShape_Component_{i+1}" targetElement="BPMNShape_Component_{i+2}">')
                elements.append(f'                <di:waypoint x="{source_x + 100}" xsi:type="dc:Point" y="158.0"/>')
                elements.append(f'                <di:waypoint x="{target_x}" xsi:type="dc:Point" y="158.0"/>')
                elements.append('            </bpmndi:BPMNEdge>')
            
            # Last component to end
            last_comp_x = 400 + (len(valid_components) - 1) * 150
            elements.append(f'            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Component_{len(valid_components)}_End" id="BPMNEdge_SequenceFlow_Component_{len(valid_components)}_End" sourceElement="BPMNShape_Component_{len(valid_components)}" targetElement="BPMNShape_EndEvent_2">')
            elements.append(f'                <di:waypoint x="{last_comp_x + 100}" xsi:type="dc:Point" y="158.0"/>')
            elements.append(f'                <di:waypoint x="{current_x}" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
            
            # Only add error flow edges if there's a Gateway component
            if has_gateway:
                # Gateway to error content modifier edge
                gateway_x = 400 + 4 * 150  # Assuming gateway is Component_5 (index 4)
                elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Component_5_Error" id="BPMNEdge_SequenceFlow_Component_5_Error" sourceElement="BPMNShape_Component_5" targetElement="BPMNShape_ErrorContentModifier">')
                elements.append(f'                <di:waypoint x="{gateway_x + 50}" xsi:type="dc:Point" y="200.0"/>')
                elements.append(f'                <di:waypoint x="{current_x - 100}" xsi:type="dc:Point" y="228.0"/>')
                elements.append('            </bpmndi:BPMNEdge>')
                
                # Error content modifier to error end edge
                elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_ErrorContentModifier_ErrorEnd" id="BPMNEdge_SequenceFlow_ErrorContentModifier_ErrorEnd" sourceElement="BPMNShape_ErrorContentModifier" targetElement="BPMNShape_ErrorEndEvent">')
                elements.append(f'                <di:waypoint x="{current_x - 50}" xsi:type="dc:Point" y="228.0"/>')
                elements.append(f'                <di:waypoint x="{current_x}" xsi:type="dc:Point" y="216.0"/>')
                elements.append('            </bpmndi:BPMNEdge>')
        else:
            elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Start_End" id="BPMNEdge_SequenceFlow_Start_End" sourceElement="BPMNShape_StartEvent_2" targetElement="BPMNShape_EndEvent_2">')
            elements.append('                <di:waypoint x="324.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('                <di:waypoint x="400.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
        
        diagram_xml = f'''    <bpmndi:BPMNDiagram id="BPMNDiagram_1" name="Default Collaboration Diagram">
        <bpmndi:BPMNPlane bpmnElement="Collaboration_1" id="BPMNPlane_1">
{chr(10).join(elements)}
        </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>'''
        
        return diagram_xml
    
    def _extract_flows_from_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract flow components from the components list"""
        flows = []
        for component in components:
            if component.get("source") == "iflow_flows_table":
                flows.append(component)
        return flows
    
    def _create_flows_from_database(self, flows: List[Dict[str, Any]], components: List[Dict[str, Any]]) -> List[str]:
        """Create flows from database flow data (both sequence flows and message flows)"""
        all_flows = []
        
        # If we have flows from database, use them
        if flows:
            for flow in flows:
                flow_config = flow.get("flow_config", {})
                flow_id = flow_config.get("flow_id", "")
                source_ref = flow_config.get("source_ref", "")
                target_ref = flow_config.get("target_ref", "")
                condition = flow_config.get("condition", "")
                flow_type = flow_config.get("flow_type", "sequence")
                
                if flow_id and source_ref and target_ref:
                    if flow_type == "message":
                        # Create message flow
                        all_flows.append(f'        <bpmn2:messageFlow id="{flow_id}" name="Message" sourceRef="{source_ref}" targetRef="{target_ref}"/>')
                    else:
                        # Create sequence flow
                        if condition:
                            all_flows.append(f'        <bpmn2:sequenceFlow id="{flow_id}" sourceRef="{source_ref}" targetRef="{target_ref}">')
                            all_flows.append(f'            <bpmn2:conditionExpression xsi:type="bpmn2:tFormalExpression">{condition}</bpmn2:conditionExpression>')
                            all_flows.append('        </bpmn2:sequenceFlow>')
                        else:
                            all_flows.append(f'        <bpmn2:sequenceFlow id="{flow_id}" sourceRef="{source_ref}" targetRef="{target_ref}"/>')
        
        return all_flows
    
    def _create_simple_components(self, query: str, component_count: int) -> List[Dict[str, Any]]:
        """Create simple, working components based on query"""
        query_lower = query.lower()
        components = []
        
        # Component 1: Always add a simple script
        components.append({
            "component_id": "SimpleScript",
            "activity_type": "Script",
            "description": "Simple data processing script",
            "script_content": """// Simple Processing Script
def inputData = new JsonSlurper().parseText(message)

// Add processing timestamp
inputData.processedAt = new Date().format('yyyy-MM-dd HH:mm:ss')
inputData.processedBy = 'Simple Script'

// Log processing
log.info("Data processed successfully")

return new JsonBuilder(inputData).toString()""",
            "source": "simple_mock"
        })
        
        # Component 2: Add based on query
        if component_count > 1:
            if any(keyword in query_lower for keyword in ["enricher", "enrich", "context"]):
                components.append({
                    "component_id": "SimpleEnricher",
                    "activity_type": "Enricher",
                    "description": "Simple context enricher",
                    "enricher_config": {
                        "properties": "processed=true,timestamp=now()",
                        "headers": "Content-Type=application/json"
                    },
                    "source": "simple_mock"
                })
            elif any(keyword in query_lower for keyword in ["api", "call", "external"]):
                components.append({
                    "component_id": "SimpleAPICall",
                    "activity_type": "ExternalCall",
                    "description": "Simple API call",
                    "external_call_config": {
                        "endpoint_path": "/api/process",
                        "method": "POST",
                        "url": "{{API_URL}}/api/process",
                        "headers": "Content-Type=application/json"
                    },
                    "source": "simple_mock"
                })
            else:
                # Default second component
                components.append({
                    "component_id": "SimpleProcessor",
                    "activity_type": "Script",
                    "description": "Simple data processor",
                    "script_content": """// Simple Data Processor
def data = new JsonSlurper().parseText(message)
data.processed = true
data.timestamp = new Date().format('yyyy-MM-dd HH:mm:ss')
return new JsonBuilder(data).toString()""",
                    "source": "simple_mock"
                })
        
        return components[:component_count]
    
    def _create_simple_blueprint(self, components: List[Dict[str, Any]], iflow_name: str, query: str) -> Dict[str, Any]:
        """Create simple blueprint with minimal components"""
        endpoint_components = []
        
        for i, component in enumerate(components):
            component_id = f"Component_{i+1}"
            component_type = component.get("activity_type", "").lower().replace(" ", "_")
            component_name = component.get("description", f"Component {i+1}")
            
            # Create simple config
            config = {}
            if component_type == "script":
                config = {
                    "script_content": component.get("script_content", ""),
                    "script_file": f"SimpleScript_{i+1}.groovy"
                }
            elif component_type == "enricher":
                config = component.get("enricher_config", {})
            elif component_type == "externalcall":
                config = component.get("external_call_config", {})
            
            rich_component = {
                "type": component_type,
                "name": component_name,
                "id": component_id,
                "config": config,
                "source": component.get("source", "simple")
            }
            
            endpoint_components.append(rich_component)
        
        # Create simple flow
        flow = [comp["id"] for comp in endpoint_components]
        
        blueprint = {
            "process_name": f"Simple {iflow_name}",
            "description": f"Simple iFlow for: {query}",
            "endpoints": [
                {
                    "id": "main_processing",
                    "name": "Main Processing",
                    "method": "POST",
                    "path": f"/{iflow_name.lower().replace('_', '-')}/process",
                    "purpose": f"Process {query.lower()}",
                    "components": endpoint_components,
                    "flow": flow
                }
            ],
            "metadata": {
                "generated_by": "Simple Generator",
                "query": query,
                "component_count": len(components),
                "generated_at": datetime.now().isoformat(),
                "version": "1.0-simple"
            }
        }
        
        return blueprint
    
    def _generate_simple_package(self, blueprint: Dict[str, Any], iflow_name: str) -> str:
        """Generate simple SAP CPI package"""
        print(f"🏗️ Creating simple SAP CPI package: {iflow_name}")
        
        # Create package structure
        iflow_dir = Path("output") / iflow_name
        self._create_package_structure(iflow_dir, iflow_name)
        
        # Generate simple BPMN
        bpmn_content = self._generate_simple_bpmn(blueprint, iflow_name)
        
        # Write BPMN file
        iflow_file = iflow_dir / "src" / "main" / "resources" / "scenarioflows" / "integrationflow" / f"{iflow_name}.iflw"
        with open(iflow_file, "w", encoding="utf-8") as f:
            f.write(bpmn_content)
        
        # Create simple asset files
        self._create_simple_asset_files(blueprint, iflow_dir)
        
        # Create zip package
        zip_path = self.create_sap_cpi_package(blueprint, iflow_name, "output")
        
        print(f"✅ Simple SAP CPI package created: {zip_path}")
        return zip_path
    
    def _generate_simple_bpmn(self, blueprint: Dict[str, Any], iflow_name: str) -> str:
        """Generate simple BPMN XML with minimal components"""
        components = blueprint["endpoints"][0]["components"]
        
        # Generate process elements
        process_elements = self._generate_simple_process_elements(components)
        
        # Generate diagram elements
        diagram_elements = self._generate_simple_diagram_elements(components)
        
        # Combine into complete BPMN
        bpmn_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn2:definitions xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:ifl="http:///com.sap.ifl.model/Ifl.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_1">
    <bpmn2:collaboration id="Collaboration_1" name="Default Collaboration">
        <bpmn2:extensionElements>
            <ifl:property>
                <key>namespaceMapping</key>
                <value></value>
            </ifl:property>
            <ifl:property>
                <key>httpSessionHandling</key>
                <value>None</value>
            </ifl:property>
            <ifl:property>
                <key>returnExceptionToSender</key>
                <value>false</value>
            </ifl:property>
            <ifl:property>
                <key>log</key>
                <value>All events</value>
            </ifl:property>
            <ifl:property>
                <key>corsEnabled</key>
                <value>false</value>
            </ifl:property>
            <ifl:property>
                <key>componentVersion</key>
                <value>1.2</value>
            </ifl:property>
            <ifl:property>
                <key>ServerTrace</key>
                <value>false</value>
            </ifl:property>
            <ifl:property>
                <key>cmdVariantUri</key>
                <value>ctype::IFlowVariant/cname::IFlowConfiguration/version::1.2.4</value>
            </ifl:property>
        </bpmn2:extensionElements>
        <bpmn2:participant id="Participant_Process_1" ifl:type="IntegrationProcess" name="Integration Process" processRef="Process_1">
            <bpmn2:extensionElements/>
        </bpmn2:participant>
    </bpmn2:collaboration>
    <bpmn2:process id="Process_1" name="Integration Process">
        <bpmn2:extensionElements>
            <ifl:property>
                <key>transactionTimeout</key>
                <value>30</value>
            </ifl:property>
            <ifl:property>
                <key>componentVersion</key>
                <value>1.2</value>
            </ifl:property>
            <ifl:property>
                <key>cmdVariantUri</key>
                <value>ctype::FlowElementVariant/cname::IntegrationProcess/version::1.2.1</value>
            </ifl:property>
            <ifl:property>
                <key>transactionalHandling</key>
                <value>Not Required</value>
            </ifl:property>
        </bpmn2:extensionElements>
{process_elements}
    </bpmn2:process>
{diagram_elements}
</bpmn2:definitions>'''
        
        return bpmn_xml
    
    def _generate_simple_process_elements(self, components: List[Dict[str, Any]]) -> str:
        """Generate simple process elements"""
        elements = []
        
        # Start event
        if components:
            start_outgoing = "SequenceFlow_Start_Component_1"
        else:
            start_outgoing = "SequenceFlow_Start_End"
            
        start_event = f'''        <bpmn2:startEvent id="StartEvent_2" name="Start">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::MessageStartEvent/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:outgoing>{start_outgoing}</bpmn2:outgoing>
            <bpmn2:messageEventDefinition/>
        </bpmn2:startEvent>'''
        elements.append(start_event)
        
        # Add components
        for i, component in enumerate(components):
            comp_id = component["id"]
            comp_name = component["name"]
            comp_type = component["type"]
            
            if i == 0:
                incoming = "SequenceFlow_Start_Component_1"
            else:
                incoming = f"SequenceFlow_Component_{i}_Component_{i+1}"
            
            if i == len(components) - 1:
                outgoing = f"SequenceFlow_Component_{i+1}_End"
            else:
                outgoing = f"SequenceFlow_Component_{i+1}_Component_{i+2}"
            
            # Generate simple component element
            if comp_type == "script":
                element = f'''        <bpmn2:scriptTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Script</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::GroovyScript/version::1.1.1</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:scriptTask>'''
            elif comp_type == "enricher":
                element = f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Enricher</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::Enricher/version::1.5.1</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
            else:
                element = f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.0</value>
                </ifl:property>
                <ifl:property>
                    <key>activityType</key>
                    <value>Service</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::ServiceTask/version::1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
            
            elements.append(element)
        
        # End event
        if components:
            end_incoming = f"SequenceFlow_Component_{len(components)}_End"
        else:
            end_incoming = "SequenceFlow_Start_End"
            
        end_event = f'''        <bpmn2:endEvent id="EndEvent_2" name="End">
            <bpmn2:extensionElements>
                <ifl:property>
                    <key>componentVersion</key>
                    <value>1.1</value>
                </ifl:property>
                <ifl:property>
                    <key>cmdVariantUri</key>
                    <value>ctype::FlowstepVariant/cname::MessageEndEvent/version::1.1.0</value>
                </ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{end_incoming}</bpmn2:incoming>
            <bpmn2:messageEventDefinition/>
        </bpmn2:endEvent>'''
        elements.append(end_event)
        
        # Generate sequence flows
        flows = []
        if components:
            flows.append('        <bpmn2:sequenceFlow id="SequenceFlow_Start_Component_1" sourceRef="StartEvent_2" targetRef="Component_1"/>')
            
            for i in range(len(components) - 1):
                flows.append(f'        <bpmn2:sequenceFlow id="SequenceFlow_Component_{i+1}_Component_{i+2}" sourceRef="Component_{i+1}" targetRef="Component_{i+2}"/>')
            
            flows.append(f'        <bpmn2:sequenceFlow id="SequenceFlow_Component_{len(components)}_End" sourceRef="Component_{len(components)}" targetRef="EndEvent_2"/>')
        else:
            flows.append('        <bpmn2:sequenceFlow id="SequenceFlow_Start_End" sourceRef="StartEvent_2" targetRef="EndEvent_2"/>')
        
        return '\n'.join(elements + flows)
    
    def _generate_simple_diagram_elements(self, components: List[Dict[str, Any]]) -> str:
        """Generate simple diagram elements"""
        elements = []
        
        # Start event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="StartEvent_2" id="BPMNShape_StartEvent_2">')
        elements.append('                <dc:Bounds height="32.0" width="32.0" x="292.0" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Component shapes
        current_x = 400
        for i, component in enumerate(components):
            comp_id = component["id"]
            elements.append(f'            <bpmndi:BPMNShape bpmnElement="{comp_id}" id="BPMNShape_{comp_id}">')
            elements.append(f'                <dc:Bounds height="56.0" width="100.0" x="{current_x}" y="130.0"/>')
            elements.append(f'            </bpmndi:BPMNShape>')
            current_x += 150
        
        # End event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="EndEvent_2" id="BPMNShape_EndEvent_2">')
        elements.append(f'                <dc:Bounds height="32.0" width="32.0" x="{current_x}" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Participant shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="Participant_Process_1" id="BPMNShape_Participant_Process_1">')
        elements.append(f'                <dc:Bounds height="220.0" width="{current_x + 100}" x="250.0" y="60.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Edges
        if components:
            elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Start_Component_1" id="BPMNEdge_SequenceFlow_Start_Component_1" sourceElement="BPMNShape_StartEvent_2" targetElement="BPMNShape_Component_1">')
            elements.append('                <di:waypoint x="324.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('                <di:waypoint x="400.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
            
            for i in range(len(components) - 1):
                source_x = 400 + i * 150
                target_x = 400 + (i + 1) * 150
                elements.append(f'            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Component_{i+1}_Component_{i+2}" id="BPMNEdge_SequenceFlow_Component_{i+1}_Component_{i+2}" sourceElement="BPMNShape_Component_{i+1}" targetElement="BPMNShape_Component_{i+2}">')
                elements.append(f'                <di:waypoint x="{source_x + 100}" xsi:type="dc:Point" y="158.0"/>')
                elements.append(f'                <di:waypoint x="{target_x}" xsi:type="dc:Point" y="158.0"/>')
                elements.append('            </bpmndi:BPMNEdge>')
            
            last_comp_x = 400 + (len(components) - 1) * 150
            elements.append(f'            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Component_{len(components)}_End" id="BPMNEdge_SequenceFlow_Component_{len(components)}_End" sourceElement="BPMNShape_Component_{len(components)}" targetElement="BPMNShape_EndEvent_2">')
            elements.append(f'                <di:waypoint x="{last_comp_x + 100}" xsi:type="dc:Point" y="158.0"/>')
            elements.append(f'                <di:waypoint x="{current_x}" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
        else:
            elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_Start_End" id="BPMNEdge_SequenceFlow_Start_End" sourceElement="BPMNShape_StartEvent_2" targetElement="BPMNShape_EndEvent_2">')
            elements.append('                <di:waypoint x="324.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('                <di:waypoint x="400.0" xsi:type="dc:Point" y="158.0"/>')
            elements.append('            </bpmndi:BPMNEdge>')
        
        # Wrap in diagram structure
        diagram = f'''    <bpmndi:BPMNDiagram id="BPMNDiagram_1" name="Default Collaboration Diagram">
        <bpmndi:BPMNPlane bpmnElement="Collaboration_1" id="BPMNPlane_1">
{chr(10).join(elements)}
        </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>'''
        
        return diagram
    
    def _create_simple_asset_files(self, blueprint: Dict[str, Any], iflow_dir: Path) -> None:
        """Create simple asset files"""
        components = blueprint["endpoints"][0]["components"]
        
        for i, component in enumerate(components):
            if component["type"] == "script":
                script_file = component["config"].get("script_file", f"SimpleScript_{i+1}.groovy")
                script_content = component["config"].get("script_content", "")
                
                script_path = iflow_dir / "src" / "main" / "resources" / "script" / script_file
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                print(f"   ✅ Created simple script: {script_file}")

    def generate_simple_solution(self, query: str, iflow_name: str = None, component_count: int = 2) -> tuple:
        """Generate a simple iFlow with just 1-2 components to ensure they work"""
        if not iflow_name:
            clean_query = re.sub(r'[^\w\s-]', '', query.lower())
            clean_query = re.sub(r'[-\s]+', '_', clean_query)
            iflow_name = clean_query  # Use full descriptive name
        
        print(f"🚀 Generating SIMPLE Solution: '{iflow_name}' with {component_count} components")
        print("=" * 80)
        
        try:
            # Create simple components based on query
            simple_components = self._create_simple_components(query, component_count)
            
            # Create simple blueprint
            blueprint = self._create_simple_blueprint(simple_components, iflow_name, query)
            
            # Generate package
            zip_path = self._generate_simple_package(blueprint, iflow_name)
            
            print("=" * 80)
            print("🎉 Simple Solution generated!")
            print(f"📦 Package: {zip_path}")
            print(f"🤖 Components: {len(simple_components)}")
            
            return blueprint, zip_path
            
        except Exception as e:
            print(f"❌ Failed to generate simple solution: {e}")
            raise e

    def generate_complete_solution(self, query: str, iflow_name: str = None, generate_package: bool = True) -> tuple:
        """Generate complete solution: search, analyze, validate, and create package"""
        if not iflow_name:
            clean_query = re.sub(r'[^\w\s-]', '', query.lower())
            clean_query = re.sub(r'[-\s]+', '_', clean_query)
            iflow_name = clean_query  # Use full descriptive name
        
        print(f"🚀 Generating Complete Solution: '{iflow_name}' for query: '{query}'")
        print("=" * 80)
        
        try:
            # Step 1: Search Supabase for components
            components = self.search_supabase_components(query)
            
            if not components:
                raise Exception("No components found. Please check your database connection.")
            
            # Step 2: Calculate similarity scores
            scored_components = self.calculate_similarity_scores(query, components)
            
            # Step 3: Analyze query with AI
            ai_analysis = self.analyze_query_with_ai(query, scored_components)
            
            # Step 4: Select components based on AI analysis
            selected_components = []
            selected_ids = ai_analysis.get("selected_components", [])
            
            # Force use of mock data components for order processing queries
            if "order" in query.lower():
                print("🎯 Forcing use of comprehensive mock data for order processing...")
                mock_components = [comp for comp, score in scored_components if comp.get("source") == "mock_data"]
                if mock_components:
                    selected_components = mock_components[:6]  # Take first 6 mock components
                    print(f"   ✅ Selected {len(selected_components)} mock components for order processing")
                else:
                    print("   ⚠️ No mock components found, using fallback...")
                    # Create fallback components
                    fallback_components = self._get_mock_components(query)
                    selected_components = fallback_components[:6]
                    print(f"   ✅ Created {len(selected_components)} fallback components")
            else:
                # First, prioritize mock data components (they have better configurations)
                mock_components = [comp for comp, score in scored_components if comp.get("source") == "mock_data"]
                if mock_components:
                    print("🎯 Prioritizing mock data components for better configurations...")
                    for comp_id in selected_ids:
                        for comp, score in mock_components:
                            if comp.get("component_id") == comp_id:
                                selected_components.append(comp)
                                print(f"   ✅ Selected {comp_id} from mock data (similarity: {score:.3f})")
                                break
            
            # If we don't have enough mock components, fill with Supabase components
            if len(selected_components) < len(selected_ids):
                for comp_id in selected_ids:
                    if not any(comp.get("component_id") == comp_id for comp in selected_components):
                        for comp, score in scored_components:
                            if comp.get("component_id") == comp_id:
                                selected_components.append(comp)
                                print(f"   ✅ Selected {comp_id} from Supabase (similarity: {score:.3f})")
                                break
            
            # If AI didn't select enough, add more based on similarity
            if len(selected_components) < 3:
                for comp, score in scored_components:
                    if comp not in selected_components and len(selected_components) < 6:
                        selected_components.append(comp)
            
            # Step 5: Create dynamic JSON blueprint
            blueprint = self.create_dynamic_json_blueprint(selected_components, iflow_name, query, ai_analysis)
            
            # Step 6: Save blueprint
            clean_query = re.sub(r'[^\w\s-]', '', query.lower())
            clean_query = re.sub(r'[-\s]+', '_', clean_query)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blueprint_filename = f"{clean_query}_{timestamp}_blueprint.json"
            
            with open(blueprint_filename, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2, ensure_ascii=False)
            
            zip_path = None
            if generate_package:
                # Step 7: Create SAP CPI package
                zip_path = self.create_sap_cpi_package(blueprint, iflow_name, "output")
                
                # Step 8: Create final filename
                new_filename = f"{clean_query}_{timestamp}.zip"
                
                # Move the file to Downloads folder with new name
                if os.path.exists(zip_path):
                    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                    final_path = os.path.join(downloads_path, new_filename)
                    shutil.move(zip_path, final_path)
                    zip_path = final_path
            
            print("=" * 80)
            print("🎉 Complete Solution generated!")
            print(f"📋 Blueprint: {blueprint_filename}")
            if zip_path:
                print(f"📦 Package: {zip_path}")
            print(f"🤖 Components: {len(selected_components)}")
            print(f"🧠 AI Scenario: {ai_analysis.get('scenario', 'Unknown')}")
            
            return blueprint_filename, zip_path
            
        except Exception as e:
            print(f"❌ Failed to generate solution: {e}")
            raise e

def main():
    """Main function for terminal usage"""
    print("🚀 Complete SAP CPI iFlow Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = CompleteIFlowGenerator()
    
    # Get user input
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        iflow_name = None
        generate_package = True
    else:
        query = input("🎯 Describe your iFlow: ").strip()
        iflow_name = input("📁 Project name (optional): ").strip() or None
        
        print("\n📦 Package Generation Options:")
        print("   1. JSON Blueprint only")
        print("   2. JSON Blueprint + SAP CPI Package")
        
        while True:
            choice = input("Choose option (1/2, default: 2): ").strip()
            if choice in ['1', '2', '']:
                generate_package = choice != '1'
                break
            else:
                print("❌ Please enter 1 or 2")
    
    if not query:
        print("❌ Please provide a description for your iFlow.")
        return
    
    try:
        # Generate complete solution
        blueprint_filename, zip_path = generator.generate_complete_solution(query, iflow_name, generate_package)
        
        print(f"\n🎯 Generated Files:")
        print(f"   📋 Blueprint: {blueprint_filename}")
        
        if zip_path:
            print(f"   📦 Package: {zip_path}")
            print(f"\n✅ Ready for deployment to SAP Integration Suite!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

if __name__ == "__main__":
    main()
