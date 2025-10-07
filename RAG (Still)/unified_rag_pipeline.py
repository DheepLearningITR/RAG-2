#!/usr/bin/env python3
"""
Unified RAG Pipeline
Connects Instruction Generation and Package Generation for complete iFlow creation
"""

import sys
import os
import json
import logging
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Note: Emojis removed for Windows compatibility

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'Instruction generation'))
sys.path.append(os.path.join(current_dir, 'package generation'))

# Import from both modules
from enhanced_kg_blueprint_generator import EnhancedKGBlueprintGenerator
from blueprint_to_package_generator import BlueprintToPackageGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedRAGPipeline:
    """
    Unified pipeline that combines Instruction Generation and Package Generation
    """
    
    def __init__(self):
        """Initialize the unified pipeline"""
        logger.info("Initializing Unified RAG Pipeline")
        
        try:
            # Initialize both generators
            self.blueprint_generator = EnhancedKGBlueprintGenerator()
            self.package_generator = BlueprintToPackageGenerator()
            
            # Set up directories
            self.instruction_output_dir = Path(current_dir) / "Instruction generation" / "Output json"
            self.package_output_dir = Path(current_dir) / "package generation" / "output"
            
            # Ensure directories exist
            self.instruction_output_dir.mkdir(exist_ok=True)
            self.package_output_dir.mkdir(exist_ok=True)
            
            logger.info("Unified RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Unified RAG Pipeline: {e}")
            raise
    
    def process_query(self, user_query: str, generate_package: bool = True) -> Dict[str, Any]:
        """
        Process a user query through the complete pipeline
        
        Args:
            user_query: Natural language query describing integration requirements
            generate_package: Whether to generate the final zip package
            
        Returns:
            Dictionary containing blueprint and package information
        """
        logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            # Step 1: Generate JSON Blueprint
            logger.info("Step 1: Generating JSON Blueprint with Knowledge Graph")
            blueprint = self.blueprint_generator.generate_perfect_blueprint(user_query)
            
            # Step 2: Save Blueprint
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blueprint_filename = f"blueprint_{timestamp}.json"
            blueprint_path = self.instruction_output_dir / blueprint_filename
            
            with open(blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Blueprint saved to: {blueprint_path}")
            
            result = {
                'query': user_query,
                'blueprint': blueprint,
                'blueprint_path': str(blueprint_path),
                'blueprint_filename': blueprint_filename,
                'package_path': None,
                'package_filename': None,
                'success': True,
                'timestamp': timestamp
            }
            
            # Step 3: Generate Package (if requested)
            if generate_package:
                logger.info("Step 2: Generating SAP CPI Package")
                package_path = self._generate_package(blueprint_path, timestamp)
                
                if package_path:
                    result['package_path'] = str(package_path)
                    result['package_filename'] = package_path.name
                    logger.info(f"Package generated: {package_path}")
                else:
                    logger.warning("Package generation failed")
                    result['success'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'query': user_query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
            }
    
    def _generate_package(self, blueprint_path: Path, timestamp: str) -> Optional[Path]:
        """Generate SAP CPI package from blueprint"""
        try:
            # Generate package using the blueprint generator
            package_dir = self.package_generator.process_blueprint(
                blueprint_path, 
                str(self.package_output_dir)
            )
            
            if package_dir and os.path.exists(package_dir):
                # Create zip file
                package_name = f"iflow_package_{timestamp}"
                zip_path = self.package_output_dir / f"{package_name}.zip"
                
                # Create zip file
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(package_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, package_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"Package zipped: {zip_path}")
                return zip_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating package: {e}")
            return None
    
    def process_multiple_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Process multiple queries in batch"""
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Processing Query {i}/{len(queries)}")
            print('='*60)
            
            result = self.process_query(query)
            results.append(result)
            
            # Print summary
            self._print_result_summary(result, i)
        
        return results
    
    def _print_result_summary(self, result: Dict[str, Any], query_num: int = None):
        """Print a summary of the processing result"""
        if query_num:
            print(f"\n📊 Query {query_num} Summary:")
        else:
            print(f"\n📊 Processing Summary:")
        print("-" * 40)
        
        if result.get('success', False):
            print(f"✅ Status: Success")
            print(f"📝 Query: {result['query'][:80]}...")
            print(f"📄 Blueprint: {result.get('blueprint_filename', 'N/A')}")
            
            if result.get('package_filename'):
                print(f"📦 Package: {result['package_filename']}")
            
            # Blueprint metadata
            blueprint = result.get('blueprint', {})
            metadata = blueprint.get('generation_metadata', {})
            print(f"🧠 KG Optimization: {metadata.get('kg_optimization_score', 0):.2f}")
            print(f"📊 Components: {metadata.get('total_components', 0)}")
            print(f"📁 Assets: {metadata.get('total_assets', 0)}")
            
        else:
            print(f"❌ Status: Failed")
            print(f"📝 Query: {result['query'][:80]}...")
            print(f"🚨 Error: {result.get('error', 'Unknown error')}")
    
    def interactive_mode(self):
        """Run in interactive mode for multiple queries"""
        print("🚀 Unified RAG Pipeline - Interactive Mode")
        print("=" * 60)
        print("Enter your integration requirements and get complete iFlow packages!")
        print("Type 'quit', 'exit', or 'q' to stop.")
        print("=" * 60)
        
        query_count = 0
        
        try:
            while True:
                print(f"\n📝 Query #{query_count + 1}")
                query = input("Enter your integration requirement: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q', '']:
                    break
                
                # Ask if user wants package generation
                generate_package = True
                package_choice = input("Generate SAP CPI package? (y/n, default: y): ").strip().lower()
                if package_choice in ['n', 'no']:
                    generate_package = False
                
                try:
                    result = self.process_query(query, generate_package)
                    self._print_result_summary(result, query_count + 1)
                    query_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    print(f"❌ Error: {e}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"❌ Error: {e}")
        
        print(f"\n📊 Session Summary: {query_count} queries processed")
        print("👋 Goodbye!")
    
    def run_examples(self):
        """Run example queries to demonstrate the system"""
        example_queries = [
            "Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling",
            "Set up a daily batch process to upload order files via SFTP, validate them, and send to database with transformation",
            "Build an event-driven integration that triggers notifications when invoice status changes, with conditional routing",
            "Create an API gateway that routes customer requests to different backend systems based on customer type",
            "Simple integration to map and transform product data between two systems"
        ]
        
        print("🧪 Running Example Queries...")
        results = self.process_multiple_queries(example_queries)
        
        # Print final summary
        successful = sum(1 for r in results if r.get('success', False))
        print(f"\n📊 Final Summary:")
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"📦 Packages Generated: {sum(1 for r in results if r.get('package_filename'))}")
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up old generated files"""
        import time
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        # Clean blueprint files
        for file_path in self.instruction_output_dir.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                logger.info(f"Deleted old blueprint: {file_path.name}")
        
        # Clean package files
        for file_path in self.package_output_dir.glob("*.zip"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                logger.info(f"Deleted old package: {file_path.name}")

def main():
    """Main function with command line argument handling"""
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            pipeline = UnifiedRAGPipeline()
            pipeline.interactive_mode()
        elif sys.argv[1] == "--examples" or sys.argv[1] == "-e":
            pipeline = UnifiedRAGPipeline()
            pipeline.run_examples()
        elif sys.argv[1] == "--cleanup":
            pipeline = UnifiedRAGPipeline()
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            pipeline.cleanup_old_files(days)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Unified RAG Pipeline")
            print("Usage:")
            print("  python unified_rag_pipeline.py                    # Interactive mode")
            print("  python unified_rag_pipeline.py -i                 # Interactive mode")
            print("  python unified_rag_pipeline.py -e                 # Run examples")
            print("  python unified_rag_pipeline.py --cleanup [days]   # Clean old files")
            print("  python unified_rag_pipeline.py -h                 # Show help")
            print("  python unified_rag_pipeline.py \"your query\"       # Single query")
        else:
            # Single query mode
            query = " ".join(sys.argv[1:])
            pipeline = UnifiedRAGPipeline()
            result = pipeline.process_query(query)
            pipeline._print_result_summary(result)
    else:
        # Default to interactive mode
        pipeline = UnifiedRAGPipeline()
        pipeline.interactive_mode()

if __name__ == "__main__":
    main()
