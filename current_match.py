from mongo_connect import LadderMatch
from query import insert_player_loadout

class PlayerData:
    document = None
    p_id = None
    team = None
    loadout = None
    score = 0
    name = ""
    def __init__(self, document, p_id, team, name, loadout = None, score = 0):
        '''Creates a new player data instance'''
        self.document = document
        self.p_id = p_id
        self.team = team
        self.loadout = loadout
        self.score = score
        self.name = name

    def to_str(self):
        '''returns a string representation of the player'''
        return_str = "player: " + self.document
        return_str += "\n" + "p_id: " + self.p_id
        return_str += "\n" + "team: " + self.team
        return_str += "\n" + "loadout: " + self.loadout
        return return_str

class CurrentMatch:
    player_one = None
    player_two = None
    map_name = ""

    def __init__(self, map_name):
        '''Initializes an empty match

        Keyword arguments:
        map_name -- Name of the current match
        '''
        self.map_name = map_name

    def set_score(self, p_id, score):
        '''Updates the score of a player'''
        if int(p_id) == self.player_one.p_id:
            self.player_one.score = score
        if int(p_id) == self.player_two.p_id:
            self.player_two.score = score

    def save_match(self):
        '''Saves the current match to database

        Keyword arguments:
        self - The current match object
        '''
        match = None
        if self.player_one.score > self.player_two.score:
            match = LadderMatch(
                map_name = self.map_name,
                winner = self.player_one.document,
                loser = self.player_two.document,
                drawn = False,
                winner_score = self.player_one.score,
                loser_score = self.player_two.score
            )
        elif self.player_two.score > self.player_one.score:
            match =  LadderMatch(
                map_name = self.map_name,
                winner = self.player_two.document,
                loser = self.player_one.document,
                drawn = False,
                winner_score = self.player_two.score,
                loser_score = self.player_one.score
            )
        if match is not None:
            match.save()
            return match

    def update_rankings(self):
        if self.player_one.score > self.player_two.score:
            winner = self.player_one.document
            loser = self.player_two.document
        elif self.player_two.score > self.player_one.score:
            winner = self.player_two.document
            loser = self.player_one.document

        if winner.ranking > loser.ranking:
            temp = winner.ranking
            winner.ranking = loser.ranking
            loser.ranking = temp
            winner.save()
            loser.save()


    def set_loadout(self, player_spawn_dict : dict):
        loadout = insert_player_loadout(player_spawn_dict)
        loadout.save()
        if self.player_one and int(player_spawn_dict['PlayerID']) == self.player_one.p_id:
            self.player_one.loadout = loadout
        if self.player_two and int(player_spawn_dict['PlayerID']) == self.player_two.p_id:
            self.player_two.loadout = loadout

    def to_str(self):
        return_str = "p1: " + str(self.player_one)
        return_str += "p2: " + str(self.player_two)
        return return_str

        