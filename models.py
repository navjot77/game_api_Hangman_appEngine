"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

#List of all words for puzzle. Random word gets selected from this list.
words = ["udacity","education","simple","easy","navjot","university",
         "goooooood","apartment","hyundai","mercedes","engine","nanodegree",
         "fullstack" ]


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()

    def add_performance(self, perform):
        perform = Performance(user=self.name, performance=perform)
        perform.put()
        perform.put()


class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    letters_guessed=ndb.StringProperty(repeated=True)
    game_history=ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user, attempts):
        """Creates and returns a new game"""
        game = Game(user=user,
                    target=random.choice(words).lower(),
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        return form

    def to_form_game(self):
        "Return the GameHistory representation of game"
        form=GameHistory()
        form.user=self.user.get().name
        form.game_over=self.game_over
        form.game_history=self.game_history
        #form.target_word=self.target

        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        performance= \
            (self.attempts_remaining / float(self.attempts_allowed))*100

        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining,
                      performance=performance)
        score.put()

class Performance(ndb.Model):
    """Performance object"""
    user = ndb.StringProperty(required=True)
    performance=ndb.FloatProperty(required=True)

    def to_form(self,rank):
        "Returns the PerformanceForm representatioon of Score"
        return PerformanceForm(user_name=self.user,
                           performance=self.performance,
                           rank=rank)

class PerformanceForm(messages.Message):
    """PerformanceForm for outbound Ranking information"""
    user_name = messages.StringField(1, required=True)
    performance=messages.FloatField(2,required=True)
    rank=messages.IntegerField(3,required=True)

class PerformanceForms(messages.Message):
    "Return multiple PerformanceForm"
    ranks=messages.MessageField(PerformanceForm,1,repeated=True)



class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    performance=ndb.FloatProperty(required=True)

    def to_form(self):
        "Returns the ScoreForm representatioon of Score"
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses,
                         performance=self.performance)



class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)

class GamesForm(messages.Message):
    "Return multiple GameForm"
    mess= messages.MessageField(GameForm,1,repeated=True)

class GameHistory(messages.Message):
    "GameHistory for outbound game history information"
    user= messages.StringField(1, required=True)
    game_over=messages.BooleanField(2,required=True)
    game_history = messages.StringField(3, repeated=True)
    #target_word= messages.StringField(4,required=True)


class GamesHistory(messages.Message):
    "Created nmultiple GameHistory form"
    game_history = messages.MessageField(GameHistory, 6, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    attempts=messages.IntegerField(2,required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    performance=messages.FloatField(5,required=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


