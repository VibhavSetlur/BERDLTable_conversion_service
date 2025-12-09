"""
db_utils.py - SQLite Database Utilities for BERDLTable Conversion Service

Provides efficient functions for extracting table data from SQLite databases
and converting to 2D array format suitable for JSON serialization.

VERSION: 1.0.0
"""

import sqlite3
import logging
from typing import List, Tuple, Optional

# Configure module logger
logger = logging.getLogger(__name__)


def list_tables(db_path: str) -> List[str]:
    """
    List all user tables in a SQLite database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        List of table names (excludes system tables)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for user tables (exclude sqlite_ system tables)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Found {len(tables)} tables in database: {tables}")
        return tables
        
    except sqlite3.Error as e:
        logger.error(f"Error listing tables from {db_path}: {e}")
        raise


def get_table_columns(db_path: str, table_name: str) -> List[str]:
    """
    Get column names for a specific table.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to query
        
    Returns:
        List of column names
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use PRAGMA to get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        return columns
        
    except sqlite3.Error as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        raise


def get_table_data(
    db_path: str, 
    table_name: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Tuple[List[str], List[List[str]], float, float]:
    """
    Extract all data from a table as a 2D string array.
    
    Converts all values to strings for consistent JSON serialization.
    NULL values are converted to empty strings.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to query
        limit: (V2.0 placeholder) Maximum number of rows to return
        offset: (V2.0 placeholder) Number of rows to skip
        
    Returns:
        Tuple of (headers, data, db_query_ms, conversion_ms) where:
            - headers: List of column names
            - data: List of rows, each row is a list of string values
            - db_query_ms: Time spent querying SQLite
            - conversion_ms: Time spent converting to strings
    """
    import time
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get column names first
        headers = get_table_columns(db_path, table_name)
        
        if not headers:
            logger.warning(f"Table {table_name} has no columns or doesn't exist")
            return [], [], 0.0, 0.0
        
        # Build query - V1.0 returns all data
        # TODO V2.0: Add pagination with LIMIT/OFFSET
        query = f"SELECT * FROM {table_name}"
        
        # V2.0 placeholder: pagination support
        # if limit is not None:
        #     query += f" LIMIT {limit}"
        #     if offset is not None:
        #         query += f" OFFSET {offset}"
        
        # TIME: SQLite SELECT query
        query_start = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        db_query_ms = (time.time() - query_start) * 1000
        
        conn.close()
        
        # TIME: Python -> string conversion
        conversion_start = time.time()
        data = []
        for row in rows:
            string_row = [
                str(value) if value is not None else "" 
                for value in row
            ]
            data.append(string_row)
        conversion_ms = (time.time() - conversion_start) * 1000
        
        logger.info(
            f"Extracted {len(data)} rows from {table_name} "
            f"(query: {db_query_ms:.2f}ms, convert: {conversion_ms:.2f}ms)"
        )
        return headers, data, db_query_ms, conversion_ms
        
    except sqlite3.Error as e:
        logger.error(f"Error extracting data from {table_name}: {e}")
        raise


def get_table_row_count(db_path: str, table_name: str) -> int:
    """
    Get the total row count for a table.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table
        
    Returns:
        Number of rows in the table
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except sqlite3.Error as e:
        logger.error(f"Error counting rows in {table_name}: {e}")
        raise


def validate_table_exists(db_path: str, table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to check
        
    Returns:
        True if table exists, False otherwise
    """
    tables = list_tables(db_path)
    return table_name in tables
