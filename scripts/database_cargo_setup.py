# Add this to your database initialization in app.py or create a new file: database_cargo_setup.py

import sqlite3
import json
import logging

def init_cargo_database():
    """Initialize database tables for cargo system"""
    try:
        conn = sqlite3.connect('awrpc.db')
        cursor = conn.cursor()
        
        # Create cargo_units table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cargo_units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_token TEXT NOT NULL,
                transport_id TEXT NOT NULL,
                cargo_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_token, transport_id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cargo_game_token 
            ON cargo_units(game_token)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cargo_transport_id 
            ON cargo_units(game_token, transport_id)
        ''')
        
        conn.commit()
        print("✅ Cargo database tables created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create cargo tables: {e}")
        raise
    finally:
        conn.close()

def save_cargo_data(token: str, transport_units: list):
    """Save cargo data for all transport units in a game"""
    try:
        conn = sqlite3.connect('awrpc.db')
        cursor = conn.cursor()
        
        # Clear existing cargo data for this game
        cursor.execute('DELETE FROM cargo_units WHERE game_token = ?', (token,))
        
        # Save cargo data for each transport unit
        for transport_data in transport_units:
            transport_id = transport_data['transport_id']
            cargo_list = transport_data['cargo']
            
            # Convert cargo units to serializable format
            cargo_data = []
            for cargo_unit in cargo_list:
                if cargo_unit is not None:
                    cargo_data.append({
                        'army': cargo_unit.army.value if hasattr(cargo_unit.army, 'value') else str(cargo_unit.army),
                        'type': cargo_unit.type.value if hasattr(cargo_unit.type, 'value') else str(cargo_unit.type),
                        'hp': cargo_unit.status.hp,
                        'fuel': cargo_unit.status.fuel,
                        'ammo': cargo_unit.status.ammo,
                        'moved': getattr(cargo_unit.status, 'moved', False),
                        'attacked': getattr(cargo_unit.status, 'attacked', False)
                    })
                else:
                    cargo_data.append(None)
            
            # Save to database
            cursor.execute('''
                INSERT OR REPLACE INTO cargo_units 
                (game_token, transport_id, cargo_data) 
                VALUES (?, ?, ?)
            ''', (token, transport_id, json.dumps(cargo_data)))
        
        conn.commit()
        logging.info(f"Saved cargo data for {len(transport_units)} transport units in game {token}")
        
    except Exception as e:
        logging.error(f"Failed to save cargo data for game {token}: {e}")
        raise
    finally:
        conn.close()

def load_cargo_data(token: str) -> dict:
    """Load cargo data for all transport units in a game"""
    try:
        conn = sqlite3.connect('awrpc.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT transport_id, cargo_data 
            FROM cargo_units 
            WHERE game_token = ?
        ''', (token,))
        
        cargo_records = cursor.fetchall()
        cargo_dict = {}
        
        for transport_id, cargo_json in cargo_records:
            cargo_dict[transport_id] = json.loads(cargo_json)
        
        logging.info(f"Loaded cargo data for {len(cargo_dict)} transport units in game {token}")
        return cargo_dict
        
    except Exception as e:
        logging.error(f"Failed to load cargo data for game {token}: {e}")
        return {}
    finally:
        conn.close()

def cleanup_old_cargo_data(days_old: int = 7):
    """Clean up cargo data for games older than specified days"""
    try:
        conn = sqlite3.connect('awrpc.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM cargo_units 
            WHERE created_at < datetime('now', '-{} days')
        '''.format(days_old))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        logging.info(f"Cleaned up {deleted_count} old cargo records")
        
    except Exception as e:
        logging.error(f"Failed to cleanup old cargo data: {e}")
    finally:
        conn.close()

# Call this when your app starts
if __name__ == "__main__":
    init_cargo_database()