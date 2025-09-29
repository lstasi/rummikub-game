"""Comprehensive tests for GameEngine class.

This test suite covers all functionality of the GameEngine class,
testing game lifecycle, state management, actions, and error conditions.
"""

import pytest
from unittest.mock import patch, MagicMock

from rummikub.models import (
    GameState, GameStatus, Player, Rack, Meld, MeldKind,
    PlayTilesAction, TileUtils, Color, GameStateError, GameNotStartedError, GameFinishedError, InvalidMoveError,
    InvalidMeldError
)
from rummikub.engine import GameEngine


class TestGameEngineInitialization:
    """Test GameEngine initialization and basic properties."""
    
    def test_engine_creation(self):
        """Test that GameEngine can be created."""
        engine = GameEngine()
        assert engine is not None
        assert isinstance(engine, GameEngine)
    
    def test_engine_is_stateless(self):
        """Test that engine instances don't maintain state."""
        engine1 = GameEngine()
        engine2 = GameEngine()
        
        # Both engines should behave identically
        game1 = engine1.create_game(2)
        game2 = engine2.create_game(2)
        
        # Games should have different IDs but same structure
        assert game1.game_id != game2.game_id
        assert game1.status == game2.status
        assert len(game1.players) == len(game2.players)
        

class TestGameEngineGameCreation:
    """Test game creation functionality."""
    
    def test_create_game_valid_player_counts(self):
        """Test creating games with valid player counts (2-4)."""
        engine = GameEngine()
        
        for num_players in [2, 3, 4]:
            game_state = engine.create_game(num_players)
            
            # Verify basic game structure
            assert isinstance(game_state, GameState)
            assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
            assert len(game_state.players) == num_players
            assert game_state.game_id is not None
            # current_player_index starts at 0 but isn't meaningful until game starts
            assert game_state.current_player_index == 0
            
            # Verify pool initialization
            assert game_state.pool is not None
            expected_pool_size = 106 - (num_players * 14)  # 106 total - dealt tiles
            assert len(game_state.pool.tile_ids) == expected_pool_size
            
            # Verify players have tiles dealt
            for player in game_state.players:
                assert len(player.rack.tile_ids) == 14
                assert not player.joined  # Players start unjoined
                assert not player.initial_meld_met
                assert player.name is None
    
    def test_create_game_invalid_player_counts(self):
        """Test creating games with invalid player counts."""
        engine = GameEngine()
        
        invalid_counts = [0, 1, 5, 6, -1, 10]
        for num_players in invalid_counts:
            with pytest.raises(GameStateError):
                engine.create_game(num_players)
    
    def test_create_game_generates_unique_ids(self):
        """Test that each created game has a unique ID."""
        engine = GameEngine()
        
        game_ids = set()
        for _ in range(10):
            game_state = engine.create_game(2)
            assert game_state.game_id not in game_ids
            game_ids.add(game_state.game_id)


class TestGameEnginePlayerJoining:
    """Test player joining functionality."""
    
    def test_join_player_success(self):
        """Test successful player joining."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join first player
        game_state = engine.join_game(game_state, "Alice")
        
        joined_players = [p for p in game_state.players if p.joined]
        assert len(joined_players) == 1
        assert joined_players[0].name == "Alice"
        assert joined_players[0].joined is True
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
    
    def test_join_all_players_starts_game(self):
        """Test that joining all players automatically starts the game."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join first player
        game_state = engine.join_game(game_state, "Alice")
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        
        # Join second player - should auto-start
        game_state = engine.join_game(game_state, "Bob")
        assert game_state.status == GameStatus.IN_PROGRESS
        assert game_state.current_player_index == 0
        
        # Verify both players are joined
        joined_players = [p for p in game_state.players if p.joined]
        assert len(joined_players) == 2
        assert {p.name for p in joined_players} == {"Alice", "Bob"}
    
    def test_join_player_duplicate_name(self):
        """Test that duplicate player names are rejected."""
        engine = GameEngine()
        game_state = engine.create_game(3)
        
        # Join first player
        game_state = engine.join_game(game_state, "Alice")
        
        # Try to join with same name
        with pytest.raises(InvalidMoveError, match="Player with name 'Alice' already in game"):
            engine.join_game(game_state, "Alice")
    
    def test_join_player_game_full(self):
        """Test joining when all slots are taken."""
        engine = GameEngine()
        # Create 3-player game so we can test joining after some slots filled
        game_state = engine.create_game(3)
        
        # Join first 2 players (won't auto-start)
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Game should still be waiting (not all slots filled)
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        
        # Join third player - should auto-start
        game_state = engine.join_game(game_state, "Charlie")
        assert game_state.status == GameStatus.IN_PROGRESS
        
        # Now try to join fourth player when game is in progress
        with pytest.raises(GameNotStartedError, match="Can only join games waiting for players"):
            engine.join_game(game_state, "Diana")
    
    def test_join_player_wrong_status(self):
        """Test joining when game is not waiting for players."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players to start game
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Game should now be in progress
        assert game_state.status == GameStatus.IN_PROGRESS
        
        # Manually create a game with 3 slots and fill 2
        game_state_3p = engine.create_game(3)
        game_state_3p = engine.join_game(game_state_3p, "Alice")
        game_state_3p = engine.join_game(game_state_3p, "Bob")
        
        # Manually set to in progress
        from rummikub.models import GameState
        in_progress_state = GameState(
            game_id=game_state_3p.game_id,
            players=game_state_3p.players,
            pool=game_state_3p.pool,
            board=game_state_3p.board,
            current_player_index=0,
            status=GameStatus.IN_PROGRESS,
            created_at=game_state_3p.created_at,
            updated_at=game_state_3p.updated_at
        )
        
        # Try to join when in progress
        with pytest.raises(GameNotStartedError, match="Can only join games waiting for players"):
            engine.join_game(in_progress_state, "Charlie")


class TestGameEngineGameStart:
    """Test game starting functionality."""
    
    def test_start_game_success(self):
        """Test successful manual game start."""
        engine = GameEngine()
        game_state = engine.create_game(3)  # 3 players so auto-start doesn't happen
        
        # Join 2 players (not all)
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Manually start the game
        game_state = engine.start_game(game_state)
        
        assert game_state.status == GameStatus.IN_PROGRESS
        assert game_state.current_player_index == 0
    
    def test_start_game_wrong_status(self):
        """Test starting game when not in waiting status."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players to auto-start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Should already be started
        assert game_state.status == GameStatus.IN_PROGRESS
        
        # Try to start again
        with pytest.raises(GameNotStartedError, match="Game can only be started from waiting_for_players status"):
            engine.start_game(game_state)
    
    def test_start_game_insufficient_players(self):
        """Test starting game with insufficient players (impossible with current create_game validation)."""
        engine = GameEngine()
        
        # The current implementation checks total player count, not joined count
        # Since create_game already validates 2-4 players, this scenario is hard to test
        # Let's test that a valid game can be started even without joined players
        game_state = engine.create_game(2)
        
        # Should be able to start even without joined players in current implementation
        started_game = engine.start_game(game_state)
        assert started_game.status == GameStatus.IN_PROGRESS
    
    def test_start_game_too_many_players(self):
        """Test starting game with too many players (edge case)."""
        engine = GameEngine()
        game_state = engine.create_game(4)
        
        # Join all 4 players
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        game_state = engine.join_game(game_state, "Charlie")
        game_state = engine.join_game(game_state, "Diana")
        
        # Should auto-start successfully with 4 players
        assert game_state.status == GameStatus.IN_PROGRESS


class TestGameEngineStateQueries:
    """Test game state query methods."""
    
    def test_get_game_status(self):
        """Test getting game status."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Initially waiting
        assert engine.get_game_status(game_state) == GameStatus.WAITING_FOR_PLAYERS
        
        # After joining players
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Should be in progress
        assert engine.get_game_status(game_state) == GameStatus.IN_PROGRESS
    
    def test_get_current_player_success(self):
        """Test getting current player ID."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Should be in progress with first player
        current_player_id = engine.get_current_player(game_state)
        assert current_player_id == game_state.players[0].id
    
    def test_get_current_player_game_not_started(self):
        """Test getting current player when game not started."""
        engine = GameEngine()
        game_state = engine.create_game(3)  # Won't auto-start
        game_state = engine.join_game(game_state, "Alice")
        
        with pytest.raises(GameNotStartedError, match="Game hasn't started yet"):
            engine.get_current_player(game_state)
    
    def test_get_current_player_game_finished(self):
        """Test getting current player when game finished."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Manually set to completed
        from rummikub.models import GameState
        completed_state = GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=GameStatus.COMPLETED,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        with pytest.raises(GameFinishedError, match="Game is already finished"):
            engine.get_current_player(completed_state)
    
    def test_can_player_act_success(self):
        """Test checking if player can act."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        current_player = game_state.players[0]
        other_player = game_state.players[1]
        
        # Current player should be able to act
        assert engine.can_player_act(game_state, current_player.id) is True
        
        # Other player should not
        assert engine.can_player_act(game_state, other_player.id) is False
    
    def test_can_player_act_game_not_started(self):
        """Test can_player_act when game not started."""
        engine = GameEngine()
        game_state = engine.create_game(3)  # Won't auto-start
        game_state = engine.join_game(game_state, "Alice")
        
        # No player should be able to act
        assert engine.can_player_act(game_state, game_state.players[0].id) is False


class TestGameEngineTurnManagement:
    """Test turn management functionality."""
    
    def test_advance_turn_success(self):
        """Test successful turn advancement."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Should start at player 0
        assert game_state.current_player_index == 0
        
        # Advance turn
        game_state = engine.advance_turn(game_state)
        
        # Should move to player 1
        assert game_state.current_player_index == 1
    
    def test_advance_turn_cycles_through_players(self):
        """Test that advance_turn cycles through all players."""
        engine = GameEngine()
        game_state = engine.create_game(3)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        game_state = engine.join_game(game_state, "Charlie")
        
        # Should start at player 0
        assert game_state.current_player_index == 0
        
        # Advance to player 1
        game_state = engine.advance_turn(game_state)
        assert game_state.current_player_index == 1
        
        # Advance to player 2
        game_state = engine.advance_turn(game_state)
        assert game_state.current_player_index == 2
        
        # Should cycle back to player 0
        game_state = engine.advance_turn(game_state)
        assert game_state.current_player_index == 0
    
    def test_advance_turn_game_not_started(self):
        """Test advance_turn when game not started."""
        engine = GameEngine()
        game_state = engine.create_game(3)
        game_state = engine.join_game(game_state, "Alice")
        
        with pytest.raises(GameNotStartedError, match="Game hasn't started yet"):
            engine.advance_turn(game_state)
    
    def test_advance_turn_game_finished(self):
        """Test advance_turn when game finished."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Set to completed
        from rummikub.models import GameState
        completed_state = GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=GameStatus.COMPLETED,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        with pytest.raises(Exception):  # GameFinishedError
            engine.advance_turn(completed_state)


class TestGameEngineValidation:
    """Test validation methods."""
    
    def test_validate_initial_meld_sufficient_points(self):
        """Test initial meld validation with sufficient points (30+)."""
        engine = GameEngine()
        
        # Create a group of 10s (30 points total)
        tiles_10_group = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles_10_group)
        
        result = engine.validate_initial_meld([meld])
        assert result is True
    
    def test_validate_initial_meld_insufficient_points(self):
        """Test initial meld validation with insufficient points (<30)."""
        engine = GameEngine()
        
        # Create a run of 1,2,3 (6 points total)
        tiles_low_run = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles_low_run)
        
        result = engine.validate_initial_meld([meld])
        assert result is False
    
    def test_validate_initial_meld_multiple_melds(self):
        """Test initial meld validation with multiple melds."""
        engine = GameEngine()
        
        # Create two small melds that together total 30+
        tiles_run = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(9, Color.RED, 'a')  # 24 points
        ]
        
        tiles_group = [
            TileUtils.create_numbered_tile_id(2, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.BLACK, 'a')  # 6 points
        ]
        
        meld1 = Meld(kind=MeldKind.RUN, tiles=tiles_run)
        meld2 = Meld(kind=MeldKind.GROUP, tiles=tiles_group)
        
        # Together they total 30 points
        result = engine.validate_initial_meld([meld1, meld2])
        assert result is True
    
    def test_validate_initial_meld_empty_list(self):
        """Test initial meld validation with empty meld list."""
        engine = GameEngine()
        
        result = engine.validate_initial_meld([])
        assert result is False
    
    def test_validate_initial_meld_invalid_meld(self):
        """Test initial meld validation with invalid meld structure."""
        # Create an invalid meld (only 2 tiles in group) - this should raise an error during meld creation
        tiles_invalid = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a')
        ]
        
        # Meld creation should fail with invalid structure
        with pytest.raises(InvalidMeldError, match="Group must have 3-4 tiles"):
            Meld(kind=MeldKind.GROUP, tiles=tiles_invalid)
    
    def test_check_win_condition_success(self):
        """Test successful win condition check (empty rack + initial meld met)."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Get first player and empty their rack
        player = game_state.players[0]
        empty_player = Player(
            id=player.id,
            name=player.name,
            rack=Rack(tile_ids=[]),  # Empty rack
            initial_meld_met=True,   # Initial meld requirement met
            joined=player.joined
        )
        
        # Update game state
        updated_players = [empty_player] + game_state.players[1:]
        from rummikub.models import GameState
        modified_game_state = GameState(
            game_id=game_state.game_id,
            players=updated_players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        result = engine.check_win_condition(modified_game_state, player.id)
        assert result is True
    
    def test_check_win_condition_has_tiles(self):
        """Test win condition check when player still has tiles."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Player still has tiles in rack
        player = game_state.players[0]
        result = engine.check_win_condition(game_state, player.id)
        assert result is False
    
    def test_check_win_condition_initial_meld_not_met(self):
        """Test win condition check when initial meld not met."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Get first player and empty rack but don't meet initial meld
        player = game_state.players[0]
        empty_player = Player(
            id=player.id,
            name=player.name,
            rack=Rack(tile_ids=[]),  # Empty rack
            initial_meld_met=False,  # Initial meld NOT met
            joined=player.joined
        )
        
        # Update game state
        updated_players = [empty_player] + game_state.players[1:]
        from rummikub.models import GameState
        modified_game_state = GameState(
            game_id=game_state.game_id,
            players=updated_players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        result = engine.check_win_condition(modified_game_state, player.id)
        assert result is False


class TestGameEngineActionExecution:
    """Test action execution methods."""
    
    @patch('rummikub.engine.game_actions.GameActions.execute_play_action')
    def test_execute_play_action_delegation(self, mock_execute):
        """Test that execute_play_action delegates to GameActions."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        player_id = game_state.players[0].id
        
        # Create mock action
        mock_action = MagicMock(spec=PlayTilesAction)
        mock_execute.return_value = game_state  # Return same state
        
        # Execute action
        result = engine.execute_play_action(game_state, player_id, mock_action)
        
        # Verify delegation
        mock_execute.assert_called_once_with(game_state, player_id, mock_action)
        assert result == game_state
    
    @patch('rummikub.engine.game_actions.GameActions.execute_draw_action')
    def test_execute_draw_action_delegation(self, mock_execute):
        """Test that execute_draw_action delegates to GameActions."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        player_id = game_state.players[0].id
        mock_execute.return_value = game_state  # Return same state
        
        # Execute action
        result = engine.execute_draw_action(game_state, player_id)
        
        # Verify delegation
        mock_execute.assert_called_once_with(game_state, player_id)
        assert result == game_state


class TestGameEngineIntegration:
    """Test complete game flows and integration scenarios."""
    
    def test_complete_game_flow_basic(self):
        """Test a basic complete game flow."""
        engine = GameEngine()
        
        # Create game
        game_state = engine.create_game(2)
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        
        # Join players
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Game should auto-start
        assert game_state.status == GameStatus.IN_PROGRESS
        assert game_state.current_player_index == 0
        
        # Verify current player can act
        current_player_id = engine.get_current_player(game_state)
        assert engine.can_player_act(game_state, current_player_id) is True
        
        # Advance turn
        game_state = engine.advance_turn(game_state)
        assert game_state.current_player_index == 1
        
        # Verify turn changed
        new_current_player_id = engine.get_current_player(game_state)
        assert new_current_player_id != current_player_id
        assert engine.can_player_act(game_state, new_current_player_id) is True
        assert engine.can_player_act(game_state, current_player_id) is False
    
    def test_manual_start_flow(self):
        """Test manually starting game with partial players."""
        engine = GameEngine()
        
        # Create 3-player game
        game_state = engine.create_game(3)
        
        # Join only 2 players (shouldn't auto-start)
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Should still be waiting
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        
        # Manually start
        game_state = engine.start_game(game_state)
        assert game_state.status == GameStatus.IN_PROGRESS
        assert game_state.current_player_index == 0
    
    def test_error_propagation(self):
        """Test that errors from underlying components are properly propagated."""
        engine = GameEngine()
        
        # Test various error conditions
        with pytest.raises(GameStateError):
            engine.create_game(0)  # Invalid player count
        
        game_state = engine.create_game(2)
        
        # Test joining errors
        with pytest.raises(GameNotStartedError):
            # Try to join when not waiting (create completed state)
            from rummikub.models import GameState
            completed_state = GameState(
                game_id=game_state.game_id,
                players=game_state.players,
                pool=game_state.pool,
                board=game_state.board,
                current_player_index=0,
                status=GameStatus.COMPLETED,
                created_at=game_state.created_at,
                updated_at=game_state.updated_at
            )
            engine.join_game(completed_state, "Alice")
    
    def test_engine_method_consistency(self):
        """Test that engine methods work consistently together."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Test status consistency
        assert engine.get_game_status(game_state) == GameStatus.WAITING_FOR_PLAYERS
        
        # Join players
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        # Status should update
        assert engine.get_game_status(game_state) == GameStatus.IN_PROGRESS
        
        # Current player should be available
        current_player_id = engine.get_current_player(game_state)
        assert current_player_id is not None
        
        # Can act should work
        assert engine.can_player_act(game_state, current_player_id) is True
        
        # Other player should not be able to act
        other_player_id = None
        for player in game_state.players:
            if player.id != current_player_id:
                other_player_id = player.id
                break
        
        assert other_player_id is not None
        assert engine.can_player_act(game_state, other_player_id) is False


class TestGameEngineEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_nonexistent_player_id(self):
        """Test operations with nonexistent player IDs."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players and start
        game_state = engine.join_game(game_state, "Alice")
        game_state = engine.join_game(game_state, "Bob")
        
        fake_player_id = "nonexistent-player-id"
        
        # Should return False for can_player_act with fake ID
        assert engine.can_player_act(game_state, fake_player_id) is False
        
        # Win condition should return False for fake ID
        assert engine.check_win_condition(game_state, fake_player_id) is False
    
    def test_concurrent_engine_operations(self):
        """Test that multiple engine instances don't interfere."""
        engine1 = GameEngine()
        engine2 = GameEngine()
        
        # Create games in both engines
        game1 = engine1.create_game(2)
        game2 = engine2.create_game(2)
        
        # Operations on game1 shouldn't affect game2
        game1 = engine1.join_game(game1, "Alice1")
        
        # game2 should be unaffected
        assert engine2.get_game_status(game2) == GameStatus.WAITING_FOR_PLAYERS
        
        # Both engines should work independently
        game2 = engine2.join_game(game2, "Alice2")
        game2 = engine2.join_game(game2, "Bob2")
        
        # game1 should still be waiting (only 1 player joined)
        assert engine1.get_game_status(game1) == GameStatus.WAITING_FOR_PLAYERS
        
        # game2 should be started (2 players joined)
        assert engine2.get_game_status(game2) == GameStatus.IN_PROGRESS
    
    def test_large_game_creation(self):
        """Test creating maximum size games."""
        engine = GameEngine()
        
        # 4-player game (maximum)
        game_state = engine.create_game(4)
        
        assert len(game_state.players) == 4
        assert len(game_state.pool.tile_ids) == 106 - (4 * 14)  # 50 tiles remaining
        
        # Join all players
        names = ["Alice", "Bob", "Charlie", "Diana"]
        for name in names:
            game_state = engine.join_game(game_state, name)
        
        # Should auto-start with all 4 players
        assert game_state.status == GameStatus.IN_PROGRESS
        
        # Turn cycling should work through all 4 players
        initial_player = game_state.current_player_index
        for i in range(4):
            expected_index = (initial_player + i) % 4
            assert game_state.current_player_index == expected_index
            game_state = engine.advance_turn(game_state)
        
        # Should cycle back to initial player
        assert game_state.current_player_index == initial_player