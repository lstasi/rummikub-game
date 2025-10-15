"""Game name generator for creating friendly, memorable game names."""

import random
from typing import Literal


ThemeType = Literal["fantasy", "scifi", "classic"]


class GameNameGenerator:
    """Generate friendly game names in various themes."""
    
    # Fantasy theme
    FANTASY_ACTIONS = ["Siege", "Defense", "Quest", "Trial", "Fall", "Reckoning"]
    FANTASY_PREPOSITIONS = ["of", "at", "for"]
    FANTASY_LOCATIONS = [
        "Gondor",
        "the Black Forest",
        "Dragon's Peak",
        "Ironhold",
        "the Whispering Caves",
    ]
    
    # Sci-fi theme
    SCIFI_ACTIONS = ["Incursion", "Blockade", "Extraction", "Breach", "Containment"]
    SCIFI_PREPOSITIONS = ["on", "at", "of"]
    SCIFI_LOCATIONS = [
        "Mars",
        "Sector 7G",
        "the Orion Nebula",
        "Titan Station",
        "Alpha Centauri",
    ]
    
    # Classic theme (inspired by original example)
    CLASSIC_ACTIONS = [
        "Battle",
        "Challenge",
        "Siege",
        "Quest",
        "War",
        "Conquest",
        "Showdown",
        "Rumble",
        "Uprising",
        "Defense",
        "Gambit",
        "Trial",
        "Clash",
        "Tournament",
        "Race",
    ]
    CLASSIC_PREPOSITIONS = ["of", "in", "at", "for"]
    CLASSIC_LOCATIONS = [
        "Barcelona",
        "Madrid",
        "Seville",
        "Tokyo",
        "Cairo",
        "London",
        "Moscow",
        "Berlin",
        "Brazil",
        "Egypt",
        "Japan",
        "New York",
    ]
    
    @classmethod
    def generate(cls, theme: ThemeType = "fantasy") -> str:
        """Generate a game name in the specified theme.
        
        Args:
            theme: Theme to use for name generation (fantasy, scifi, or classic)
            
        Returns:
            A generated game name in format: "[Action] [Preposition] [Location]"
            
        Raises:
            ValueError: If theme is not one of the supported types
        """
        if theme == "fantasy":
            actions = cls.FANTASY_ACTIONS
            prepositions = cls.FANTASY_PREPOSITIONS
            locations = cls.FANTASY_LOCATIONS
        elif theme == "scifi":
            actions = cls.SCIFI_ACTIONS
            prepositions = cls.SCIFI_PREPOSITIONS
            locations = cls.SCIFI_LOCATIONS
        elif theme == "classic":
            actions = cls.CLASSIC_ACTIONS
            prepositions = cls.CLASSIC_PREPOSITIONS
            locations = cls.CLASSIC_LOCATIONS
        else:
            raise ValueError(f"Unsupported theme: {theme}. Must be 'fantasy', 'scifi', or 'classic'")
        
        chosen_action = random.choice(actions)
        chosen_prep = random.choice(prepositions)
        chosen_location = random.choice(locations)
        
        return f"{chosen_action} {chosen_prep} {chosen_location}"
