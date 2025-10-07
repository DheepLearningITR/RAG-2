#!/usr/bin/env python3
"""
Simple Launcher for Unified RAG Pipeline
Easy way to run the complete iFlow generation pipeline
"""

import sys
import os
from pathlib import Path

# Note: Emojis removed for Windows compatibility

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def main():
    """Simple launcher with user-friendly interface"""
    print("RAG Prime - Complete iFlow Generation Pipeline")
    print("=" * 60)
    print("This pipeline will:")
    print("1. Analyze your integration requirements")
    print("2. Use Knowledge Graph for optimal component selection")
    print("3. Generate JSON blueprint")
    print("4. Create SAP CPI package (zip file)")
    print("=" * 60)
    
    # Import and run the unified pipeline
    try:
        from unified_rag_pipeline import UnifiedRAGPipeline
        
        pipeline = UnifiedRAGPipeline()
        
        if len(sys.argv) > 1:
            # Command line mode
            if sys.argv[1] == "--help" or sys.argv[1] == "-h":
                print("\nUsage Options:")
                print("  python run_pipeline.py                    # Interactive mode")
                print("  python run_pipeline.py -i                 # Interactive mode")
                print("  python run_pipeline.py -e                 # Run examples")
                print("  python run_pipeline.py \"your query\"       # Single query")
                print("  python run_pipeline.py -h                 # Show this help")
            elif sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
                pipeline.interactive_mode()
            elif sys.argv[1] == "--examples" or sys.argv[1] == "-e":
                pipeline.run_examples()
            else:
                # Single query mode
                query = " ".join(sys.argv[1:])
                result = pipeline.process_query(query)
                pipeline._print_result_summary(result)
        else:
            # Default to interactive mode
            pipeline.interactive_mode()
            
    except ImportError as e:
        print(f"Error importing pipeline: {e}")
        print("Make sure all dependencies are installed and files are in place.")
    except Exception as e:
        print(f"Error running pipeline: {e}")

if __name__ == "__main__":
    main()
