class SuGoError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class GameDoesNotExistError(SuGoError):

    def __init__(self, game_name):
        self.message = f"Game named \"{game_name}\" does not exist. Please create one."


class GameAlreadyExistsError(SuGoError):
    
    def __init__(self, game_name):
        self.message = f"Game named \"{game_name}\" already exists"


class GameInProgressError(SuGoError):
    
    def __init__(self, game_name):
        self.message = f"Game named \"{game_name}\" already in progress"


class PlayerAlreadyJoinedError(SuGoError):
    
    def __init__(self, game_name, player_name):
        self.message = f"Game named \"{game_name}\" already has player named \"{player_name}\""
