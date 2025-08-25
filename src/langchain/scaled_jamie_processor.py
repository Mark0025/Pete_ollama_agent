#!/usr/bin/env python3
"""
Scaled Jamie Conversation Processor
==================================

Enhanced version of the LangGraph Jamie processor optimized for large-scale
batch processing with improved performance, progress tracking, and resource management.

Features:
- Batch processing with configurable chunk sizes
- Progress tracking and ETA calculations
- Memory-efficient processing with chunking
- Parallel processing capabilities
- Advanced error handling and recovery
- Performance metrics and optimization
- Resume functionality for interrupted processing
"""

import os
import sys
import json
import sqlite3
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports
from database.pete_db_manager import PeteDBManager
from utils.logger import logger
from langchain.langgraph_jamie_processor import (
    LangGraphJamieProcessor, ConversationSegment, TestCase
)


@dataclass 
class BatchProcessingConfig:
    """Configuration for batch processing"""
    batch_size: int = 50
    chunk_size: int = 10
    max_workers: int = 4
    enable_parallel: bool = True
    resume_from_checkpoint: bool = True
    checkpoint_interval: int = 25
    progress_update_interval: int = 10
    max_memory_mb: int = 512
    quality_threshold: float = 0.5
    export_intermediate_results: bool = True


@dataclass
class ProcessingStats:
    """Enhanced processing statistics"""
    start_time: datetime
    conversations_total: int = 0
    conversations_processed: int = 0
    conversations_skipped: int = 0
    test_cases_generated: int = 0
    jamie_responses_extracted: int = 0
    processing_errors: int = 0
    average_quality_score: float = 0.0
    processing_rate: float = 0.0  # conversations per second
    estimated_completion: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    
    def update_progress(self):
        """Update calculated fields"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed > 0:
            self.processing_rate = self.conversations_processed / elapsed
            
        remaining = self.conversations_total - self.conversations_processed
        if self.processing_rate > 0:
            eta_seconds = remaining / self.processing_rate
            self.estimated_completion = datetime.now() + timedelta(seconds=eta_seconds)


class ScaledJamieProcessor(LangGraphJamieProcessor):
    """
    Enhanced Jamie processor optimized for large-scale batch processing
    
    Extends the base processor with performance optimizations, batch processing,
    progress tracking, and parallel processing capabilities.
    """
    
    def __init__(self, config: Optional[BatchProcessingConfig] = None):
        super().__init__()
        self.config = config or BatchProcessingConfig()
        self.stats = ProcessingStats(start_time=datetime.now())
        self.checkpoint_data = {}
        self.processed_ids = set()
        
    def _load_checkpoint(self, checkpoint_file: str) -> bool:
        """Load processing checkpoint to resume interrupted processing"""
        try:
            if Path(checkpoint_file).exists():
                with open(checkpoint_file, 'r') as f:
                    self.checkpoint_data = json.load(f)
                    self.processed_ids = set(self.checkpoint_data.get('processed_ids', []))
                    logger.info(f"📂 Loaded checkpoint: {len(self.processed_ids)} conversations already processed")
                    return True
        except Exception as e:
            logger.error(f"❌ Error loading checkpoint: {e}")
        return False
    
    def _save_checkpoint(self, checkpoint_file: str, current_batch: int):
        """Save processing checkpoint"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'current_batch': current_batch,
                'processed_ids': list(self.processed_ids),
                'stats': asdict(self.stats),
                'config': asdict(self.config)
            }
            
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
                
            logger.info(f"💾 Saved checkpoint at batch {current_batch}")
        except Exception as e:
            logger.error(f"❌ Error saving checkpoint: {e}")
    
    def _get_conversation_batches(self, limit: int) -> List[List[Tuple]]:
        """Load conversations from database and organize into processing batches"""
        try:
            connection = sqlite3.connect(self.db_manager.db_path)
            
            # Enhanced query with more metadata
            query = """
            SELECT 
                rowid, CreationDate, Data, Transcription, Incoming,
                LENGTH(Transcription) as transcript_length
            FROM communication_logs 
            WHERE Transcription IS NOT NULL 
            AND LENGTH(Transcription) > 200
            AND Transcription LIKE '%jamie%'
            ORDER BY CreationDate DESC
            LIMIT ?
            """
            
            cursor = connection.cursor()
            cursor.execute(query, (limit,))
            conversations = cursor.fetchall()
            connection.close()
            
            # Filter out already processed conversations if resuming
            if self.config.resume_from_checkpoint and self.processed_ids:
                conversations = [
                    conv for conv in conversations 
                    if conv[0] not in self.processed_ids  # conv[0] is the rowid
                ]
                logger.info(f"📋 After filtering processed conversations: {len(conversations)} remaining")
            
            # Organize into batches
            batches = []
            for i in range(0, len(conversations), self.config.batch_size):
                batch = conversations[i:i + self.config.batch_size]
                batches.append(batch)
                
            return batches
            
        except Exception as e:
            logger.error(f"❌ Error loading conversation batches: {e}")
            return []
    
    def _process_conversation_chunk(self, conversations: List[Tuple]) -> List[Dict[str, Any]]:
        """Process a small chunk of conversations synchronously"""
        chunk_results = []
        
        for conv_data in conversations:
            try:
                conv_id, date, data, transcription, incoming, length = conv_data
                conversation_id = f"conv_{conv_id}_{date.replace(' ', '_').replace(':', '-')}"
                
                # Skip if already processed
                if conv_id in self.processed_ids:
                    continue
                
                # Process the conversation
                result = asyncio.run(self.process_conversation(
                    conversation_id=conversation_id,
                    raw_transcription=transcription,
                    metadata={
                        "date": date, 
                        "data": data, 
                        "id": conv_id,
                        "length": length,
                        "incoming": incoming
                    }
                ))
                
                chunk_results.append(result)
                self.processed_ids.add(conv_id)
                
                # Update stats (using the base class stats dict)
                self.stats.conversations_processed += 1
                if result.get("processing_errors"):
                    self.stats.processing_errors += 1
                self.stats.test_cases_generated += result.get("test_cases_generated", 0)
                self.stats.jamie_responses_extracted += result.get("jamie_responses_extracted", 0)
                
            except Exception as e:
                logger.error(f"❌ Error processing conversation {conv_id}: {e}")
                self.stats.processing_errors += 1
                
        return chunk_results
    
    def _process_batch_parallel(self, batch: List[Tuple]) -> List[Dict[str, Any]]:
        """Process a batch of conversations in parallel using thread pool"""
        if not self.config.enable_parallel or len(batch) < self.config.chunk_size:
            return self._process_conversation_chunk(batch)
        
        # Split batch into smaller chunks for parallel processing
        chunks = [
            batch[i:i + self.config.chunk_size] 
            for i in range(0, len(batch), self.config.chunk_size)
        ]
        
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit chunk processing tasks
            future_to_chunk = {
                executor.submit(self._process_conversation_chunk, chunk): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_results = future.result()
                    batch_results.extend(chunk_results)
                    logger.debug(f"✅ Completed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"❌ Error processing chunk {chunk_idx}: {e}")
        
        return batch_results
    
    def _update_progress(self, batch_idx: int, total_batches: int):
        """Update and display processing progress"""
        self.stats.update_progress()
        
        progress_pct = (batch_idx / total_batches) * 100
        
        logger.info(f"📊 Progress Update - Batch {batch_idx}/{total_batches} ({progress_pct:.1f}%)")
        logger.info(f"   Processed: {self.stats.conversations_processed}")
        logger.info(f"   Test Cases: {self.stats.test_cases_generated}")
        logger.info(f"   Jamie Responses: {self.stats.jamie_responses_extracted}")
        logger.info(f"   Processing Rate: {self.stats.processing_rate:.2f} conv/sec")
        
        if self.stats.estimated_completion:
            eta_str = self.stats.estimated_completion.strftime("%H:%M:%S")
            logger.info(f"   ETA: {eta_str}")
    
    def _export_intermediate_results(self, batch_idx: int):
        """Export intermediate results during processing"""
        if not self.config.export_intermediate_results:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jamie_test_cases_batch_{batch_idx}_{timestamp}.json"
            
            if self.export_test_cases(filename):
                logger.info(f"📄 Exported intermediate results: {filename}")
        except Exception as e:
            logger.error(f"❌ Error exporting intermediate results: {e}")
    
    async def process_large_batch(self, 
                                limit: int = 500, 
                                checkpoint_file: str = "processing_checkpoint.json") -> Dict[str, Any]:
        """
        Process a large batch of conversations with enhanced performance and tracking
        
        Args:
            limit: Maximum number of conversations to process
            checkpoint_file: File to save/load processing checkpoints
            
        Returns:
            Comprehensive processing results and statistics
        """
        logger.info("=" * 80)
        logger.info(f"🚀 Starting Large-Scale Jamie Processing - {datetime.now().isoformat()}")
        logger.info(f"   Target conversations: {limit}")
        logger.info(f"   Batch size: {self.config.batch_size}")
        logger.info(f"   Parallel processing: {self.config.enable_parallel}")
        logger.info(f"   Max workers: {self.config.max_workers}")
        logger.info("=" * 80)
        
        # Load checkpoint if resuming
        if self.config.resume_from_checkpoint:
            self._load_checkpoint(checkpoint_file)
        
        # Load conversation batches
        logger.info("📂 Loading conversations from database...")
        batches = self._get_conversation_batches(limit)
        
        if not batches:
            return {"error": "No conversations found to process"}
        
        self.stats.conversations_total = sum(len(batch) for batch in batches)
        logger.info(f"📋 Organized {self.stats.conversations_total} conversations into {len(batches)} batches")
        
        # Process batches
        all_results = []
        
        for batch_idx, batch in enumerate(batches, 1):
            batch_start_time = time.time()
            
            logger.info(f"\n🔄 Processing Batch {batch_idx}/{len(batches)} ({len(batch)} conversations)")
            
            # Process batch (parallel or sequential)
            batch_results = self._process_batch_parallel(batch)
            all_results.extend(batch_results)
            
            batch_duration = time.time() - batch_start_time
            logger.info(f"⏱️  Batch {batch_idx} completed in {batch_duration:.2f}s")
            
            # Update progress
            if batch_idx % self.config.progress_update_interval == 0 or batch_idx == len(batches):
                self._update_progress(batch_idx, len(batches))
            
            # Save checkpoint
            if batch_idx % self.config.checkpoint_interval == 0:
                self._save_checkpoint(checkpoint_file, batch_idx)
            
            # Export intermediate results
            if self.config.export_intermediate_results and batch_idx % (self.config.checkpoint_interval // 2) == 0:
                self._export_intermediate_results(batch_idx)
            
            # Basic memory management
            if batch_idx % (self.config.checkpoint_interval * 2) == 0:
                import gc
                gc.collect()
        
        # Final statistics calculation
        total_duration = (datetime.now() - self.stats.start_time).total_seconds()
        
        # Calculate quality statistics
        quality_scores = []
        for conv in self.processed_conversations:
            if conv.get("quality_score", 0) > 0:
                quality_scores.append(conv["quality_score"])
        
        if quality_scores:
            self.stats.average_quality_score = sum(quality_scores) / len(quality_scores)
        
        # Compile final results
        summary = {
            "processing_completed": True,
            "total_duration_seconds": total_duration,
            "conversations_processed": self.stats.conversations_processed,
            "conversations_total": self.stats.conversations_total,
            "processing_rate": self.stats.processing_rate,
            "total_test_cases_generated": self.stats.test_cases_generated,
            "total_jamie_responses_extracted": self.stats.jamie_responses_extracted,
            "average_quality_score": self.stats.average_quality_score,
            "processing_errors": self.stats.processing_errors,
            "success_rate": (self.stats.conversations_processed - self.stats.processing_errors) / max(1, self.stats.conversations_processed),
            "quality_conversations": len([c for c in self.processed_conversations if c.get("quality_score", 0) > self.config.quality_threshold]),
            "batches_processed": len(batches),
            "configuration": asdict(self.config),
            "detailed_stats": asdict(self.stats)
        }
        
        # Clean up checkpoint
        if Path(checkpoint_file).exists():
            try:
                os.remove(checkpoint_file)
                logger.info("🧹 Cleaned up checkpoint file")
            except:
                pass
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 Large-Scale Processing Complete!")
        logger.info(f"📊 Processed {summary['conversations_processed']} conversations")
        logger.info(f"🧪 Generated {summary['total_test_cases_generated']} test cases")
        logger.info(f"📝 Extracted {summary['total_jamie_responses_extracted']} Jamie responses")
        logger.info(f"⚡ Average processing rate: {summary['processing_rate']:.2f} conv/sec")
        logger.info(f"✅ Success rate: {summary['success_rate']:.1%}")
        logger.info("=" * 80)
        
        return summary
    
    def generate_processing_report(self, results: Dict[str, Any], output_path: str = None) -> str:
        """Generate a comprehensive processing report"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"processing_report_{timestamp}.md"
        
        # Category analysis
        category_stats = {}
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for conv in self.processed_conversations:
            for test_case in conv.get("test_cases", []):
                category = test_case.issue_category
                category_stats[category] = category_stats.get(category, 0) + 1
                
                # Quality distribution
                avg_quality = sum(test_case.quality_metrics.values()) / len(test_case.quality_metrics)
                if avg_quality > 0.8:
                    quality_distribution["high"] += 1
                elif avg_quality > 0.6:
                    quality_distribution["medium"] += 1
                else:
                    quality_distribution["low"] += 1
        
        report_content = f"""# Large-Scale Jamie Processing Report

## Executive Summary

**Processing Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Duration**: {results['total_duration_seconds']:.1f} seconds ({results['total_duration_seconds']/60:.1f} minutes)
**Processing Rate**: {results['processing_rate']:.2f} conversations per second
**Success Rate**: {results['success_rate']:.1%}

## Processing Results

| Metric | Value |
|--------|-------|
| Conversations Processed | {results['conversations_processed']:,} |
| Test Cases Generated | {results['total_test_cases_generated']:,} |
| Jamie Responses Extracted | {results['total_jamie_responses_extracted']:,} |
| Quality Conversations | {results['quality_conversations']:,} |
| Processing Errors | {results['processing_errors']:,} |
| Average Quality Score | {results['average_quality_score']:.3f} |

## Category Distribution

| Category | Count |
|----------|-------|
"""
        
        for category, count in sorted(category_stats.items()):
            report_content += f"| {category.title()} | {count} |\n"
        
        report_content += f"""

## Quality Distribution

- **High Quality** (>0.8): {quality_distribution['high']} test cases
- **Medium Quality** (0.6-0.8): {quality_distribution['medium']} test cases  
- **Low Quality** (<0.6): {quality_distribution['low']} test cases

## Configuration Used

- **Batch Size**: {results['configuration']['batch_size']}
- **Chunk Size**: {results['configuration']['chunk_size']}
- **Max Workers**: {results['configuration']['max_workers']}
- **Parallel Processing**: {results['configuration']['enable_parallel']}
- **Quality Threshold**: {results['configuration']['quality_threshold']}

## Performance Metrics

- **Batches Processed**: {results['batches_processed']}
- **Average Quality Score**: {results['average_quality_score']:.3f}
- **Processing Efficiency**: {(results['total_test_cases_generated'] / results['conversations_processed']):.2f} test cases per conversation

## Recommendations

Based on the processing results:

1. **Quality Optimization**: Consider adjusting quality thresholds if needed
2. **Category Enhancement**: Focus on improving category classification for better organization
3. **Scale Efficiency**: Processing rate of {results['processing_rate']:.2f} conv/sec is {'excellent' if results['processing_rate'] > 1 else 'good' if results['processing_rate'] > 0.5 else 'acceptable'}

Generated by Scaled Jamie Processor v2.0
"""
        
        # Save report
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"📊 Generated processing report: {output_path}")
        return output_path


async def main():
    """Main function for large-scale processing"""
    # Configuration for large-scale processing
    config = BatchProcessingConfig(
        batch_size=50,           # Process 50 conversations per batch
        chunk_size=10,           # 10 conversations per parallel chunk
        max_workers=4,           # Use 4 parallel workers
        enable_parallel=True,    # Enable parallel processing
        resume_from_checkpoint=True,  # Resume if interrupted
        checkpoint_interval=25,  # Save checkpoint every 25 batches
        progress_update_interval=5,   # Progress update every 5 batches
        export_intermediate_results=True,  # Export results during processing
        quality_threshold=0.5    # Quality threshold for filtering
    )
    
    logger.info("🚀 Initializing Scaled Jamie Processor")
    processor = ScaledJamieProcessor(config)
    
    # Process large batch (500 conversations)
    results = await processor.process_large_batch(limit=500)
    
    if "error" not in results:
        # Export final test cases
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_export = f"jamie_test_cases_large_batch_{timestamp}.json"
        
        if processor.export_test_cases(final_export):
            logger.info(f"📄 Exported final test cases: {final_export}")
        
        # Generate comprehensive report
        report_path = processor.generate_processing_report(results)
        
        logger.info("\n🎊 Large-scale processing completed successfully!")
        logger.info(f"📊 Report available at: {report_path}")
        
    else:
        logger.error(f"❌ Processing failed: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())
