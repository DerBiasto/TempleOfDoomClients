import library

class Game_State:
    def __init__(self):
        self.move_number = 0
        self.players= library.get_players()
        self.active_player = self.players[0]
        self.treasures_found = 0
        self.traps_found = 0

    def update(self,move):
        self.update_move_number()
        self.update_active_player(move)
        self.update_traps(move)
        self.update_treasures(move)

   
    def update_move_number(self):
        self.move_number += 1


    def update_active_player(self, move):
        if "Choice" in move:
            self.active_player = move["Choice"][0]
        else:
            self.active_player = self.players[(self.players.index(self.active_player) +1)%len(self.players)]


    def update_treasures(self,move):
        if "Choice" in move:
            if move ["Choice"][1] == "Treasure":
                self.treasures_found += 1


    def update_traps(self,move):
        if "Choice" in move:
            if move ["Choice"][1] == "Trap":
                self.traps_found += 1