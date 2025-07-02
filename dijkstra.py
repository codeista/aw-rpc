'''[Dijkstra's Shortest Path First algorithm]

For a given source node in the graph, the algorithm finds the shortest path
between that node and every other. It can also be used for finding
the shortest paths from a single node to a single destination node by stopping
the algorithm once the shortest path to the destination node has been
determined
'''

from dataclasses import dataclass
from typing import List
from map_system import MOVEMENT_COST, INF

from gameboard import GameTile, GameBoard

INF = 99999999


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
    """Enhanced dijkstra with better error handling"""
    
    # Validate inputs
    if not source or not target:
        return INF
    
    if not source.unit:
        return INF
    
    """Dijkstra's Path Finding Algorithm for a rectangular grid where the
       distance between each adjacent (non-diagonal) node is given by the
       variable cost"""
    # mark all nodes unvisited
    # set the distance to 0 for initial node and infinity for others
    nodes = []
    for tile in board.grid:
        cost = MOVEMENT_COST[tile.mapTile.type][source.unit.status.cls.value]
        
        # Determine if tile blocks movement
        occupied = False
        if tile.unit and tile.unit.army != source.unit.army:
            # Enemy unit blocks movement
            occupied = True
        elif tile.unit and tile.unit.army == source.unit.army:
            # Friendly unit - only blocks if can't join
            if (tile.unit.type != source.unit.type or 
                tile.unit.status.hp >= 100):
                occupied = True
    area = Area(nodes, board.width, board.height)
    destination = node_at(area, target.x, target.y)
    if not destination:
        return INF
    while True:
        # select the unvisited node with the smallest distance,
        #  make it the current node
        current_node = least_unvisited_distance(area)
        # print(current_node, current_node.x, current_node.y)
        # find unvisited neighbours and calc distances,
        # compare to assigned distance and save if is smaller
        calc_neighbor_distances(area, current_node)
        # set current node as visited
        current_node.visited = True
        # check if destination has been visited
        if destination.visited:
            return destination.distance
        # check smallest unvisited distance
        node = least_unvisited_distance(area)
        if not node or node.distance >= INF:
            return INF
