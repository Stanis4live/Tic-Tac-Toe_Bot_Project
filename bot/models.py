import uuid

from django.db import models
from random import choice


class Player(models.Model):
    user_id = models.BigIntegerField(null=True, blank=True)
    username = models.CharField(max_length=64, null=True, blank=True)
    is_bot = models.BooleanField(default=False)

    def __str__(self):
        return self.username or 'Bot' if self.is_bot else str(self.user_id)


class Game(models.Model):
    player_x = models.ForeignKey(Player, related_name='games_as_x', on_delete=models.SET_NULL, null=True, blank=True)
    player_o = models.ForeignKey(Player, related_name='games_as_o', on_delete=models.SET_NULL, null=True, blank=True)
    current_turn = models.ForeignKey(
        Player,
        related_name='current_turn_games',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    board = models.CharField(max_length=25, default=' ' * 9)
    is_active = models.BooleanField(default=True)
    against_bot = models.BooleanField(default=False)
    game_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    board_size = models.IntegerField(default=3)

    def assign_players(self, player1, player2=None):
        if self.against_bot:
            bot_player = Player.objects.create(is_bot=True)
            self.player_o = bot_player
        else:
            players = [player1, player2]
            self.player_x = choice(players)
            players.remove(self.player_x)
            self.player_o = players[0]
        self.current_turn = self.player_x
        self.save()

    def __str__(self):
        return f"{self.player_x or 'Waiting...'} vs {self.player_o or 'Waiting...'}"
