#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.

# pylint: disable-msg=C6310

"""Channel Tic Tac Toe

This module demonstrates the App Engine Channel API by implementing a
simple tic-tac-toe game.
"""

import datetime
import logging
import os
import random
random.seed()
import re
import sys
from django.utils import simplejson
from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class Game(ndb.Model):
  """All the data we store for a game"""
  dealer   = ndb.PickleProperty()
  user     = ndb.PickleProperty()
  game_key = ndb.StringProperty()
  user_id  = ndb.StringProperty()

def createNewGame(game_key):
  return Game(
                game_key = game_key,
                dealer   = Dealer().getHand().cards,
                user     = User().getHand().cards,
                user_id  = 'JasonHarris'
              )


class GameUpdater():
  game = None

  def __init__(self, game):
    self.game = game

  def get_game_message(self):
    gameUpdate = {
      'dealer': self.game.dealer,
      'user'  : self.game.user
    }
    logging.info('JSON game update: ' + str(simplejson.dumps(gameUpdate)))
    return simplejson.dumps(gameUpdate)

  def send_update(self):
    message = self.get_game_message()
    channel.send_message(self.game.user_id + self.game.game_key, message)
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


class MainPage(webapp.RequestHandler):
  """The main UI page, renders the 'index.html' template."""

  def get(self):
    """Renders the main page. When this page is shown, we create a new
    channel to push asynchronous updates to the client."""

    #delete all previous games
    games = Game.query().fetch()
    for game in games:
      game.key.delete()

    user_id = 'JasonHarris'
    game_key = self.request.get('g')
    game = None
    if not game_key:
        game_key = '12345'
        logging.info('creating new game')
        game = createNewGame(game_key)
        game.put()
    else:
        logging.info('getting old game from db')
        game = Game.query(Game.game_key == game_key).fetch(1)[0]

    game_link = 'http://localhost:8080/?g=' + game_key

    if game:
        token = channel.create_channel(user_id + game_key)
        template_values = {'token': token,
                           'game_key': game_key,
                           'game_link': game_link
                          }
        path = os.path.join(os.path.dirname(__file__), 'index.html')

        self.response.out.write(template.render(path,template_values))
    else:
        self.response.out.write('No such game')


class Hand(object):
  all_cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]

  def __init__(self):
    self.cards = []
    self.cards.append(random.choice(self.all_cards));
    self.cards.append(random.choice(self.all_cards));

  def hitMe():
    if len(cards) < 5:
      cards.append(random.choice(cards));

  def total():
      aces = cards.count(11)
      t = sum(cards)
      if t > 21 and aces > 0:
          while aces > 0 and t > 21:
              t -= 10
              aces -= 1
      return t

class Dealer():
  def __init__(self):
    self.hand = Hand()

  def getHand(self):
    return self.hand


class User():
  def __init__(self):
    self.hand = Hand()

  def getHand(self):
    return self.hand



application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/opened', OpenedPage),
    ('/move', MovePage)], debug=True)


def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
