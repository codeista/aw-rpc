"""
Enhanced database operations with connection pooling and optimization
"""

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    """Simple connection pool for SQLite"""
    
    def __init__(self, database_url: str, pool_size: int = 5):
        self.database_url = database_url
        self.pool_size = pool_size
        self._connections = []
        self._lock = threading.Lock()
        self._create_initial_connections()
        self.stats = {
            'total_queries': 0,
            'avg_query_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _create_initial_connections(self):
        """Create initial connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self._connections.append(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimizations"""
        try:
            if self.database_url.startswith('sqlite:///'):
                db_path = self.database_url.replace('sqlite:///', '')
                conn = sqlite3.connect(
                    db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Enable optimizations
                conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
                conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
                conn.execute('PRAGMA cache_size=10000')  # 10MB cache
                conn.execute('PRAGMA temp_store=MEMORY')  # Use memory for temp
                conn.execute('PRAGMA mmap_size=268435456')  # 256MB memory map
                
                return conn
            else:
                # For PostgreSQL connections, use basic connection
                import psycopg2
                conn = psycopg2.connect(self.database_url)
                return conn
                
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        start_time = time.time()
        
        try:
            with self._lock:
                if self._connections:
                    conn = self._connections.pop()
                else:
                    # Pool exhausted, create new connection
                    conn = self._create_connection()
                    if not conn:
                        raise Exception("Could not create database connection")
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            if conn:
                # Connection might be corrupted, don't return to pool
                try:
                    conn.close()
                except:
                    pass
                conn = None
            raise
            
        finally:
            # Record statistics
            query_time = time.time() - start_time
            self.stats['total_queries'] += 1
            self.stats['avg_query_time'] = (
                (self.stats['avg_query_time'] * (self.stats['total_queries'] - 1) + query_time) 
                / self.stats['total_queries']
            )
            
            # Return connection to pool
            if conn:
                with self._lock:
                    if len(self._connections) < self.pool_size:
                        self._connections.append(conn)
                    else:
                        # Pool full, close connection
                        try:
                            conn.close()
                        except:
                            pass
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except:
                    pass
            self._connections.clear()
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        return self.stats.copy()

# Global connection pool
_db_pool: Optional[DatabasePool] = None

def init_database_pool(database_url: str, pool_size: int = 5):
    """Initialize the global database pool"""
    global _db_pool
    _db_pool = DatabasePool(database_url, pool_size)
    logger.info(f"Database pool initialized with {pool_size} connections")

def get_db_connection():
    """Get a database connection from the pool"""
    if not _db_pool:
        raise Exception("Database pool not initialized")
    return _db_pool.get_connection()

def create_indexes():
    """Create database indexes for better performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_game_token ON game(token)",
        "CREATE INDEX IF NOT EXISTS idx_game_date ON game(date)",
        "CREATE INDEX IF NOT EXISTS idx_game_updated ON game(updated)",
    ]
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for index_sql in indexes:
                cursor.execute(index_sql)
                logger.debug(f"Created index: {index_sql}")
            conn.commit()
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

def optimize_game_save(game_data: dict, token: str) -> bool:
    """Optimized game save operation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Use UPSERT for better performance
            if 'sqlite' in str(type(conn)).lower():
                # SQLite UPSERT
                cursor.execute("""
                    INSERT OR REPLACE INTO game (token, date, updated, board)
                    VALUES (?, datetime('now'), datetime('now'), ?)
                """, (token, game_data))
            else:
                # PostgreSQL UPSERT
                cursor.execute("""
                    INSERT INTO game (token, date, updated, board)
                    VALUES (%s, NOW(), NOW(), %s)
                    ON CONFLICT (token) 
                    DO UPDATE SET updated = NOW(), board = EXCLUDED.board
                """, (token, game_data))
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save game {token}: {e}")
        return False

def optimize_game_load(token: str) -> Optional[dict]:
    """Optimized game load operation with caching"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Use prepared statement equivalent
            cursor.execute(
                "SELECT board, updated FROM game WHERE token = ? LIMIT 1",
                (token,)
            )
            
            result = cursor.fetchone()
            if result:
                _db_pool.stats['cache_hits'] += 1
                return {
                    'board': result[0],
                    'updated': result[1]
                }
            else:
                _db_pool.stats['cache_misses'] += 1
                return None
                
    except Exception as e:
        logger.error(f"Failed to load game {token}: {e}")
        return None

def cleanup_old_games(days_old: int = 7) -> int:
    """Clean up games older than specified days"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if 'sqlite' in str(type(conn)).lower():
                cursor.execute("""
                    DELETE FROM game 
                    WHERE updated < datetime('now', '-{} days')
                """.format(days_old))
            else:
                cursor.execute("""
                    DELETE FROM game 
                    WHERE updated < NOW() - INTERVAL '%s days'
                """, (days_old,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old games")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Failed to cleanup old games: {e}")
        return 0

def get_database_stats() -> dict:
    """Get comprehensive database statistics"""
    stats = {}
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get table statistics
            cursor.execute("SELECT COUNT(*) FROM game")
            stats['total_games'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM game 
                WHERE updated > datetime('now', '-1 day')
            """)
            stats['active_games_24h'] = cursor.fetchone()[0]
            
            # Get pool statistics
            if _db_pool:
                stats.update(_db_pool.get_stats())
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        stats['error'] = str(e)
    
    return stats

def vacuum_database():
    """Optimize database storage (SQLite only)"""
    try:
        with get_db_connection() as conn:
            if 'sqlite' in str(type(conn)).lower():
                conn.execute('VACUUM')
                logger.info("Database vacuumed successfully")
            else:
                logger.info("VACUUM not needed for non-SQLite database")
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
