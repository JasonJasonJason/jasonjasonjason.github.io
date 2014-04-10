import urllib

from google.appengine.api import urlfetch

def test():
	url = 'http://heroku-team-bankin.herokuapp.com/services/account/deposit'

	form_fields = {
	  'email': 'coolguy9@example.com',
	  'deposit': 100
	}

	form_data = urllib.urlencode(form_fields)
	result = urlfetch.fetch(url=url,
	  payload=form_data,
	  method=urlfetch.PUT,
	  headers={'Content-Type': 'application/x-www-form-urlencoded'}
	)

	return result