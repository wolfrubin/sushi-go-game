from collections import namedtuple


SuGoRequest = namedtuple('SuGoRequest',
    ['protocol', 'action_type', 'game_name', 'player', 'body']
)

SuGoResponse = namedtuple('SuGoRequest',
    ['protocol', 'action_type', 'game_name', 'player', 'status', 'body']
)
