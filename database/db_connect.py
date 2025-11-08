
"""
Database Connection Script for Supabase PostgreSQL
This script connects to a Supabase database using SQLAlchemy with proper SSL support.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd

# Module-level cached engine
_engine = None

def create_db_connection():
    """Create and return a cached database connection engine with proper SSL support for Supabase.
    
    The engine is created once on first call and reused for all subsequent calls.
    This is more efficient than creating a new engine each time.
    """
    global _engine
    
    # Return cached engine if it already exists
    if _engine is not None:
        return _engine
    
    # Load environment variables
    load_dotenv()
    
    # Get database credentials from environment variables
    db_user = os.getenv("db_user")
    db_password = os.getenv("db_password")
    db_host = os.getenv("db_host")
    db_port = os.getenv("db_port")
    db_name = os.getenv("db_name")
    
    # Validate that all required environment variables are set
    required_vars = [db_user, db_password, db_host, db_port, db_name]
    if None in required_vars:
        missing_vars = [var for var, value in zip(
            ["db_user", "db_password", "db_host", "db_port", "db_name"], 
            required_vars
        ) if value is None]
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    
    # Build connection string
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Create engine with SSL support (required for Supabase)
    _engine = create_engine(
        connection_string,
        connect_args={"sslmode": "require"},  # Required for Supabase
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300     # Recycle connections every 5 minutes
    )

    return _engine



if __name__ == "__main__":
    # Create database connection
    engine = create_db_connection()
    
    if engine is None:
        print("\nCannot proceed without database connection.")
        print("Please fix the connection issues and try again.")
        exit(1)
    
    # Example: Query security_master tables
    print("\nTesting database queries...")
    
    # Get available tables
    tables_query = """
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name;
    """
    
    tables = pd.read_sql(tables_query, engine)
    if tables is not None:
        print("Available tables:")
        print(tables)
    