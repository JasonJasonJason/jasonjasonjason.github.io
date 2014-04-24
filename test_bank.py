import unittest
from banklogic import *

class MyTest(unittest.TestCase):
	def test(self):
		#Test the getUser functionality
		print "Testing api call for getUser/1"
		print "This is the aaron moore account, and is a test account"
		user = getUser(1)
		self.assertEqual(user['id'], 1)
		self.assertEqual(user['email'], 'mooreaarond@gmail.com')
		self.assertEqual(user['screenName'], 'Jack Bauer')
		print str(user)
		print "		Good!"

	def test2(self):
		#Test the requestFunds functionality of Aaron <oore
		print "Testing api call for requestFunds for user_id=1 and amount=100"
		print "Test account, will put money right back in"
		user = getUser(1)
		self.assertEqual(user['id'], 1)
		self.assertEqual(user['email'], 'mooreaarond@gmail.com')
		self.assertEqual(user['screenName'], 'Jack Bauer')
		response = requestFunds(user['id'], 100)
		print str(response)
		print "		Good!"

	def test3(self):
		#Test the addTransaction functionality for Aaron Moore
		print "Testing api call for addTransaction for user_id = 1 and amount = 100"
		print "Test account! No harm no foul"
		user = getUser(1)
		self.assertEqual(user['id'], 1)
		self.assertEqual(user['email'], 'mooreaarond@gmail.com')
		self.assertEqual(user['screenName'], 'Jack Bauer')
		response = addTransaction(user['id'], 100)
		print str(response)
		print "		Good!"

if __name__ == '__main__':
    unittest.main()