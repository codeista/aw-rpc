# AI System Planning for Advance Wars RPC

## Goals
1. Create an AI opponent that can play Advance Wars strategically
2. Use local LLM for decision making (not just rule-based)
3. Integrate seamlessly with existing RPC system
4. Support different difficulty levels/playstyles

## Key Questions to Answer

### 1. What should the AI control?
- Unit movement and pathfinding
- Combat decisions (when/who to attack)
- Economic decisions (what units to build)
- Strategic planning (which properties to capture)
- Defensive positioning

### 2. How should we represent game state for the AI?
- Current board state (terrain, units, buildings)
- Economic situation (funds, income rate)
- Strategic objectives (enemy HQ location, key properties)
- Threat assessment (enemy unit positions and capabilities)
- Historical data (previous moves, patterns)

### 3. What architecture should we use?
Options:
a) **Pure LLM approach** - Feed game state to LLM, get decisions
b) **Hybrid approach** - LLM for strategy, algorithms for tactics
c) **Multi-agent** - Different AI agents for different aspects
d) **Reinforcement learning** - Train on game outcomes

### 4. Integration approach
- Connect to existing RPC endpoints
- Create new AI-specific endpoints
- Run as separate service or integrated

### 5. Training/Tuning approach
- Use replay data from human games
- Self-play to improve
- Hand-crafted scenarios
- Strategy templates

## Proposed Architecture

### Phase 1: Basic AI Player
1. Game state parser (convert RPC data to AI-readable format)
2. Strategy evaluator (assess current position)
3. Move generator (list all possible actions)
4. Decision maker (choose best action via LLM)
5. RPC interface (execute chosen actions)

### Phase 2: Enhanced Intelligence
1. Pattern recognition (learn from games)
2. Opponent modeling (adapt to player style)
3. Long-term planning (multi-turn strategies)
4. Difficulty scaling

### Phase 3: Advanced Features
1. Commentary system (explain AI decisions)
2. Training mode (help players improve)
3. Custom AI personalities
4. Tournament support

## Technical Considerations

### Performance
- LLM inference time per decision
- Caching for similar game states
- Batch processing multiple units
- Async decision making

### Model Selection
- Small models (Phi-3, Llama 3.2 7B) for speed
- Larger models (Llama 3.2 70B) for complex strategy
- Fine-tuned models on Advance Wars data
- Quantization for performance

### Data Format
```json
{
  "game_state": {
    "turn": 5,
    "player": "AI",
    "board": [...],
    "units": {...},
    "economy": {...}
  },
  "possible_actions": [...],
  "strategic_goals": [...]
}
```

## Implementation Steps

1. **Research Phase**
   - Study existing game AI approaches
   - Analyze current codebase structure
   - Identify integration points

2. **Prototype Phase**
   - Simple rule-based AI baseline
   - LLM integration for one decision type
   - Performance testing

3. **Development Phase**
   - Full game state representation
   - Complete action space coverage
   - Strategy system implementation

4. **Testing Phase**
   - AI vs AI games
   - Human vs AI playtesting
   - Difficulty tuning

## Questions for You

1. **Difficulty Levels** - What kind of AI opponents do you want?
   - Easy (makes mistakes, limited strategy)
   - Medium (solid fundamentals)
   - Hard (optimal play)
   - Unfair (perfect information)

2. **Play Style** - Should AI have different personalities?
   - Aggressive (rush tactics)
   - Economic (build up forces)
   - Defensive (turtle strategy)
   - Balanced

3. **Integration** - How should AI connect to game?
   - Separate AI service
   - Integrated into game server
   - Client-side AI option

4. **Features** - What AI features matter most?
   - Fast decision making
   - Explainable moves
   - Human-like play
   - Maximum strength

5. **Model Constraints**
   - Max model size you can run?
   - Response time requirements?
   - GPU available for inference?