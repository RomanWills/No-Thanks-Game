import random
import tkinter as tk

from no_thanks import Community, Player, RandomPlayer

from no_thanks_learning import GeneticPlayer
#good_bot = GeneticPlayer.from_file("Evolved Bot", "best_weights.json")

class GUIPlayer(Player):
    """Human player controlled by buttons instead of input().

    The GUI stores the clicked action in next_action, and decide() simply
    returns it. All the game rules still live in Player.play_turn().
    """

    def __init__(self, name):
        super().__init__(name)
        self.next_action = "pass"

    def decide(self, community):
        return self.next_action


class NoThanksApp:
    BOT_DELAY_MS = 900

    def __init__(self, root):
        self.root = root
        root.title("No Thanks!")
        root.resizable(False, False)
        self.after_id = None

        # ---- top info bar ----
        top = tk.Frame(root, padx=10, pady=10)
        top.pack(fill="x")
        self.card_label = tk.Label(top, text="-", font=("Helvetica", 48, "bold"),
                                   width=4, relief="ridge", bd=4, bg="white")
        self.card_label.pack(side="left", padx=(0, 20))
        info = tk.Frame(top)
        info.pack(side="left")
        self.pot_label = tk.Label(info, text="Pot: 0", font=("Helvetica", 18))
        self.pot_label.pack(anchor="w")
        self.deck_label = tk.Label(info, text="Cards left: 0", font=("Helvetica", 12))
        self.deck_label.pack(anchor="w")

        # ---- player panels (created in new_game) ----
        self.players_frame = tk.Frame(root, padx=10)
        self.players_frame.pack(fill="x")

        # ---- buttons ----
        buttons = tk.Frame(root, pady=10)
        buttons.pack()
        self.pass_btn = tk.Button(buttons, text="Pass (pay 1 token)", width=18,
                                  command=lambda: self.human_action("pass"))
        self.pass_btn.pack(side="left", padx=5)
        self.take_btn = tk.Button(buttons, text="Take card + pot", width=18,
                                  command=lambda: self.human_action("take"))
        self.take_btn.pack(side="left", padx=5)
        tk.Button(buttons, text="New game", command=self.new_game).pack(side="left", padx=20)

        # ---- status + log ----
        self.status = tk.Label(root, text="", font=("Helvetica", 12, "bold"))
        self.status.pack()
        self.log = tk.Text(root, height=8, width=60, state="disabled")
        self.log.pack(padx=10, pady=(5, 10))

        self.new_game()

    # ------------------------------------------------------------------
    # setup
    # ------------------------------------------------------------------
    def new_game(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        deck = list(range(3, 36))
        random.shuffle(deck)
        self.deck = deck[9:]  # 9 cards removed unseen

        self.players = [GUIPlayer("You"), GeneticPlayer.from_file("Evolved Bot 1", "best_weights.json"), GeneticPlayer.from_file("Evolved Bot 2", "best_weights.json")]
        random.shuffle(self.players)
        self.human = self.players[0]
        self.community = Community()
        self.current = 0
        self.game_over = False

        self.build_player_panels()
        self.clear_log()
        self.write_log("New game started.")
        self.draw_card()
        self.refresh()
        self.next_turn()

    def build_player_panels(self):
        for child in self.players_frame.winfo_children():
            child.destroy()
        self.panels = []
        for p in self.players:
            frame = tk.Frame(self.players_frame, bd=2, relief="groove", padx=8, pady=6)
            frame.pack(side="left", fill="both", expand=True, padx=4)
            name = tk.Label(frame, text=p.name, font=("Helvetica", 14, "bold"))
            name.pack()
            tokens = tk.Label(frame, text="")
            tokens.pack()
            cards = tk.Label(frame, text="", wraplength=150, justify="center")
            cards.pack()
            score = tk.Label(frame, text="", fg="gray30")
            score.pack()
            self.panels.append((frame, name, tokens, cards, score))

    # ------------------------------------------------------------------
    # game flow
    # ------------------------------------------------------------------
    def draw_card(self):
        self.community.card = self.deck.pop()
        self.write_log(f"New card: {self.community.card}")

    def next_turn(self):
        """Wait for the human, or schedule a bot's move."""
        if self.game_over:
            return
        player = self.players[self.current]
        if player is self.human:
            self.status.config(text="Your turn")
            self.pass_btn.config(state="normal" if player.tokens > 0 else "disabled")
            self.take_btn.config(state="normal")
        else:
            self.status.config(text=f"{player.name} is thinking...")
            self.pass_btn.config(state="disabled")
            self.take_btn.config(state="disabled")
            self.after_id = self.root.after(self.BOT_DELAY_MS, self.do_turn)

    def human_action(self, action):
        self.human.next_action = action
        self.do_turn()

    def do_turn(self):
        self.after_id = None
        player = self.players[self.current]
        card, pot = self.community.card, self.community.pot
        action = player.play_turn(self.community)

        if action == "pass":
            self.write_log(f"{player.name} passed.")
            self.current = (self.current + 1) % len(self.players)
        else:
            self.write_log(f"{player.name} took {card} and {pot} token(s).")
            if self.deck:
                self.draw_card()  # taker stays as the next starting player
            else:
                self.community.card = None
                self.refresh()
                self.end_game()
                return

        self.refresh()
        self.next_turn()

    def end_game(self):
        self.game_over = True
        self.pass_btn.config(state="disabled")
        self.take_btn.config(state="disabled")
        winner = min(self.players, key=lambda p: p.score())
        self.status.config(text=f"Game over - {winner.name} wins!")
        self.write_log("Final scores (lowest wins):")
        for p in sorted(self.players, key=lambda p: p.score()):
            self.write_log(f"  {p.name}: {p.score()}")

    # ------------------------------------------------------------------
    # display helpers
    # ------------------------------------------------------------------
    def refresh(self):
        card = self.community.card
        self.card_label.config(text="-" if card is None else str(card))
        self.pot_label.config(text=f"Pot: {self.community.pot}")
        self.deck_label.config(text=f"Cards left: {len(self.deck)}")
        for i, (p, panel) in enumerate(zip(self.players, self.panels)):
            frame, name, tokens, cards, score = panel
            tokens.config(text=f"Tokens: {p.tokens}")
            cards.config(text=" ".join(map(str, sorted(p.cards))) or "(no cards)")
            score.config(text=f"Score: {p.score()}")
            active = i == self.current and not self.game_over
            for w in (frame, name, tokens, cards, score):
                w.config(bg="#fff3b0" if active else self.root.cget("bg"))

    def write_log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    NoThanksApp(root)
    root.mainloop()
