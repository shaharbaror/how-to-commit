#NAMES AND MEMES
#phase is where the looby si rn, for examle phase zero is firstpage

import json
import time
import os
from random import randint

from Protocol import Protocol
from mememaker import MemeMaker


ERR_EXCEPTIONS = ["makeuser.html", "makeuser.css", "makeuser","makeuser.js", "favicon.ico", "favicon.png"]
# If the header contains "index" in it then go to this function
def index_functions(header, body, player_ip):
    ip = player_ip
    print(ip)
    body = body.split("\n")

    username = body[0]
    if len(username) > 11:
        username = username[:10]

    action = header[1].split("?")[-1]

    print(action)
    if action == "a=c":

        # create a new lobby for players

        with open("lobbies.json", "r") as f:
            lobbies = json.load(f)
            lobby = Protocol.generate_lobby_name()
            print("goes")

            while lobby in lobbies:
                lobby = Protocol.generate_lobby_name()

            print("generated:" + lobby)

            lobbies[lobby] = Protocol.new_lobby(username, ip)

        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)

        print(Protocol.create_msg(f"{lobby}".encode(), "text/txt"))
        return Protocol.create_msg(f"{lobby}".encode(), "text/txt")
    # add a player to a lobby he chose to join
    if "a=j" in action:
        lobby = header[1].split("/")[0]

        with open("lobbies.json", "r") as f:
            lobbies = json.load(f)
            lobbies[lobby] = Protocol.add_player(username, ip, lobbies[lobby])

        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)
        msg = lobby.encode()
        msg += b"\n" + Protocol.get_phase(lobbies[lobby]["phase"]).encode()

        return Protocol.create_msg(msg, "text/txt")
    return b""


# if the header contains "firstpage" in it then go to this function
def first_page_functions(header, body, ip):
    lobby_name = header[1].split("/")[0]
    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
    lobby = lobbies[lobby_name]

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if not lobby["phase"] == 1:
        msg = "{" + f'"send":"{Protocol.get_phase(lobby["phase"])}"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")

    if "s=t" in header[1]:

        # submit the meme into the right lobby

        meme = json.loads(body)
        inactive = True
        cou = 0
        for i in meme["captions"]:
            print(cou)
            cou += 1
            print(i)
            if not (i == "Caption 1" or i == "Caption 2"):
                inactive = False
        print(inactive)
        if inactive:
            lobby = Protocol.remove_player(ip, lobby)
            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
            return Protocol.create_msg(b"inactive", "text/txt")
        player_index = lobby["players_ip"].index(ip)
        lobby["finished"][player_index] = True
        meme["creator"] = player_index
        for i in range(len(meme["captions"])):
            if len(meme["captions"][i]) > 250:
                meme["captions"][i] = meme["captions"][i][:249]
        lobby["memes_this_round"].append(meme)
        lobbies[lobby_name] = lobby

        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)
        return Protocol.create_msg(b"done", "text/txt")

    else:
        if "a=startgame" in header[1]:

            # send the user all the required data for sarting the meme

            rnd = randint(1, 8)

            roll_amount = 5

            player_index = lobby["players_ip"].index(ip)



            print(lobby["remaining_rolls"][player_index])
            print(player_index)

            # if a player already has used up all of his rolls, and he refreshes then just get him his meme back
            if lobby["started"][player_index]:
                msg = Protocol.update_json(lobby["players_meme"][player_index])
                print(msg)
                dones = 0
                for i in lobby["finished"]:
                    if i:
                        dones += 1
                msg += (f', "time": {int(lobby["round_timer"] - time.time())}, "done":"{dones}/{len(lobby["finished"])} are done"' + "}").encode()
                print(msg)
                return Protocol.create_msg(msg, "text/json")
            lobby["remaining_rolls"][player_index] = roll_amount
            lobby["started"][player_index] = True
            lobby["players_meme"][player_index] = rnd
            #lobby["phase"] = 0 #need to change how this works
            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)

            msg = Protocol.update_json(rnd)
            msg += (f', "time":{int(lobby["round_timer"] - time.time())}' + "}").encode()
            print(msg)
            return Protocol.create_msg(msg, "text/json")

        if "a=newmeme" in header[1]:

            rnd = randint(1, 8)
            print("got there")

            players_index = lobby["players_ip"].index(ip)
            for i in range(len(lobby["players_ip"])):
                print(lobby["players_ip"][i])

                if lobby["players_ip"][i] == ip:
                    if lobby["remaining_rolls"][i] >= 1:
                        lobby["remaining_rolls"][i] -= 1
                        lobby["players_meme"][i] = rnd
                        print(lobby["remaining_rolls"][i])
                        new_meme = Protocol.update_json(rnd)
                        new_meme += "}".encode()
                        lobbies[lobby_name] = lobby
                        with open("lobbies.json", "w") as f:
                            json.dump(lobbies, f)
                        print(new_meme)
                        return Protocol.create_msg(new_meme, "text/json")
                    else:
                        return Protocol.create_msg('{"is_ok":false}'.encode(), "text/json")

        if "a=gettime" in header[1]:
            timer = str(int(lobby["round_timer"] - time.time()))
            dones = 0
            for i in lobby["finished"]:
                if i:
                    dones += 1
            respond = ("{" + f'''
                "time":{timer},
                "done":"{dones}/{len(lobby["finished"])} are done"
            ''' + "}").encode()

            return Protocol.create_msg(respond, "text/json")
    return b""


def ratememe_functions(header,body, ip):
    lobby_name = header[1].split("/")[0]
    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
        lobby = lobbies[lobby_name]

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if not lobby["phase"] == 3:
        msg = "{" + f'"send":"{Protocol.get_phase(lobby["phase"])}"' + "}"
        return Protocol.create_msg(msg.encode(),"text/json")

    if "a=getmeme" in header[1]:
        if len(lobby["memes_this_round"]) == 0:
            lobbies.pop(lobby_name)
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
                return b""
        if "score" not in lobby["memes_this_round"][0]:

            lobby["memes_this_round"].append(lobby["memes_this_round"][0])
            lobby["memes_this_round"][-1]["score"] = 0
            lobby["memes_this_round"].pop(0)

            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
            msg = Protocol.prepare_meme(lobby["memes_this_round"][0], -1)
        else:
            msg = b'{"hasnext":true}'
            lobby["phase"] += 1
            lobby["round_timer"] = time.time() + 30
            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
            # if the players are done with rating all of the memes this round
        return Protocol.create_msg(msg, "text/json")

    if "a=rated" in header[1]:
        rating = header[1][-1]
        print(rating)

        if rating == "1":
            lobby["memes_this_round"][-1]["score"] -= 1
            lobby["score"][lobby["memes_this_round"][-1]["creator"]] -= 1
        elif rating == "2":
            lobby["memes_this_round"][-1]["score"] += 1
            lobby["score"][lobby["memes_this_round"][-1]["creator"]] += 1

        elif rating == "3":
            lobby["memes_this_round"][-1]["score"] += 1.5
            lobby["score"][lobby["memes_this_round"][-1]["creator"]] += 1.5
        lobbies[lobby_name] = lobby
        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)
        return Protocol.create_msg("done".encode(), "text/txt")
    # If player needs the first meme get them the first meme, after everyone done voting: get the meme to the all_time_meme zone and update the player's score
    return b""


def waiting_functions(header, body, ip, lobbies):
    lobby_name = header[1].split("/")[0]
    lobby = lobbies[lobby_name]

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg.encode(),"text/json")

    if "a=gettime" in header[1]:
        msg = "{" + f'"time":{int(lobby["round_timer"]- time.time())}' + "}"
        print(time.time())
        print(lobby["round_timer"])
        return Protocol.create_msg(msg.encode(), "text/json")

    if "a=setup" in header[1]:
        msg = "{" + f'"time":{int(lobby["round_timer"] - time.time())}' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")

    if "a=rate" in header[1]:
        if lobby["round_timer"] < time.time() or False not in lobby["finished"]:
            lobby["phase"] = 3
            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
            return Protocol.create_msg(b"ok","text/txt")
        #MAKE SURE THAT ALL THE PLAYERS FINISHED THE ROUND OR THE TIME IS ZERO
    return b""


def show_meme_functions(header, body, ip):
    lobby_name = header[1].split("/")[0]
    print(header)
    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
        lobby = lobbies[lobby_name]

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg. encode(), "text/json")
    if not lobby["phase"] == 4:
        print("FSDFSDL:FSADF")
        print(Protocol.get_phase(lobby["phase"]))
        msg = "{" + f'"send":"{Protocol.get_phase(lobby["phase"])}"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")

    print("herer")
    if "a=getalldata" in header[1]:
        print("here")
        msg = Protocol.show_all_memes(lobby)
        print(msg)
        return Protocol.create_msg(msg.encode(), "text/json")
    if "a=gettime" in header[1]:
        msg = "{" + f'\"time\":{int(lobby["round_timer"]- time.time())}' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if "a=nextphase" in header[1]:
        if lobby["round_timer"] < time.time():
            if lobby["round"] >= lobby["rounds"]:
                lobby = Protocol.add_memes(lobby)
                lobby["phase"] = 5
                lobbies[lobby_name] = lobby
                msg = Protocol.get_phase(5)
                print(msg)
            else:
                lobby["round"] += 1
                lobby = Protocol.add_memes(lobby)
                lobby = Protocol.reset_stats_round(lobby)
                lobby["phase"] = 1
                lobby["round_timer"] = time.time() + lobby["time_per_meme"]
                lobbies[lobby_name] = lobby
                msg = Protocol.get_phase(lobby["phase"])
            msg = "{" + f'"send":"{msg}"' + "}"
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
            print(msg)
        else:
            msg = "{" + f'"time":{int(lobby["round_timer"] - time.time())}' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    return b""


def leaderboards_functions (header, body, ip):
    lobby_name = header[1].split("/")[0]
    print(header)
    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
        lobby = lobbies[lobby_name]

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if not lobby["phase"] == 5:
        print(Protocol.get_phase(lobby["phase"]))
        msg = "{" + f'"send":"{Protocol.get_phase(lobby["phase"])}"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    print("DFS")
    if "a=getallmemes" in header[1]:
        print("DFSDF")
        msg = Protocol.leaderboard_show(lobby)
        print(msg)
        return Protocol.create_msg(msg.encode(), "text/json")
    elif "a=gettime" in header[1]:
        if lobby["round_timer"] < time.time():
            lobby["phase"] = 0
            lobbies[lobby_name] = lobby
            with open("lobbies.json", "w") as f:
                json.dump(lobbies, f)
        msg = "{" + f'"time":{int(lobby["round_timer"] - time.time())}' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    elif "a=tolobby" in header[1]:
        lobby["phase"] = 0
        lobbies[lobby_name] = lobby
        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)
    return b""

def lobby_functions(header, body, ip):
    lobby_name = header[1].split("/")[0]
    print(header)
    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
        lobby = lobbies[lobby_name]
    player_index = lobby["players_ip"].index(ip)

    if ip not in lobby["players_ip"]:
        msg = "{" + f'"send":"makeuser.html"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if not lobby["phase"] == 0:
        print(Protocol.get_phase(lobby["phase"]))
        msg = "{" + f'"send":"{Protocol.get_phase(lobby["phase"])}"' + "}"
        return Protocol.create_msg(msg.encode(), "text/json")
    if "a=getusers" in header[1]:
        msg = Protocol.get_all_users(lobby, ip)
        return Protocol.create_msg(msg.encode(), "text/json")
    if "a=tolobby" and player_index == 0:
        lobby["phase"] = 1

        roll_amount = 5
        timer = 40  # need to make it so that the timer wont reset every time a player joins the game

        print("hello from the other")
        lobby["round_timer"] = int(time.time() + timer)

        lobbies[lobby_name] = lobby
        with open("lobbies.json", "w") as f:
            json.dump(lobbies, f)
        return Protocol.create_msg(b"ok", "text/txt")


def check_for_errors(header, body, ip):
    some_error = None
    lobby_name = header[1].split("/")[0]
    print(lobby_name)

    with open("lobbies.json", "r") as f:
        lobbies = json.load(f)
    print(ERR_EXCEPTIONS, lobby_name in ERR_EXCEPTIONS)
    if (lobby_name not in lobbies) and (lobby_name not in ERR_EXCEPTIONS):
        print("did")
        some_error = "404 not found"

    if some_error:
        msg = f'''
                <html>
                    <body>
                        <h1> {some_error} </h1>
                    </body>
                </html>
                '''.encode()
        return Protocol.create_msg(msg, "text/html")
    return b"ok"

class HandleResponse:

    @staticmethod
    def handle_request(request, ip):
        print("ehy")
        with open("lobbies.json", "r") as f:
            lobbies = json.load(f)
        header, body = Protocol.proces_request(request)
        print(f"handle_request {header}")

        header[1] = header[1][1:]

        # header: /firstpage/WHDSK?s=f&a=something

        # header: /index?a=c
        print(header)
        is_error = check_for_errors(header, body, ip[0])
        if not is_error == b"ok":
            print("errr")
            print(is_error)
            return is_error

        # get info about the file and its name

        #FFJDS/firstpage.html
        #MemeBank/meme01.png
        #makeuser/index?a=c
        file_name = header[1].split("/")
        if file_name[0] in lobbies:
            file_name = file_name[1:]
            file_name = "/".join(file_name)
        else:
            file_name = file_name[0]

        header_without_lobby = header[1].split("/")
        if len(header_without_lobby) > 2:
            header_without_lobby = header_without_lobby[1:]
        header_without_lobby = "/".join(header_without_lobby)
        print(file_name)

        # if the file is accessible then access and send it
        if os.path.isfile(file_name) or file_name == "":
            if file_name == "":
                file_name = "index.html"
            file_type = Protocol.get_file_type(file_name)

            with open(file_name, "rb") as f:
                f = f.read()
                msg = Protocol.create_msg(f, file_type)
                print(msg)
                return msg

        print(header_without_lobby)

        lobby_name = header[1].split("/")[0]


        res = b""
        # if the request is fetch then respond correctly
        if "makeuser" in header_without_lobby:
            print("ok")
            res = index_functions(header, body, ip[0])
        elif "firstpage" in header_without_lobby:
            print("here")
            res = first_page_functions(header, body, ip[0])
        elif "ratememe" in header_without_lobby:
            res = ratememe_functions(header, body, ip[0])
        elif "waitingpage" in header_without_lobby:
            res = waiting_functions(header, body, ip[0], lobbies)
        elif "showmeme" in header_without_lobby:
            print("h")
            res = show_meme_functions(header, body, ip[0])
        elif "leaderboards" in header_without_lobby:
            res = leaderboards_functions(header, body, ip[0])
        elif "lobby" in header_without_lobby:
            res = lobby_functions(header, body, ip[0])
        if not res == b"":
            return res

        msg = f'''
                        <html>
                            <body>
                                <h1> 404 page not found </h1>
                            </body>
                        </html>
                        '''.encode()
        return Protocol.create_msg(msg, "text/html")

