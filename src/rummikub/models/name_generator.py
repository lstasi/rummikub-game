"""Game name generator for creating friendly, memorable game names."""

import random


class GameNameGenerator:
    """Generate friendly game names by combining all themes."""
    
    # Merged actions from all themes
    ACTIONS = [
        # Fantasy
        "Siege",
        "Defense",
        "Quest",
        "Trial",
        "Fall",
        "Reckoning",
        # Sci-fi
        "Incursion",
        "Blockade",
        "Extraction",
        "Breach",
        "Containment",
        # Classic
        "Battle",
        "Challenge",
        "War",
        "Conquest",
        "Showdown",
        "Rumble",
        "Uprising",
        "Gambit",
        "Clash",
        "Tournament",
        "Race",
    ]
    
    # Merged prepositions from all themes (removing duplicates)
    PREPOSITIONS = ["of", "at", "for", "on", "in"]
    
    # Merged locations from all themes
    LOCATIONS = [
        # Fantasy
        "Gondor",
        "the Black Forest",
        "Dragon's Peak",
        "Ironhold",
        "the Whispering Caves",
        # Sci-fi
        "Mars",
        "Sector 7G",
        "the Orion Nebula",
        "Titan Station",
        "Alpha Centauri",
        # Classic
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
    def generate(cls) -> str:
        """Generate a game name.
        
        Returns:
            A generated game name in format: "[Action] [Preposition] [Location]"
        """
        chosen_action = random.choice(cls.ACTIONS)
        chosen_prep = random.choice(cls.PREPOSITIONS)
        chosen_location = random.choice(cls.LOCATIONS)
        
        return f"{chosen_action} {chosen_prep} {chosen_location}"
