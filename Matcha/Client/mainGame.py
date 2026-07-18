import lib
import time

def lobby_wait():
    print('Waiting for game to start')
    current_players = []
    print(lib.lobby_state())
    while lib.lobby_state():
        for player in lib.lobby_state()['players']:
            if player not in current_players:
                print(f'{player} is waiting in the Lobby')
                current_players.append(player)
        time.sleep(1)
        # Ausgabe wenn ein neuer Spieler beitritt
    print('Game has started')

def main_loop():
    username = lib.get_username()
    players = lib.get_players()
    game_state = lib.gameState(players)
    role = lib.get_role()
    print(f"You are {username} and your role is {role}\nThe following players are in your lobby:/n{players}")
    moves = 0
    while True:
        for move in lib.get_state(moves):
            moves += 1
            game_state.update(move)
            print(f"New announcement: {game_state.current_announcements[-1]}")
            print(game_state.active_player)
            print(game_state.current_round)
            print(game_state.traps)
            print(game_state.treasures)
 
        if game_state.winner:
            print(f"Winner: {game_state.winner}")
            break
        if game_state.active_player == username:
            if game_state.game_phase == "choosing":
                lib.choose(input("Input the Player you want to uncover a card from:\n"))
            else:
                role = input("Which role do you want to announce?\n")
                treasures = int(input("How many treasures do you claim to have?"))
                traps = int(input("How many traps do you claim to have?"))
                lib.announce(role, treasures, traps)
        time.sleep(1)

action = int(input('Gib eine 1 ein, um einer Lobby beizutreten\neine 2, um eine Lobby zu erstellen\nund eine 3, um ein Probespiel zu starten.\n'))
if action == 1:
    print(lib.list_lobbies())
    if lib.join_lobby(input('Which Lobby would you like to join?')):
        print('Joined sucessfully')
        lobby_wait()
    else:
        print('Lobby not found, too bad')
elif action == 2:
    if lib.create_lobby(int(input('How many players do you want to be in your game?'))):
        print('Lobby created sucessfully')
        lobby_wait()
    else:
        print('Invalid player count')
elif action == 3:
    lib.create_example_game(int(input('How many Players should be in this example game?\n')))
else:
    print('Invalid Input')

main_loop()