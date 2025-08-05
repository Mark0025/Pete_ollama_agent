"""
Virtual Jamie.V1 Property Management Agent - Database Extractor
==============================================================

This module extracts communication logs from prod-db and creates a local SQLite 
database for training Virtual Jamie.V1, our property management agent.

Target Query: Communication logs for CompanyId=1, UserId=6, phone calls >15 seconds
Output: pete.db in /Users/markcarpenter/Desktop/pete/ollama_agent
"""

from sqlalchemy import create_engine
from loguru import logger
import os
from dotenv import load_dotenv
import pandas as pd
import sqlite3
from datetime import datetime

# Set up loguru logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
logger.add(os.path.join(log_dir, "virtual_jamie_extraction.log"), rotation="5 MB", retention="10 days", level="INFO")

class VirtualJamieDataExtractor:
    def __init__(self):
        """Initialize the data extractor for Virtual Jamie.V1"""
        self.load_environment()
        self.setup_prod_connection()
        # Output database in ollama_agent directory
        self.target_db_path = os.path.join(os.path.dirname(__file__), "pete.db")
        
    def load_environment(self):
        """Load environment variables from local .env file"""
        # Load .env from ollama_agent directory
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        # Get prod-db connection details using new environment variable names
        self.db_user = os.getenv("PROD_DB_USERNAME")
        self.db_pass = os.getenv("PROD_DB_PASSWORD")
        self.db_host = os.getenv("PROD_DB_HOST") 
        self.db_name = os.getenv("PROD_DB_DATABASE")
        self.db_driver = os.getenv("PROD_DB_DRIVER", "ODBC Driver 18 for SQL Server")
        
        logger.info("Environment variables loaded for Virtual Jamie.V1 data extraction")
        logger.info(f"Target database: {self.db_host}/{self.db_name}")
        
    def setup_prod_connection(self):
        """Setup connection to prod-db"""
        if all([self.db_user, self.db_pass, self.db_host, self.db_name]):
            self.prod_db_url = (
                f"mssql+pyodbc://{self.db_user}:{self.db_pass}@{self.db_host}:1433/{self.db_name}"
                f"?driver={self.db_driver.replace(' ', '+')}"
            )
            logger.info(f"Connecting to prod-db for Virtual Jamie.V1: {self.db_host}/{self.db_name}")
        else:
            missing = [k for k, v in {
                'PROD_DB_USERNAME': self.db_user,
                'PROD_DB_PASSWORD': self.db_pass, 
                'PROD_DB_HOST': self.db_host,
                'PROD_DB_DATABASE': self.db_name
            }.items() if not v]
            raise ValueError(f"Missing required database connection parameters: {missing}")
            
        self.prod_engine = create_engine(self.prod_db_url, echo=False, future=True)
        
    def get_virtual_jamie_training_query(self):
        """
        Return the specific query for Virtual Jamie.V1 training data
        
        This query gets communication logs for:
        - CompanyId = 1 
        - UserId = 6 (receiver or sender)
        - Excludes phone number +14052752322
        - CommunicationType = 3 (phone calls)
        - Duration > 15 seconds
        - Has transcription data
        """
        return """
        SELECT 
            cl.Incoming, 
            cl.[Data], 
            cl.CreationDate, 
            cl.Transcription, 
            cl.TranscriptionJson
        FROM CommunicationLogs cl
        WHERE cl.CompanyId = 1
            AND (cl.ReceiverUserId = 6 OR cl.SenderUserId = 6)
            AND cl.Receiver <> '+14052752322'
            AND cl.Sender <> '+14052752322'
            AND cl.CommunicationType = 3
            AND cl.[Data] IS NOT NULL
            AND cl.Duration > 15
        ORDER BY cl.Id DESC
        """
        
    def extract_training_data(self):
        """Extract training data from prod-db"""
        logger.info("🚀 Starting Virtual Jamie.V1 training data extraction from prod-db")
        
        query = self.get_virtual_jamie_training_query()
        
        try:
            # Execute query and get results as DataFrame
            df = pd.read_sql(query, self.prod_engine)
            logger.info(f"✅ Extracted {len(df)} communication records for Virtual Jamie.V1")
            
            # Log some stats about the data
            if not df.empty:
                date_range = f"from {df['CreationDate'].min()} to {df['CreationDate'].max()}"
                logger.info(f"📅 Data range: {date_range}")
                incoming_count = df['Incoming'].sum() if 'Incoming' in df.columns else 0
                logger.info(f"📞 Incoming calls: {incoming_count}")
                logger.info(f"📞 Outgoing calls: {len(df) - incoming_count}")
                
                # Check for transcription data
                has_transcription = df['Transcription'].notna().sum() if 'Transcription' in df.columns else 0
                logger.info(f"🎤 Records with transcription: {has_transcription}")
                
            return df
            
        except (pd.errors.DatabaseError, pd.errors.ParserError, ConnectionError) as e:
            logger.error(f"❌ Error extracting training data: {e}")
            raise
            
    def create_local_database(self, df):
        """Create local SQLite database for Virtual Jamie.V1"""
        logger.info(f"🗄️ Creating Virtual Jamie.V1 database at: {self.target_db_path}")
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(self.target_db_path), exist_ok=True)
        
        try:
            # Create SQLite connection and save data
            with sqlite3.connect(self.target_db_path) as conn:
                # Save communication logs
                df.to_sql('communication_logs', conn, if_exists='replace', index=False)
                
                # Create metadata table
                metadata = pd.DataFrame([{
                    'extraction_date': datetime.now().isoformat(),
                    'source_database': f"{self.db_host}/{self.db_name}",
                    'source_query': self.get_virtual_jamie_training_query().strip(),
                    'total_records': len(df),
                    'purpose': 'Virtual Jamie.V1 Property Management Agent Training Data',
                    'query_criteria': 'CompanyId=1, UserId=6, CommunicationType=3, Duration>15s',
                    'agent_version': 'Virtual Jamie.V1',
                    'training_focus': 'Property Management Communications'
                }])
                metadata.to_sql('extraction_metadata', conn, if_exists='replace', index=False)
                
                # Create training summary table
                if not df.empty:
                    summary = pd.DataFrame([{
                        'total_conversations': len(df),
                        'incoming_calls': df['Incoming'].sum() if 'Incoming' in df.columns else 0,
                        'outgoing_calls': len(df) - (df['Incoming'].sum() if 'Incoming' in df.columns else 0),
                        'with_transcription': df['Transcription'].notna().sum() if 'Transcription' in df.columns else 0,
                        'date_range_start': df['CreationDate'].min() if 'CreationDate' in df.columns else None,
                        'date_range_end': df['CreationDate'].max() if 'CreationDate' in df.columns else None,
                    }])
                    summary.to_sql('training_summary', conn, if_exists='replace', index=False)
                
                logger.info(f"✅ Successfully created pete.db with {len(df)} records for Virtual Jamie.V1")
                
        except (sqlite3.Error, pd.errors.DatabaseError, OSError) as e:
            logger.error(f"❌ Error creating local database: {e}")
            raise
            
    def verify_local_database(self):
        """Verify the created database"""
        try:
            with sqlite3.connect(self.target_db_path) as conn:
                # Check tables
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
                logger.info(f"📋 Created tables: {tables['name'].tolist()}")
                
                # Check record count
                count = pd.read_sql("SELECT COUNT(*) as count FROM communication_logs", conn)
                logger.info(f"📊 Total communication records: {count['count'].iloc[0]}")
                
                # Show sample of data
                sample = pd.read_sql("SELECT * FROM communication_logs LIMIT 3", conn)
                logger.info("👀 Sample data preview:")
                for idx, row in sample.iterrows():
                    creation_date = row.get('CreationDate', 'Unknown date')
                    incoming = row.get('Incoming', 'Unknown direction')
                    logger.info(f"  📝 Record {idx+1}: {creation_date} - Incoming: {incoming}")
                    
                # Show metadata
                metadata = pd.read_sql("SELECT * FROM extraction_metadata", conn)
                if not metadata.empty:
                    logger.info("🏷️ Extraction metadata:")
                    logger.info(f"  📅 Extracted: {metadata['extraction_date'].iloc[0]}")
                    logger.info(f"  🎯 Purpose: {metadata['purpose'].iloc[0]}")
                    
        except (sqlite3.Error, pd.errors.DatabaseError, OSError) as e:
            logger.error(f"❌ Error verifying database: {e}")
            
    def run_full_extraction(self):
        """Run the complete data extraction process for Virtual Jamie.V1"""
        logger.info("=" * 80)
        logger.info("🤖 STARTING VIRTUAL JAMIE.V1 DATA EXTRACTION FOR OLLAMA AGENT")
        logger.info("=" * 80)
        
        try:
            # Extract data from prod-db
            df = self.extract_training_data()
            
            if df.empty:
                logger.warning("⚠️ No data found matching criteria. Check query parameters.")
                logger.info("Query criteria:")
                logger.info("  - CompanyId = 1")
                logger.info("  - UserId = 6 (receiver or sender)")
                logger.info("  - CommunicationType = 3 (phone calls)")
                logger.info("  - Duration > 15 seconds")
                logger.info("  - Has transcription data")
                return False
                
            # Create local database
            self.create_local_database(df)
            
            # Verify creation
            self.verify_local_database()
            
            logger.info("=" * 80)
            logger.info("🎉 VIRTUAL JAMIE.V1 DATA EXTRACTION COMPLETED SUCCESSFULLY")
            logger.info(f"📁 Database created at: {self.target_db_path}")
            logger.info("🤖 Ready for Ollama property management agent training!")
            logger.info("=" * 80)
            
            return True
            
        except (sqlite3.Error, pd.errors.DatabaseError, ConnectionError, OSError, ValueError) as e:
            logger.error(f"❌ Data extraction failed: {e}")
            return False


def main():
    """Main execution function"""
    print("🤖 Virtual Jamie.V1 - Ollama Property Management Agent Data Extractor")
    print("=" * 80)
    
    extractor = VirtualJamieDataExtractor()
    success = extractor.run_full_extraction()
    
    if success:
        print("✅ Virtual Jamie.V1 training database created successfully!")
        print(f"📁 Location: {extractor.target_db_path}")
        print("🤖 Ready for Ollama property management agent training!")
        print("🏠 Virtual Jamie.V1 can now learn from real property management conversations!")
    else:
        print("❌ Data extraction failed. Check logs for details.")
        print("📋 Log location: ollama_agent/logs/virtual_jamie_extraction.log")


if __name__ == "__main__":
    main()