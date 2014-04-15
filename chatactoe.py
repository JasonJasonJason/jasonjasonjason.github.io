import datetime
import logging
import os
import random
random.seed()
import re
import sys
from django.utils import simplejson
import json
from gamelogic import *
from banklogic import *
from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class GAME_STATE:
  NEW_GAME  = 'new_game'
  END_GAME  = 'end_game'
  USER_TURN = 'user_turn'

class Game(ndb.Model):
  """All the data we store for a game"""
  dealer          = ndb.PickleProperty()
  users           = ndb.PickleProperty()
  game_key        = ndb.StringProperty()
  current_user_id = ndb.StringProperty()
  deck            = ndb.PickleProperty()
  state           = ndb.StringProperty()
  end_message     = ndb.StringProperty()

def generateGameKey():
    return random.randrange(100)

def createNewGame(game_key, user_id):
    deck = Deck()
    deck.shuffle()
    dealer = Dealer(deck)
    users = [User(deck, user_id), User(deck, '123')]
    return Game(
                game_key        = game_key,
                dealer          = dealer,
                users           = users,
                deck            = deck,
                current_user_id = '',
                state           = GAME_STATE.NEW_GAME,
                end_message     = 'End string...123'
                )

class GameUpdater():
  game = None

  def __init__(self, game):
    self.game = game

  def get_game_message_for_user(self, current_user):
    logging.info('get_game_message_for_user: '+str(current_user.user_id))

    users_list = [user.getDict() for user in self.game.users if user != current_user]

    gameUpdate = {
      'dealer'          : self.game.dealer.getDict(),
      'users'           : users_list,
      'me'              : current_user.getDict(),
      'current_user_id' : self.game.current_user_id,
      'state'           : self.game.state,
      'end_message'     : self.game.end_message
    }
    logging.info('JSON game update: ' + str(json.dumps(gameUpdate)))
    return json.dumps(gameUpdate)

  def send_update(self):
    for user in self.game.users:
        message = self.get_game_message_for_user(user)
        channel.send_message(user.user_id + self.game.game_key, message)
    # if self.game.userO:
    #   channel.send_message(self.game.userO.user_id() + self.game.key().id_or_name(), message)

  def check_win(self):
    return
    # if self.game.moveX:
      # O just moved, check for O wins
      # wins = Wins().o_wins
      # potential_winner = self.game.userO.user_id()
    # else:
      # X just moved, check for X wins
      # wins = Wins().x_wins
      # potential_winner = self.game.userX.user_id()
      
    # for win in wins:
    #   if win.match(self.game.board):
    #     self.game.winner = potential_winner
    #     self.game.winning_board = win.pattern
    #     return

  def make_move(self, position, user):
    return
    # if position >= 0 and user == self.game.userX or user == self.game.userO:
    #   if self.game.moveX == (user == self.game.userX):
    #     boardList = list(self.game.board)
    #     if (boardList[position] == ' '):
    #       boardList[position] = 'X' if self.game.moveX else 'O'
    #       self.game.board = "".join(boardList)
    #       self.game.moveX = not self.game.moveX
    #       self.check_win()
    #       self.game.put()
    #       self.send_update()
    #       return


class GameFromRequest():
  game = None;

  def __init__(self, request):
    user = users.get_current_user()
    game_key = request.get('g')
    game_from_db = Game.query(Game.game_key == game_key).fetch(1)  
    self.game = game_from_db[0]

  def get_game(self):
    return self.game


class Test(webapp.RequestHandler):
  def get(self):
    self.response.write('Currently testing nothing. Have a nice day.')

  class MovePage(webapp.RequestHandler):

    def post(self):
      game = GameFromRequest(self.request).get_game()
      user = users.get_current_user()
      if game and user:
        id = int(self.request.get('i'))
        GameUpdater(game).make_move(id, user)


class OpenedPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    GameUpdater(game).send_update()
    game.state = GAME_STATE.USER_TURN
    game.put()

class BetPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    betAmount = int(self.request.get('bet_amount'))
    logging.info('betting for user_id: ' + str(id) + ' with bet amount: ' + str(betAmount))
    betForUser(game, id, betAmount)

class HitPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    logging.info('hitting for user_id: ' + str(id))
    hitForUser(game, id)

class StandPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    logging.info('standing for user_id: ' + str(id))
    standForUser(game, id)  

def hitForUser(game, id):

    current_user = next((user for user in game.users if user.user_id == id), None)
    
    if len(current_user.getHand().cards) < 5:
        current_user.hitMe()
    game.put()
    GameUpdater(game).send_update()

def standForUser(game, id):

    current_user = next((user for user in game.users if user.user_id == id), None)

    dealer = game.dealer
    while dealer.getHand().score() < 18:
        dealer.hitMe()
    game.state = GAME_STATE.END_GAME

    game.end_message = 'End of round'

    current_user.setGameResult(game.dealer.getHand())

    game.put()
    GameUpdater(game).send_update()

def betForUser(game, id, betAmount):
    current_user = next((user for user in game.users if user.user_id == id), None)
    current_user.changeBet(betAmount);
    game.put()
    GameUpdater(game).send_update()


class Page(webapp.RequestHandler):
    def get(self):
        return

    def sendGameInfo(self, game, user_id):
        logging.info("parent's sendGameInfo method")  

        game_link = 'http://localhost:8080/?g=' + game.game_key
        token = channel.create_channel(user_id + game.game_key)
        template_values = {'token': token,
                           'game_key': game.game_key,
                           'game_link': game_link
                          }
        path = os.path.join(os.path.dirname(__file__), 'index.html')

        self.response.out.write(template.render(path,template_values))  

class NewPage(Page):
    def get(self):
        id = self.request.get('id')
        game_key = str(generateGameKey())
        logging.info('Creating new game with user: ' + str(id) + " and game_key: " + game_key)
        
        game = createNewGame(game_key, id)
        game.put()
        self.sendGameInfo(game, id);

class MainPage(Page):
    """The main UI page, renders the 'index.html' template."""

    def get(self):
        """Renders the main page. When this page is shown, we create a new
        channel to push asynchronous updates to the client."""

        game_key = self.request.get('g')
        if not game_key:
            self.showGameMenu()
            return

        user_id = self.request.get('id')
        game = Game.query(Game.game_key == game_key).fetch(1)[0]

        if game:
            self.sendGameInfo(game, user_id);
        else:
            self.response.out.write('No such game')

    def showGameMenu(self):
        self.response.out.write('No games! <a href=\'http://localhost:8080/new\'>Create one</a>')



application = webapp.WSGIApplication([
    ('/',       MainPage),
    ('/opened', OpenedPage),
    ('/hit',    HitPage),
    ('/stand',  StandPage),
    ('/bet',    BetPage),
    ('/new',    NewPage),
    ('/test',   Test)], debug=True)


def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()


# delete all previous games
# games = Game.query().fetch()
# for game in games:
#     game.key.delete()
