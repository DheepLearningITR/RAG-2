#!/usr/bin/env python3
"""
Blueprint to Package Generator
Converts JSON blueprints from Instruction generation to complete SAP CPI packages
"""

import json
import os
import re
import sys
import zipfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

class BlueprintToPackageGenerator:
    def __init__(self):
        print("🚀 Blueprint to Package Generator initialized!")
        
        # Paths
        self.instruction_gen_path = Path(__file__).parent.parent / "Instruction generation"
        self.output_json_path = self.instruction_gen_path / "Output json"
        self.sample_blueprint_path = self.instruction_gen_path / "sample_perfect_blueprint.json"
        
        print(f"📁 Instruction generation path: {self.instruction_gen_path}")
        print(f"📁 Output JSON path: {self.output_json_path}")
    
    def list_available_blueprints(self) -> List[Path]:
        """List all available JSON blueprint files"""
        blueprints = []
        
        # Check Output json directory
        if self.output_json_path.exists():
            for file_path in self.output_json_path.glob("*.json"):
                blueprints.append(file_path)
        
        # Check for sample blueprint
        if self.sample_blueprint_path.exists():
            blueprints.append(self.sample_blueprint_path)
        
        return sorted(blueprints)
    
    def load_blueprint(self, blueprint_path: Path) -> Dict[str, Any]:
        """Load and validate JSON blueprint"""
        print(f"📋 Loading blueprint: {blueprint_path.name}")
        
        try:
            with open(blueprint_path, 'r', encoding='utf-8') as f:
                blueprint = json.load(f)
            
            # Validate blueprint structure
            required_sections = ['package_info', 'iflow_definition', 'package_assets']
            for section in required_sections:
                if section not in blueprint:
                    raise ValueError(f"Missing required section: {section}")
            
            print(f"✅ Blueprint loaded successfully")
            print(f"   📦 Package: {blueprint['package_info'].get('package_name', 'Unknown')}")
            print(f"   🔄 Type: {blueprint['package_info'].get('integration_type', 'Unknown')}")
            print(f"   🤖 Components: {len(blueprint['iflow_definition']['bpmn_structure'].get('activities', []))}")
            
            return blueprint
            
        except Exception as e:
            print(f"❌ Error loading blueprint: {e}")
            raise
    
    def create_sap_cpi_package(self, blueprint: Dict[str, Any], output_dir: str = "package generation/output") -> str:
        """Create complete SAP CPI package from blueprint"""
        package_info = blueprint['package_info']
        iflow_name = package_info.get('package_name', 'generated_iflow')
        
        print(f"🏗️ Creating SAP CPI package: {iflow_name}")
        
        # Create output directory
        output_path = Path(output_dir)
        iflow_dir = output_path / iflow_name
        iflow_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package structure
        self._create_package_structure(iflow_dir, iflow_name, package_info)
        
        # Generate BPMN XML
        bpmn_xml = self._generate_bpmn_xml(blueprint, iflow_name)
        
        # Write BPMN file
        iflow_file = iflow_dir / "src" / "main" / "resources" / "scenarioflows" / "integrationflow" / f"{iflow_name}.iflw"
        with open(iflow_file, "w", encoding="utf-8") as f:
            f.write(bpmn_xml)
        
        # Create asset files
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
    
    def _create_package_structure(self, iflow_dir: Path, iflow_name: str, package_info: Dict[str, Any]):
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
 y,org.apache.cxf.service.model,org.apache.cxf.transport,org.apache.cxf.tran
 sport.common.gzip,org.apache.cxf.transport.http,org.apache.cxf.transport.
 http.policy,org.apache.cxf.workqueue,org.apache.cxf.ws.rm.persist
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
        description = package_info.get('description', f'SAP Integration Flow: {iflow_name}')
        metainfo_content = f"""#Store metainfo properties
#{datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")}
description={description}
"""
        
        with open(iflow_dir / "metainfo.prop", "w", encoding="utf-8") as f:
            f.write(metainfo_content)
        
        # Create parameters.prop
        parameters_content = f"""#{datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")}
# Integration Flow Parameters
# Generated from blueprint: {package_info.get('package_id', 'unknown')}
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
        """Generate BPMN XML from blueprint"""
        print("📝 Generating BPMN XML from blueprint...")
        
        iflow_def = blueprint['iflow_definition']
        bpmn_structure = iflow_def['bpmn_structure']
        
        # Generate process elements
        process_elements = self._generate_process_elements(bpmn_structure)
        
        # Generate diagram elements
        diagram_elements = self._generate_diagram_elements(bpmn_structure)
        
        # Complete BPMN XML
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
    
    def _generate_process_elements(self, bpmn_structure: Dict[str, Any]) -> str:
        """Generate BPMN process elements from blueprint structure"""
        elements = []
        flows = []
        
        # Create a simple, valid flow structure: Start -> Service Task -> End
        # Start event
        start_element = '''        <bpmn2:startEvent id="StartEvent_1" name="Start">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::MessageStartEvent/version::1.0</value></ifl:property>
                <ifl:property><key>adapterType</key><value>HTTPS</value></ifl:property>
                <ifl:property><key>address</key><value>/api/v1/process</value></ifl:property>
                <ifl:property><key>httpMethod</key><value>POST</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:outgoing>SequenceFlow_1</bpmn2:outgoing>
            <bpmn2:messageEventDefinition/>
        </bpmn2:startEvent>'''
        elements.append(start_element)
        
        # Add a simple service task
        service_task = '''        <bpmn2:serviceTask id="ServiceTask_1" name="Process Data">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::Script/version::1.0</value></ifl:property>
                <ifl:property><key>script</key><value>// Process the incoming data\nreturn message;</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>SequenceFlow_1</bpmn2:incoming>
            <bpmn2:outgoing>SequenceFlow_2</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        elements.append(service_task)
        
        # End event
        end_element = '''        <bpmn2:endEvent id="EndEvent_1" name="End">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::MessageEndEvent/version::1.0</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>SequenceFlow_2</bpmn2:incoming>
            <bpmn2:messageEventDefinition/>
        </bpmn2:endEvent>'''
        elements.append(end_element)
        
        # Add sequence flows
        flows.append('        <bpmn2:sequenceFlow id="SequenceFlow_1" sourceRef="StartEvent_1" targetRef="ServiceTask_1"/>')
        flows.append('        <bpmn2:sequenceFlow id="SequenceFlow_2" sourceRef="ServiceTask_1" targetRef="EndEvent_1"/>')
        
        return '\n'.join(elements + flows)
    
    def _generate_component_bpmn_element(self, comp_id: str, comp_name: str, comp_type: str, 
                                       properties: Dict[str, Any], bpmn_xml: str, 
                                       incoming: str, outgoing: str) -> str:
        """Generate BPMN element for a component"""
        
        # Clean component name for XML
        comp_name = comp_name.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        
        if comp_type == "script":
            return f'''        <bpmn2:scriptTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>activityType</key><value>Script</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::GroovyScript/version::1.1.1</value></ifl:property>
                <ifl:property><key>scriptFile</key><value>{comp_id}.groovy</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:scriptTask>'''
        
        elif comp_type in ["contentmodifier", "enricher"]:
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>activityType</key><value>ContentModifier</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::ContentModifier/version::1.1.2</value></ifl:property>
                <ifl:property><key>properties</key><value>processed=true,timestamp=now(),component_id={comp_id}</value></ifl:property>
                <ifl:property><key>headers</key><value>Content-Type=application/json,X-Process-ID={{uuid}}</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type in ["requestreply", "externalcall"]:
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>activityType</key><value>Request-Reply</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::RequestReply/version::1.0.4</value></ifl:property>
                <ifl:property><key>endpointPath</key><value>/api/process</value></ifl:property>
                <ifl:property><key>method</key><value>POST</value></ifl:property>
                <ifl:property><key>url</key><value>{{API_BASE_URL}}/api/process</value></ifl:property>
                <ifl:property><key>headers</key><value>Content-Type=application/json</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        elif comp_type in ["messagemapping", "mapping"]:
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>activityType</key><value>Mapping</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::MessageMapping/version::1.3.0</value></ifl:property>
                <ifl:property><key>mappingFile</key><value>src/main/resources/mapping/{comp_id}.mmap</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
        
        else:
            # Default service task
            return f'''        <bpmn2:serviceTask id="{comp_id}" name="{comp_name}">
            <bpmn2:extensionElements>
                <ifl:property><key>componentVersion</key><value>1.0</value></ifl:property>
                <ifl:property><key>activityType</key><value>Service</value></ifl:property>
                <ifl:property><key>cmdVariantUri</key><value>ctype::FlowstepVariant/cname::ServiceTask/version::1.0</value></ifl:property>
            </bpmn2:extensionElements>
            <bpmn2:incoming>{incoming}</bpmn2:incoming>
            <bpmn2:outgoing>{outgoing}</bpmn2:outgoing>
        </bpmn2:serviceTask>'''
    
    def _generate_diagram_elements(self, bpmn_structure: Dict[str, Any]) -> str:
        """Generate BPMN diagram elements"""
        elements = []
        
        # Simple diagram for Start -> Service Task -> End
        # Start event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="StartEvent_1" id="BPMNShape_StartEvent_1">')
        elements.append('                <dc:Bounds height="32.0" width="32.0" x="292.0" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Service task shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="ServiceTask_1" id="BPMNShape_ServiceTask_1">')
        elements.append('                <dc:Bounds height="56.0" width="100.0" x="400.0" y="130.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # End event shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="EndEvent_1" id="BPMNShape_EndEvent_1">')
        elements.append('                <dc:Bounds height="32.0" width="32.0" x="550.0" y="142.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Participant shape
        elements.append('            <bpmndi:BPMNShape bpmnElement="Participant_Process_1" id="BPMNShape_Participant_Process_1">')
        elements.append('                <dc:Bounds height="220.0" width="350.0" x="250.0" y="60.0"/>')
        elements.append('            </bpmndi:BPMNShape>')
        
        # Sequence flow edges
        # Start to Service Task
        elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_1" id="BPMNEdge_SequenceFlow_1" sourceElement="BPMNShape_StartEvent_1" targetElement="BPMNShape_ServiceTask_1">')
        elements.append('                <di:waypoint x="324.0" xsi:type="dc:Point" y="158.0"/>')
        elements.append('                <di:waypoint x="400.0" xsi:type="dc:Point" y="158.0"/>')
        elements.append('            </bpmndi:BPMNEdge>')
        
        # Service Task to End
        elements.append('            <bpmndi:BPMNEdge bpmnElement="SequenceFlow_2" id="BPMNEdge_SequenceFlow_2" sourceElement="BPMNShape_ServiceTask_1" targetElement="BPMNShape_EndEvent_1">')
        elements.append('                <di:waypoint x="500.0" xsi:type="dc:Point" y="158.0"/>')
        elements.append('                <di:waypoint x="550.0" xsi:type="dc:Point" y="158.0"/>')
        elements.append('            </bpmndi:BPMNEdge>')
        
        diagram_xml = f'''    <bpmndi:BPMNDiagram id="BPMNDiagram_1" name="Default Collaboration Diagram">
        <bpmndi:BPMNPlane bpmnElement="Collaboration_1" id="BPMNPlane_1">
{chr(10).join(elements)}
        </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>'''
        
        return diagram_xml
    
    def _create_asset_files(self, iflow_dir: Path, blueprint: Dict[str, Any]):
        """Create script and mapping files from blueprint assets"""
        print("📝 Creating asset files from blueprint...")
        
        package_assets = blueprint.get('package_assets', {})
        bpmn_structure = blueprint['iflow_definition']['bpmn_structure']
        activities = bpmn_structure.get('activities', [])
        
        script_count = 0
        mapping_count = 0
        
        # Create scripts from activities
        for activity in activities:
            comp_type = activity.get('type', '').lower()
            comp_id = activity.get('id', '')
            comp_name = activity.get('name', '')
            
            if comp_type == "script":
                script_count += 1
                script_file = f"{comp_id}.groovy"
                script_content = self._generate_default_script(comp_name, comp_id)
                
                script_path = iflow_dir / "src" / "main" / "resources" / "script" / script_file
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                print(f"   ✅ Created script: {script_file}")
        
        # Create scripts from package assets
        groovy_scripts = package_assets.get('groovy_scripts', [])
        for script in groovy_scripts:
            script_count += 1
            script_file = script.get('file_name', f'Script_{script_count}.groovy')
            script_content = script.get('content', self._generate_default_script('Generated Script', f'Script_{script_count}'))
            
            script_path = iflow_dir / "src" / "main" / "resources" / "script" / script_file
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            print(f"   ✅ Created script: {script_file}")
        
        # Create mappings from activities
        for activity in activities:
            comp_type = activity.get('type', '').lower()
            comp_id = activity.get('id', '')
            comp_name = activity.get('name', '')
            
            if comp_type in ["messagemapping", "mapping"]:
                mapping_count += 1
                mapping_file = f"{comp_id}.mmap"
                mapping_content = self._generate_default_mapping(comp_name, comp_id)
                
                mapping_path = iflow_dir / "src" / "main" / "resources" / "mapping" / mapping_file
                with open(mapping_path, "w", encoding="utf-8") as f:
                    f.write(mapping_content)
                
                print(f"   ✅ Created mapping: {mapping_file}")
        
        # Create mappings from package assets
        message_mappings = package_assets.get('message_mappings', [])
        for mapping in message_mappings:
            mapping_count += 1
            mapping_file = mapping.get('file_name', f'Mapping_{mapping_count}.mmap')
            mapping_content = mapping.get('content', self._generate_default_mapping('Generated Mapping', f'Mapping_{mapping_count}'))
            
            mapping_path = iflow_dir / "src" / "main" / "resources" / "mapping" / mapping_file
            with open(mapping_path, "w", encoding="utf-8") as f:
                f.write(mapping_content)
            
            print(f"   ✅ Created mapping: {mapping_file}")
        
        print(f"📁 Created {script_count} script files and {mapping_count} mapping files")
    
    def _generate_default_script(self, comp_name: str, comp_id: str) -> str:
        """Generate default Groovy script content"""
        return f"""// {comp_name} - {comp_id}
// Generated from blueprint

import com.sap.gateway.ip.core.customdev.util.Message
import groovy.json.JsonSlurper
import groovy.json.JsonBuilder

def Message processData(Message message) {{
    try {{
        // Get input data
        def body = message.getBody(java.lang.String)
        log.info("Processing data in {comp_name}")
        
        // Parse JSON if present
        def inputData
        if (body && body.trim().startsWith('{{')) {{
            inputData = new JsonSlurper().parseText(body)
        }} else {{
            inputData = [data: body, processed: true]
        }}
        
        // Add processing metadata
        inputData.processedAt = new Date().format('yyyy-MM-dd HH:mm:ss')
        inputData.processedBy = '{comp_name}'
        inputData.componentId = '{comp_id}'
        inputData.status = 'PROCESSED'
        
        // Log processing
        log.info("Data processed successfully by {comp_name}")
        
        // Return processed data
        message.setBody(new JsonBuilder(inputData).toString())
        return message
        
    }} catch (Exception e) {{
        log.error("Error in {comp_name}: ${{e.message}}")
        throw new Exception("Processing failed in {comp_name}: ${{e.message}}")
    }}
}}"""
    
    def _generate_default_mapping(self, comp_name: str, comp_id: str) -> str:
        """Generate default mapping content"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<mapping>
    <description>{comp_name} - {comp_id}</description>
    <source>
        <messageType>JSON</messageType>
        <structure>InputMessage</structure>
    </source>
    <target>
        <messageType>JSON</messageType>
        <structure>OutputMessage</structure>
    </target>
    <mappingRules>
        <rule>
            <source>//data</source>
            <target>//output/data</target>
        </rule>
        <rule>
            <source>//processedAt</source>
            <target>//output/processedAt</target>
        </rule>
        <rule>
            <source>//status</source>
            <target>//output/status</target>
        </rule>
        <rule>
            <source>//componentId</source>
            <target>//output/componentId</target>
        </rule>
    </mappingRules>
</mapping>"""
    
    def process_blueprint(self, blueprint_path: Path, output_dir: str = "output") -> str:
        """Process a single blueprint file and create SAP CPI package"""
        print(f"🚀 Processing blueprint: {blueprint_path.name}")
        print("=" * 60)
        
        try:
            # Load blueprint
            blueprint = self.load_blueprint(blueprint_path)
            
            # Create SAP CPI package
            zip_path = self.create_sap_cpi_package(blueprint, output_dir)
            
            # Keep package in output directory
            if zip_path and os.path.exists(zip_path):
                print(f"📦 Package created: {zip_path}")
                return zip_path
            else:
                print(f"❌ Package creation failed")
                return None
            
        except Exception as e:
            print(f"❌ Error processing blueprint: {e}")
            raise
    
    def process_all_blueprints(self, output_dir: str = "output") -> List[str]:
        """Process all available blueprints"""
        print("🚀 Processing all available blueprints")
        print("=" * 60)
        
        blueprints = self.list_available_blueprints()
        if not blueprints:
            print("❌ No blueprint files found!")
            return []
        
        print(f"📋 Found {len(blueprints)} blueprint files:")
        for i, bp in enumerate(blueprints, 1):
            print(f"   {i}. {bp.name}")
        
        created_packages = []
        
        for blueprint_path in blueprints:
            try:
                package_path = self.process_blueprint(blueprint_path, output_dir)
                created_packages.append(package_path)
                print(f"✅ Successfully processed: {blueprint_path.name}")
            except Exception as e:
                print(f"❌ Failed to process {blueprint_path.name}: {e}")
        
        print("=" * 60)
        print(f"🎉 Processing complete! Created {len(created_packages)} packages")
        
        return created_packages

def main():
    """Main function for terminal usage"""
    print("🚀 Blueprint to Package Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = BlueprintToPackageGenerator()
    
    # List available blueprints
    blueprints = generator.list_available_blueprints()
    
    if not blueprints:
        print("❌ No blueprint files found!")
        print("📁 Please ensure you have JSON blueprint files in:")
        print(f"   - {generator.output_json_path}")
        print(f"   - {generator.sample_blueprint_path}")
        return
    
    print(f"📋 Found {len(blueprints)} blueprint files:")
    for i, bp in enumerate(blueprints, 1):
        print(f"   {i}. {bp.name}")
    
    # Get user choice
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1])
            if 1 <= choice <= len(blueprints):
                selected_blueprint = blueprints[choice - 1]
                generator.process_blueprint(selected_blueprint)
            else:
                print("❌ Invalid choice. Please select a number from the list.")
        except ValueError:
            print("❌ Please provide a valid number.")
    else:
        print("\n📦 Processing Options:")
        print("   1. Process specific blueprint")
        print("   2. Process all blueprints")
        
        while True:
            choice = input("Choose option (1/2, default: 1): ").strip()
            if choice in ['1', '2', '']:
                if choice == '2':
                    generator.process_all_blueprints()
                else:
                    # Process first blueprint by default
                    generator.process_blueprint(blueprints[0])
                break
            else:
                print("❌ Please enter 1 or 2")

if __name__ == "__main__":
    main()
