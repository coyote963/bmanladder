# import the enum type for rcon events
from rcontypes import rcon_event, rcon_receive
# import json parsing to translate server messages into JSON type
import json
from helpers import send_request, send_packet, execute_webhook
from query import upsert_player, insert_ladder_kill, insert_player_loadout, find_by_id
from current_match import CurrentMatch, PlayerData
from parseconfigs import webhook_url
ladder_kills = []
# A bounceback rcon handler for when the rcon connects
# It calls for the match info when the rcon connects
def handle_connect(event_id, message_string, sock, current_match):
    if event_id == rcon_event.rcon_logged_in.value:
        send_request(sock, "initial", "initial", rcon_receive.request_match.value)

# A handler for when the request match packet returns
def handle_rcon_connect(event_id, message_string, sock, current_match):
    if event_id == rcon_event.request_data.value:
        js = json.loads(message_string)
        if int(js['CaseID']) == rcon_receive.request_match.value and js['RequestID'] == "initial":
            current_match = CurrentMatch(js['Map'])
            if int(js['Team1Score']) != 0 or int(js['Team2Score']) != 0:
                # Reset the score if it is not both zero
                send_packet(sock, "restartmap", rcon_receive.command.value)


# A bounceback rcon handler for when a player joins
# It calls for the player dict whenever a player joins, but does nothing else
def handle_player_spawn(event_id, message_string, sock, current_match):
    # if passed in event_id is a chat_message
    if event_id == rcon_event.player_spawn.value:
        js = json.loads(message_string)
        if current_match is not None:
            current_match.set_loadout(js)
            send_request(sock, "coyote", js['PlayerID'], rcon_receive.request_player.value)


# A catching rcon handler for when a player information is returned from the rcon
# It sets the current match's corresponding player with the new data.
def handle_request_player(event_id, message_string, sock, current_match):
    if event_id == rcon_event.request_data.value:
        js = json.loads(message_string)
        if int(js['CaseID']) == rcon_receive.request_player.value:
            player = upsert_player(js)
            player.save()
            new_player = PlayerData(player, js['ID'], js['Team'], js['Name'])
            if js['Team'] == '1':
                current_match.player_one = new_player
            else:
                current_match.player_two = new_player

# A rcon handler for when a kill occurs
def handle_death(event_id, message_string, sock, current_match):
    if event_id == rcon_event.player_death.value:
        js = json.loads(message_string)
        # if int(js['VictimID']) > 0 and int(js['KillerID']) > 0:
        if current_match.player_one is not None and current_match.player_two is not None:
            ladder_kill = insert_ladder_kill(js, current_match)
            if ladder_kill is not None:
                ladder_kills.append(ladder_kill)
# A rcon handler for when a round ends
def handle_round_end(event_id, message_string, sock, current_match):
    if event_id == rcon_event.tdm_round_end.value and current_match.player_one is not None:
        js = json.loads(message_string)
        if current_match.player_one.team == "1":
            current_match.player_one.score = int(js['Score1'])
            current_match.player_two.score = int(js['Score2'])
        else:
            current_match.player_one.score = int(js['Score2'])
            current_match.player_two.score = int(js['Score1'])

# A rcon handler for a chat message
# This will handle the debug for when a client types !debug in chat
def handle_debug_chat(event_id, message_string, sock, current_match):
    if event_id == rcon_event.chat_message.value:
        js = json.loads(message_string)
        if js['Message'].startswith("!debug") and ('coyote' in js['Name'] or 'nemo' in js['Name']):
            message = current_match.to_str()
            message += "current match: " + str(current_match)
            send_packet(sock, 'rawsay "{}" "{}"'.format(message, "8421376"), rcon_receive.command.value)


def handle_game_over(event_id, message_string, sock, current_match):
    if event_id == rcon_event.match_end.value:
        if current_match is not None and current_match.player_one is not None and current_match.player_two is not None:
            # Handle updating the database with the new match value
            match_document = current_match.save_match()
            if match_document is not None:
                # import p  db;pdb.set_trace()
                for lk in ladder_kills:
                    lk.match = match_document
                    lk.save()
                ladder_kills.clear()
                current_match.update_rankings()

def handle_get_names(event_id, message_string, sock, current_match):
    if event_id == rcon_event.chat_message.value:
        js = json.loads(message_string)
        if js['Message'].startswith("!names"):
            message = ""
            if current_match.player_one is not None:
                message += current_match.player_one.document.name
            else:
                message += "player one has no name. "

            if current_match.player_two is not None:
                message += current_match.player_two.document.name
            else:
                message += "player two has no name. "

            send_packet(sock, 'rawsay "{}" "{}"'.format(message, "8421376"), rcon_receive.command.value)

def handle_request_rating(event_id, message_string, sock, current_match):
    if event_id == rcon_event.chat_message.value and current_match is not None:
        js = json.loads(message_string)
        print(js)
        if js['Message'].startswith('!elo'):
            print("hello world")
            message = ""
            if js['PlayerID'] == current_match.player_one.p_id:
                message = current_match.player_one.document.elo
            elif js['PlayerID'] == current_match.player_two.p_id:
                message = current_match.player_two.document.elo
            else:
                message = "Could not get elo"
            send_packet(sock, 'rawsay "{}" "{}"'.format(message, "8421376"), rcon_receive.command.value)

def handle_player_connect_webhook(event_id, message_string, sock, current_match):
    if event_id == rcon_event.player_connect.value:
        js = json.loads(message_string)
        message = "`{}` just connected to a ladder server! ".format(js['PlayerName'])
        
        player = find_by_id(js['Profile'])
        if player is not None:
            message += "`[{} elo]`".format(round(player.elo))
        execute_webhook(message, webhook_url)

example_functions  = [
    handle_connect,
    handle_rcon_connect,
    handle_player_spawn,
    handle_request_player,
    handle_death,
    handle_round_end,
    handle_debug_chat,
    handle_game_over,
    handle_get_names,
    handle_request_rating,
    handle_player_connect_webhook
]