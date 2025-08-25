#!/usr/bin/env python3
"""
Jamie Batch Processor CLI
========================

Command-line interface for large-scale Jamie conversation processing with
configurable parameters and monitoring capabilities.

Usage Examples:
    # Process 100 conversations with default settings
    python batch_processor_cli.py --limit 100

    # High-performance processing with custom configuration
    python batch_processor_cli.py --limit 500 --batch-size 100 --workers 8 --parallel

    # Resume interrupted processing
    python batch_processor_cli.py --limit 500 --resume

    # Conservative processing for debugging
    python batch_processor_cli.py --limit 50 --batch-size 10 --no-parallel --verbose
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.scaled_jamie_processor import (
    ScaledJamieProcessor, BatchProcessingConfig
)
from utils.logger import logger


def create_config_from_args(args) -> BatchProcessingConfig:
    """Create BatchProcessingConfig from command line arguments"""
    return BatchProcessingConfig(
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        max_workers=args.workers,
        enable_parallel=args.parallel,
        resume_from_checkpoint=args.resume,
        checkpoint_interval=args.checkpoint_interval,
        progress_update_interval=args.progress_interval,
        export_intermediate_results=args.export_intermediate,
        quality_threshold=args.quality_threshold
    )


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Large-scale Jamie conversation processing system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --limit 100                    # Process 100 conversations
  %(prog)s --limit 500 --workers 8        # High-performance processing
  %(prog)s --limit 200 --resume           # Resume interrupted processing
  %(prog)s --limit 50 --no-parallel       # Sequential processing for debugging
        """
    )
    
    # Main processing arguments
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='Number of conversations to process (default: 100)'
    )
    
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=50,
        help='Number of conversations per batch (default: 50)'
    )
    
    parser.add_argument(
        '--chunk-size', '-c',
        type=int,
        default=10,
        help='Number of conversations per parallel chunk (default: 10)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    # Processing mode arguments
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Enable parallel processing (default: True)'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_false',
        dest='parallel',
        help='Disable parallel processing'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from checkpoint if available (default: True)'
    )
    
    parser.add_argument(
        '--no-resume',
        action='store_false',
        dest='resume',
        help='Start fresh, ignore existing checkpoints'
    )
    
    # Progress and output arguments
    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=25,
        help='Save checkpoint every N batches (default: 25)'
    )
    
    parser.add_argument(
        '--progress-interval',
        type=int,
        default=5,
        help='Show progress every N batches (default: 5)'
    )
    
    parser.add_argument(
        '--export-intermediate',
        action='store_true',
        default=True,
        help='Export intermediate results during processing (default: True)'
    )
    
    parser.add_argument(
        '--no-export-intermediate',
        action='store_false',
        dest='export_intermediate',
        help='Disable intermediate result exports'
    )
    
    # Quality and filtering arguments
    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=0.5,
        help='Quality threshold for conversations (default: 0.5)'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for results (default: current directory)'
    )
    
    parser.add_argument(
        '--prefix',
        type=str,
        default='jamie_batch',
        help='Prefix for output files (default: jamie_batch)'
    )
    
    # Debug and monitoring
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show configuration and exit without processing'
    )
    
    return parser


async def run_batch_processing(config: BatchProcessingConfig, args) -> bool:
    """Run the batch processing with given configuration"""
    try:
        # Initialize processor
        logger.info("🚀 Initializing Scaled Jamie Processor")
        processor = ScaledJamieProcessor(config)
        
        # Setup checkpoint file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = f"{args.output_dir}/checkpoint_{args.prefix}_{timestamp}.json"
        
        # Run processing
        logger.info(f"🔥 Starting large-scale processing of {args.limit} conversations")
        results = await processor.process_large_batch(
            limit=args.limit,
            checkpoint_file=checkpoint_file
        )
        
        if "error" in results:
            logger.error(f"❌ Processing failed: {results['error']}")
            return False
        
        # Export final results
        output_file = f"{args.output_dir}/{args.prefix}_test_cases_{timestamp}.json"
        if processor.export_test_cases(output_file):
            logger.info(f"📄 Final test cases exported to: {output_file}")
        
        # Generate comprehensive report
        report_file = f"{args.output_dir}/{args.prefix}_report_{timestamp}.md"
        processor.generate_processing_report(results, report_file)
        
        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 BATCH PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Conversations processed: {results['conversations_processed']:,}")
        logger.info(f"🧪 Test cases generated: {results['total_test_cases_generated']:,}")
        logger.info(f"📝 Jamie responses extracted: {results['total_jamie_responses_extracted']:,}")
        logger.info(f"⚡ Processing rate: {results['processing_rate']:.2f} conv/sec")
        logger.info(f"✅ Success rate: {results['success_rate']:.1%}")
        logger.info(f"⏱️  Total time: {results['total_duration_seconds']/60:.1f} minutes")
        logger.info("=" * 60)
        logger.info(f"📄 Results: {output_file}")
        logger.info(f"📊 Report: {report_file}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Unexpected error during processing: {e}")
        return False


def print_configuration(config: BatchProcessingConfig, args):
    """Print the processing configuration"""
    print("\n" + "=" * 60)
    print("📋 BATCH PROCESSING CONFIGURATION")
    print("=" * 60)
    print(f"Target conversations:     {args.limit:,}")
    print(f"Batch size:              {config.batch_size}")
    print(f"Chunk size:              {config.chunk_size}")
    print(f"Max workers:             {config.max_workers}")
    print(f"Parallel processing:     {config.enable_parallel}")
    print(f"Resume from checkpoint:  {config.resume_from_checkpoint}")
    print(f"Quality threshold:       {config.quality_threshold}")
    print(f"Output directory:        {args.output_dir}")
    print(f"File prefix:             {args.prefix}")
    print("-" * 60)
    print(f"Checkpoint interval:     {config.checkpoint_interval} batches")
    print(f"Progress interval:       {config.progress_update_interval} batches")
    print(f"Export intermediate:     {config.export_intermediate_results}")
    print("=" * 60)
    
    # Estimate processing time
    estimated_batches = (args.limit + config.batch_size - 1) // config.batch_size
    estimated_time_minutes = estimated_batches * 0.5  # Rough estimate
    print(f"📈 Estimated batches:     {estimated_batches}")
    print(f"⏰ Estimated time:        {estimated_time_minutes:.1f} minutes")
    print("=" * 60)


async def main():
    """Main CLI function"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Create configuration from arguments
    config = create_config_from_args(args)
    
    # Validate arguments
    if args.limit <= 0:
        print("❌ Error: limit must be positive")
        sys.exit(1)
    
    if args.batch_size <= 0:
        print("❌ Error: batch-size must be positive")
        sys.exit(1)
    
    if args.workers <= 0:
        print("❌ Error: workers must be positive")
        sys.exit(1)
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Print configuration
    print_configuration(config, args)
    
    # Dry run mode
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Configuration shown above")
        print("Run without --dry-run to start processing")
        return
    
    # Confirm for large batches
    if args.limit > 200 and not args.resume:
        response = input(f"\n⚠️  You're about to process {args.limit} conversations. Continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Processing cancelled")
            return
    
    # Run the processing
    print("\n🚀 Starting batch processing...")
    success = await run_batch_processing(config, args)
    
    if success:
        print("\n✅ Batch processing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Batch processing failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
