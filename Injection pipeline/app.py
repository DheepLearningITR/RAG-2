#!/usr/bin/env python3
"""
iFlow Package Processor API for Cloud Foundry
Production-ready Flask API for processing SAP Integration Suite iFlow packages
"""

import os
import json
import hashlib
import zipfile
import tempfile
import shutil
import csv
import uuid
import logging
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from lxml import etree
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from openai import OpenAI
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Global dictionary to track processing status for long-running operations
processing_status = {}

# Load environment variables first
load_dotenv()

# Get environment variables with Cloud Foundry VCAP_SERVICES support
def get_env_var(key):
    """Get environment variable from direct env or Cloud Foundry VCAP_SERVICES"""
    # First try direct environment variable (for local development)
    value = os.getenv(key)
    if value:
        return value

    # Try to get from VCAP_SERVICES (for Cloud Foundry)
    vcap_services = os.getenv('VCAP_SERVICES')
    if vcap_services:
        try:
            import json
            services = json.loads(vcap_services)
            user_provided = services.get('user-provided', [])
            for service in user_provided:
                credentials = service.get('credentials', {})
                if key in credentials:
                    return credentials[key]
        except (json.JSONDecodeError, KeyError):
            pass

    return None

OPENAI_API_KEY = get_env_var('OPENAI_API_KEY')
SUPABASE_URL = get_env_var('SUPABASE_URL')
SUPABASE_KEY = get_env_var('SUPABASE_KEY')

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is required")

# Configure logging for Cloud Foundry
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Only console logging for Cloud Foundry
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Enable CORS for all routes
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
logger.info("OpenAI client initialized successfully")

class EnhancedIFlowChunker:
    """Enhanced iFlow chunker with component-level grouping and complete coverage."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.chunks = []
        self.processed_files = []
        self.script_index: Dict[str, Dict[str, Any]] = {}
        # Initialize embedding generator for process descriptions
        try:
            self.embedding_generator = EmbeddingGenerator()
        except Exception as e:
            logger.warning(f"Could not initialize embedding generator: {e}")
            self.embedding_generator = None
        
    def process_complete_iflow_package(self) -> Dict[str, Any]:
        """Process complete iFlow package with coverage verification."""
        logger.info(f"Processing complete iFlow package: {self.base_path}")
        
        # Step 1: Discover all files
        all_files = self._discover_all_files()
        
        # Step 2: Process main iFlow
        main_iflow = self._find_main_iflow(all_files)
        # Build script index before component processing so we can resolve references
        self._build_script_index(all_files)
        if main_iflow:
            iflow_chunks = self._process_main_iflow_with_components(main_iflow)
            self.chunks.extend(iflow_chunks)
            self.processed_files.append(main_iflow)
        
        # Step 3: Process all related files
        related_files = self._process_all_related_files(all_files)
        self.processed_files.extend(related_files)
        
        # Step 4: Verify complete coverage
        coverage_report = self._verify_complete_coverage(all_files)
        
        return {
            'total_chunks': len(self.chunks),
            'processed_files': len(self.processed_files),
            'coverage_report': coverage_report,
            'chunks': self.chunks
        }
    
    def _discover_all_files(self) -> Dict[str, List[str]]:
        """Discover integration-related files only in iFlow package."""
        all_files = {
            'main_iflow': [],
            'groovy_scripts': [],
            'xsd_files': [],
            'message_mappings': [],
            'wsdl_files': [],
            'properties_files': [],
            'xslt_files': [],
            'json_files': [],
            'manifest_files': []
        }
        
        # Files to exclude completely
        exclude_patterns = [
            '_chunks.json', '.env', '.py', '.md', '.txt', '.pyc', '__pycache__'
        ]
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                # Skip excluded files
                if any(pattern in file for pattern in exclude_patterns):
                    continue
                    
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                if file_ext == '.iflw':
                    all_files['main_iflow'].append(file_path)
                elif file_ext in ['.groovy', '.gsh']:
                    all_files['groovy_scripts'].append(file_path)
                elif file_ext == '.xsd':
                    all_files['xsd_files'].append(file_path)
                elif file_ext == '.mmap':
                    all_files['message_mappings'].append(file_path)
                elif file_ext == '.wsdl':
                    all_files['wsdl_files'].append(file_path)
                elif file_ext in ['.properties', '.prop', '.propdef']:
                    all_files['properties_files'].append(file_path)
                elif file_ext in ['.xsl', '.xslt']:
                    all_files['xslt_files'].append(file_path)
                elif file_ext == '.json':
                    # Only include small JSON config files
                    try:
                        if os.path.getsize(file_path) <= 10000:  # 10KB limit
                            all_files['json_files'].append(file_path)
                    except OSError:
                        continue
                elif Path(file_path).name == 'MANIFEST.MF':
                    all_files['manifest_files'].append(file_path)
        
        return all_files
    
    def _find_main_iflow(self, all_files: Dict[str, List[str]]) -> Optional[str]:
        """Find the main iFlow file."""
        if all_files['main_iflow']:
            return all_files['main_iflow'][0]
        return None

    def _process_main_iflow_with_components(self, iflow_file: str) -> List[Dict[str, Any]]:
        """Process main iFlow with component-level chunking, message flows, and full-XML chunk."""
        chunks = []

        try:
            with open(iflow_file, 'r', encoding='utf-8') as f:
                content = f.read()

            root = etree.fromstring(content.encode('utf-8'))

            # Add a full-XML chunk for complete context
            chunks.append(self._create_full_iflow_chunk(iflow_file, content))

            # Extract all component IDs
            component_ids = self._extract_all_component_ids(root)

            # Process each component with proper sourceRef logic
            for component_id in component_ids:
                component_chunk = self._create_component_chunk(component_id, root, iflow_file)
                if not component_chunk:
                    continue
                # Include all components including multiple startEvents
                chunks.append(component_chunk)

            # Add messageFlow chunks if present
            message_flow_chunks = self._extract_message_flows(root, iflow_file)
            chunks.extend(message_flow_chunks)

            # Add sequenceFlow chunks with participant mapping
            sequence_flow_chunks = self._extract_sequence_flows(root, iflow_file)
            chunks.extend(sequence_flow_chunks)

            # NEW: Add process chunks
            process_chunks = self._extract_processes(root, iflow_file)
            chunks.extend(process_chunks)

            # NEW: Add subprocess chunks
            subprocess_chunks = self._extract_subprocesses(root, iflow_file)
            chunks.extend(subprocess_chunks)

            logger.info(f"Processed main iFlow: {len(chunks)} total chunks")
            logger.info(f"  - Components: {len([c for c in chunks if c.get('component_type') not in ['process', 'subProcess', 'sequenceFlow', 'messageFlow', 'bpmnDefinitions']])}")
            logger.info(f"  - Processes: {len(process_chunks)}")
            logger.info(f"  - SubProcesses: {len(subprocess_chunks)}")
            logger.info(f"  - Sequence Flows: {len(sequence_flow_chunks)}")
            logger.info(f"  - Message Flows: {len(message_flow_chunks)}")
            logger.info(f"  - Full XML: 1")

        except Exception as e:
            logger.error(f"Error processing main iFlow {iflow_file}: {e}")

        return chunks

    def _extract_sequence_flows(self, root, iflow_file: str) -> List[Dict[str, Any]]:
        """Extract bpmn:sequenceFlow elements and map them to participants via processRef."""
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
        }
        chunks: List[Dict[str, Any]] = []

        try:
            # Map processRef -> participantId
            process_to_participant: Dict[str, str] = {}
            for ns in ['bpmn2', 'bpmn']:
                participants = root.xpath(f'//{ns}:participant', namespaces=namespaces)
                for p in participants:
                    pref = p.get('processRef')
                    pid = p.get('id')
                    if pref and pid and pref not in process_to_participant:
                        process_to_participant[pref] = pid

            # Map element id -> owning process id by walking ancestors
            element_process: Dict[str, Optional[str]] = {}
            for el in root.xpath('//*[@id]'):
                el_id = el.get('id')
                parent = el.getparent()
                proc_id: Optional[str] = None
                while parent is not None:
                    tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                    if tag == 'process':
                        proc_id = parent.get('id')
                        break
                    parent = parent.getparent()
                if el_id and el_id not in element_process:
                    element_process[el_id] = proc_id

            # Build sequence flow chunks
            for ns in ['bpmn2', 'bpmn']:
                flows = root.xpath(f'//{ns}:sequenceFlow', namespaces=namespaces)
                for flow in flows:
                    flow_id = flow.get('id') or 'sequenceFlow'
                    src = flow.get('sourceRef', '')
                    tgt = flow.get('targetRef', '')
                    src_proc = element_process.get(src)
                    tgt_proc = element_process.get(tgt)
                    src_part = process_to_participant.get(src_proc, '') if src_proc else ''
                    tgt_part = process_to_participant.get(tgt_proc, '') if tgt_proc else ''

                    # Assemble content: sequenceFlow + DI edges
                    content_parts = [etree.tostring(flow, encoding='unicode', pretty_print=True)]
                    di_edges = root.xpath(f'//bpmndi:BPMNEdge[@bpmnElement="{flow_id}"]', namespaces=namespaces)
                    for edge in di_edges:
                        content_parts.append(etree.tostring(edge, encoding='unicode', pretty_print=True))
                    complete = '\n'.join(content_parts)

                    chunk = {
                        'id': f"{Path(iflow_file).stem}_{flow_id}",
                        'file_name': os.path.relpath(iflow_file, self.base_path),
                        'file_type': 'bpmn_sequence_flow',
                        'component_id': flow_id,
                        'component_type': 'sequenceFlow',
                        'content': complete,
                        'description': f"Sequence Flow {src}->{tgt} (participants: {src_part or '-'}→{tgt_part or '-'})",
                        'properties': {},
                        'connections': [src, tgt],
                        'participants': {'source': src_part, 'target': tgt_part},
                        'signature': hashlib.sha256(complete.encode()).hexdigest()[:16]
                    }
                    chunks.append(chunk)
        except Exception as e:
            logger.error(f"Error extracting sequence flows: {e}")

        return chunks

    def _extract_all_component_ids(self, root) -> List[str]:
        """Extract all component IDs from BPMN XML."""
        component_ids = []

        # Define BPMN component types
        component_types = [
            'startEvent', 'endEvent', 'serviceTask', 'callActivity',
            'scriptTask', 'userTask', 'manualTask', 'receiveTask', 'sendTask',
            'exclusiveGateway', 'parallelGateway', 'inclusiveGateway',
            'eventBasedGateway', 'participant', 'boundaryEvent',
            'intermediateCatchEvent', 'intermediateThrowEvent'
        ]

        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
        }

        for component_type in component_types:
            for ns in ['bpmn2', 'bpmn']:
                xpath = f".//{ns}:{component_type}"
                elements = root.xpath(xpath, namespaces=namespaces)

                for element in elements:
                    component_id = element.get('id')
                    if component_id and component_id not in component_ids:
                        component_ids.append(component_id)

        return component_ids

    def _create_component_chunk(self, component_id: str, root, iflow_file: str) -> Optional[Dict[str, Any]]:
        """Create component chunk with outgoing sequence flows only (where component is sourceRef)."""
        try:
            # Extract component elements including both outgoing and incoming flows
            component_elements = self._extract_component_elements(component_id, root)

            if not component_elements['main_component']:
                return None

            # Build complete XML structure
            complete_xml = self._build_complete_component_xml(component_elements)

            # Generate description
            description = self._generate_component_description(component_id, component_elements)

            # Extract properties
            properties = self._extract_component_properties(component_elements['main_component'])

            # Extract inline scripts related to this component (if any)
            related_scripts = self._extract_inline_scripts(component_elements['main_component'])

            # Resolve file-based scripts referenced in properties/content against existing script files
            file_related, unresolved = self._resolve_component_script_files(
                properties,
                complete_xml
            )
            if file_related:
                related_scripts.extend(file_related)

            # Resolve participant that owns this component (via ancestor processRef)
            participant_id = self._resolve_participant_for_element(component_elements['main_component'], root)

            # Prepare sequence flow data
            outgoing_flows_data = [
                {
                    'id': flow.get('id'),
                    'sourceRef': flow.get('sourceRef'),
                    'targetRef': flow.get('targetRef'),
                    'name': flow.get('name', '')
                }
                for flow in component_elements['outgoing_flows']
            ]

            # Extract activityType from the main component
            activity_type = self._extract_activity_type(component_elements['main_component'])

            chunk_data = {
                'id': f"{Path(iflow_file).stem}_{component_id}",
                'file_name': os.path.relpath(iflow_file, self.base_path),
                'file_type': 'bpmn',
                'component_id': component_id,
                'component_type': self._get_component_type(component_elements['main_component']),
                'activity_type': activity_type,
                'complete_bpmn_xml': complete_xml,
                'description': description,
                'properties': properties,
                'related_scripts': related_scripts,
                'unresolved_script_refs': unresolved,
                'participant': participant_id or '',
                'sequence_flows': outgoing_flows_data,  # Only outgoing flows in main field
                'connections': [flow.get('id') for flow in component_elements['outgoing_flows']],
                'signature': hashlib.sha256(complete_xml.encode()).hexdigest()[:16]
            }

            return chunk_data

        except Exception as e:
            logger.error(f"Error creating component chunk for {component_id}: {e}")
            return None

    def _extract_component_elements(self, component_id: str, root) -> Dict[str, Any]:
        """Extract BPMN elements for a component including outgoing and incoming sequence flows."""
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
        }

        elements = {
            'main_component': None,
            'outgoing_flows': [],
            'bpmn_shapes': [],
            'bpmn_edges': []
        }

        # 1. Main component element
        main_component = root.xpath(f'//*[@id="{component_id}"]')
        if main_component:
            elements['main_component'] = main_component[0]

        # 2a. Outgoing sequence flows (where component is sourceRef) - DEDUPLICATED
        seen_flow_ids = set()
        for ns in ['bpmn2', 'bpmn']:
            outgoing_flows = root.xpath(f'//{ns}:sequenceFlow[@sourceRef="{component_id}"]',
                                       namespaces=namespaces)
            for flow in outgoing_flows:
                flow_id = flow.get('id')
                if flow_id and flow_id not in seen_flow_ids:
                    elements['outgoing_flows'].append(flow)
                    seen_flow_ids.add(flow_id)

        # 3. BPMN shapes for the component - DEDUPLICATED
        seen_shape_ids = set()
        bpmn_shapes = root.xpath(f'//bpmndi:BPMNShape[@bpmnElement="{component_id}"]',
                                namespaces=namespaces)
        for shape in bpmn_shapes:
            shape_id = shape.get('id')
            if shape_id and shape_id not in seen_shape_ids:
                elements['bpmn_shapes'].append(shape)
                seen_shape_ids.add(shape_id)

        # 4. BPMN edges for outgoing sequence flows only - DEDUPLICATED
        seen_edge_ids = set()
        outgoing_flow_ids = [flow.get('id') for flow in elements['outgoing_flows']]
        for flow_id in outgoing_flow_ids:
            if flow_id:  # Ensure flow_id is not None
                bpmn_edges = root.xpath(f'//bpmndi:BPMNEdge[@bpmnElement="{flow_id}"]',
                                       namespaces=namespaces)
                for edge in bpmn_edges:
                    edge_id = edge.get('id')
                    if edge_id and edge_id not in seen_edge_ids:
                        elements['bpmn_edges'].append(edge)
                        seen_edge_ids.add(edge_id)

        return elements

    def _build_process_to_participant_map(self, root) -> Dict[str, str]:
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
        }
        process_to_participant: Dict[str, str] = {}
        for ns in ['bpmn2', 'bpmn']:
            participants = root.xpath(f'//{ns}:participant', namespaces=namespaces)
            for p in participants:
                pref = p.get('processRef')
                pid = p.get('id')
                if pref and pid and pref not in process_to_participant:
                    process_to_participant[pref] = pid
        return process_to_participant

    def _find_owning_process_id(self, element) -> Optional[str]:
        parent = element.getparent()
        while parent is not None:
            tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
            if tag == 'process':
                return parent.get('id')
            parent = parent.getparent()
        return None

    def _resolve_participant_for_element(self, element, root) -> Optional[str]:
        proc_id = self._find_owning_process_id(element)
        if not proc_id:
            return None
        proc_to_part = self._build_process_to_participant_map(root)
        return proc_to_part.get(proc_id)

    def _extract_inline_scripts(self, component_element) -> List[Dict[str, Any]]:
        """Extract inline <script> elements within the component and return as related scripts."""
        related = []
        try:
            # Any descendant tag that ends with 'script'
            for elem in component_element.iter():
                tag = elem.tag
                local = tag.split('}')[-1] if '}' in tag else tag
                if local.lower() == 'script':
                    script_text = (elem.text or '').strip()
                    if script_text:
                        related.append({
                            'relation': 'inline',
                            'language_hint': 'auto',
                            'content': script_text,
                            'length': len(script_text)
                        })
        except Exception:
            return related
        return related

    def _extract_message_flows(self, root, iflow_file: str) -> List[Dict[str, Any]]:
        """Extract bpmn:messageFlow elements and create chunks including DI edges if available."""
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
        }
        chunks: List[Dict[str, Any]] = []
        try:
            for ns in ['bpmn2', 'bpmn']:
                flows = root.xpath(f'//{ns}:messageFlow', namespaces=namespaces)
                for flow in flows:
                    flow_id = flow.get('id') or 'messageFlow'
                    content_parts = [etree.tostring(flow, encoding='unicode', pretty_print=True)]
                    # include DI edge if any
                    edges = root.xpath(f'//bpmndi:BPMNEdge[@bpmnElement="{flow_id}"]', namespaces=namespaces)
                    for edge in edges:
                        content_parts.append(etree.tostring(edge, encoding='unicode', pretty_print=True))
                    complete = '\n'.join(content_parts)
                    chunks.append({
                        'id': f"{Path(iflow_file).stem}_{flow_id}",
                        'file_name': os.path.relpath(iflow_file, self.base_path),
                        'file_type': 'bpmn_message_flow',
                        'component_id': flow_id,
                        'component_type': 'messageFlow',
                        'content': complete,
                        'description': f"Message Flow '{flow.get('name', flow_id)}'",
                        'properties': {},
                        'connections': [
                            flow.get('sourceRef', ''),
                            flow.get('targetRef', '')
                        ],
                        'signature': hashlib.sha256(complete.encode()).hexdigest()[:16]
                    })
        except Exception as e:
            logger.error(f"Error extracting message flows: {e}")
        return chunks

    def _extract_processes(self, root, iflow_file: str) -> List[Dict[str, Any]]:
        """Extract bpmn:process elements and create chunks - both complete processes and separate subprocesses."""
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
        }
        chunks: List[Dict[str, Any]] = []
        processed_ids = set()  # Track processed IDs to avoid duplicates

        try:
            # Use only bpmn2 namespace to avoid duplicates
            processes = root.xpath('//bpmn2:process', namespaces=namespaces)

            for process in processes:
                process_id = process.get('id') or 'process'

                # Skip if already processed (avoid duplicates)
                if process_id in processed_ids:
                    continue
                processed_ids.add(process_id)

                process_name = process.get('name', '')

                # Extract process type from direct ifl:property elements (not nested ones)
                process_type = ''
                properties = {}

                # Get only direct child properties of this process (not from nested subprocesses)
                # Try multiple XPath patterns to find properties
                direct_props = process.xpath('./bpmn2:extensionElements/ifl:property', namespaces=namespaces)
                if not direct_props:
                    # Try without namespace prefix in case XML was cleaned
                    direct_props = process.xpath('./extensionElements/property', namespaces=namespaces)

                for prop in direct_props:
                    # Try with namespace first, then without
                    key_elem = prop.find('ifl:key', namespaces)
                    value_elem = prop.find('ifl:value', namespaces)

                    if key_elem is None:
                        key_elem = prop.find('key')
                    if value_elem is None:
                        value_elem = prop.find('value')

                    if key_elem is not None and value_elem is not None:
                        key = key_elem.text if key_elem.text else ''
                        value = value_elem.text if value_elem.text else ''
                        if key and value:
                            properties[key] = value
                            if key == 'processType':
                                process_type = value

                # Get the complete XML content for the process (includes nested subprocesses)
                complete_xml = etree.tostring(process, encoding='unicode', pretty_print=True)

                # Clean the XML - remove namespaces and format properly
                clean_xml = self._clean_process_xml(complete_xml)

                # Generate enhanced description using GPT
                description_context = f"Process ID: {process_id}\nProcess Name: {process_name}\nProcess Type: {process_type}\nProperties: {properties}"
                enhanced_description = self._generate_process_description(description_context, "process")

                chunk = {
                    'id': f"{Path(iflow_file).stem}_{process_id}",
                    'file_name': os.path.relpath(iflow_file, self.base_path),
                    'file_type': 'bpmn',
                    'component_id': process_id,
                    'component_type': 'process',
                    'activity_type': process_type,  # This will be the processType (e.g., 'directCall')
                    'complete_bpmn_xml': clean_xml,
                    'description': enhanced_description,
                    'properties': properties,
                    'related_scripts': [],
                    'unresolved_script_refs': [],
                    'participant': '',
                    'sequence_flows': [],
                    'connections': [],
                    'signature': hashlib.sha256(clean_xml.encode()).hexdigest()[:16]
                }
                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error extracting processes: {e}")

        return chunks

    def _extract_subprocesses(self, root, iflow_file: str) -> List[Dict[str, Any]]:
        """Extract bpmn:subProcess elements and create separate chunks for each subprocess."""
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
        }
        chunks: List[Dict[str, Any]] = []
        processed_ids = set()  # Track processed IDs to avoid duplicates

        try:
            # Use only bpmn2 namespace to avoid duplicates
            subprocesses = root.xpath('//bpmn2:subProcess', namespaces=namespaces)

            for subprocess in subprocesses:
                subprocess_id = subprocess.get('id') or 'subprocess'

                # Skip if already processed (avoid duplicates)
                if subprocess_id in processed_ids:
                    continue
                processed_ids.add(subprocess_id)

                subprocess_name = subprocess.get('name', '')

                # Extract activity type from direct ifl:property elements
                activity_type = ''
                properties = {}

                # Get only direct child properties of this subprocess
                # Try multiple XPath patterns to find properties
                direct_props = subprocess.xpath('./bpmn2:extensionElements/ifl:property', namespaces=namespaces)
                if not direct_props:
                    # Try without namespace prefix in case XML was cleaned
                    direct_props = subprocess.xpath('./extensionElements/property', namespaces=namespaces)

                for prop in direct_props:
                    # Try with namespace first, then without
                    key_elem = prop.find('ifl:key', namespaces)
                    value_elem = prop.find('ifl:value', namespaces)

                    if key_elem is None:
                        key_elem = prop.find('key')
                    if value_elem is None:
                        value_elem = prop.find('value')

                    if key_elem is not None and value_elem is not None:
                        key = key_elem.text if key_elem.text else ''
                        value = value_elem.text if value_elem.text else ''
                        if key and value:
                            properties[key] = value
                            if key == 'activityType':
                                activity_type = value

                # Get the complete XML content for the subprocess
                complete_xml = etree.tostring(subprocess, encoding='unicode', pretty_print=True)

                # Clean the XML - remove namespaces and format properly
                clean_xml = self._clean_process_xml(complete_xml)

                # Generate enhanced description using GPT
                description_context = f"SubProcess ID: {subprocess_id}\nSubProcess Name: {subprocess_name}\nActivity Type: {activity_type}\nProperties: {properties}"
                enhanced_description = self._generate_process_description(description_context, "subprocess")

                chunk = {
                    'id': f"{Path(iflow_file).stem}_{subprocess_id}",
                    'file_name': os.path.relpath(iflow_file, self.base_path),
                    'file_type': 'bpmn',
                    'component_id': subprocess_id,
                    'component_type': 'subProcess',
                    'activity_type': activity_type,  # This will be the activityType (e.g., 'ErrorEventSubProcessTemplate')
                    'complete_bpmn_xml': clean_xml,
                    'description': enhanced_description,
                    'properties': properties,
                    'related_scripts': [],
                    'unresolved_script_refs': [],
                    'participant': '',
                    'sequence_flows': [],
                    'connections': [],
                    'signature': hashlib.sha256(clean_xml.encode()).hexdigest()[:16]
                }
                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error extracting subprocesses: {e}")

        return chunks

    def _clean_process_xml(self, xml_content: str) -> str:
        """Clean XML content - remove namespaces, newlines, and format properly."""
        if not xml_content:
            return xml_content

        import re

        # Remove namespace declarations
        xml_content = re.sub(r'\s+xmlns(:\w+)?="[^"]+"', '', xml_content)

        # Remove namespace prefixes from tags
        xml_content = re.sub(r'<(/?)(bpmn2|bpmndi|di|dc|ifl):', r'<\1', xml_content)

        # Remove newlines and extra whitespace
        xml_content = re.sub(r'\n\s*', '', xml_content)
        xml_content = re.sub(r'>\s+<', '><', xml_content)

        # Format with proper indentation
        return self._format_xml_with_indentation(xml_content)

    def _format_xml_with_indentation(self, xml_content: str) -> str:
        """Format XML with proper indentation."""
        if not xml_content:
            return xml_content

        import re
        elements = re.split(r'(<[^>]+>)', xml_content)
        formatted_lines = []
        indent_level = 0

        for element in elements:
            if not element.strip():
                continue

            if element.startswith('</'):
                indent_level = max(0, indent_level - 1)
                formatted_lines.append('    ' * indent_level + element)
            elif element.startswith('<') and not element.endswith('/>'):
                formatted_lines.append('    ' * indent_level + element)
                if not element.startswith('<?') and not element.startswith('<!'):
                    indent_level += 1
            else:
                formatted_lines.append('    ' * indent_level + element)

        return '\n'.join(formatted_lines)

    def _generate_process_description(self, context: str, process_type: str) -> str:
        """Generate enhanced description for process/subprocess using GPT."""
        try:
            # Use the existing embedding generator's description method
            if hasattr(self, 'embedding_generator'):
                return self.embedding_generator.generate_description(context, process_type)
            else:
                # Fallback to simple description if no embedding generator available
                if process_type == "subprocess":
                    return f"SubProcess component that handles specific error handling or specialized processing tasks within the integration flow."
                else:
                    return f"Process component that orchestrates the main integration flow logic and coordinates message processing between systems."
        except Exception as e:
            logger.error(f"Error generating process description: {e}")
            # Fallback description
            if process_type == "subprocess":
                return f"SubProcess component for specialized processing within the integration flow."
            else:
                return f"Process component for main integration flow orchestration."

    def _create_full_iflow_chunk(self, iflow_file: str, full_xml: str) -> Dict[str, Any]:
        """Create a full-XML chunk for the entire iFlow file for holistic retrieval."""
        relative_path = os.path.relpath(iflow_file, self.base_path)
        return {
            'id': f"{Path(iflow_file).stem}_full_xml",
            'file_name': relative_path,
            'file_type': 'bpmn_full_xml',
            'component_id': 'full_xml',
            'component_type': 'bpmnDefinitions',
            'content': full_xml,
            'description': 'Complete iFlow BPMN XML',
            'properties': {},
            'connections': [],
            'signature': hashlib.sha256(full_xml.encode()).hexdigest()[:16]
        }

    def _build_complete_component_xml(self, component_elements: Dict[str, Any]) -> str:
        """Build complete XML structure for the component chunk (main + outgoing flows only + shapes/edges)."""
        xml_parts = []

        # Add main component
        if component_elements['main_component'] is not None:
            xml_parts.append(etree.tostring(component_elements['main_component'],
                                           encoding='unicode', pretty_print=True))

        # Add ONLY outgoing sequence flows (where component is sourceRef)
        for flow in component_elements['outgoing_flows']:
            xml_parts.append(etree.tostring(flow, encoding='unicode', pretty_print=True))

        # Add BPMN shapes
        for shape in component_elements['bpmn_shapes']:
            xml_parts.append(etree.tostring(shape, encoding='unicode', pretty_print=True))

        # Add BPMN edges for outgoing flows only
        for edge in component_elements['bpmn_edges']:
            # Only include edges for outgoing flows
            edge_element = edge.get('bpmnElement')
            outgoing_flow_ids = [flow.get('id') for flow in component_elements['outgoing_flows']]
            if edge_element in outgoing_flow_ids:
                xml_parts.append(etree.tostring(edge, encoding='unicode', pretty_print=True))

        return '\n'.join(xml_parts)

    def _generate_component_description(self, component_id: str, component_elements: Dict[str, Any]) -> str:
        """Generate intelligent description for component."""
        main_component = component_elements['main_component']
        if main_component is None:
            return f"BPMN component {component_id}"

        component_type = self._get_component_type(main_component)
        component_name = main_component.get('name', '')

        # Extract properties for context
        properties = self._extract_component_properties(main_component)

        # Build description
        desc_parts = [component_type.replace('Event', ' Event').replace('Task', ' Task').title()]

        if component_name:
            desc_parts.append(f"'{component_name}'")

        # Add property-based context
        if 'activityType' in properties:
            desc_parts.append(f"with activityType={properties['activityType']}")

        if 'cmdVariantUri' in properties:
            variant = properties['cmdVariantUri']
            if 'ErrorStartEvent' in variant:
                desc_parts.append("for error handling")
            elif 'Timer' in variant:
                desc_parts.append("for scheduled execution")
            elif 'HTTP' in variant:
                desc_parts.append("for HTTP communication")

        return ' '.join(desc_parts)

    def _get_component_type(self, element) -> str:
        """Get component type from XML element."""
        tag = element.tag
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _extract_activity_type(self, element) -> str:
        """Extract activityType from ifl:property elements."""
        namespaces = {
            'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
        }

        # Look for ifl:property with key 'activityType'
        activity_type_props = element.xpath('.//ifl:property[key="activityType"]/value', namespaces=namespaces)
        if activity_type_props and activity_type_props[0].text:
            return activity_type_props[0].text.strip()

        # If no activityType found, return empty string as requested
        return ""

    def _extract_component_properties(self, element) -> Dict[str, Any]:
        """Extract ifl:property elements from component."""
        properties = {}

        # Try multiple approaches for property extraction
        for child in element.iter():
            if child.tag.endswith('}property') or 'property' in child.tag:
                key_elem = None
                value_elem = None

                for subchild in child:
                    if subchild.tag.endswith('}key') or subchild.tag == 'key':
                        key_elem = subchild
                    elif subchild.tag.endswith('}value') or subchild.tag == 'value':
                        value_elem = subchild

                if key_elem is not None and value_elem is not None:
                    key = key_elem.text if key_elem.text else ''
                    value = value_elem.text if value_elem.text else ''
                    if key and value:
                        properties[key] = value

        return properties

    def _process_all_related_files(self, all_files: Dict[str, List[str]]) -> List[str]:
        """Process all related files in the iFlow package."""
        processed = []

        # Process each file type
        for file_type, files in all_files.items():
            if file_type == 'main_iflow':
                continue

            for file_path in files:
                try:
                    chunk = self._process_related_file(file_path, file_type)
                    if chunk:
                        self.chunks.append(chunk)
                        processed.append(file_path)
                        logger.info(f"Processed {file_type}: {Path(file_path).name}")
                        # If it's a script, update script index with final chunk id reference
                        if file_type == 'groovy_scripts':
                            self._update_script_index_with_chunk(chunk)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        return processed

    def _process_related_file(self, file_path: str, file_type: str) -> Optional[Dict[str, Any]]:
        """Process a related file (Groovy, XSD, etc.)."""
        try:
            file_name = Path(file_path).name
            file_ext = Path(file_path).suffix.lower()

            # Skip output files, source code, documentation, and sensitive files
            skip_patterns = [
                '_chunks.json', 'enhanced_iflow_chunks.json', 'clean_iflow_chunks.json',
                '.env', '.py', '.md', '.txt', '.pyc'
            ]

            if any(pattern in file_name or file_name.endswith(pattern) for pattern in skip_patterns):
                logger.info(f"Skipping excluded file: {file_name}")
                return None

            # Only process integration-related files
            allowed_extensions = ['.groovy', '.gsh', '.xsd', '.mmap', '.wsdl', '.properties', '.prop', '.propdef', '.xsl', '.xslt']
            if file_ext == '.json':
                # Only process small JSON config files, not large data files
                if os.path.getsize(file_path) > 10000:  # 10KB limit for JSON
                    logger.info(f"Skipping large JSON file: {file_name}")
                    return None
            elif file_ext not in allowed_extensions and Path(file_path).name != 'MANIFEST.MF':
                logger.info(f"Skipping non-integration file: {file_name}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip files that are too large (> 50KB)
            if len(content) > 50000:
                logger.info(f"Skipping large file: {file_name} ({len(content)} bytes)")
                return None

            relative_path = os.path.relpath(file_path, self.base_path)

            # Generate description based on file type
            description = self._generate_file_description(file_name, file_type, content)

            chunk = {
                'id': f"{Path(file_path).stem}_{file_type}",
                'file_name': relative_path,
                'file_type': file_type,
                'content': content,
                'description': description,
                'signature': hashlib.sha256(content.encode()).hexdigest()[:16]
            }
            # Pre-index script files immediately
            if file_type == 'groovy_scripts':
                self._index_script_file(Path(file_path).name, relative_path, chunk['id'])
            return chunk

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None

    def _generate_file_description(self, file_name: str, file_type: str, content: str) -> str:
        """Generate description for related files."""
        file_lower = file_name.lower()
        content_lower = content.lower()

        if file_type == 'groovy_scripts':
            if 'commission' in file_lower:
                return "Groovy script for commission processing and data iteration"
            elif 'validation' in file_lower or 'validate' in content_lower:
                return "Groovy script for data validation and quality checks"
            elif 'transformation' in file_lower or 'transform' in content_lower:
                return "Groovy script for data transformation and mapping"
            else:
                return "Groovy script for integration flow processing"

        elif file_type == 'xsd_files':
            if 'employee' in file_lower:
                return "XSD schema definition for employee data structure"
            elif 'title' in file_lower:
                return "XSD schema definition for title and response data"
            else:
                return "XSD schema definition for data validation"

        elif file_type == 'message_mappings':
            return "Message mapping configuration for data transformation between systems"

        elif file_type == 'properties_files':
            if 'parameter' in file_lower:
                return "Properties file defining integration flow parameters and configuration"
            elif 'metainfo' in file_lower:
                return "Properties file with integration package metadata"
            else:
                return "Properties configuration file"

        elif file_type == 'manifest_files':
            return "MANIFEST.MF file containing package metadata and deployment information"

        else:
            return f"{file_type.replace('_', ' ').title()} file"

    def _verify_complete_coverage(self, all_files: Dict[str, List[str]]) -> Dict[str, Any]:
        """Verify complete coverage of all files."""
        total_files = sum(len(files) for files in all_files.values())

        coverage_report = {
            'total_files_discovered': total_files,
            'total_files_processed': len(self.processed_files),
            'coverage_percentage': (len(self.processed_files) / total_files * 100) if total_files > 0 else 100,
            'file_type_breakdown': {},
            'missing_files': []
        }

        # Check coverage by file type
        for file_type, files in all_files.items():
            processed_count = sum(1 for f in files if f in self.processed_files)

            coverage_report['file_type_breakdown'][file_type] = {
                'total': len(files),
                'processed': processed_count,
                'coverage': (processed_count / len(files) * 100) if len(files) > 0 else 100
            }

            # Track missing files
            for file_path in files:
                if file_path not in self.processed_files:
                    coverage_report['missing_files'].append(file_path)

        return coverage_report

    def _build_script_index(self, all_files: Dict[str, List[str]]) -> None:
        """Index available script files by common keys (exact name and lower base name)."""
        script_files = all_files.get('groovy_scripts', [])
        for path in script_files:
            relative = os.path.relpath(path, self.base_path)
            name = Path(path).name
            base = Path(path).stem
            self._index_script_file(name, relative, None)
            self._index_script_file(base, relative, None)

    def _index_script_file(self, key: str, relative_path: str, chunk_id: Optional[str]) -> None:
        index_key = key.lower()
        self.script_index[index_key] = {
            'file_name': relative_path,
            'chunk_id': chunk_id
        }

    def _update_script_index_with_chunk(self, chunk: Dict[str, Any]) -> None:
        """Attach final chunk id for previously indexed script entries."""
        name = Path(chunk['file_name']).name
        base = Path(chunk['file_name']).stem
        for k in [name.lower(), base.lower()]:
            if k in self.script_index:
                self.script_index[k]['chunk_id'] = chunk['id']

    def _resolve_component_script_files(self, properties: Dict[str, Any], component_xml: str = "") -> tuple[List[Dict[str, Any]], List[str]]:
        """Resolve script references in properties against indexed scripts."""
        resolved: List[Dict[str, Any]] = []
        unresolved: List[str] = []
        # Heuristics: look for property values that look like script names or keys that hint scripts
        candidates: List[str] = []
        for key, value in properties.items():
            if isinstance(value, str):
                val = value.strip()
                if val:
                    if val.lower().endswith(('.groovy', '.gsh')):
                        candidates.append(val)
                    elif any(h in key.lower() for h in ['script', 'groovy', 'gsh']):
                        candidates.append(val)
        # Also scan component XML for obvious script filename literals
        if component_xml:
            import re
            for m in re.findall(r"[A-Za-z0-9_\-/]+\.(?:groovy|gsh)", component_xml):
                candidates.append(m)
        # Deduplicate
        seen: set[str] = set()
        for cand in candidates:
            lc = cand.lower()
            if lc in seen:
                continue
            seen.add(lc)
            stem = Path(lc).stem
            entry = self.script_index.get(lc) or self.script_index.get(stem)
            if entry:
                resolved.append({
                    'relation': 'file',
                    'file_name': entry['file_name'],
                    'file_type': 'groovy_scripts',
                    'chunk_id': entry.get('chunk_id') or ''
                })
            else:
                unresolved.append(cand)
        return resolved, unresolved


class EmbeddingGenerator:
    """Generate embeddings using OpenAI and descriptions using GPT-4o-mini."""

    def generate_embedding(self, text: str, dimensions: int = 1536) -> List[float]:
        """Generate embeddings using OpenAI text-embedding-3-small model with 1536 dimensions."""
        # Handle NaN, None, or empty text
        if text is None or pd.isna(text) or not str(text).strip():
            logger.debug(f"Empty/NaN text provided for embedding, returning zero vector of dimension {dimensions}")
            return [0.0] * dimensions

        try:
            # Clean the text to remove any problematic characters
            clean_text = str(text).strip()
            if len(clean_text) == 0:
                logger.debug(f"Text became empty after cleaning, returning zero vector of dimension {dimensions}")
                return [0.0] * dimensions

            # Use OpenAI text-embedding-3-small model with 1536 dimensions
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=clean_text,
                dimensions=dimensions
            )

            embedding = response.data[0].embedding

            # Validate the result has the correct dimensions
            if len(embedding) != dimensions:
                logger.warning(f"Embedding dimension mismatch: expected {dimensions}, got {len(embedding)}")
                return [0.0] * dimensions

            # Final validation to ensure no NaN values
            import math
            result = []
            for val in embedding:
                if math.isnan(val) or math.isinf(val):
                    result.append(0.0)
                else:
                    result.append(float(val))

            return result

        except Exception as e:
            logger.error(f"Error generating embedding for text '{text[:100]}...': {e}")
            return [0.0] * dimensions

    def generate_description(self, text: str, context_type: str = "general") -> str:
        """Generate comprehensive human-readable descriptions using GPT-4o-mini for RAG pipeline."""
        if not text or not str(text).strip():
            return "No description available."

        try:
            # Clean the input text
            clean_text = str(text).strip()

            # Context-specific prompts for concise, complete descriptions
            context_prompts = {
                "package": """Analyze this SAP Integration Flow package and create a concise business description.

                **Focus on:**
                - Business purpose and main functionality
                - Key integration patterns
                - Primary use cases

                **Requirements:**
                - Write exactly 100-200 words
                - Use clear, professional language
                - Focus on business value
                - Complete all sentences properly""",

                "component": """Analyze this BPMN component and create a clear technical description.

                **Focus on:**
                - Component type and primary function
                - Key configuration and purpose
                - Role in the integration workflow

                **Requirements:**
                - Write exactly 80-150 words
                - Explain technical concepts clearly
                - Complete all sentences properly
                - Focus on practical functionality""",

                "flow": """Analyze this BPMN flow connection and create a clear description.

                **Focus on:**
                - Flow type and connection purpose
                - Source and target relationship
                - Data handling role

                **Requirements:**
                - Write exactly 60-120 words
                - Explain the flow's role clearly
                - Complete all sentences properly
                - Focus on data movement""",

                "asset": """Analyze this integration asset and create a clear description.

                **Focus on:**
                - Asset type and business purpose
                - Key capabilities
                - Usage context

                **Requirements:**
                - Write exactly 80-150 words
                - Explain both technical and business aspects
                - Complete all sentences properly
                - Focus on practical applications""",

                "general": """Analyze this content and create a clear description.

                **Focus on:**
                - Purpose and functionality
                - Key capabilities
                - Business value

                **Requirements:**
                - Write exactly 80-150 words
                - Use clear, professional language
                - Complete all sentences properly
                - Focus on practical value"""
            }

            prompt = context_prompts.get(context_type, context_prompts["general"])

            # Generate concise, complete description using GPT-4o-mini
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a senior SAP Integration Suite consultant and technical writer.

                        **Your Task**: Create concise, complete, human-readable descriptions optimized for RAG systems.

                        **Critical Requirements:**
                        - Write COMPLETE descriptions only - never cut off mid-sentence
                        - Stay within the specified word limits
                        - Use clear, professional language
                        - Focus on practical value
                        - End with complete sentences and proper punctuation
                        - If you cannot complete a description within the word limit, write a shorter complete description instead"""
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nContent to analyze:\n{clean_text}"
                    }
                ],
                max_tokens=300,  # Reduced to ensure shorter, complete descriptions
                temperature=0.3
            )

            description = response.choices[0].message.content.strip()

            # Ensure description ends with complete sentence
            if description and not description.endswith(('.', '!', '?')):
                # Find the last complete sentence
                last_period = description.rfind('.')
                last_exclamation = description.rfind('!')
                last_question = description.rfind('?')
                last_complete = max(last_period, last_exclamation, last_question)

                if last_complete > 50:  # Only truncate if we have reasonable content
                    description = description[:last_complete + 1]
                else:
                    # If no complete sentence found, add a period to make it complete
                    description = description.rstrip() + "."

            return description

        except Exception as e:
            logger.error(f"Error generating description with GPT-4o-mini: {e}")
            # Enhanced fallback descriptions - short and complete
            fallbacks = {
                "package": "SAP Integration Flow package for enterprise data integration and process automation. Contains multiple integration flows, components, and configurations for seamless data exchange between systems.",
                "component": "BPMN component that handles specific processing tasks, data transformations, or system interactions as part of the integration process.",
                "flow": "BPMN flow connection that manages data and control flow between integration components, ensuring proper message routing and processing.",
                "asset": "Integration asset that provides specific functionality or resources for the integration flow, including configuration settings and processing logic.",
                "general": "Integration element that supports enterprise data integration and business process automation with reliable processing capabilities."
            }
            return fallbacks.get(context_type, fallbacks["general"])

    def clean_bpmn_xml(self, xml_content: str) -> str:
        if not xml_content:
            return xml_content

        # Remove actual newlines and literal \n sequences
        xml_content = xml_content.replace('\r', '')
        xml_content = xml_content.replace('\n', '')
        xml_content = xml_content.replace('\\n', '')
        xml_content = xml_content.replace('\\r', '')

        # Remove all xmlns declarations
        xml_content = re.sub(r'\s+xmlns(:\w+)?="[^"]+"', '', xml_content)

        # Strip known prefixes
        xml_content = re.sub(r'<(/?)(bpmn2|bpmndi|di|dc|ifl):', r'<\1', xml_content)

        # Collapse whitespace between tags
        xml_content = re.sub(r'>\s+<', '><', xml_content)

        xml_content = xml_content.strip()
        return self.format_xml_with_indentation(xml_content)

    def format_xml_with_indentation(self, xml_content: str) -> str:
        """Indent xml tags nicely."""
        if not xml_content:
            return xml_content

        elements = re.split(r'(<[^>]+>)', xml_content)
        formatted_lines = []
        indent_level = 0

        for element in elements:
            if not element.strip():
                continue

            if element.startswith('</'):
                indent_level = max(0, indent_level - 1)
                formatted_lines.append('    ' * indent_level + element)
            elif element.startswith('<') and not element.endswith('/>'):
                formatted_lines.append('    ' * indent_level + element)
                indent_level += 1
            else:
                formatted_lines.append('    ' * indent_level + element)

        return '\n'.join(formatted_lines)


class SupabaseClient:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        self.client: Client = create_client(self.url, self.key)
        logger.info("Connected to Supabase database")



    def insert_package(self, data: Dict[str, Any]) -> Optional[str]:
        """Insert package data into iflow_packages table - Always creates new package"""
        try:
            # Always create a new package for each upload (no duplicate checking)
            # This allows multiple packages with same name but different UUIDs
            package_data = {
                'package_name': data.get('package_name', ''),
                'version': data.get('version', ''),
                'description': data.get('description', ''),
                'iflw_xml': data.get('iflw_xml', ''),
                'description_embedding': data.get('description_embedding', []),
                'metadata': data.get('metadata', {})
            }

            result = self.client.table('iflow_packages').insert(package_data).execute()
            logger.info(f"Inserted new package: {data['package_name']} with ID: {result.data[0]['id']}")
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error inserting package: {e}")
            return None

    def insert_component(self, data: Dict[str, Any]) -> bool:
        """Insert component data into iflow_components table - Prevents duplicates within same package"""
        try:
            package_id = data.get('package_id')
            component_id = data.get('component_id', '')

            # Check for duplicates ONLY within the same package_id
            # This allows same component_id across different packages but prevents duplicates within same package
            try:
                existing = self.client.table('iflow_components')\
                    .select('id').eq('component_id', component_id)\
                    .eq('package_id', package_id).limit(1).execute()
                if existing.data:
                    logger.info(f"Component already exists in package {package_id}: {component_id}")
                    return True  # Skip insertion but return success
            except Exception as e:
                logger.warning(f"Component duplicate check failed, proceeding with insert: {e}")

            # Insert new component (no duplicates found within this package)
            component_data = {
                'package_id': package_id,
                'component_id': component_id,
                'activity_type': data.get('activity_type', ''),
                'activity_type_embedding': data.get('activity_type_embedding', []),
                'description': data.get('description', ''),
                'complete_bpmn_xml': data.get('complete_bpmn_xml', ''),
                'properties': data.get('properties', {}),
                'related_scripts': data.get('related_scripts', []),
                'code_embedding': data.get('code_embedding', []),
                'description_embedding': data.get('description_embedding', [])
            }

            self.client.table('iflow_components').insert(component_data).execute()
            logger.info(f"Inserted component: {component_id} for package: {package_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting component: {e}")
            return False

    def insert_flow(self, data: Dict[str, Any]) -> bool:
        """Insert flow data into iflow_flows table - Prevents duplicates within same package"""
        try:
            # Extract key fields for logging
            source_id = data.get('source_component_id', '')
            target_id = data.get('target_component_id', '')
            package_id = data.get('package_id')
            flow_type = data.get('flow_type', 'sequence')
            file_type = data.get('file_type', '')

            # Check for duplicates ONLY within the same package_id
            # This allows same flows across different packages but prevents duplicates within same package
            try:
                existing = self.client.table('iflow_flows') \
                    .select('id') \
                    .eq('package_id', package_id) \
                    .eq('source_component_id', source_id) \
                    .eq('target_component_id', target_id) \
                    .eq('flow_type', flow_type) \
                    .eq('file_type', file_type) \
                    .limit(1).execute()

                if existing.data:
                    logger.info(f"Flow already exists in package {package_id}: {source_id} -> {target_id} ({flow_type})")
                    return True  # Skip insertion but return success
            except Exception as e:
                logger.warning(f"Flow duplicate check failed, proceeding with insert: {e}")

            # Insert new flow (no duplicates found within this package)
            flow_data = {
                'package_id': package_id,
                'source_component_id': source_id,
                'target_component_id': target_id,
                'flow_type': flow_type,
                'file_type': file_type,
                'content': data.get('content', ''),
                'connections': data.get('connections', []),
                'flow_embedding': data.get('flow_embedding', []),
                'description': data.get('description', ''),
                'description_embedding': data.get('description_embedding', [])
            }

            self.client.table('iflow_flows').insert(flow_data).execute()
            logger.info(f"Inserted flow: {source_id} -> {target_id} ({flow_type}) for package: {package_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting flow: {e}")
            return False

    def insert_asset(self, data: Dict[str, Any]) -> bool:
        """Insert asset data into iflow_assets table - Prevents duplicates within same package"""
        try:
            package_id = data.get('package_id')
            file_name = data.get('file_name', '')

            # Check for duplicates ONLY within the same package_id
            # This allows same asset filename across different packages but prevents duplicates within same package
            try:
                existing = self.client.table('iflow_assets')\
                    .select('id').eq('file_name', file_name)\
                    .eq('package_id', package_id).limit(1).execute()
                if existing.data:
                    logger.info(f"Asset already exists in package {package_id}: {file_name}")
                    return True  # Skip insertion but return success
            except Exception as e:
                logger.warning(f"Asset duplicate check failed, proceeding with insert: {e}")

            # Insert new asset (no duplicates found within this package)
            asset_data = {
                'package_id': package_id,
                'file_name': file_name,
                'file_type': data.get('file_type', ''),
                'description': data.get('description', ''),
                'content': data.get('content', ''),
                'content_embedding': data.get('content_embedding', []),
                'description_embedding': data.get('description_embedding', [])
            }

            self.client.table('iflow_assets').insert(asset_data).execute()
            logger.info(f"Inserted asset: {file_name} for package: {package_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting asset: {e}")
            return False


class IFlowPackageProcessor:
    """Main processor class that combines ZIP extraction, chunking, and embedding."""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.supabase_client = SupabaseClient()

    def extract_zip(self, zip_file_path: str) -> str:
        """Extract ZIP file to temporary directory."""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix='iflow_')
            logger.info(f"Extracting ZIP to temporary directory: {temp_dir}")

            # Extract ZIP file
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            logger.info(f"Successfully extracted ZIP file to {temp_dir}")
            return temp_dir

        except Exception as e:
            logger.error(f"Error extracting ZIP file: {e}")
            raise

    def cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")

    def _save_chunks_to_json(self, chunks: List[Dict[str, Any]], package_name: str):
        """Save chunks to JSON file for inspection before Supabase processing."""
        try:
            # Create a safe filename from package name
            safe_name = "".join(c for c in package_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')

            # Add timestamp to make filename unique
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chunks_{safe_name}_{timestamp}.json"

            # Classify chunks by type for better organization
            classified_chunks = {
                'package': [],
                'component': [],
                'flow': [],
                'asset': [],
                'summary': {
                    'total_chunks': len(chunks),
                    'package_name': package_name,
                    'timestamp': timestamp,
                    'chunk_counts': {}
                }
            }

            # Classify and organize chunks
            for chunk in chunks:
                chunk_type = self.classify_chunk_type(chunk)
                classified_chunks[chunk_type].append(chunk)

            # Update summary with counts
            for chunk_type in ['package', 'component', 'flow', 'asset']:
                classified_chunks['summary']['chunk_counts'][chunk_type] = len(classified_chunks[chunk_type])

            # Save to JSON file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(classified_chunks, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(chunks)} chunks to {filename}")
            logger.info(f"Chunk breakdown: Package={len(classified_chunks['package'])}, "
                       f"Component={len(classified_chunks['component'])}, "
                       f"Flow={len(classified_chunks['flow'])}, "
                       f"Asset={len(classified_chunks['asset'])}")

        except Exception as e:
            logger.error(f"Error saving chunks to JSON: {e}")

    def classify_chunk_type(self, chunk: Dict[str, Any]) -> str:
        """Classify chunk into one of the 4 new schema types."""
        file_type = chunk.get('file_type', '').lower()
        component_type = chunk.get('component_type', '').lower()

        # Package metadata (full XML)
        if file_type == 'bpmn_full_xml' or component_type == 'bpmndefinitions':
            return 'package'

        # BPMN components (events, tasks, gateways, processes, subprocesses)
        elif file_type == 'bpmn' and component_type in ['startevent', 'endevent', 'task', 'callactivity', 'gateway', 'usertask', 'servicetask', 'process', 'subprocess']:
            return 'component'

        # Flow connections (sequence flows, message flows)
        elif (file_type in ['bpmn_sequence_flow', 'bpmn_message_flow'] or
              (file_type == 'bpmn' and component_type in ['sequenceflow', 'messageflow'])):
            return 'flow'

        # Assets (scripts, schemas, mappings, properties)
        elif file_type in ['groovy_scripts', 'xsd_files', 'xslt_files', 'properties_files', 'message_mappings', 'json_files']:
            return 'asset'

        # Default to component for BPMN elements
        elif file_type == 'bpmn':
            return 'component'

        # Default to asset for other files
        else:
            return 'asset'

    def safe_json(self, val: str):
        try:
            return json.loads(val.replace("'", '"')) if isinstance(val, str) else val
        except Exception:
            return {} if "{" in str(val) else []

    def extract_activity_type_from_description(self, description: str) -> str:
        """Extract activity type from description text"""
        if not description:
            return ""

        # Look for pattern like "with activityType=ActivityName"
        import re
        pattern = r"activityType=([A-Za-z0-9_]+)"
        match = re.search(pattern, description)
        if match:
            return match.group(1)

        # If no activityType found, return empty string
        return ""

    def get_bundle_symbolic_name(self, temp_dir: str) -> str:
        manifest_path = Path(temp_dir) / "META-INF" / "MANIFEST.MF"
        if manifest_path.exists():
            try:
                manifest_content = manifest_path.read_text(encoding='utf-8', errors='ignore')
                for line in manifest_content.split('\n'):
                    if line.startswith('Bundle-SymbolicName:'):
                        name = line.split(':', 1)[1].strip()
                        next_lines = manifest_content.split('\n')[manifest_content.split('\n').index(line)+1:]
                        for next_line in next_lines:
                            if next_line.startswith(' '):
                                name += next_line.strip()
                            else:
                                break
                        return name.replace(' ', '').replace('\n', '').replace('\r', '')
                return "iflow_package"
            except Exception as e:
                logger.error(f"Error reading MANIFEST.MF: {e}")
                return "iflow_package"
        return "iflow_package"

    def get_iflow_xml_content(self, temp_dir: str) -> str:
        """Read the iFlow XML content from the .iflw file"""
        try:
            # Find .iflw file in the extracted directory
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.iflw'):
                        iflow_path = Path(root) / file
                        xml_content = iflow_path.read_text(encoding='utf-8', errors='ignore')
                        logger.info(f"Successfully read iFlow XML content from {iflow_path}")
                        return xml_content

            logger.warning(f"No .iflw file found in {temp_dir}")
            return ""
        except Exception as e:
            logger.error(f"Error reading iFlow XML file: {e}")
            return ""

    def ensure_package(self, chunks: List[Dict[str, Any]], temp_dir: str, zip_file_path: str = None) -> Optional[str]:
        """Ensure package exists in database and return package ID."""
        if zip_file_path:
            # Use ZIP file name as base package name (remove .zip extension)
            import os
            base_package_name = os.path.splitext(os.path.basename(zip_file_path))[0]
        else:
            # Fallback to MANIFEST.MF if no ZIP file path provided
            base_package_name = self.get_bundle_symbolic_name(temp_dir)

        # Make package name unique by adding timestamp to avoid UNIQUE constraint violation
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # microseconds to milliseconds
        unique_package_name = f"{base_package_name}_{timestamp}"

        # Find package chunk for description
        package_chunks = [chunk for chunk in chunks if self.classify_chunk_type(chunk) == 'package']
        if package_chunks:
            description = package_chunks[0].get('description', 'SAP Integration Flow package')
        else:
            description = "SAP Integration Flow package for enterprise data integration and automation"

        # Generate enhanced description for package
        enhanced_description = self.embedding_generator.generate_description(description, "package")

        # Get the actual iFlow XML content
        iflow_xml_content = self.get_iflow_xml_content(temp_dir)

        data = {
            'package_name': unique_package_name,
            'version': '1.0.0',
            'description': enhanced_description,
            'iflw_xml': iflow_xml_content,
            'description_embedding': self.embedding_generator.generate_embedding(enhanced_description, 1536),
            'metadata': {
                'source': 'MANIFEST.MF',
                'type': 'integration_flow',
                'original_name': base_package_name,  # Keep original name for reference
                'upload_timestamp': timestamp
            }
        }
        package_id = self.supabase_client.insert_package(data)
        return package_id

    def process_components(self, chunks: List[Dict[str, Any]], package_id: str):
        """Process component chunks."""
        component_chunks = [chunk for chunk in chunks if self.classify_chunk_type(chunk) == 'component']
        logger.info(f"Processing {len(component_chunks)} components")

        for chunk in component_chunks:
            try:
                # Handle description
                desc = chunk.get('description', '')
                if pd.isna(desc):
                    desc = ''
                desc = str(desc)

                props = chunk.get('properties', {})
                if isinstance(props, str):
                    props = self.safe_json(props)

                # Extract activity type from description first, then fallback to other methods
                activity_type = self.extract_activity_type_from_description(desc)
                if not activity_type:
                    activity_type = props.get('activityType') or props.get('activity_name') or chunk.get('activity_type', '') or chunk.get('component_type', '')

                # Handle content
                content = chunk.get('content', '') or chunk.get('complete_bpmn_xml', '')
                if pd.isna(content):
                    content = ''
                content = str(content)

                cleaned_content = self.embedding_generator.clean_bpmn_xml(content)

                # Handle component_id
                component_id = chunk.get('component_id', '')
                if pd.isna(component_id):
                    component_id = ''
                component_id = str(component_id)

                # Generate enhanced description for component
                enhanced_description = self.embedding_generator.generate_description(
                    f"Component ID: {component_id}\nActivity Type: {activity_type}\nDescription: {desc}\nXML Content: {cleaned_content[:500]}",
                    "component"
                )

                data = {
                    'package_id': package_id,
                    'component_id': component_id,
                    'activity_type': str(activity_type) if activity_type else '',
                    'activity_type_embedding': self.embedding_generator.generate_embedding(str(activity_type) if activity_type else '', 1536),
                    'description': enhanced_description,
                    'complete_bpmn_xml': cleaned_content,
                    'properties': props,
                    'related_scripts': chunk.get('related_scripts', []),
                    'code_embedding': self.embedding_generator.generate_embedding(cleaned_content, 1536),
                    'description_embedding': self.embedding_generator.generate_embedding(enhanced_description, 1536)
                }
                self.supabase_client.insert_component(data)
            except Exception as e:
                logger.error(f"Error processing component {chunk.get('component_id', 'unknown')}: {e}")
                continue

    def process_flows(self, chunks: List[Dict[str, Any]], package_id: str):
        """Process flow chunks."""
        flow_chunks = [chunk for chunk in chunks if self.classify_chunk_type(chunk) == 'flow']
        logger.info(f"Processing {len(flow_chunks)} flows")

        for chunk in flow_chunks:
            try:
                # Extract flow information
                connections = chunk.get('connections', [])
                if isinstance(connections, str):
                    connections = self.safe_json(connections)

                source_component_id = connections[0] if len(connections) > 0 else ''
                target_component_id = connections[1] if len(connections) > 1 else ''

                # Determine flow type
                file_type = chunk.get('file_type', '')
                if 'sequence' in file_type:
                    flow_type = 'sequence'
                elif 'message' in file_type:
                    flow_type = 'message'
                else:
                    flow_type = 'sequence'

                content = chunk.get('content', '')
                description = chunk.get('description', '')

                # Clean content and ensure it's not empty for embedding
                cleaned_content = self.embedding_generator.clean_bpmn_xml(content) if content else ""
                if not cleaned_content.strip():
                    cleaned_content = f"Flow from {source_component_id} to {target_component_id}"

                if not description.strip():
                    description = f"Flow connecting {source_component_id} to {target_component_id}"

                # Generate enhanced description for flow
                enhanced_description = self.embedding_generator.generate_description(
                    f"Flow Type: {flow_type}\nSource: {source_component_id}\nTarget: {target_component_id}\nDescription: {description}\nContent: {cleaned_content[:300]}",
                    "flow"
                )

                data = {
                    'package_id': package_id,
                    'source_component_id': source_component_id,
                    'target_component_id': target_component_id,
                    'flow_type': flow_type,
                    'file_type': file_type,
                    'content': cleaned_content,
                    'connections': [source_component_id, target_component_id],
                    'flow_embedding': self.embedding_generator.generate_embedding(cleaned_content, 1536),
                    'description': enhanced_description,
                    'description_embedding': self.embedding_generator.generate_embedding(enhanced_description, 1536)
                }
                self.supabase_client.insert_flow(data)
            except Exception as e:
                logger.error(f"Error processing flow: {e}")
                continue

    def process_assets(self, chunks: List[Dict[str, Any]], package_id: str):
        """Process asset chunks."""
        asset_chunks = [chunk for chunk in chunks if self.classify_chunk_type(chunk) == 'asset']
        logger.info(f"Processing {len(asset_chunks)} assets")

        for chunk in asset_chunks:
            try:
                content = chunk.get('content', '')
                description = chunk.get('description', '')

                # Generate enhanced description for asset
                enhanced_description = self.embedding_generator.generate_description(
                    f"File: {chunk.get('file_name', '')}\nType: {chunk.get('file_type', '')}\nDescription: {description}\nContent: {content[:500]}",
                    "asset"
                )

                data = {
                    'package_id': package_id,
                    'file_name': chunk.get('file_name', ''),
                    'file_type': chunk.get('file_type', ''),
                    'content': content,
                    'description': enhanced_description,
                    'content_embedding': self.embedding_generator.generate_embedding(content, 1536),
                    'description_embedding': self.embedding_generator.generate_embedding(enhanced_description, 1536)
                }
                self.supabase_client.insert_asset(data)
            except Exception as e:
                logger.error(f"Error processing asset: {e}")
                continue

    def process_zip_package(self, zip_file_path: str, original_filename: str = None) -> Dict[str, Any]:
        """Main processing pipeline for ZIP package."""
        temp_dir = None
        try:
            # Use original filename if provided, otherwise use the zip_file_path
            display_name = original_filename if original_filename else zip_file_path
            logger.info(f"Starting processing of ZIP package: {display_name}")

            # Step 1: Extract ZIP
            temp_dir = self.extract_zip(zip_file_path)

            # Step 2: Chunk package
            chunker = EnhancedIFlowChunker(temp_dir)
            result = chunker.process_complete_iflow_package()
            chunks = result['chunks']

            logger.info(f"Generated {len(chunks)} chunks from package")

            # NEW: Save chunks to JSON file for inspection before Supabase processing
            self._save_chunks_to_json(chunks, display_name)

            # Step 3: Ensure package exists in database
            # Use original filename for package naming if provided
            filename_for_naming = original_filename if original_filename else zip_file_path
            package_id = self.ensure_package(chunks, temp_dir, filename_for_naming)
            if not package_id:
                raise Exception("Failed to create/find package in database")

            # Step 4: Process all chunk types (no cleanup needed - each package gets new UUID)
            self.process_components(chunks, package_id)
            self.process_flows(chunks, package_id)
            self.process_assets(chunks, package_id)

            logger.info(f"Successfully processed package with ID: {package_id}")

            return {
                'status': 'success',
                'package_id': package_id,
                'total_chunks': len(chunks),
                'coverage_report': result['coverage_report'],
                'message': f'Successfully processed {len(chunks)} chunks'
            }

        except Exception as e:
            logger.error(f"Error processing ZIP package: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to process package: {str(e)}'
            }
        finally:
            # Step 6: Cleanup
            if temp_dir:
                self.cleanup_temp_dir(temp_dir)


# Flask API Routes

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Foundry."""
    return jsonify({
        'status': 'healthy',
        'service': 'iFlow Package Processor API',
        'version': '1.0.0'
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Lightweight health check endpoint for Cloud Foundry."""
    # Ultra-fast response for health checks - no database or external calls
    return jsonify({
        'status': 'healthy',
        'service': 'iFlow Package Processor API',
        'version': '1.0.0',
        'timestamp': time.time()
    }), 200

@app.route('/health/detailed', methods=['GET'])
def health_detailed():
    """Detailed health check endpoint."""
    try:
        # Basic health check without database connection test
        return jsonify({
            'status': 'healthy',
            'service': 'iFlow Package Processor API',
            'version': '1.0.0',
            'openai': 'configured' if OPENAI_API_KEY else 'not configured',
            'supabase': 'configured' if SUPABASE_URL and SUPABASE_KEY else 'not configured'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/process-iflow', methods=['POST'])
def process_iflow():
    """Process iFlow ZIP package endpoint for n8n integration."""
    try:
        # Check if file is present in form data or as raw binary data
        file = None
        filename = None

        if 'file' in request.files:
            # Standard multipart form data
            file = request.files['file']
            filename = file.filename

            # Check if file is selected
            if filename == '':
                return jsonify({
                    'status': 'error',
                    'error': 'No file selected',
                    'message': 'Please select a file to upload'
                }), 400

        elif request.data:
            # Raw binary data (from n8n sendBinaryData)
            file = request.data
            filename = request.headers.get('X-Filename', 'uploaded_file.zip')
            logger.info(f"Received raw binary data, size: {len(file)} bytes")

        else:
            return jsonify({
                'status': 'error',
                'error': 'No file provided',
                'message': 'Please provide a file in the "file" field or as binary data'
            }), 400

        # Check file extension
        if not filename.lower().endswith('.zip'):
            return jsonify({
                'status': 'error',
                'error': 'Invalid file type',
                'message': 'Only ZIP files are allowed'
            }), 400

        # Secure the filename
        filename = secure_filename(filename)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            if hasattr(file, 'save'):
                # File object from form data
                file.save(temp_file.name)
            else:
                # Raw binary data
                temp_file.write(file)
                temp_file.flush()
            temp_file_path = temp_file.name

        try:
            # Generate unique tracking ID
            tracking_id = str(uuid.uuid4())

            # Initialize processing status
            processing_status[tracking_id] = {
                'status': 'processing',
                'message': f'Processing iFlow package: {filename}',
                'started_at': time.time(),
                'filename': filename
            }

            logger.info(f"Processing uploaded file: {filename} (Tracking ID: {tracking_id})")

            # Return success immediately - processing happens in background
            response_data = {
                'status': 'success',
                'message': 'iFlow package processing started successfully',
                'tracking_id': tracking_id,
                'filename': filename,
                'processing_status': 'started',
                'note': 'Processing is happening in the background. This may take 5-10 minutes.'
            }

            # Start background processing (simplified for immediate response)
            try:
                start_time = time.time()
                processor = IFlowPackageProcessor()
                result = processor.process_zip_package(temp_file_path, filename)
                processing_time = time.time() - start_time

                logger.info(f"Processing completed for {filename} in {processing_time:.2f} seconds: {result['status']}")

                # Update response with actual results
                response_data.update({
                    'processing_status': 'completed',
                    'processing_time': processing_time,
                    'total_flows': result.get('total_flows', 0),
                    'total_components': result.get('total_components', 0),
                    'total_assets': result.get('total_assets', 0),
                    'package_id': result.get('package_id', '')
                })

            except Exception as e:
                logger.error(f"Background processing failed: {str(e)}")
                response_data.update({
                    'processing_status': 'failed',
                    'error': str(e)
                })

            return jsonify(response_data), 200

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

    except Exception as e:
        logger.error(f"Unexpected error in process_iflow: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/status/<package_id>', methods=['GET'])
def get_package_status(package_id):
    """Get processing status for a package (supports long-running operations)."""
    try:
        # First check in-memory processing status for ongoing operations
        if package_id in processing_status:
            status_info = processing_status[package_id]
            current_time = time.time()

            # Calculate elapsed time
            if 'started_at' in status_info:
                elapsed_time = current_time - status_info['started_at']
                status_info['elapsed_time'] = elapsed_time

                # Estimate remaining time (rough estimate based on 20-25 min average)
                if status_info['status'] == 'processing':
                    avg_processing_time = 22 * 60  # 22 minutes average
                    progress_percentage = min((elapsed_time / avg_processing_time) * 100, 95)
                    estimated_remaining = max(0, avg_processing_time - elapsed_time)

                    status_info['progress_percentage'] = progress_percentage
                    status_info['estimated_remaining_seconds'] = estimated_remaining

            return jsonify({
                'status': 'success',
                'package_id': package_id,
                **status_info
            }), 200

        # If not in processing status, check database for completed packages
        supabase_client = SupabaseClient()

        # Query package status from database
        response = supabase_client.client.table('iflow_packages')\
            .select('id, package_name, created_at')\
            .eq('id', package_id)\
            .execute()

        if not response.data:
            return jsonify({
                'status': 'error',
                'error': 'Package not found',
                'package_id': package_id,
                'message': 'Package not found in processing queue or database'
            }), 404

        package_info = response.data[0]

        # Get component count
        components_response = supabase_client.client.table('iflow_components')\
            .select('id', count='exact')\
            .eq('package_id', package_id)\
            .execute()

        component_count = components_response.count or 0

        return jsonify({
            'status': 'completed',
            'package_id': package_id,
            'package_name': package_info['package_name'],
            'created_at': package_info['created_at'],
            'component_count': component_count,
            'message': 'Package processing completed and stored in database'
        }), 200

    except Exception as e:
        logger.error(f"Error getting package status: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'status': 'error',
        'error': 'File too large',
        'message': 'File size exceeds 100MB limit'
    }), 413

def main():
    """Main function for local development and testing."""
    if len(sys.argv) > 1:
        # Command-line usage for local testing
        zip_file_path = sys.argv[1]

        if not os.path.exists(zip_file_path):
            print(f"Error: ZIP file not found: {zip_file_path}")
            sys.exit(1)

        if not zip_file_path.endswith('.zip'):
            print("Error: File must be a ZIP file")
            sys.exit(1)

        try:
            processor = IFlowPackageProcessor()
            result = processor.process_zip_package(zip_file_path)

            print("\n" + "="*50)
            print("PROCESSING RESULT")
            print("="*50)
            print(json.dumps(result, indent=2))

            if result['status'] == 'success':
                print(f"\n✅ Successfully processed package!")
                print(f"📦 Package ID: {result['package_id']}")
                print(f"📊 Total chunks: {result['total_chunks']}")
            else:
                print(f"\n❌ Processing failed: {result['error']}")
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Start Flask app for local development
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
