'''[Dijkstra's Shortest Path First algorithm]

For a given source node in the graph, the algorithm finds the shortest path
between that node and every other. It can also be used for finding
the shortest paths from a single node to a single destination node by stopping
the algorithm once the shortest path to the destination node has been
determined
'''

from dataclasses import dataclass
from typing import List
from core.map_system import get_movement_cost, INF

from gameboard import GameTile, GameBoard


@dataclass
class Node():
    '''Defines the node.'''
    x: int
    y: int
    cost: int
    occupied: bool
    visited: bool
    distance: float


@dataclass
class Area():
    '''Defines the list of nodes, width and hight.'''
    nodes: List[Node]
    width: int
    height: int


def least_unvisited_distance(area):
    '''Returns the least unvisited distance.'''
    candidate = None
    for node in area.nodes:
        if node.occupied or node.visited:
            continue
        if not candidate or node.distance < candidate.distance:
            candidate = node
    return candidate

def node_at(area, x, y):
    '''Get node at coordinates with bounds checking'''
    if x < 0 or y < 0 or x >= area.width or y >= area.height:
        return None
    
    index = x + y * area.width
    if index >= 0 and index < len(area.nodes):
        return area.nodes[index]
    return None

def calc_neighbor_distances(area, current_node):
    '''East, West, North, South nodes'''
    # West
    node = node_at(area, current_node.x - 1, current_node.y)
    if node and not node.occupied:
        new_dist = current_node.distance + node.cost
        if new_dist < node.distance:
            node.distance = new_dist
    # North node
    node = node_at(area, current_node.x, current_node.y - 1)
    if node and not node.occupied:
        new_dist = current_node.distance + node.cost
        if new_dist < node.distance:
            node.distance = new_dist
    # East node
    node = node_at(area, current_node.x + 1, current_node.y)
    if node and not node.occupied:
        new_dist = current_node.distance + node.cost
        if new_dist < node.distance:
            node.distance = new_dist
    # South node
    node = node_at(area, current_node.x, current_node.y + 1)
    if node and not node.occupied:
        new_dist = current_node.distance + node.cost
        if new_dist < node.distance:
            node.distance = new_dist


def dijkstra(board: GameBoard, source: GameTile, target: GameTile) -> int:
    """Dijkstra's Path Finding Algorithm for a rectangular grid"""
    
    if not source or not source.unit:
        return INF
        
    unit_class = source.unit.status.cls
    width = board.width
    height = board.height
    
    # Initialize distances
    distances = {}
    visited = set()
    
    # Set source distance to 0
    source_idx = source.x + source.y * width
    distances[source_idx] = 0
    
    # Priority queue: (distance, tile_index)
    import heapq
    pq = [(0, source_idx)]
    
    while pq:
        current_dist, current_idx = heapq.heappop(pq)
        
        if current_idx in visited:
            continue
            
        visited.add(current_idx)
        
        # Check if we reached the target
        current_x = current_idx % width
        current_y = current_idx // width
        
        if current_x == target.x and current_y == target.y:
            return current_dist
            
        # Check all adjacent tiles
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_x, next_y = current_x + dx, current_y + dy
            
            # Check bounds
            if not (0 <= next_x < width and 0 <= next_y < height):
                continue
                
            next_idx = next_x + next_y * width
            
            if next_idx in visited:
                continue
                
            # Get the tile and calculate movement cost
            tile = board.grid[next_idx]
            
            # Skip if tile is occupied by another unit (except target)
            if tile.unit and not (next_x == target.x and next_y == target.y):
                if tile.unit.army != source.unit.army:
                    continue
                
            try:
                cost = get_movement_cost(unit_class, tile.mapTile.type)
                if cost == INF:
                    continue  # Impassable terrain
                    
                new_dist = current_dist + cost
                
                if next_idx not in distances or new_dist < distances[next_idx]:
                    distances[next_idx] = new_dist
                    heapq.heappush(pq, (new_dist, next_idx))
                    
            except (KeyError, IndexError):
                # Unknown terrain or unit class - skip
                continue
    
    return INF  # Target unreachable