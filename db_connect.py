


"""
Database Connection Script for Supabase PostgreSQL
This script connects to a Supabase database using SQLAlchemy with proper SSL support.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd

def create_db_connection():
    """Create and return a database connection engine with proper SSL support for Supabase."""
    
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
    
    print(f"Connecting to: {db_host}:{db_port}/{db_name}")
    print(f"User: {db_user}")
    print(f"Database: {db_name}")
    
    # Test network connectivity first
    import socket
    try:
        print(f"Testing network connectivity to {db_host}...")
        socket.create_connection((db_host, int(db_port)), timeout=10)
        print("Network connectivity: OK")
    except Exception as e:
        print(f"Network connectivity failed: {e}")
        print("Possible issues:")
        print("1. Supabase project might be paused")
        print("2. Incorrect hostname in .env file")
        print("3. Network firewall blocking connection")
        print("4. Supabase project might be deleted")
        return None
    
    try:
        # Build connection string
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create engine with SSL support (required for Supabase)
        engine = create_engine(
            connection_string,
            connect_args={"sslmode": "require"},  # Required for Supabase
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=300     # Recycle connections every 5 minutes
        )
        
        # Test the connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW();"))
            current_time = result.fetchone()[0]
            print("Connection successful!")
            print(f"Current Time: {current_time}")
        
        return engine
        
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if your Supabase project is active (not paused)")
        print("2. Verify the hostname in your .env file")
        print("3. Check if your database password is correct")
        print("4. Ensure your IP is whitelisted in Supabase (if using IP restrictions)")
        print("5. Try connecting from Supabase dashboard to verify credentials")
        return None

def execute_query(engine, sql_query):
    """Execute a SQL query and return results as DataFrame."""
    try:
        return pd.read_sql(sql_query, engine)
    except Exception as e:
        print(f"Query failed: {e}")
        return None

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
    
    tables = execute_query(engine, tables_query)
    if tables is not None:
        print("Available tables:")
        print(tables)
    