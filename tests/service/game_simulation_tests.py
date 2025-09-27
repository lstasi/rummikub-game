"""Game simulation tests using GameService with predefined scenarios."""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch

import fakeredis

from rummikub.service import GameService
from rummikub.models import (
    GameState, GameStatus, Player, Rack, Pool, Board,
    PlayTilesAction, DrawAction, Meld, MeldKind
)
from rummikub.models.tiles import TileInstance, Color, NumberedTile, JokerTile


class TestGameSimulation:
    """Test game simulations from predefined scenario files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.redis = fakeredis.FakeRedis()
        self.service = GameService(self.redis)
        self.test_data_dir = Path(__file__).parent / "test_data"
    
    def _create_mock_pool_and_tiles(self, pool_tile_ids: List[str]) -> tuple[Pool, Dict[str, TileInstance]]:
        """Create a Pool and tile instances from predefined tile IDs.
        
        Args:
            pool_tile_ids: List of tile IDs in specific order
            
        Returns:
            Tuple of (Pool, tile_instances_dict)
        """
        tile_instances = {}
        
        for tile_id in pool_tile_ids:
            if tile_id.startswith('j'):
                # Joker tile: ja, jb
                copy = tile_id[1]
                tile = TileInstance.create_joker_tile(copy=copy)
            else:
                # Numbered tile: format like "10ra" = number + color_code + copy
                # Parse from the end: last char is copy, second-to-last is color
                copy = tile_id[-1]
                color_code = tile_id[-2]
                number_str = tile_id[:-2]
                number = int(number_str)
                
                # Map color codes to Color enum
                color_map = {'k': Color.BLACK, 'r': Color.RED, 'b': Color.BLUE, 'o': Color.ORANGE}
                color = color_map[color_code]
                
                tile = TileInstance.create_numbered_tile(number=number, color=color, copy=copy)
            
            tile_instances[tile.id] = tile
        
        pool = Pool(tile_ids=pool_tile_ids)
        return pool, tile_instances
    
    def _create_mock_game_with_fixed_pool(self, num_players: int, scenario_data: Dict[str, Any]) -> tuple[GameState, Dict[str, TileInstance]]:
        """Create a game with a fixed pool based on scenario data.
        
        Args:
            num_players: Number of players
            scenario_data: Scenario data from JSON file
            
        Returns:
            Tuple of (GameState with fixed pool and racks, tile_instances dict)
        """
        # Create pool and tile instances from scenario data
        pool, tile_instances = self._create_mock_pool_and_tiles(scenario_data["initial_pool"])
        
        with patch('rummikub.models.game.Pool.create_full_pool') as mock_create_pool:
            mock_create_pool.return_value = (pool, tile_instances)
            
            # Create the game normally - it will use our mocked pool
            game_state = self.service.create_game(num_players=num_players)
            
            # Now we need to set up the specific racks from the scenario
            players = []
            remaining_pool_tiles = list(scenario_data["initial_pool"])
            
            for i, player_name in enumerate(scenario_data["players"]):
                # Get the predefined rack for this player
                rack_tile_ids = scenario_data["initial_racks"][player_name]
                
                # Remove these tiles from the remaining pool
                for tile_id in rack_tile_ids:
                    if tile_id in remaining_pool_tiles:
                        remaining_pool_tiles.remove(tile_id)
                
                # Create player with specific rack
                player = Player(
                    id=game_state.players[i].id,  # Use the generated ID
                    name=player_name,
                    rack=Rack(tile_ids=rack_tile_ids),
                    initial_meld_met=False,
                    joined=True
                )
                players.append(player)
            
            # Update the pool with remaining tiles
            updated_pool = Pool(tile_ids=remaining_pool_tiles)
            
            # Create updated game state
            updated_game_state = GameState(
                game_id=game_state.game_id,
                players=players,
                pool=updated_pool,
                board=Board(melds=[]),
                current_player_index=0,
                status=GameStatus.IN_PROGRESS,
                created_at=game_state.created_at,
                updated_at=game_state.updated_at,
                winner_player_id=None,
                id=game_state.id,
                num_players=num_players
            )
            
            # Save the updated state
            self.service._save_game_state(updated_game_state)
            
            return updated_game_state, tile_instances
    
    def _create_action_from_data(self, action_data: Dict[str, Any]) -> Any:
        """Create an Action object from scenario data.
        
        Args:
            action_data: Action data from scenario
            
        Returns:
            Action object (PlayTilesAction or DrawAction)
        """
        if action_data["type"] == "draw":
            return DrawAction()
        elif action_data["type"] == "play_tiles":
            melds = []
            for meld_data in action_data["melds"]:
                meld = Meld(
                    kind=MeldKind.RUN if meld_data["kind"] == "run" else MeldKind.GROUP,
                    tiles=meld_data["tiles"]
                )
                melds.append(meld)
            return PlayTilesAction(melds=melds)
        else:
            raise ValueError(f"Unknown action type: {action_data['type']}")
    
    def _find_player_by_name(self, game_state: GameState, player_name: str) -> Player:
        """Find a player by name in the game state."""
        for player in game_state.players:
            if player.name == player_name:
                return player
        raise ValueError(f"Player {player_name} not found")
    
    def _simulate_game_from_scenario(self, scenario_file: Path) -> GameState:
        """Simulate a complete game from a scenario file.
        
        Args:
            scenario_file: Path to scenario JSON file
            
        Returns:
            Final game state after all actions
        """
        # Load scenario data
        with open(scenario_file, 'r') as f:
            scenario_data = json.load(f)
        
        # Create game with fixed pool
        num_players = len(scenario_data["players"])
        game_state, tile_instances = self._create_mock_game_with_fixed_pool(num_players, scenario_data)
        
        # Join all players
        for player_name in scenario_data["players"]:
            game_state = self.service.join_game(str(game_state.game_id), player_name)
        
        # Patch the GameRules.validate_initial_meld to use our tile instances
        with patch('rummikub.engine.game_rules.GameRules.validate_initial_meld') as mock_validate:
            def validate_with_instances(tile_instances_dict: Dict[str, TileInstance], melds: List[Meld]) -> bool:
                """Use our tile instances for validation."""
                # Merge with our known tile instances
                combined_instances = {**tile_instances, **tile_instances_dict}
                
                if not melds:
                    return False
                
                total_value = 0
                for meld in melds:
                    try:
                        total_value += meld.get_value(combined_instances)
                    except Exception:
                        return False
                
                return total_value >= 30
            
            mock_validate.side_effect = validate_with_instances
        
            # Execute all actions in sequence
            for action_data in scenario_data["actions"]:
                player_name = action_data["player"]
                player = self._find_player_by_name(game_state, player_name)
                action = self._create_action_from_data(action_data)
                
                # Get current player to check if it's their turn
                current_player = game_state.players[game_state.current_player_index]
                
                # If it's not the expected player's turn, we may need to advance turns
                # For now, let's print debug info and see what's happening
                print(f"Expected player: {player_name} (ID: {player.id})")
                print(f"Current player: {current_player.name} (ID: {current_player.id})")
                print(f"Current player index: {game_state.current_player_index}")
                
                # Execute the action
                game_state = self.service.execute_turn(
                    str(game_state.game_id), 
                    player.id, 
                    action
                )
                
                # Check if game is completed
                if game_state.status == GameStatus.COMPLETED:
                    print(f"Game completed after action by {player_name}")
                    break
                    
                # Advance the turn after successful action
                print(f"Advancing turn from player index {game_state.current_player_index}")
                game_state = self.service.engine.advance_turn(game_state)
                print(f"Turn advanced to player index {game_state.current_player_index}, status: {game_state.status}")
                
                # Update the game state in Redis
                self.service._save_game_state(game_state)
                
                # Check if game is completed after turn advance
                if game_state.status == GameStatus.COMPLETED:
                    print(f"Game completed after turn advance")
                    break
        
        return game_state
    
    def test_simple_win_scenario(self):
        """Test the simple win scenario."""
        scenario_file = self.test_data_dir / "simple_win_scenario.json"
        
        # Run the simulation
        final_state = self._simulate_game_from_scenario(scenario_file)
        
        # Load expected results
        with open(scenario_file, 'r') as f:
            scenario_data = json.load(f)
        
        # Verify the game completed as expected
        assert final_state.status.value == scenario_data["expected_final_status"]
        
        # Verify the correct winner
        if scenario_data["expected_winner"]:
            winner = self._find_player_by_name(final_state, scenario_data["expected_winner"])
            assert final_state.winner_player_id == winner.id
            
            # Winner should have empty rack
            assert len(winner.rack.tile_ids) == 0
    
    @pytest.mark.parametrize("scenario_file", [
        "simple_win_scenario.json"
    ])
    def test_game_scenario_parametrized(self, scenario_file: str):
        """Parametrized test for different game scenarios.
        
        Args:
            scenario_file: Name of the scenario file to test
        """
        scenario_path = self.test_data_dir / scenario_file
        
        if not scenario_path.exists():
            pytest.skip(f"Scenario file {scenario_file} not found")
        
        # Run the simulation
        final_state = self._simulate_game_from_scenario(scenario_path)
        
        # Load expected results
        with open(scenario_path, 'r') as f:
            scenario_data = json.load(f)
        
        # Basic validations that apply to all scenarios
        assert final_state.status.value == scenario_data["expected_final_status"]
        
        if scenario_data.get("expected_winner"):
            winner = self._find_player_by_name(final_state, scenario_data["expected_winner"])
            assert final_state.winner_player_id == winner.id
            assert len(winner.rack.tile_ids) == 0
        
        # Verify game state integrity
        assert len(final_state.players) == len(scenario_data["players"])
        assert final_state.num_players == len(scenario_data["players"])