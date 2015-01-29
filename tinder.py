import json, time, re, sys, datetime, random
import requests
from error import Error
from db import db

generic_tinder_headers = {"platform" : "android",
 "os-version" : "18", "app-version" : "762" , "Accept" : "application/json; charset=utf-8",
 "User-Agent" : "Tinder Android Version 3.3.2", "Accept-Encoding" : "gzip, deflate",
 "Host" : "api.gotinder.com", "Connection" : "Keep-Alive"}

generic_post_tinder_headers = {"platform" : "android",
 "os-version" : "18", "app-version" : "762" , "Accept" : "application/json; charset=utf-8",
 "User-Agent" : "Tinder Android Version 3.3.2", "Accept-Encoding" : "gzip, deflate",
 "Host" : "api.gotinder.com", "Connection" : "Keep-Alive", "Content-type" : "application/json; charset=utf-8"}

SEC_WAIT_FIRST_MESSAGE = 60*15
SEC_SERVER_DIFFERENCE = -2*60*60
TIME_OUT_TINDER = 10000
SLEEP_LIKE_MIN = 2
SLEEP_LIKE_MAX = 3
SLEEP_LIKE_PERIOD = 50
SLEEP_LIKE_PERIOD_MIN = 60
SLEEP_LIKE_PERIOD_MAX = 60*3
SLEEP_MESSAGE_MIN = 1
SLEEP_MESSAGE_MAX = 2
SLEEP_MESSAGE_PERIOD = 60
SLEEP_FORBIDDEN = 5
SLEEP_BEFORE_ANSWERING = 5*60
MAX_MESSAGES_RESPONSES = 40

class tinder():
	token = ''
	base_url = 'https://api.gotinder.com'
	id = ''
	created_date = ''
	web_session = requests.Session()
	MAX_RETRY = 5
	DISLIKE_EACH = 5
	likes_counter = 0
	messages_counter = 0
	sql_lite = db()
	def __init__(self, *args):
		if len(args) == 2:
			self.auth(args[0])
			self.config_user()
			self.update_bio(args[1])
		elif len(args) == 3:
			self.id = args[0]
			self.token = args[1]
			self.created_date = args[2]
		else:
			raise Error(0)

	def print_stats(self):
		print('Likes done ' + str(self.likes_counter - (self.likes_counter/self.DISLIKE_EACH)))
		print('Messages sent ' + str(self.messages_counter))

	def auth(self, fb_token):
		auth_response = self.post('/auth', json.dumps({'facebook_token' : fb_token}), use_token=False)
		if auth_response.status_code == 200:
			json_decoded_response = json.loads(auth_response.text)
			self.token = json_decoded_response['token']
			self.id = json_decoded_response['user']['_id']
			self.created_date = json_decoded_response['user']['create_date']	
		else:
			raise Error(auth_response.status_code)

	def update_bio(self, name):
		payload = json.dumps({"bio":"hi, im {0}. looking for someone fun to chat with!".format(name)})
		bio_response = self.post('/profile', payload)
		if bio_response.status_code != 200:
			raise Error(bio_response.status_code)

	#Gender = 0 -> Male, 1 -> Female, -1 -> Both
	def config_user(self, distance=100, max_age=1000, min_age=18, gender=0, discoverable=True):
		payload = json.dumps({'distance_filter' : distance, 'age_filter_max' : max_age,
		 'age_filter_min' : min_age, 'gender_filter' : gender, 'discoverable' : discoverable})
		config_response = self.post('/profile', payload)
		if config_response.status_code != 200:
			raise Error(config_response.status_code)

	def like(self, id):
		like_response = self.get('/like/' + str(id))
		if like_response.status_code == 200:
                    try:
			if json.loads(like_response.text)['match']:
				print("Liked, match found, user id = " + str(id))
				return True
			else:
				print("Liked, match not found, user id = " + str(id))
				return True
                    except ValueError:
                        print('Error decoding json response')
                        return False
		else:
			raise Error(like_response.status_code)

	def message(self, id, message):
		payload = json.dumps({'message' : message})
		message_response = self.post('/user/matches/' + str(id), payload)
		if message_response.status_code != 200:
			raise Error(message_response.status_code)

	def ping(self, lat, lon):
		payload = json.dumps({'lon' : lon, 'lat' : lat})
		ping_response = self.post('/user/ping', payload)
		if ping_response.status_code != 200:
			raise Error(ping_response.status_code)

	def dislike(self, id):
		dislike_response = self.get('/pass/' + str(id))
		if dislike_response.status_code == 200:
			print('Disliked user id = '+str(id))
			return True
		else:
			raise Error(dislike_response.status_code)

	def get(self, url, use_token=True):
		headers = generic_tinder_headers
		for i in range(self.MAX_RETRY):
			try:
				if use_token:
					headers.update({"X-Auth-Token" : self.token})

				result = self.web_session.get(self.base_url + url, headers=headers, verify=False, timeout=120)
                                if result.status_code == 500 or result.status_code == 504:
                                    raise requests.exceptions.ConnectionError
                                else:
                                    return result

			except (requests.exceptions.ConnectionError,requests.exceptions.Timeout) as e:
				if i == (self.MAX_RETRY-1):
					raise e
				else:
					print('Server connection problem, sleeping and retrying')
					time.sleep(SLEEP_FORBIDDEN)
					continue

	def count_messages(self, messages):
		bot_messages_counter = 0
		for message in messages:
			if message['from'] == self.id:
					bot_messages_counter = bot_messages_counter + 1
		return bot_messages_counter

	def post(self, url, payload, use_token=True):
		for i in range(self.MAX_RETRY):
			try:
				if not use_token:
					result = self.web_session.post(self.base_url + url, data=payload, headers=generic_post_tinder_headers, verify=False, timeout=120)
                                        if result.status_code == 500 or result.status_code == 504:
                                            raise requests.exceptions.ConnectionError
                                        else:
                                            return result
				else:
					headers = generic_post_tinder_headers
					headers.update({"X-Auth-Token" : self.token})
					result = self.web_session.post(self.base_url + url, data=payload, headers=headers, verify=False, timeout=120)
                                        if result.status_code == 500  or result.status_code == 504:
                                            raise requests.exceptions.ConnectionError
                                        else:
                                            return result

			except (requests.exceptions.ConnectionError,requests.exceptions.Timeout) as e:
				if i == (self.MAX_RETRY-1):
					raise e
				else:
					print('Server connection problem, sleeping and retrying')
					time.sleep(SLEEP_FORBIDDEN)
					continue

	def do_likes(self, MAX_LIKES_RETRY):
		payload = json.dumps({'limit' : 40})
		recs_timeout_counter = 0
		while(self.likes_counter <= MAX_LIKES_RETRY):
                    #Try likes retrieval, check if connection gets declined
                    recs_response = self.post("/user/recs", payload)
                    #Response was correct
                    if recs_response.status_code == 200:
                            json_decoded_response = json.loads(recs_response.text)
                            #Check if server has recs exhausted or has timed out
                            if 'message' in json_decoded_response:
                                    #The api sends timeout or exhausted for two reason, it doesnt have more people to mathc
                                    #or it has disabled the token
                                    if (json_decoded_response['message'] == 'recs timeout') or (json_decoded_response['message'] == 'recs exhausted'):
                                            recs_timeout_counter = recs_timeout_counter + 1
                                            if recs_timeout_counter > 10:
                                                    print('Recs timeout exceeded')
                                                    return
                                            else:
                                                    print('Recs timeout, sleeping')
                                                    time.sleep(SLEEP_FORBIDDEN)
                                                    continue
                            #Message has the people to like
                            else:
                                    recs_timeout_counter = 0
                                    for user in json_decoded_response['results']:
                                            #Try liking user, checks for
                                            if not self.sql_lite.has_liked_before(user['_id']):
                                                    try:
                                                            if (self.likes_counter % self.DISLIKE_EACH) == 0:
                                                                    if self.dislike(user['_id']):
                                                                            self.likes_counter += 1
                                                                            print('Dislike done: '+str(self.likes_counter))
                                                                            self.sql_lite.save_like(user['_id'])
                                                            else:
                                                                    if self.like(user['_id']):
                                                                            self.likes_counter += 1
                                                                            print('Likes done: ' +str(self.likes_counter))
                                                                            self.sql_lite.save_like(user['_id'])
                                                            if (self.likes_counter % SLEEP_LIKE_PERIOD) == 0:
                                                                    print('Sleep like period')
                                                                    time.sleep(random.randrange(SLEEP_LIKE_PERIOD_MIN, SLEEP_LIKE_PERIOD_MAX))
                                                    #Catch account banning, stop the liking process
                                                    except Error as e:
                                                            if e.value == 401:
                                                                    return
                                            #Sleep some random time between likes
                                            time.sleep(random.randrange(SLEEP_LIKE_MIN, SLEEP_LIKE_MAX))
                    elif recs_response.status_code == 403 or recs_response.status_code == 401:
                            return
                    else:
                            #Uknown error, raise
                            raise Error(recs_response.status_code)


	def respond(self, messages, page):
		payload = json.dumps({'last_activity_date' : self.created_date})
		updates_response = self.post('/updates', payload)
		if updates_response.status_code == 200:
			#Decode matches
                    try:
                        json_decoded_response = json.loads(updates_response.text)
			print('Matches: ' + str(len(json_decoded_response['matches'])))
			for match in json_decoded_response['matches']:
				print('Length messages: ' + str(len(match['messages'])))
				if len(match['messages']) == 0:
					print('No messages from id '+str(match['_id']) + ' send one')
					self.message(match['_id'], messages['init'])
				else:
					#Check if the last message was from the bot
					print('Checking if last message was from bot')
					if match['messages'][-1]['from'] != self.id:
						print('Last message, wasnt from bot')
						print('Message was: ' + match['messages'][-1]['message'].encode('utf-8'))
						#Check for common words in text
						if re.match('.*(( bot|bot )|( porn|porn )|( spam|spam )|( fake|fake )).*', match['messages'][-1]['message'].encode('utf-8')):
							print('Bot or robot in message, skip')
							continue
						#Count the messages the bot has sent
						bot_messages_counter = self.count_messages(match['messages'])
						#Detect which message to send
						message_to_send = ''
						if match['messages'][0]['from'] == self.id:
							#Bot sent the first message
							if bot_messages_counter == 1:
								print('The bot sent the first message and the user responded from id '+str(match['_id']))
								message_to_send = messages['first_reply'].format(page)
							elif bot_messages_counter == 2:
								print('The bot sent the second message and the user responded from id '+str(match['_id']))
								message_to_send = messages['second_reply'].format(page)
						else:
							#Bot didn't send the first message
							if bot_messages_counter == 0:
								print('The user messaged us first, respond, from id '+str(match['_id']))
								message_to_send = messages['first_reply'].format(page)
							elif bot_messages_counter == 1:
								print('The user messaged us first, respond the second reply, from id '+str(match['_id']))
								message_to_send = messages['second_reply'].format(page)
						try:
							self.message(match['_id'], message_to_send)
							self.messages_counter = self.messages_counter + 1 
						except Error as e:
							if e == 401:
								print('Cant use the token to respond anymore')
								raise Error(401)
                                #Sleep some time between messages
				time.sleep(random.randrange(SLEEP_MESSAGE_MIN, SLEEP_MESSAGE_MAX))

                    except ValueError:
                        print('Error decoding the messages response')

		else:
			raise Error(updates_response.status_code)


