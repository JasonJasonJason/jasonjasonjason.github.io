import datetime
import logging
import os
import random
random.seed()
import re
import sys
import time
import json
from gamelogic import *
from banklogic import *
from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext import deferred
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
  waiting_users   = ndb.PickleProperty()
  game_key        = ndb.StringProperty()
  current_user_id = ndb.StringProperty()
  deck            = ndb.PickleProperty()
  state           = ndb.StringProperty()
  end_message     = ndb.StringProperty()
  game_link = ''

  def addUser(self, newUserId):
    if(self.state != GAME_STATE.NEW_GAME):
        if not self.waiting_users:
            self.waiting_users = []
        self.waiting_users.append(User(self.deck, newUserId, True))

    elif not self.users or len(self.users) == 0:
        self.users = [User(self.deck, newUserId, False)]
        self.current_user_id = self.users[0].user_id

    else:
        self.users.append(User(self.deck, newUserId, False))

def generateGameKey():
    return random.randrange(100)

def generateUserId():
    return random.randrange(10)

def createNewGame(game_key):
    deck = Deck()
    deck.shuffle()
    dealer = Dealer(deck)
    return Game(
                game_key        = game_key,
                dealer          = dealer,
                users           = [],
                waiting_users   = [],
                deck            = deck,
                current_user_id = '0',
                state           = GAME_STATE.NEW_GAME,
                end_message     = 'End string...123'
                )
def resetGame(game):
    game.deck = Deck()
    game.deck.shuffle()
    game.dealer = Dealer(game.deck)
    game.users = []
    game.waiting_users = []
    game.current_user_id = '0'
    game.state = GAME_STATE.NEW_GAME
    game.end_message = 'End string...123'
    return game

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
    logging.info('JSON game update: ' + str(json.dumps(gameUpdate, indent=4)))
    return json.dumps(gameUpdate)

  def send_update(self):
    for user in self.game.users:
        message = self.get_game_message_for_user(user)
        channel.send_message(user.user_id + self.game.game_key, message)
    for user in self.game.waiting_users:
        message = self.get_game_message_for_user(user)
        channel.send_message(user.user_id + self.game.game_key, message)

  def send_user_update(self, user, message):
    channel.send_message(user.user_id + self.game.game_key, message)
    

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

class OpenedPage(webapp.RequestHandler):
    def post(self):
        game = GameFromRequest(self.request).get_game()
        GameUpdater(game).send_update()

class ClosedPage(webapp.RequestHandler):
    def post(self):
        logging.info('closed!!!');
        game = GameFromRequest(self.request).get_game()
        id = self.request.get('user_id')

        for i in range(0, len(game.users)):
            if id == game.users[i].user_id: #Find user
                if game.users[i].user_id == game.current_user_id: #Move to next user, if current user
                    onGameStateChanged(game)
                game.users.pop(i) #Remove user
                i = len(game.users)+1 # break from loop

        game.put()

        logging.info('length of users: ' + str(len(game.users)))
        if len(game.users) == 0:
            game.key.delete();

class NewGamePage(webapp.RequestHandler):
    def post(self):
        game = GameFromRequest(self.request).get_game()
        if game.state != GAME_STATE.END_GAME:
            return

        users = game.users
        if game.waiting_users:
            users.extend(game.waiting_users)

        for user in users:
            user.waiting = False

        game = resetGame(game)
        for user in users:
            game.addUser(user.user_id)

        game.state = GAME_STATE.NEW_GAME
        game.put()
        GameUpdater(game).send_update()

        time.sleep(1)

        game.state = GAME_STATE.USER_TURN
        GameUpdater(game).send_update()
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
    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return

    if len(current_user.getHand().cards) < 5:
        current_user.hitMe()
    game.put()
    GameUpdater(game).send_update()

def standForUser(game, id):
    current_user = next((user for user in game.users if user.user_id == id), None)
    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return
    
    onGameStateChanged(game)

def betForUser(game, id, betAmount):
    current_user = next((user for user in game.users if user.user_id == id), None)
    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return

    try:
        current_user.changeBet(betAmount);
        game.put()
        GameUpdater(game).send_update()
    except ValueError, ex:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':str(ex)}))


def finishGame(game):
    game.state = GAME_STATE.END_GAME

    while game.dealer.getHand().score() < 18:
        game.dealer.hitMe()

    for user in game.users:
        user.setGameResult(game.dealer.getHand())

    
def updateGameState(game):
    if game.state == GAME_STATE.USER_TURN:
        for i in range(0, len(game.users)):
            # All users set, end the game
            if i == len(game.users)-1:
                finishGame(game)
                
            # Proceed to next user
            elif game.users[i].user_id == game.current_user_id:
                logging.info("user's turn: " + str(game.users[i].user_id))
                logging.info('len(game.users): '+str(len(game.users)))
                game.current_user_id = game.users[i+1].user_id
                return

def onGameStateChanged(game):
    updateGameState(game)
    game.put()
    GameUpdater(game).send_update()

class Page(webapp.RequestHandler):
    def get(self):
        return

    def sendGameInfo(self, game, user_id):
        token = channel.create_channel(user_id + game.game_key)
        template_values = {
                           'token': token,
                           'game_key': game.game_key
                          }
        path = os.path.join(os.path.dirname(__file__), 'index.html')

        self.response.out.write(template.render(path,template_values))  

class MainPage(Page):
    """The main UI page, renders the 'index.html' template."""

    def get(self):
        game_key = self.request.get('g')
        user_id = self.request.get('userID')

        if not game_key:
            self.showGameMenu()
            return

        games = Game.query(Game.game_key == game_key).fetch(1)
        if games:
            game = games[0]
            game.addUser(user_id)
        else:
            game = createNewGame(game_key)
            game.addUser(user_id)
            game.state = GAME_STATE.USER_TURN

        if game:
            game.put()
            self.sendGameInfo(game, user_id);
        else:
            self.response.out.write('No such game')

    def showGameMenu(self):
        games = Game.query().fetch()
        for game in games:
            game.game_link = 'http://localhost:8080/?g=' + game.game_key

        user_id = generateUserId()
        template_values = { 'games': games, 'user_id':user_id, 'new_game_id':generateGameKey() }
        path = os.path.join(os.path.dirname(__file__), 'menu.html')

        self.response.out.write(template.render(path,template_values))  



application = webapp.WSGIApplication([
    ('/',       MainPage),
    ('/hit',    HitPage),
    ('/stand',  StandPage),
    ('/bet',    BetPage),
    ('/opened', OpenedPage),
    ('/closed', ClosedPage),
    ('/again',  NewGamePage),
    ('/test',   Test)], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()

# delete all previous games
# games = Game.query().fetch()
# for game in games:
#     game.key.delete()
