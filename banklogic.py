import urllib
import urllib2
import json

def getUser(user_id):
	url = 'http://casino.curtiswendel.me:3000/api/getUser/' + str(user_id)
	response = urllib2.urlopen(url)
	return json.load(response)  

def requestFunds(user_id, amount):
	url = 'http://casino.curtiswendel.me:3000/api/requestFunds/'
	return postRequest(url, user_id, amount)

def addTransaction(user_id, amount):
	url = 'http://casino.curtiswendel.me:3000/api/addTransaction/'
	return postRequest(url, user_id, amount)

def postRequest(url, user_id, amount):
	data = urllib.urlencode({
	  'userID': user_id,
	  'amount': amount,
	  'gameID': 1
	})
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	return response.read()