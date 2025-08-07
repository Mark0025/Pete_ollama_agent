"""
Advanced benchmark analytics using Pandas, Pendulum, and Loguru
"""

import json
import pandas as pd
import pendulum
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from .benchmark_models import (
    BenchmarkRecord, 
    BenchmarkSummary, 
    ModelComparison,
    PerformanceMetrics,
    QualityMetrics
)


class BenchmarkAnalyzer:
    """Advanced analytics for benchmark data"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configure loguru for analytics logging
        logger.add(
            self.logs_dir / "analytics.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO"
        )
    
    def load_benchmark_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Load benchmark data into pandas DataFrame"""
        logger.info("Loading benchmark data for analysis")
        
        if date is None:
            # Try to find the most recent benchmark file
            benchmark_files = list(self.logs_dir.glob("benchmark_*.jsonl"))
            if benchmark_files:
                # Sort by modification time and get the most recent
                most_recent = max(benchmark_files, key=lambda x: x.stat().st_mtime)
                date = most_recent.stem.replace("benchmark_", "")
                logger.info(f"Loading most recent benchmark data from {date}")
            else:
                date = pendulum.now().format("YYYY-MM-DD")
        
        log_file = self.logs_dir / f"benchmark_{date}.jsonl"
        
        if not log_file.exists():
            logger.warning(f"No benchmark data found for {date}")
            return pd.DataFrame()
        
        records = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    # Validate with Pydantic
                    record = BenchmarkRecord(**data)
                    records.append(record.dict())
                except Exception as e:
                    logger.warning(f"Skipping invalid record on line {line_num}: {e}")
                    continue
        
        if not records:
            logger.warning(f"No valid benchmark records found for {date}")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Convert timestamp to proper datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Flatten nested structures for easier analysis
        df = self._flatten_dataframe(df)
        
        logger.info(f"Loaded {len(df)} benchmark records for {date}")
        return df
    
    def load_all_benchmark_data(self) -> pd.DataFrame:
        """Load all available benchmark data from all files"""
        logger.info("Loading all benchmark data for analysis")
        
        all_records = []
        benchmark_files = list(self.logs_dir.glob("benchmark_*.jsonl"))
        
        if not benchmark_files:
            logger.warning("No benchmark files found")
            return pd.DataFrame()
        
        for log_file in sorted(benchmark_files):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line.strip())
                            # Validate with Pydantic
                            record = BenchmarkRecord(**data)
                            all_records.append(record.dict())
                        except Exception as e:
                            logger.warning(f"Skipping invalid record in {log_file.name} line {line_num}: {e}")
                            continue
            except Exception as e:
                logger.error(f"Error reading {log_file.name}: {e}")
                continue
        
        if not all_records:
            logger.warning("No valid benchmark records found in any files")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        
        # Convert timestamp to proper datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Flatten nested structures for easier analysis
        df = self._flatten_dataframe(df)
        
        logger.info(f"Loaded {len(df)} total benchmark records from {len(benchmark_files)} files")
        return df
    
    def load_benchmark_data_for_range(self, days: int = 7) -> pd.DataFrame:
        """Load benchmark data for the last N days"""
        logger.info(f"Loading benchmark data for last {days} days")
        
        all_records = []
        end_date = pendulum.now()
        start_date = end_date.subtract(days=days)
        
        # Generate list of dates to check
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.format("YYYY-MM-DD")
            log_file = self.logs_dir / f"benchmark_{date_str}.jsonl"
            
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            try:
                                data = json.loads(line.strip())
                                # Validate with Pydantic
                                record = BenchmarkRecord(**data)
                                all_records.append(record.dict())
                            except Exception as e:
                                logger.warning(f"Skipping invalid record in {log_file.name} line {line_num}: {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error reading {log_file.name}: {e}")
            
            current_date = current_date.add(days=1)
        
        if not all_records:
            logger.warning(f"No valid benchmark records found for last {days} days")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        
        # Convert timestamp to proper datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date range
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        # Flatten nested structures for easier analysis
        df = self._flatten_dataframe(df)
        
        logger.info(f"Loaded {len(df)} benchmark records for last {days} days")
        return df
    
    def _flatten_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flatten nested performance and quality metrics"""
        if df.empty:
            return df
        
        # Flatten performance metrics
        perf_df = pd.json_normalize(df['performance'])
        perf_df.columns = [f"perf_{col}" for col in perf_df.columns]
        
        # Flatten quality metrics
        quality_df = pd.json_normalize(df['quality_metrics'])
        quality_df.columns = [f"quality_{col}" for col in quality_df.columns]
        
        # Combine with main dataframe
        result_df = pd.concat([
            df.drop(['performance', 'quality_metrics'], axis=1),
            perf_df,
            quality_df
        ], axis=1)
        
        return result_df
    
    def generate_summary(self, df: pd.DataFrame) -> BenchmarkSummary:
        """Generate comprehensive summary statistics"""
        logger.info("Generating benchmark summary")
        
        if df.empty:
            return BenchmarkSummary(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                median_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                avg_quality_score=0,
                success_rate=0,
                fast_responses_count=0,
                quality_responses_count=0,
                models_tested=[],
                time_range={"start": "", "end": ""}
            )
        
        successful_df = df[df['status'] == 'success']
        
        # Calculate time-based metrics
        response_times = successful_df['perf_total_duration_ms']
        
        # Calculate quality metrics
        quality_scores = successful_df['quality_estimated_quality_score']
        
        # Fast responses (< 3 seconds)
        fast_responses = successful_df[successful_df['perf_total_duration_ms'] < 3000]
        
        # Quality responses (> 7/10)
        quality_responses = successful_df[successful_df['quality_estimated_quality_score'] > 7.0]
        
        return BenchmarkSummary(
            total_requests=len(df),
            successful_requests=len(successful_df),
            failed_requests=len(df[df['status'] != 'success']),
            avg_response_time_ms=float(response_times.mean()) if len(response_times) > 0 else 0,
            median_response_time_ms=float(response_times.median()) if len(response_times) > 0 else 0,
            min_response_time_ms=int(response_times.min()) if len(response_times) > 0 else 0,
            max_response_time_ms=int(response_times.max()) if len(response_times) > 0 else 0,
            avg_quality_score=float(quality_scores.mean()) if len(quality_scores) > 0 else 0,
            success_rate=(len(successful_df) / len(df)) * 100,
            fast_responses_count=len(fast_responses),
            quality_responses_count=len(quality_responses),
            models_tested=df['model'].unique().tolist(),
            time_range={
                "start": df['timestamp'].min().isoformat() if len(df) > 0 else "",
                "end": df['timestamp'].max().isoformat() if len(df) > 0 else ""
            }
        )
    
    def compare_models(self, df: pd.DataFrame) -> List[ModelComparison]:
        """Compare performance across different models"""
        logger.info("Generating model comparison analysis")
        
        if df.empty:
            return []
        
        comparisons = []
        successful_df = df[df['status'] == 'success']
        
        for model in df['model'].unique():
            model_df = successful_df[successful_df['model'] == model]
            
            if len(model_df) == 0:
                continue
            
            # Get base model if available
            base_model = "unknown"
            if 'perf_base_model' in model_df.columns:
                base_model = model_df['perf_base_model'].iloc[0] if not model_df['perf_base_model'].empty else "unknown"
            
            # Calculate metrics - use actual_duration_seconds for more accurate timing
            timing_column = 'perf_actual_duration_seconds' if 'perf_actual_duration_seconds' in model_df.columns else 'perf_total_duration_ms'
            if timing_column == 'perf_actual_duration_seconds':
                avg_response_time = float(model_df[timing_column].mean() * 1000)  # Convert to ms
            else:
                avg_response_time = float(model_df[timing_column].mean())
            
            avg_quality = float(model_df['quality_estimated_quality_score'].mean())
            success_rate = (len(model_df) / len(df[df['model'] == model])) * 100
            fast_responses = len(model_df[model_df[timing_column] < (3.0 if timing_column.endswith('seconds') else 3000)])
            fast_rate = (fast_responses / len(model_df)) * 100 if len(model_df) > 0 else 0
            
            # Check if model is preloaded (affects performance)
            preload_rate = 0.0
            if 'perf_model_preloaded' in model_df.columns:
                preload_rate = (model_df['perf_model_preloaded'].sum() / len(model_df)) * 100
            
            # Generate recommendation
            recommendation = self._generate_recommendation(avg_response_time, avg_quality, success_rate, fast_rate)
            
            comparison = ModelComparison(
                model_name=model,
                request_count=len(model_df),
                avg_response_time_ms=avg_response_time,
                avg_quality_score=avg_quality,
                success_rate=success_rate,
                fast_response_rate=fast_rate,
                recommendation=recommendation,
                base_model=base_model,
                preload_rate=preload_rate
            )
            
            comparisons.append(comparison)
        
        # Sort by performance grade
        comparisons.sort(key=lambda x: x.performance_grade)
        
        return comparisons
    
    def _generate_recommendation(self, avg_time: float, avg_quality: float, success_rate: float, fast_rate: float) -> str:
        """Generate recommendation based on metrics"""
        if avg_time < 2000 and avg_quality > 8 and success_rate > 95:
            return "🏆 Excellent - Recommended for production"
        elif avg_time < 3000 and avg_quality > 7 and success_rate > 90:
            return "✅ Good - Suitable for most use cases"
        elif avg_time < 5000 and avg_quality > 6 and success_rate > 80:
            return "⚠️ Fair - Needs optimization"
        else:
            return "❌ Poor - Requires significant improvement"
    
    def get_time_series_data(self, df: pd.DataFrame, interval: str = "1H") -> pd.DataFrame:
        """Generate time-series analysis data"""
        logger.info(f"Generating time-series data with {interval} intervals")
        
        if df.empty:
            return pd.DataFrame()
        
        # Set timestamp as index
        df_time = df.set_index('timestamp')
        
        # Resample by time interval
        time_series = df_time.groupby('model').resample(interval).agg({
            'perf_total_duration_ms': ['mean', 'count'],
            'quality_estimated_quality_score': 'mean',
            'status': lambda x: (x == 'success').sum()
        }).reset_index()
        
        return time_series
    
    def export_analysis_report(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Dict:
        """Export comprehensive analysis report"""
        logger.info("Exporting comprehensive analysis report")
        
        if output_path is None:
            output_path = self.logs_dir / f"analysis_report_{pendulum.now().format('YYYY-MM-DD_HH-mm-ss')}.json"
        
        summary = self.generate_summary(df)
        model_comparisons = self.compare_models(df)
        
        report = {
            "generated_at": pendulum.now().isoformat(),
            "summary": summary.dict(),
            "model_comparisons": [comp.dict() for comp in model_comparisons],
            "detailed_stats": {
                "response_time_percentiles": self._calculate_percentiles(df, 'perf_total_duration_ms'),
                "quality_score_distribution": self._calculate_distribution(df, 'quality_estimated_quality_score'),
                "hourly_request_volume": self._calculate_hourly_volume(df)
            }
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Analysis report exported to {output_path}")
        return report
    
    def _calculate_percentiles(self, df: pd.DataFrame, column: str) -> Dict:
        """Calculate percentile distribution"""
        if df.empty or column not in df.columns:
            return {}
        
        data = df[column].dropna()
        return {
            "p50": float(data.quantile(0.5)),
            "p75": float(data.quantile(0.75)),
            "p90": float(data.quantile(0.9)),
            "p95": float(data.quantile(0.95)),
            "p99": float(data.quantile(0.99))
        }
    
    def _calculate_distribution(self, df: pd.DataFrame, column: str) -> Dict:
        """Calculate value distribution"""
        if df.empty or column not in df.columns:
            return {}
        
        data = df[column].dropna()
        return {
            "min": float(data.min()),
            "max": float(data.max()),
            "mean": float(data.mean()),
            "std": float(data.std()),
            "count": int(len(data))
        }
    
    def _calculate_hourly_volume(self, df: pd.DataFrame) -> Dict:
        """Calculate hourly request volume"""
        if df.empty:
            return {}
        
        hourly = df.set_index('timestamp').resample('1H').size()
        return {
            "peak_hour": hourly.idxmax().isoformat() if len(hourly) > 0 else "",
            "peak_volume": int(hourly.max()) if len(hourly) > 0 else 0,
            "avg_hourly": float(hourly.mean()) if len(hourly) > 0 else 0
        }