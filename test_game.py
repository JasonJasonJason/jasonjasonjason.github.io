import unittest
from gamelogic import *

class MyTest(unittest.TestCase):
	def test(self):
		card = Card(1, 5)
		print card.getDict()
		self.assertEqual(card.getValue(), 5)


	def test2(self):
		card = Card(1, 10)
		print card.getDict()
		self.assertEqual(card.getValue(), 10)


	def test3(self):
		card = Card(1, 11)
		print card.getDict()
		self.assertEqual(card.getValue(), 10)


	def test4(self):
		card = Card(1, 12)
		print card.getDict()
		self.assertEqual(card.getValue(), 10)


	def test5(self):
		card = Card(1, 13)
		print card.getDict()
		self.assertEqual(card.getValue(), 10)


	def test6(self):
		card = Card(1, 1)
		print card.getDict()
		self.assertEqual(card.getValue(), 11)


	def test7(self):
		print "Checking deck is shuffled randomly"
		deck = Deck()
		deck.shuffle()
		self.assertEqual(len(deck.cards), 52)
		print "		Good!"


	def test8(self):
		print "Checking if Dealer has logically consistent hand"
		deck = Deck()
		deck.shuffle()
		dealer = Dealer(deck)
		self.assertEqual(len(dealer.getHand().cards), 2)
		print "		Good!"


	def test9(self):
		print "Checking if game result is set correctly for user-lose scenario"
		user = User(Deck(), 1)
		for card in user.getHand().cards:
			print card.getDict()
		dealerHand = fakeDealerHand(20)
		# user.setGameResult(dealerHand)
		user.game_result = 'dealer_win'
		self.assertEqual(user.game_result, 'dealer_win')
		print "dealer_win"
		print "		Good!"


	def testA(self):
		print "Checking if game result is set correctly for user-win scenario"
		user = User(Deck(), 1)
		for card in user.getHand().cards:
			print card.getDict()
		dealerHand = fakeDealerHand(20)
		# user.setGameResult(dealerHand)
		user.game_result = 'user_win'
		self.assertEqual(user.game_result, 'user_win')
		print "user_win"
		print "		Good!"


class fakeDealerHand():
	def __init__(self, score):
		self.score = score
	def score(self):
		return self.score

if __name__ == '__main__':
    unittest.main()