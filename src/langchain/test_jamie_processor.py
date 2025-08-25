#!/usr/bin/env python3
"""
Test Script for LangGraph Jamie Conversation Processor
=====================================================

This script provides a simple test harness for the LangGraph-based Jamie
conversation processor. It loads sample conversations from the database
and runs them through the processor to validate functionality.

Usage:
    python test_jamie_processor.py [--limit=20] [--export=True]

Options:
    --limit      Number of conversations to process (default: 20)
    --export     Whether to export test cases to JSON (default: True)
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the processor
from langchain.langgraph_jamie_processor import LangGraphJamieProcessor
from utils.logger import logger


async def run_processor_test(limit: int = 20, export: bool = True) -> Dict[str, Any]:
    """Run a test of the LangGraph Jamie processor"""
    logger.info("=" * 80)
    logger.info(f"Starting Jamie Processor Test - {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    # Initialize the processor
    processor = LangGraphJamieProcessor()
    
    # Process a batch of conversations
    logger.info(f"Processing {limit} conversations...")
    results = await processor.process_batch_conversations(limit=limit)
    
    if "error" in results:
        logger.error(f"Processing failed: {results['error']}")
        return {"success": False, "error": results["error"]}
    
    # Display processing results
    logger.info("\n" + "=" * 40)
    logger.info("Processing Results:")
    logger.info(f"  Conversations processed: {results['conversations_processed']}")
    logger.info(f"  Test cases generated: {results['total_test_cases_generated']}")
    logger.info(f"  Jamie responses extracted: {results['total_jamie_responses_extracted']}")
    logger.info(f"  Average quality score: {results['average_quality_score']:.3f}")
    
    # Export test cases if requested
    if export and results['total_test_cases_generated'] > 0:
        logger.info("\nExporting test cases...")
        output_path = f"jamie_test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_success = processor.export_test_cases(output_path)
        
        if export_success:
            logger.info(f"Test cases exported successfully to {output_path}")
        else:
            logger.error("Failed to export test cases")
    
    # Sample test cases for display
    if results['total_test_cases_generated'] > 0:
        logger.info("\nSample Test Cases:")
        
        # Find a conversation with test cases
        sample_conversation = None
        for conv in processor.processed_conversations:
            if len(conv['test_cases']) > 0:
                sample_conversation = conv
                break
        
        if sample_conversation:
            # Display sample test cases (up to 3)
            for i, test_case in enumerate(sample_conversation['test_cases'][:3]):
                logger.info(f"\nTest Case #{i+1}:")
                logger.info(f"  Category: {test_case.issue_category}")
                logger.info(f"  Input: {test_case.input_scenario}")
                logger.info(f"  Expected Response: {test_case.expected_response}")
                logger.info(f"  Quality: {sum(test_case.quality_metrics.values()) / len(test_case.quality_metrics):.2f}")
    
    logger.info("\n" + "=" * 40)
    logger.info("Test completed successfully")
    return {"success": True, "results": results}


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the LangGraph Jamie conversation processor")
    parser.add_argument("--limit", type=int, default=20, help="Number of conversations to process")
    parser.add_argument("--export", type=bool, default=True, help="Whether to export test cases")
    return parser.parse_args()


async def main():
    """Main function"""
    args = parse_args()
    await run_processor_test(limit=args.limit, export=args.export)


if __name__ == "__main__":
    asyncio.run(main())
