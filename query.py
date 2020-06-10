import json
from mongo_connect import LadderPlayer, LadderKill, Loadout, LadderMatch
from mongoengine.errors import DoesNotExist
def number_of_players():
    return LadderPlayer.objects.count()

def upsert_player(player_dict):
    '''
    Upserts a player into the database

    Keyword arguments:
    player_dict -- The dictionary containing the player dict. See rcon example to see what the dict keywords are
    '''

    # Attempt to find the user in the database
    new_player = LadderPlayer.objects(
        platform = player_dict['Store'],
        platform_id = player_dict['Profile']
    ).first()
    if new_player is not None:
        # Return the found user if it was found successfully
        return new_player
    else:
        if 'ClanTag' in player_dict:
        # Register a new user
            return LadderPlayer(
                name = player_dict['Name'],
                platform = player_dict['Store'],
                platform_id = player_dict['Profile'],
                clan_tag = player_dict['ClanTag'],
                clan_id = player_dict['ClanID'],
                ranking = number_of_players() + 1
            )
        else:
            return LadderPlayer(
                name = player_dict['Name'],
                platform = player_dict['Store'],
                platform_id = player_dict['Profile'],
                clan_tag = "unknown",
                clan_id = "unknown",
                ranking = number_of_players() + 1
            )


def perform_elo_adjustment(killer_elo, victim_elo):
    k = 32
    """Performs an elo adjustment as well as updating the database"""
    killer_prob = (1.0 / (1.0 + pow(10, ((victim_elo-killer_elo) / 400))))
    victim_prob = (1.0 / (1.0 + pow(10, ((killer_elo-victim_elo) / 400))))
    killer_adjust = int(k) * (1 - killer_prob)
    victim_adjust = int(k) * victim_prob
    killer_new_elo = killer_elo + killer_adjust
    victim_new_elo = victim_elo - victim_adjust
    
    return [killer_new_elo, victim_new_elo]


def insert_player_loadout(player_spawn_dict : dict):
    # print(player_spawn_dict)
    # import pdb; pdb.set_trace()
    return Loadout(
        primary = player_spawn_dict['Weap1'],
        secondary = player_spawn_dict['Weap2'],
        equipment = player_spawn_dict['Equip'],
    )


def insert_ladder_kill_helper(kill_dict, killer, killer_loadout, victim, victim_loadout):
    print(killer.elo, victim.elo)
    adjustment = perform_elo_adjustment(killer.elo, victim.elo)
    killer_new_rating = adjustment[0]
    victim_new_rating = adjustment[1]
    lk = LadderKill(
        victim = victim,
        killer = killer,
        victim_loadout = victim_loadout,
        killer_loadout = killer_loadout,
        killer_location =  kill_dict["KillerX"] + "," + kill_dict["KillerY"] if "KillerX" in kill_dict else "unknown",
        victim_location = kill_dict["VictimX"] + "," + kill_dict["VictimY"],
        weapon_used = kill_dict["KillerWeapon"],
        killer_elo = killer_new_rating,
        victim_elo = victim_new_rating,
    )
    lk.save()
    return lk

def insert_ladder_kill(kill_dict, current_match):
    '''
    Inserts a kill into the database

    Keyword arguments:
    kill_dict -- The dictionary containing the kill dict. See rcon example to see what the dict keywords are
    '''
    
    killer = None
    victim = None
    if current_match.player_one.p_id == kill_dict['KillerID']:
        # import pdb; pdb.set_trace()
        killer = current_match.player_one
        victim = current_match.player_two
    elif current_match.player_two.p_id == kill_dict['KillerID']:
        killer = current_match.player_two
        victim = current_match.player_one
    if killer is not None and victim is not None:
        lk = insert_ladder_kill_helper(kill_dict, 
            killer.document,
            killer.loadout,
            victim.document,
            victim.loadout
        )
        # import pdb; pdb.set_trace()
        killer.document.elo=lk.killer_elo
        victim.document.elo=lk.victim_elo
        killer.document.save()
        victim.document.save()
        return lk

def find_by_id(platform_id : str):
    try:
        return LadderPlayer.objects.get(platform_id = platform_id)
    except DoesNotExist:
        return None

    