from mongoengine import connect
from parseconfigs import uri
import datetime

connect(host = uri, db="bmdb")

from mongoengine import *


# Ladder player created when the player first joins the 1v1 server
class LadderPlayer(Document):
    name = StringField(max_length=50, required=True)
    platform = IntField(required=True)
    platform_id = StringField(max_length=50, required=True)
    date_created = DateTimeField(default = datetime.datetime.utcnow)
    wins = IntField(default = 0)
    losses = IntField(default = 0)
    draws = IntField(default = 0)
    elo = FloatField(default = 1000.0)
    ip = StringField()
    clan_tag = StringField()
    clan_id = StringField()
    ranking = IntField(required=True)

# Ladder match is an object that is created when a 1v1 has ceased
class LadderMatch(Document):
    map_name = StringField()
    winner = ReferenceField("LadderPlayer")
    loser = ReferenceField("LadderPlayer")
    drawn = BooleanField(required=True)
    winner_score = IntField(required = True)
    loser_score = IntField(required = True)

# Class created when a player spawns in with a loadout
class Loadout(Document):
    primary = IntField(required=True)
    secondary = IntField(required=True)
    equipment = IntField(required=True)


# Kills on the ladder represented by this class
class LadderKill(Document):
    victim = ReferenceField('LadderPlayer', required=True)
    killer = ReferenceField('LadderPlayer', required=True)
    victim_loadout = ReferenceField("Loadout")
    killer_loadout = ReferenceField("Loadout")
    victim_location = StringField()
    killer_location = StringField()
    weapon_used = StringField(required=True)
    killer_elo = FloatField(required=True)
    victim_elo = FloatField(required=True)
    match = ReferenceField('LadderMatch')