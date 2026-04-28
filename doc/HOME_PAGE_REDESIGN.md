# Home Page Redesign

## Status

Implemented.

## Current Home-Page Behavior

The home page now acts as the single entry point for game discovery and creation.

Implemented features:
- Quick-create form with 2 to 4 player selection
- My Games list
- Available Games list filtered to `waiting_for_players`
- Direct join from available-game cards
- Resume navigation for joined games
- Delete action from the home page
- 5-second polling refresh for both lists

Related API behavior that supports the redesign:
- `GET /games/my-games`
- `GET /games?status=waiting_for_players`
- `POST /games` auto-joins the creator

## Files Involved

- `static/pages/home.html`
- `static/js/home.js`
- `static/css/main.css`
- `src/rummikub/api/main.py`

## What Was Removed

The redesign made separate create and join pages unnecessary. The current root app only routes to:
- `home`
- `game`
- `win`

## Follow-Up Gaps

The redesign shipped, but a few polish items remain:
- Home cards try to render `current_player_name`, which the API does not provide.
- The player-info banner exists in the markup but is not wired up in JavaScript.
- Translation coverage for the redesigned home-page text is incomplete.

These follow-ups are tracked in `doc/CODE_REVIEW.md` and `TODO.md`.
4. ✅ Can create and join game from home page directly
5. ✅ Can join available game from home page directly
6. ✅ Can resume my games from home page
7. ✅ No broken navigation or references
8. ✅ All tests passing
9. ✅ Quality gates passing (ruff, mypy)
10. ✅ Documentation updated

## Rollback Plan

If issues arise:
1. Git revert commits in reverse order
2. Restore create.html and join.html from git history
3. Restore create.js and join.js from git history
4. Restore main.py page routing
5. Revert API endpoint changes
6. Run tests to verify rollback

## Timeline Estimate

- Phase 1 (Backend): ~2-3 commits, 30-45 minutes
- Phase 2 (Frontend): ~3-4 commits, 45-60 minutes
- Phase 3 (Remove pages): ~1 commit, 10 minutes
- Phase 4 (Navigation): ~1 commit, 15 minutes
- Phase 5 (Testing): ~1-2 commits, 30 minutes
- Phase 6 (Cleanup): ~1 commit, 15 minutes

**Total**: ~8-12 commits, ~2.5-3 hours

## References

- Current Basic Auth implementation: See commits 7f9fdac, 75a5977, 6d8bcbf, 1c46f5e
- GameService interface: `src/rummikub/service/`
- API models: `src/rummikub/api/models.py`
- Current home page: `static/pages/home.html`, `static/js/home.js`
