#!/usr/bin/env python3
"""
Load testing scenarios for AW-RPC using Locust
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:5000
"""

from locust import HttpUser, task, between
import json
import time
import random


class GamePlayer(HttpUser):
    """Simulates a player interacting with the game"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.token = f"load-test-{self.environment.runner.user_count}-{int(time.time())}"
        self.create_game()
    
    def make_rpc_call(self, method, params):
        """Helper to make RPC calls"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        with self.client.post("/api", json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
                return None
            
            try:
                data = response.json()
                if 'error' in data:
                    response.failure(f"RPC error: {data['error']}")
                    return None
                return data.get('result')
            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
                return None
    
    def create_game(self):
        """Create a new game for this user"""
        result = self.make_rpc_call('game_create_test', {"token": self.token})
        if result == 'ok':
            self.game_created = True
        else:
            self.game_created = False
    
    @task(5)
    def check_game_board(self):
        """Frequently check game board state"""
        if not self.game_created:
            return
        
        result = self.make_rpc_call('game_board', {"token": self.token})
        if result:
            self.current_turn = result.get('current_turn', 'RED')
            self.grid = result.get('grid', [])
    
    @task(3)
    def create_unit(self):
        """Create units at random positions"""
        if not self.game_created:
            return
        
        unit_types = ['INFANTRY', 'TANK', 'RECON', 'APC', 'ARTILLERY']
        x = random.randint(0, 11)
        y = random.randint(0, 10)
        
        self.make_rpc_call('unit_create', {
            "token": self.token,
            "army": self.current_turn if hasattr(self, 'current_turn') else 'RED',
            "unit_type": random.choice(unit_types),
            "x": x,
            "y": y
        })
    
    @task(2)
    def move_units(self):
        """Move random units"""
        if not self.game_created or not hasattr(self, 'grid'):
            return
        
        # Find units to move
        for _ in range(5):  # Try up to 5 times
            x = random.randint(0, 11)
            y = random.randint(0, 10)
            
            # Check movement range
            result = self.make_rpc_call('movement_range', {
                "token": self.token,
                "unit_x": x,
                "unit_y": y
            })
            
            if result and 'movement_tiles' in result:
                tiles = result['movement_tiles']
                if tiles:
                    # Move to random valid tile
                    target = random.choice(tiles)
                    self.make_rpc_call('movement_execute', {
                        "token": self.token,
                        "from_x": x,
                        "from_y": y,
                        "to_x": target['x'],
                        "to_y": target['y']
                    })
                    break
    
    @task(1)
    def end_turn(self):
        """End turn occasionally"""
        if not self.game_created:
            return
        
        self.make_rpc_call('army_end_turn', {"token": self.token})
    
    @task(2)
    def check_tile_info(self):
        """Check random tile information"""
        if not self.game_created:
            return
        
        x = random.randint(0, 11)
        y = random.randint(0, 10)
        
        self.make_rpc_call('tile', {
            "token": self.token,
            "x": x,
            "y": y
        })
    
    @task(1)
    def get_economy_info(self):
        """Check economic information"""
        if not self.game_created:
            return
        
        self.make_rpc_call('get_army_economy', {"token": self.token})


class IntenseGamePlayer(GamePlayer):
    """More aggressive player for stress testing"""
    wait_time = between(0.1, 0.5)  # Much faster actions
    
    @task(10)
    def rapid_unit_creation(self):
        """Create many units quickly"""
        if not self.game_created:
            return
        
        for _ in range(5):
            self.create_unit()
    
    @task(5)
    def combat_spam(self):
        """Check combat previews rapidly"""
        if not self.game_created:
            return
        
        for _ in range(10):
            self.make_rpc_call('combat_preview', {
                "token": self.token,
                "attacker_x": random.randint(0, 11),
                "attacker_y": random.randint(0, 10),
                "defender_x": random.randint(0, 11),
                "defender_y": random.randint(0, 10)
            })


class APIBrowser(HttpUser):
    """User that browses API documentation and info"""
    wait_time = between(2, 5)
    
    @task
    def browse_api_docs(self):
        """Access API documentation"""
        self.client.get("/api/docs")
    
    @task
    def get_troop_info(self):
        """Get troop configuration info"""
        self.make_rpc_call('troop_info', {})
    
    def make_rpc_call(self, method, params):
        """Helper to make RPC calls"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        self.client.post("/api", json=payload)


# Locust configuration for different test scenarios
class NormalLoadTest(HttpUser):
    """Normal load test scenario"""
    tasks = [GamePlayer]
    min_wait = 1000
    max_wait = 3000


class StressTest(HttpUser):
    """Stress test scenario"""
    tasks = [IntenseGamePlayer]
    min_wait = 100
    max_wait = 500


class MixedLoadTest(HttpUser):
    """Mixed load test with different user types"""
    tasks = {
        GamePlayer: 7,
        IntenseGamePlayer: 2,
        APIBrowser: 1
    }