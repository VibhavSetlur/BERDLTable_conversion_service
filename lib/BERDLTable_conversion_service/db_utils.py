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
    offset: Optional[int] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[str] = None,
    search_value: Optional[str] = None,
    query_filters: Optional[dict] = None
) -> Tuple[List[str], List[List[str]], int, int, float, float]:
    """
    Extract table data with pagination, sorting, and filtering.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to query
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        sort_column: Column name to sort by
        sort_order: Sort direction ('asc' or 'desc')
        search_value: Global search term to filter all columns
        query_filters: Dictionary of column-specific search terms (col: value)
        
    Returns:
        Tuple of (headers, data, total_count, filtered_count, db_query_ms, conversion_ms)
    """
    import time
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get column names first
        headers = get_table_columns(db_path, table_name)
        
        if not headers:
            logger.warning(f"Table {table_name} has no columns or doesn't exist")
            return [], [], 0, 0, 0.0, 0.0
        
        # 1. Get total count (before filtering)
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        # 2. Build where clause
        conditions = []
        params = []
        
        # 2a. Global Search (OR logic across all columns)
        if search_value:
            search_conditions = []
            term = f"%{search_value}%"
            for col in headers:
                search_conditions.append(f"{col} LIKE ?")
                params.append(term)
            
            if search_conditions:
                conditions.append(f"({' OR '.join(search_conditions)})")
        
        # 2b. Column Filters (AND logic)
        if query_filters:
            for col, val in query_filters.items():
                if col in headers and val:
                    # Basic LIKE search for now
                    conditions.append(f"{col} LIKE ?")
                    params.append(f"%{val}%")
        
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        
        # 3. Get filtered count (if filters exist)
        if where_clause:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} {where_clause}", params)
            filtered_count = cursor.fetchone()[0]
        else:
            filtered_count = total_count
        
        # 4. Build final query
        query = f"SELECT * FROM {table_name}{where_clause}"
        
        # Add sorting
        if sort_column and sort_column in headers:
            direction = "DESC" if sort_order and sort_order.lower() == "desc" else "ASC"
            query += f" ORDER BY {sort_column} {direction}"
        elif not sort_column:
             # Default sort to ensure consistent pagination
             query += f" ORDER BY {headers[0]} ASC"
            
        # Add pagination
        if limit is not None:
             query += f" LIMIT {int(limit)}"
        
        if offset is not None:
             query += f" OFFSET {int(offset)}"
        
        # TIME: SQLite SELECT query
        query_start = time.time()
        cursor.execute(query, params)
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
        
        return headers, data, total_count, filtered_count, db_query_ms, conversion_ms
        
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
