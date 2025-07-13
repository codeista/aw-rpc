
import sys
sys.path.insert(0, '.')

try:
    from app_core import app, db
    from app import game_board_rpc
    
    print("Testing with Flask app context...")
    with app.app_context():
        db.create_all()
        result = game_board_rpc('test123')
        print(f"API Result: {type(result)}")
        if result:
            print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        else:
            print("No result returned")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
