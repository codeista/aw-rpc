#!/usr/bin/env python3
"""Test just the production variety test"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.unit.test_game_features import test_production_variety

# Run just the production test
print("Running production variety test in isolation...")
result = test_production_variety()
print(f"\nTest result: {result}")