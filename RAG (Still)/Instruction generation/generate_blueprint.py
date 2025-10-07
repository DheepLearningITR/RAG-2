#!/usr/bin/env python3
"""
Simple Blueprint Generator Script
Generate JSON blueprints from natural language queries
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from enhanced_kg_blueprint_generator import EnhancedKGBlueprintGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_single_blueprint(query: str, output_file: str = None):
    """Generate a single JSON blueprint from a query"""

    print("🚀 RAG Prime Knowledge Graph Blueprint Generator")
    print("=" * 50)
    print(f"📝 Query: {query}")
    print("-" * 50)

    try:
        # Initialize the generator
        print("⚙️  Initializing Enhanced Knowledge Graph Blueprint Generator...")
        generator = EnhancedKGBlueprintGenerator()

        # Generate blueprint
        print("🔍 Analyzing query and retrieving components...")
        blueprint = generator.generate_perfect_blueprint(query)

        # Create Output json directory if it doesn't exist
        output_dir = Path(current_dir) / "Output json"
        output_dir.mkdir(exist_ok=True)

        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"blueprint_{timestamp}.json"

        # Save to Output json folder
        output_path = output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)
        
        print("✅ Blueprint generated successfully!")
        print(f"📁 Saved to: {output_path.absolute()}")
        
        # Print summary
        print_blueprint_summary(blueprint)
        
        return blueprint
        
    except Exception as e:
        logger.error(f"Error generating blueprint: {e}")
        print(f"❌ Error: {e}")
        return None

def print_blueprint_summary(blueprint: dict):
    """Print a summary of the generated blueprint"""
    print("\n📊 Blueprint Summary:")
    print("-" * 30)
    
    # Package info
    package_info = blueprint.get('package_info', {})
    print(f"📋 Package Name: {package_info.get('package_name', 'Unknown')}")
    print(f"🔄 Integration Type: {package_info.get('integration_type', 'Unknown')}")
    print(f"🏢 Source Systems: {', '.join(package_info.get('source_systems', []))}")
    print(f"🎯 Target Systems: {', '.join(package_info.get('target_systems', []))}")
    print(f"📦 Data Types: {', '.join(package_info.get('data_types', []))}")
    
    # Metadata
    metadata = blueprint.get('generation_metadata', {})
    print(f"📊 Components: {metadata.get('total_components', 0)}")
    print(f"📁 Assets: {metadata.get('total_assets', 0)}")
    print(f"⏱️  Processing Time: {metadata.get('processing_time_seconds', 0):.2f}s")
    print(f"🎯 Query Confidence: {metadata.get('query_confidence', 0):.2f}")
    print(f"🧠 KG Optimization Score: {metadata.get('kg_optimization_score', 0):.2f}")
    print(f"🔧 Generator Version: {metadata.get('generator_version', 'Unknown')}")
    print(f"🧠 Intelligence Level: {metadata.get('intelligence_level', 'Unknown')}")
    
    # KG Integration info
    kg_integration = blueprint.get('kg_integration', {})
    if kg_integration.get('enabled', False):
        print(f"🔗 Knowledge Graph: Enabled")
        print(f"📈 KG Optimization: {kg_integration.get('optimization_score', 0):.2f}")
    else:
        print(f"🔗 Knowledge Graph: Disabled")

def interactive_mode():
    """Run in interactive mode for multiple queries"""
    print("🚀 RAG Prime Knowledge Graph Blueprint Generator - Interactive Mode")
    print("=" * 60)
    print("Enter your integration requirements and get JSON blueprints!")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("=" * 60)
    
    try:
        # Initialize generator once
        generator = EnhancedKGBlueprintGenerator()
        query_count = 0

        # Create Output json directory if it doesn't exist
        output_dir = Path(current_dir) / "Output json"
        output_dir.mkdir(exist_ok=True)

        while True:
            print(f"\n📝 Query #{query_count + 1}")
            query = input("Enter your integration requirement: ").strip()

            if query.lower() in ['quit', 'exit', 'q', '']:
                break

            try:
                # Generate blueprint
                blueprint = generator.generate_perfect_blueprint(query)

                # Save with timestamp and query number to Output json folder
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"blueprint_{query_count + 1}_{timestamp}.json"
                output_path = output_dir / filename

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(blueprint, f, indent=2, ensure_ascii=False)

                print(f"✅ Blueprint saved to: {output_path}")
                print_blueprint_summary(blueprint)
                
                query_count += 1
                
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}")
        print(f"❌ Error: {e}")
    
    print(f"\n📊 Session Summary: {query_count} blueprints generated")
    print("👋 Goodbye!")

def main():
    """Main function with command line argument handling"""
    
    # Example queries for quick testing
    example_queries = [
        "Create a sync integration to transfer employee data from SAP S/4HANA to SuccessFactors with validation and error handling",
        "Set up a daily batch process to upload order files via SFTP, validate them, and send to database with transformation",
        "Build an event-driven integration that triggers notifications when invoice status changes, with conditional routing",
        "Create an API gateway that routes customer requests to different backend systems based on customer type",
        "Simple integration to map and transform product data between two systems"
    ]
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            interactive_mode()
        elif sys.argv[1] == "--examples" or sys.argv[1] == "-e":
            print("🧪 Running example queries...")
            for i, query in enumerate(example_queries, 1):
                print(f"\n{'='*60}")
                print(f"Example {i}/5")
                print('='*60)
                output_file = f"example_{i}_blueprint.json"
                generate_single_blueprint(query, output_file)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("RAG Prime Blueprint Generator")
            print("Usage:")
            print("  python generate_blueprint.py                    # Interactive mode")
            print("  python generate_blueprint.py -i                 # Interactive mode")
            print("  python generate_blueprint.py -e                 # Run examples")
            print("  python generate_blueprint.py -h                 # Show help")
            print("  python generate_blueprint.py \"your query\"       # Single query")
        else:
            # Single query mode
            query = " ".join(sys.argv[1:])
            generate_single_blueprint(query)
    else:
        # Default to interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
