'''Main game file: creates and runs the game.'''
import sys                  # For closing the game
import os                   # For saving/loading and clearscreen
import random               # For randomness!
import math                 # To round up the floats
import json                 # For saving/loading
from pygame import mixer    # For music
import webbrowser           # For opening the rules page

# Title graphic
TITLE_GRAPHIC = ("""
 /$$$$$$$  /$$                     /$$                               /$$      
| $$__  $$| $$                    | $$                              | $$      
| $$  \ $$| $$  /$$$$$$   /$$$$$$$| $$   /$$ /$$  /$$$$$$   /$$$$$$$| $$   /$$
| $$$$$$$ | $$ |____  $$ /$$_____/| $$  /$$/|__/ |____  $$ /$$_____/| $$  /$$/
| $$__  $$| $$  /$$$$$$$| $$      | $$$$$$/  /$$  /$$$$$$$| $$      | $$$$$$/ 
| $$  \ $$| $$ /$$__  $$| $$      | $$_  $$ | $$ /$$__  $$| $$      | $$_  $$ 
| $$$$$$$/| $$|  $$$$$$$|  $$$$$$$| $$ \  $$| $$|  $$$$$$$|  $$$$$$$| $$ \  $$
|_______/ |__/ \_______/ \_______/|__/  \__/| $$ \_______/ \_______/|__/  \__/
                                       /$$  | $$               
                                      |  $$$$$$/                 by Sneezycat
                                       \______/                     2022-2023
""")
# Game related values
CARD_TYPES = ["A", 2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K"] # All the values a card can take
DEFAULT_SETTINGS = {
    "stacks":           2, # number of card stacks
    "num_decks":        6, # number of decks in each stack
    "players_human":    1, # number of human players
    "players_ai":       2, # number of CPU   players
    "blackjack_multiplier": 1.5,    # Payout multiplier on natural blackjack
    "starting_money":       100,    # Initial amount of money players/CPU has
    "minimum_bet":          2,     # Minimum amount to bet
    "maximum_bet":          500,    # Maximum amount to bet
    "names_human":  True,   # True to name human players (Default name: Player #)
    "names_ai":     True,   # True to name CPU   players (Default name: CPU #)
    "autoname":     True,   # True to name CPU players with names from file (names.txt)
    "detailed_scores": True,    # True to show round results on the score
    "autopause":    True,       # Pause at the end of CPU turns and
    "bgm_volume":   30,            # BGM Volume
    "CPU_difficulty":   "easy"  # CPU difficulty (easy or hard)
}
# Special thanks to ChatGPT, which gave me these names for a "high stakes blackjack tournament in a neo-noir spy film"
DEFAULT_CPU_NAMES = ["Victor Davenport", "Isabella Sinclair", "Maximilian St. Clair", "Gabrielle Duval", "Jonathan Beaumont", 
"Penelope Harrington", "Sebastian von Braun", "Arabella Kensington", "Xavier Moncrief", "Seraphina Rossi", "Alexander Whitaker",
"Celeste Van der Linde", "Hugo Belmont", "Genevieve Fontaine", "Lucas Sinclair", "Cordelia Beaumont", "Nicholas Ashford", 
"Vivienne Carmichael","Nathaniel Devereaux","Olivia Fontaine"]

### PLAYER CLASSES AND PLAYER FUNCTIONS #######
class Player:
    """For both CPU and human-controlled players."""
    def __init__(self, money, name):
        self.money      = money     # Amount of money a player currently has
        self.name       = name      # Name of a player
        self.bankruptcy  = False     # For determining if a player is still playing
        self.results    = []      # Store the results for each round
        self.hands      = [[]]      # Hands for each player (more than one if player splits pairs)
        self.hand_id    = 0         # Index for the hand the player is currently playing
        self.hand       = self.hands[self.hand_id] # The current hand for the player
        self.bet        = [0]         # Bet for current hand
    def check_bankrupcy(self):
        """Kick player if they don't have enough money to bet"""
        if self.money < settings["minimum_bet"] and not self.bankruptcy: 
            self.bankruptcy = True
            if isinstance(self, Human_Player) or settings["autopause"]:
                wait_for_player_input(f"{self.name} ran out of money! Better luck next time!\n")
            else:
                print(f"{self.name} ran out of money! Better luck next time!\n")
    def detailed_scores(self):
        _rounds_drawn = 0
        _rounds_won = 0
        _blackjacks = 0
        _rounds_lost = 0
        for round_results in self.results:
            for hand_result in round_results:
                if hand_result == 0: # Draw
                    _rounds_drawn += 1
                elif hand_result == 1: # Win
                    _rounds_won += 1
                elif hand_result == "bj": # Blackjack
                    _blackjacks += 1
                else: # | || || |_
                    _rounds_lost += 1
        total_hands = _rounds_drawn+ _rounds_won + _blackjacks + _rounds_lost
        return f"Blackjacks: {_blackjacks} | Won: {_rounds_won} | Drawn: {_rounds_drawn} | Lost: {_rounds_lost} | Total rounds: {len(self.results)} | Total hands: {total_hands}"
    def double_down(self, dealing_cards):
        '''Gives you one card, doubles your bet'''
        print(f"{self.name} doubles down.")             
        self.hand.append(dealing_cards.pop(0))
        self.money -= self.bet[self.hand_id]
        self.bet[self.hand_id] += self.bet[self.hand_id]
        return True
    def split_pairs(self):
        print(f"{self.name} splits pairs.")
        self.money -= self.bet[self.hand_id]
        self.bet.append(self.bet[self.hand_id])
        self.results[-1].append(0)
        self.hands.append([self.hands[self.hand_id].pop(0)]) # Appends new hand with the second player card
        self.hand_id -= 1 # "Flag" to not increment hand_id at end of turn
    def deal_two_cards(self, dealing_cards):
        """Deal two cards to a player"""
        # We initially deal two cards to each player
        if self.bankruptcy:
            return
        for card in range(2):                
            self.hand.append(dealing_cards.pop(0))
        # Initialize player.results' new element for each round
        self.results.append([0])  # Starts as a draw
    def payout(self):
        # Payout time
        if self.bankruptcy:
            return
        # (bj_mul+1)*bet if Blackjack / 2*bet Win / 1*bet Draw / 0*bet Loss
        winnings = 0
        for hand in range(len(self.hands)):
            hand_result = self.results[-1][hand]
            # +1 to recover initial bet
            if hand_result == "bj": # Blackjack
                hand_winnings = self.bet[hand] * (settings["blackjack_multiplier"] + 1)
            elif hand_result == 1: # Win
                hand_winnings = self.bet[hand] * 2
            elif hand_result == 0: # Draw
                hand_winnings = self.bet[hand]
            else: # Loss
                hand_winnings = 0
            winnings += hand_winnings
        self.money += winnings  # Update before winnings_text
        winnings_text = f"{self.name}'s winnings: ${winnings} Total: ${self.money}"
        print(winnings_text)
    def reinitialize_hands(self):
        self.hands = [[]]
        self.hand_id = 0
        self.hand = self.hands[self.hand_id]

class Human_Player(Player):
    def set_name(self, cpu_names):
        """Input name for a human player"""
        if settings["names_human"]:
            _name = input(f"Input the name for {self.name}: ")
            self.name = _name or self.name
    def make_bets(self, minimum_bet, maximum_bet):
        """Bets for human players"""
        if self.bankruptcy:
            return                            
        # Making bets (human)
        self.bet = [0]
        print(f"{self.name}, how much do you want to bet?\nYou have: ${math.floor(self.money)}\
                \nMinimum: ${minimum_bet} Maximum: ${maximum_bet}")
        while True:
            selection = wait_for_player_input("")
            try:
                self.bet[0] = int(selection)
                if self.bet[0] < minimum_bet:
                    print(f"The minimum bet amount is ${minimum_bet}")
                elif self.bet[0] > maximum_bet:
                    print(f"The maximum bet amount is ${maximum_bet}")
                elif self.bet[0] > self.money:
                    print("You don't have enough money!")
                else:
                    print(f"{self.name} bets ${self.bet[0]}")
                    self.money -= self.bet[0]
                    break
            except ValueError:
                    print("Invalid amount (only numbers, no symbols or letters)")
    def split_pairs_logic(self):
        # TODO: Add payout and round results logic, make it work with multiple hands
        if self.money < self.bet[self.hand_id]: # We check that the player has enough money to split
            return False
        print("Do you want to split pairs? (y/n)")
        player_choice = str(wait_for_player_input(f"Your money: ${self.money} Your bet: ${self.bet[self.hand_id]}\n")).lower()
        if player_choice in ["y", "yes", "3"]:
            self.split_pairs()
            return True
        else:
            wait_for_player_input(f"{self.name} does not split pairs.")
            return False
    def turn(self, dealing_cards):
        '''Player turn logic'''
        if self.bankruptcy:
            return
        turn_num = 0
        while self.hand_id <= (len(self.hands) - 1):
            self.hand = self.hands[self.hand_id] # Refresh hand value
            if turn_num == 0:
                print(f"-{self.name}'s turn-")
            else:
                print(f"-{self.name}'s {turn_num}{ordinal(turn_num)} hand-")
            if len(self.hand) >= 2: # Don't print when we only got one card
                print(f"Your hand: {self.hand} (Total: {total_up(self.hand)})")
            # Checking for blackjack
            if len(self.hands) == 1: # Only can get Blackjack on the first dealing
                if total_up(self.hand) == 21:
                    self.results[-1][0] = "bj"
                    wait_for_player_input(f"{self.name} got a blackjack!")
                    break          
            # Checking for split pairs
            if self.hand == ["A"]: # After splitting aces you only get one card
                self.hand.append(dealing_cards.pop(0))
                wait_for_player_input(f"Your hand: {self.hand} (Total: {total_up(self.hand)})")
                self.hand_id += 1           # We skipping the rest of the turn
                turn_num = self.hand_id + 1 # so we have to increase counter here too
                continue
            ################                  
            # Dealing loop #
            ################
            while total_up(self.hand) < 21:                
                if len(self.hand) == 1: # Always gives you a card if you only have one
                    self.hand.append(dealing_cards.pop(0))
                    print(f"Your hand: {self.hand} (Total: {total_up(self.hand)})")
                    if total_up(self.hand) == 21: # Auto-stand if on 21
                        wait_for_player_input(f"{self.name} stands.")
                        break
                # Splitting pairs
                if len(self.hand) == 2 and self.hand[0] == self.hand[1]:
                     if self.split_pairs_logic(): #Skip rest of dealing if splitting pairs
                        break
                # Doubling Down
                if total_up(self.hand) in [9, 10, 11] and len(self.hand) == 2 and (self.money >= self.bet[self.hand_id]):
                    print("Do you want to double down? (y/n)")
                    player_choice = str(wait_for_player_input(f"Your money: ${self.money} Your bet: ${self.bet[self.hand_id]}\n")).lower()
                    if player_choice in ["y", "yes", "3"]:
                        self.double_down(dealing_cards)
                        wait_for_player_input(f"Your hand: {self.hand} (Total: {total_up(self.hand)})")
                        break
                    print(f"{self.name} does not double down.")                       
                # Hit or stand
                player_choice = str(wait_for_player_input("(H)it or (S)tand?\n")).lower()
                if player_choice in ["h", "hit", "3"]:
                    self.hand.append(dealing_cards.pop(0))
                    print(f"Your hand: {self.hand} (Total: {total_up(self.hand)})")
                    if total_up(self.hand) == 21: # Auto-stand if on 21
                        wait_for_player_input(f"{self.name} stands.")
                        break
                    if total_up(self.hand) > 21:
                        self.results[-1][self.hand_id] = -1
                        wait_for_player_input(f"\n{self.name} busted!")
                        break
                else:
                    wait_for_player_input(f"{self.name} stands.")
                    break
            self.hand_id += 1 # Increment the hand ID count at the end of the turn
            turn_num = self.hand_id + 1
        print("")
    
class CPU_Player(Player):
    def set_name(self, cpu_names):
        """Input name for an AI player"""
        if settings["names_ai"]:
                if settings["autoname"]:
                    self.name = random.choice(cpu_names)
                else:
                    _name = input(f"Input the name for {self.name}: ")
                    self.name = _name or self.name
    def make_bets(self, minimum_bet, maximum_bet):
        """Bets for AI players"""    
        if self.bankruptcy:
            return 
        # Making bets (CPU)
        # CPU bets half their money, respecting min/max bets
        self.bet = [0]
        self.bet[0] = int(min(maximum_bet,max(self.money/4, minimum_bet)))
        print(f"{self.name} bets ${self.bet[0]}.")
        self.money -= self.bet[0]
    def double_down_logic(self, dealing_cards, dealer_hand):
        if settings["CPU_difficulty"] == "easy": # On easy difficulty we only split aces or 8s
            if total_up(self.hand) in [10, 11]:
                return self.double_down(dealing_cards)
        else:
            if total_up(self.hand) == 9 and dealer_hand[0] in range(3, 7):
                return self.double_down(dealing_cards)
            if total_up(self.hand) == 10 and dealer_hand[0] in range(2, 10):
                return self.double_down(dealing_cards)
            if total_up(self.hand) == 11 and dealer_hand[0] != 'A':
                return self.double_down(dealing_cards)
        return False
    def split_pairs_logic(self, dealer_hand):
        if self.money < self.bet[self.hand_id]: # We check that the player has enough money to split
            return False
        if total_up(self.hand) in [20, 10]: # Never split 10s or 5s
            return False
        if self.hand == ['A', 'A'] or total_up(self.hand) == 16: # Always split aces or 8s
            self.split_pairs()
            return True
        if settings["CPU_difficulty"] == "easy": # On easy difficulty we only split aces or 8s
            return False
        elif settings["CPU_difficulty"] == "hard":
            if total_up(self.hand) == 18 and not dealer_hand[0] in [7, 10, 'J', 'Q', 'K', 'A']: # Split 9s if dealer card is not 7, 10 or Ace #TODO CHECK THIS ISNT PROBLEMATIC DETECTING ACES
                self.split_pairs()
                return True
            elif total_up(self.hand) in [4, 6, 14] and dealer_hand[0] in range(2, 8): # Split 2s, 3s or 7s if dealer card is poor
                self.split_pairs()
                return True
            elif total_up(self.hand) == 12 and dealer_hand[0] in range(2, 7): # Split 6s if dealer card is poorer
                self.split_pairs()
                return True
            elif total_up(self.hand) == 8 and dealer_hand[0] in [5, 6]: # Split 4s if dealer card is poorest
                self.split_pairs()
                return True
            return False
    def hit_or_stand_logic(self, dealer_hand):
        '''Returns True for hitting, False for standing'''
        hand = self.hand
        if settings["CPU_difficulty"] == "easy": # Easy difficulty logic
            if ((random.random() >= 0.35) or total_up(hand) <= 11) and (total_up(hand) <= 17):
                return True
            return False
        # -Hard difficulty logic-
        # Soft hands
        if is_soft(hand):
            if total_up(hand) <= 17:
                return True
            if total_up(hand) == 18:
                if dealer_hand[0] in [2, 7, 8]:
                    return False
                return True
            return False
        # Hard hands
        if total_up(hand) == 12 and dealer_hand[0] in [4, 5, 6]:
            return False
        if total_up(hand) in range(13, 17) and dealer_hand[0] in range(2, 7):
            return False
        if total_up(hand) >= 17:
            return False
        return True
    def turn(self, dealing_cards, dealer_hand):
        '''CPU turn logic'''
        if self.bankruptcy:
            return
        turn_num = 0
        while self.hand_id <= (len(self.hands) - 1):
            self.hand = self.hands[self.hand_id] # Refresh hand value
            if turn_num == 0:
                print(f"-{self.name}'s turn-")
            else:
                print(f"-{self.name}'s {turn_num}{ordinal(turn_num)} hand-")
            if len(self.hand) >= 2: # Don't print when we only got one card
                print(f"{self.name}'s hand: {self.hand} (Total: {total_up(self.hand)})")
            # Checking for blackjack
            if len(self.hands) == 1: # Only can get Blackjack on the first dealing
                if total_up(self.hand) == 21:
                    self.results[-1][0] = "bj"
                    print(f"{self.name} got a blackjack!")
                    break          
            # Checking for split pairs
            if self.hand == ["A"]: # After splitting aces you only get one card
                self.hand.append(dealing_cards.pop(0))
                print(f"{self.name}'s hand: {self.hand} (Total: {total_up(self.hand)})")
                self.hand_id += 1           # We skipping the rest of the turn
                turn_num = self.hand_id + 1 # so we have to increase counter here too
                continue
            ################                  
            # Dealing loop #
            ################
            while total_up(self.hand) < 21:                
                if len(self.hand) == 1: # Always gives you a card if you only have one
                    self.hand.append(dealing_cards.pop(0))
                    print(f"{self.name}'s hand: {self.hand} (Total: {total_up(self.hand)})")
                    if total_up(self.hand) == 21: # Auto-stand if on 21
                        print(f"{self.name} stands.")
                        break
                # Splitting pairs
                if len(self.hand) == 2 and self.hand[0] == self.hand[1]:
                    if self.split_pairs_logic(dealer_hand): # Skip rest of dealing if splitting pairs                        
                        break
                # Doubling Down
                if total_up(self.hand) in [9, 10, 11] and len(self.hand) == 2 and (self.money >= self.bet[self.hand_id]):
                    if self.double_down_logic(dealing_cards, dealer_hand): # Skip rest of dealing if doubling down
                        print(f"{self.name}'s hand: {self.hand} (Total: {total_up(self.hand)})")
                        break                        
                # Hit or stand
                if self.hit_or_stand_logic(dealer_hand):
                    print(f"{self.name} hits.")
                    self.hand.append(dealing_cards.pop(0))
                    print(f"{self.name}'s hand: {self.hand} (Total: {total_up(self.hand)})")
                    if total_up(self.hand) == 21: # Auto-stand if on 21
                        print(f"{self.name} stands.")
                        break
                    if total_up(self.hand) > 21:
                        self.results[-1][self.hand_id] = -1
                        print(f"\n{self.name} busted!")
                        break
                else:
                    print(f"{self.name} stands.")
                    break
            self.hand_id += 1 # Increment the hand ID count at the end of the turn
            turn_num = self.hand_id + 1
        print("")

def create_players(players_human, players_ai, starting_money):
    """Creates the requested number of human and AI players."""
    players = []
    for player in range(players_human):
        players.append(Human_Player(starting_money, f"Player {player+1}"))
    for player in range(players_ai):
        players.append(CPU_Player(starting_money, f"CPU {player+1}"))
    cpu_names = DEFAULT_CPU_NAMES
    if settings["autoname"]: # Load CPU name list if the setting is on
        if os.path.exists('names.txt'):
            with open('names.txt') as file:
                data = file.read()
                cpu_names = data.split("\n")
    for player in players:
        player.set_name(cpu_names)
    return players
def reinitialize_player_hands(players):
    for player in players:
        player.reinitialize_hands()

### SETTINGS MENU FUNCTIONS #######
def load_settings():
    # Load settings from a JSON file
    if os.path.exists('game_blackjack_settings.json'):
        with open('game_blackjack_settings.json') as file:
            settings = json.load(file)        
        # Convert JSON boolean values to Python boolean values
        for key, value in settings.items():
            if value in ['false', 'true']:
                settings[key] = value == 'true' # Key is True if word is true
        return settings
    # If no file is found, return default settings
    settings = DEFAULT_SETTINGS.copy()
    return settings
def save_settings(settings):
    # Save settings to a JSON file
    with open('game_blackjack_settings.json', 'w') as file:
        json.dump(settings, file, indent=4)
def settings_menu(settings): #TODO: no permitir valores negativos o 0 en stacks y asi aunque es grasioso
    """Settings menu"""
    settings_labels = {
        "stacks":               "Number of card stacks",
        "num_decks":            "Number of decks in each stack",
        "players_human":        "Number of human players",
        "players_ai":           "Number of CPU players",
        "blackjack_multiplier": "Payout multiplier for blackjack",
        "starting_money":       "Starting money",
        "minimum_bet":          "Minimum bet",
        "maximum_bet":          "Maximum bet",
        "names_human":          "Name human players",
        "names_ai":             "Name CPU players",
        "autoname":             "Auto-name CPUs",
        "detailed_scores":      "Show detailed scores (round results)",
        "autopause":            "Auto-pause in between turns (makes gameplay slower)",
        "bgm_volume":           "Background music volume (0-100)",
        "CPU_difficulty":       "CPU difficulty (easy/hard)"
    }
    while True:
        for index, (key, value) in enumerate(settings.items(), start=1):
            print(f"{index}- {settings_labels[key]} (default: {DEFAULT_SETTINGS[key]}): {value}")
        try:
            selection = int(input("\nSelect one (0 to exit): "))            
            if selection == 0:
                return
            setting_key = list(settings.keys())[selection - 1]
            setting_value = settings[setting_key]
            new_value = input(f"Enter the new value for {settings_labels[setting_key].lower().replace('cpu', 'CPU')}: ")
            if new_value.strip():  # Check if input is not empty
                if type(setting_value) == int:
                    settings[setting_key] = int(new_value)
                elif type(setting_value) == bool:
                    settings[setting_key] = True
                    if new_value.lower() in ["0", "false", "f", "n", "no", "untrue"]: # TODO Add more synonyms. More.
                        settings[setting_key] = False
                elif type(setting_value) == str:
                    if new_value.lower() == "easy":
                        settings[setting_key] = "easy"
                    elif new_value.lower() == "hard":
                        settings[setting_key] = "hard"
                else:
                    settings[setting_key] = float(new_value)            
            # Update global variables based on the modified settings
            mixer.music.set_volume(settings["bgm_volume"]/100) # Refresh music volume
            save_settings(settings)  # Save settings before exiting
            clear()
        except ValueError: #Just kidding, negative values also break the game but it's fine
            clear()
            print("Wrong input! (perhaps you didn't write a number?)\n")
        except IndexError:
            clear()
            print("Invalid selection! Please choose a number from the list.\n")
        except Exception as e: #I have a feeling someone will manage to break it more than I intended
            clear()
            print("How did you get here??")
            print(e)
            print("")
def controls_screen():
    TEXT_SEPARATOR = "---------------------------------------------"
    CONTROLS_TEXT = ("""
Recommended controls:

Numpad 3 to hit (or \"h\" or \"hit\")
Intro to stand (any button stands by default)

At any time, you can write \"m\" or \"menu\" to go 
back to the main menu, and \"q\" or \"quit\" or 
\"exit\" to exit the game.""")    
    AUTONAME_TEXT = ("""If you use the auto-name setting, you need to
also set \"Name CPU players\" to True.

You can create a names.txt file and write one name
on each line to use those for autonaming.""")
    PROTIP_LIST = [
            "try not to go over 21!",
            "digital money isn't real money. Spend it.",
            "try changing the settings! What could go wrong?",
            "try negative numbers on the options. Not sure about this one.",
            "check out bicyclecards.com/how-to-play/blackjack/ for a rundown of the rules.\
            \nShoutouts to their neat page! (Tyoe \"rules\" anytime to open on your web browser)"]
    print(CONTROLS_TEXT)
    settings = load_settings()
    if settings["autoname"]:
        print(TEXT_SEPARATOR)
        print(AUTONAME_TEXT)
    print(TEXT_SEPARATOR)
    print(f"Protip: {random.choice(PROTIP_LIST)}") 
    print("")

### TEXT FUNCTIONS #######
def emboss(text): 
    '''Prints text with a slash symbol border'''
    print("\n" + "/"*(len(text) + 2) + "\n" + "/" + text + "/" + "\n" + "/"*(len(text) + 2) + "\n")
def ordinal(number):
    '''Takes an int, returns its ordinal indicator string (st,nd,rd,th)'''
    if type(number) is not int:
        return ""
    elif number%10 == 1 and number%100 != 11:
        return "st"
    elif number%10 == 2 and number%100 != 12:
        return "nd"
    elif number%10 == 3 and number%100 != 13:
        return "rd"
    else:
        return "th"    
def clear():
    """Calls the OS clearscreen method"""
    if os.name == "nt":  # For Windows
        _ = os.system("cls")
    else:  # For Unix/Linux and MacOS
        _ = os.system("clear")
def wait_for_player_input(text):
    '''For when player input can lead to main menu or quitting'''
    player_choice = input(f"{text}")
    if player_choice.strip():
        if player_choice.lower() in ["q", "quit", "exit"]:
            sys.exit()
        elif player_choice.lower() in ["m", "menu"]:
            main_loop()
        elif player_choice.lower() == "rules":
            webbrowser.open('https://bicyclecards.com/how-to-play/blackjack/')
            player_choice = wait_for_player_input("")
        else:   
            return player_choice
    return player_choice  

### MUSIC #######
def music_initialize():
    '''Initializes pygame's mixer and sets the music volume'''
    mixer.init()    # Initialize pygame audio mixer
    settings = load_settings()
    mixer.music.set_volume(settings["bgm_volume"]/100)
def queue_song():
    '''Plays a song, adds another one to the pygame mixer queue'''
    path = "music/"
    music_list = []
    if os.path.exists(path):
        music_list = os.listdir(path)
    if music_list != []:
        if mixer.music.get_busy():                              # Queue song if music is already playing
            mixer.music.queue(path + random.choice(music_list))
        else:                                                   # Play a song otherwise
            mixer.music.load(path + random.choice(music_list))
            mixer.music.play() # (-1) for loop play                                 
            mixer.music.queue(path + random.choice(music_list)) # And queue another one
            
### MAIN FUNCTIONS #################################################################################################################
def make_decks(num_decks, CARD_TYPES):
    """Creates a shuffled deck out of 52-card decks * num_decks"""
    new_deck = []
    for deck in range(num_decks):       #For each of our decks
        for suit in range(4):           #Four suits => 4 loops
            new_deck.extend(CARD_TYPES) #Appends one of each card into deck
    random.shuffle(new_deck)            #Shuffles deck
    return new_deck                     #Returns shuffled decks
def total_up(hand):
    """Returns the total value of a hand."""
    _aces  = 0
    _total = 0
    for card in hand:
        if card in ('J', 'Q', 'K'):  # Face cards are worth 10
            _total += 10
        elif card != "A":  # Number cards are worth their value
            _total += card
        else:  # Aces can be worth 11 or 1, so we need to check the max value of the hand <= 21
            _aces += 1
    while _aces > 0:  # Could be a for loop, but this just works, so don't touch it
        if  _total >= 12 - _aces:  # Don't go over 21 when there are multiple aces in the hand
            _total += 1
        else:
            _total += 11  # Player should decide between 1 and 11, but 11 is always better
        _aces -= 1
    return _total
def is_soft(hand):
    '''Returns True if the hand is a soft hand'''
    _aces  = 0
    _total = 0
    for card in hand:
        if card in ('J', 'Q', 'K'):  # Face cards are worth 10
            _total += 10
        elif card != "A":  # Number cards are worth their value
            _total += card
        else:  # Aces can be worth 11 or 1, so we need to check the max value of the hand <= 21
            _aces += 1
    if _aces > 0:  
        if  _total >= 12 - _aces:  # Soft hand condition
            return False
        else:
            return True
    return False

def check_house_blackjack(dealer_hand, players):
    house_blackjack = False
    if total_up(dealer_hand) == 21:
        house_blackjack = True
        print("House blackjack!\n")
        if settings["autopause"]:
            wait_for_player_input("")
        print("-"*11 + "Round Results" + "-"*11 + "\n")
        for player in players:
            if not player.bankruptcy:
                if total_up(player.hand) != 21:
                    print(f"{player.name} loses the round.")
                    player.results[-1] = [-1]
                else:
                    print(f"{player.name} draws the round.")
                    player.results[-1] = [0]
    return house_blackjack
def dealer_turn(dealer_hand, dealing_cards, players):
    # Skip Dealer's turn if they got blackjack
    if total_up(dealer_hand) == 21 and len(dealer_hand) == 2:
        return
    # Dealer hits based on the rules
    print("-Dealer's turn-")
    print(f"Dealer's hand: {dealer_hand} (Total: {total_up(dealer_hand)})")
    # Hitting until 17 loop
    while total_up(dealer_hand) < 17:
        dealer_hand.append(dealing_cards.pop(0))
        print("Dealer hits.")
        print(f"Dealer's hand: {dealer_hand} (Total: {total_up(dealer_hand)})")
    # If dealer busts, check if player has busted too
    if total_up(dealer_hand) > 21: 
        print("Dealer busted!")
        if settings["autopause"]:
            wait_for_player_input("") 
        print("-"*11 + "Round Results" + "-"*11 + "\n")  
        for player in players:
            check_player_bust(player,dealer_hand)
    # If no dealer bust, check which players won
    else:
        print("Dealer stands.")
        if settings["autopause"]:
            wait_for_player_input("")
        print("-"*11 + "Round Results" + "-"*11 + "\n")
        for player in players:
            check_player_win(player,dealer_hand)
    if settings["autopause"]:
        wait_for_player_input("")
    else:
        print("")       
def check_player_bust(player,dealer_hand):
    # Check if dealer busted; players that didn't bust win
    if player.bankruptcy:
        return
    if len(player.results[-1]) > 1:
        for hand in range(len(player.hands)):
            if player.results[-1][hand] == -1:
                print(f"{player.name} loses the hand.")
                continue
            print(f"{player.name} wins the hand!")
            if player.results[-1][hand] == 0:
                player.results[-1][hand] = 1
    else:
        if player.results[-1][0] == -1:
            print(f"{player.name} loses the round.")
            return             
        print(f"{player.name} wins the round!")
        if player.results[-1][0] == 0:
            player.results[-1][0] = 1            
def check_player_win(player,dealer_hand):   
    if player.bankruptcy:
        return
    label = "round" # Change to "hand" if player has split pairs
    if len(player.hands) > 1: 
        label = "hand"
    hand_id = 0
    for hand in (player.hands):
        if total_up(hand) > total_up(dealer_hand) or player.results[-1][hand_id] == "bj":
            if total_up(hand) <= 21:
                print(f"{player.name} wins the {label}!")
                # Don't change if player got a blackjack 
                if not player.results[-1][hand_id] == "bj":
                    player.results[-1][hand_id] = 1
            else:
                print(f"{player.name} loses the {label}.")
                player.results[-1][hand_id] = -1
        elif total_up(hand) == total_up(dealer_hand) and total_up(hand) <= 21:
            print(f"{player.name} draws the {label}.")
            player.results[-1][hand_id] = 0
        else:
            print(f"{player.name} loses the {label}.")
            player.results[-1][hand_id] = -1
        hand_id += 1
def end_game_scores(total_rounds, players):
    # End of the game
    print("\n" + "/" * 35 + "\n")
    print("End of game. Results:\n")
    print(f"Total number of rounds: {total_rounds} rounds.")
    print(f"Casino winnings: ${settings['starting_money']*(len(players))-(sum(player.money for player in players))}")
    input("\n>Show scores\n")
    players = sorted(players, key=lambda player: player.money, reverse=True)  # Sort by money
    players = sorted(players, key=lambda player: len(player.results), reverse=True) # Sort by rounds played (non-bankrupt)
    for position, player in enumerate(players):  # Print sorted player list
        print(f"{position+1}{ordinal(position+1)} place - {player.name}: ${math.floor(player.money)}" + f"{' - ' + player.detailed_scores() if settings['detailed_scores'] else ''}")
    player_choice = ""
    while player_choice == "":
        player_choice = input("\nType anything to continue...")
    clear()
    print(TITLE_GRAPHIC)
def play_game(players, CARD_TYPES, total_rounds):
    for stack in range(settings["stacks"]):  
        # STACK START
        # Each "stack" is made of decks, and it lasts until we run out of cards
        emboss(f"STACK {stack+1}")
        round_num = 0
        dealing_cards = make_decks(settings["num_decks"], CARD_TYPES)        
        # Each round uses one stack, until the amount of cards left is low 
        while len(dealing_cards) >= settings["num_decks"]*13 + 2*len(players): # 3/4ths of all cards are used
            # ROUND START         
            print(f"----ROUND {round_num+1}----\n")
            queue_song() # We try to queue a song at the start of each round so they don't stop coming and they don't stop coming...
            reinitialize_player_hands(players) # Re-initialize player hands
            # //////
            # /BETS/
            # //////
            for player in players:
                player.make_bets(settings["minimum_bet"], settings["maximum_bet"])
                if isinstance(player, Human_Player) and not player.bankruptcy:      #TODO Maybe delete this idk
                    print("")                                                       #TODO Maybe delete this idk
            # /////////
            # /DEALING/
            # /////////
            print("\n" + "-"*11 + "Round Start" + "-"*11 + "\n")
            for player in players:
                player.deal_two_cards(dealing_cards) # Deal 2 cards to the first hand of each player
            # Dealer's hand
            dealer_hand = []
            # We append two cards for the dealer
            dealer_hand.append(dealing_cards.pop(0))
            dealer_hand.append(dealing_cards.pop(0))
            # We show the first card of the dealer's hand
            print(f"Dealer's hand: {dealer_hand[0]}\n")
            # ////////////
            # /GAME LOGIC/
            # ////////////
            # Check for house blackjack
            house_blackjack = check_house_blackjack(dealer_hand, players)                    
            # Skip players' turn when house blackjack
            if not house_blackjack:
                # Players' turn
                for player in players:
                    if isinstance(player, CPU_Player):
                        player.turn(dealing_cards, dealer_hand)
                        if settings["autopause"]:
                            wait_for_player_input("")
                    else:
                        player.turn(dealing_cards)
            # Dealer's Turn
            dealer_turn(dealer_hand, dealing_cards, players)
            # Payout for non-busted players
            for player in players:
                player.payout()
            # Wait for player input at the end of each round unless
            # it's only CPU players or all humans have run out of money.
            if settings["players_human"] > 0 and any(isinstance(player, Human_Player) and not player.bankruptcy for player in players) or settings["autopause"]:
                wait_for_player_input("")
            else:
                print("")
            # Check for bankruptcy
            for player in players:
                player.check_bankrupcy() # Update value
            if all(player.bankruptcy for player in players): # End loop if no-one has money to bet
                total_rounds +=1 #Count last round too
                break
            # Increment round counters
            round_num += 1  # Increment at the end cause we use it for results index
            total_rounds +=1  # This one can be incremented whenever
        for player in players:
            player.check_bankrupcy() # Update value
        if all(player.bankruptcy for player in players): # End loop if no-one has money to bet
            input("Everyone ran out of money. Table closed.\n")
            break
    # End of the game
    end_game_scores(total_rounds, players)

######################
## GAME STARTS HERE ##
######################
MAIN_MENU = {"1-":"Play Blackjack.","2-":"Settings.","3-":"How to play.","4-":"Quit."}
music_initialize()
#############
# Main loop #
#############
def main_loop():
    queue_song() # Start playing music
    clear()  # We clear the screen to start
    print(TITLE_GRAPHIC)  # Prints the main title
    global settings
    options = MAIN_MENU.keys()
    while True:
        for entry in options:
            print(entry,MAIN_MENU[entry])
        selection = wait_for_player_input("\nSelect one: ").lower()
        if selection == "2": # Settings menu
            clear()
            settings = load_settings()
            settings_menu(settings)
            clear()
            print(TITLE_GRAPHIC)
        elif selection == "3": # Controls
            clear()
            controls_screen()
        elif selection in ["4", "q", "quit", "exit"]:
            sys.exit()
        elif selection == "1":  # Play game
            clear() #Clear the screen
            #Initialize new game
            settings = load_settings()
            total_rounds = 0  # Round counter for games with >= 2 stacks
            players = create_players(settings["players_human"], settings["players_ai"], settings["starting_money"])  # Create the players for the current game      
            play_game(players, CARD_TYPES, total_rounds) 
        else:
            clear()
            print(TITLE_GRAPHIC)
            print("\nUnknown selection.\n")
main_loop()