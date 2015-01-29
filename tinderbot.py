import json, time, re, sys, datetime, random
import requests, signal, argparse
from error import Error
from db import db
from tinder import tinder
from facebook import facebook
from glob import glob
import shutil
import random
import sqlite3
import platform

#Declares para user agent, max likes retry, timeout, sleep forbidden


#mobile_get_photos('.*/photo.php?fbid=\d+&id=\d+&.*')


#Prevenir jsons mal formateados
#Mensajes

# generic_facebook_headers = {"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#  "Accept-Encoding" : "gzip, deflate", "Accept-Language" : "en-US,en;q=0.5",
#  "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0",
#  "Connection" : "Keep-Alive"}

#Otro
#Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25

# generic_facebook_headers = {"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#  "Accept-Encoding" : "gzip, deflate", "Accept-Language" : "en-US,en;q=0.5",
#  "User-Agent" : "Mozilla/5.0 (iPad; U; CPU iPhone OS 5_1_1 like Mac OS X; en_US) AppleWebKit "
#  "(KHTML, like Gecko) Mobile [FBAN/FBForIPhone;FBAV/4.1.1;FBBV/4110.0;FBDV/iPad2,1;FBMD/iPad;FBSN/iPhone OS;FBSV/5.1.1;FBSS/1;"
#  " FBCR/;FBID/tablet;FBLC/en_US;FBSF/1.0]", "Connection" : "Keep-Alive"}
UPLOAD_PHOTOS = True
MAX_LIKES_RETRY = 1300
MAX_MESSAGES_RESPONSES = 22
UPLOAD_PHOTOS = False
CHANGE_DATE = False
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

def get_tinder_messages():
	try:
		fd = open('messages.txt', 'r')
		languages = []
		messages_list = []
		for line in fd:
			content = line.split('|')
			if content[0] in languages:
				messages_list[languages.index(content[0])]['messages'][content[1]] = content[2]
			else:
				languages.append(content[0])
				messages_list.append({'messages' : {'init' : '', 'first_reply' : '', 'second_reply' : ''}})
				messages_list[-1]['messages'][content[1]] = content[2]

		fd.close()
		return dict(zip(languages, messages_list))
	except IOError:
		sys.exit('Error opening messages.txt')


def new_worker(user, messages, page):
	if not 'tinder_token' in user:
		print('Gettin facebook token for the first time')
                fb_user = facebook(user['email'], user['passwd'])
                if UPLOAD_PHOTOS:
                    print('Uploading photos')
                    if platform.system() != 'Windows':
                        new_photos = glob('newphotos/*.jpg') +  glob('newphotos/*.png')
                    else:
                        new_photos = glob('newphotos\*.jpg') +  glob('newphotos\*.png')
                    if len(new_photos) >= 3:
                        fb_user.upload_picture(new_photos[0])
                        fb_user.upload_picture(new_photos[1])
                        fb_user.upload_picture(new_photos[2])

                        if platform.system() != 'Windows':
                            shutil.move(new_photos[0], new_photos[0].replace('newphotos/', 'oldphotos/'))
                            shutil.move(new_photos[1], new_photos[1].replace('newphotos/', 'oldphotos/'))
                            shutil.move(new_photos[2], new_photos[2].replace('newphotos/', 'oldphotos/'))
                        else:
                            shutil.move(new_photos[0], new_photos[0].replace('newphotos\\', 'oldphotos\\'))
                            shutil.move(new_photos[1], new_photos[1].replace('newphotos\\', 'oldphotos\\'))
                            shutil.move(new_photos[2], new_photos[2].replace('newphotos\\', 'oldphotos\\'))

                        print('Photos uploaded')
                    else:
                        raise Error('Less than 3 photos in newphotos folder')
                if CHANGE_DATE:
                    fb_user.change_date(11, 7, 1994)
                user['fb_token'] = fb_user.get_token()
                user['fb_name'] = fb_user.get_user_name()
                print('User name ' + user['fb_name'])
	try:
		if not 'tinder_token' in user:
			print('Getting tinder token')
			tinder_user = tinder(user['fb_token'], user['fb_name'])
		else:
			tinder_user = tinder(user['tinder_id'], user['tinder_token'], user['tinder_created_date'])

		print('User loged in, saving')
		database = db()
		database.save_user(user['email'], user['fb_name'], tinder_user.id, tinder_user.token, tinder_user.created_date)

		while(True):
			try:
				tinder_user.ping(user['lat'], user['lon'])
			except Error as e:
				print('Error ' + str(e.value) + ' while doing ping, skipping action')

			if not FORGET_LIKING:
				try:
				    tinder_user.do_likes(MAX_LIKES_RETRY)
				except KeyboardInterrupt:
					print('Liking skipped, press Control+C again to exit')
					#Wait ten seconds for a new Control+C
					time.sleep(10)
				except Error as e:
					print('Error ' + str(e.value) + ' while doing likes, closing app')
					tinder_user.print_stats()
					return


			try:
                            print('Page to send: ' + page + user['fb_name'].replace(' ', '_'))
                            for i in range(MAX_MESSAGES_RESPONSES):
				tinder_user.respond(messages, page + user['fb_name'].replace(' ', '.'))
				print('Sleeping before aswering messages')
				time.sleep(SLEEP_BEFORE_ANSWERING)
			except KeyboardInterrupt:
				print('Responding skipped, press Control+C again to exit')
				#Wait ten seconds for a new Control+C
				time.sleep(10)
			except Error as e:
				print('Error ' + str(e.value) + ' while responding messages, closing app')
				tinder_user.print_stats()
				return
	except KeyboardInterrupt:
		print('Exiting, stats:')
		tinder_user.print_stats()
		return
	except (requests.exceptions.ConnectionError,requests.exceptions.Timeout) as e:
		print('Connection error, closing app')
		tinder_user.print_stats()
		return


def save_user(fb_id, fb_name, tinder_id, tinder_token, tinder_created_date):
	sqlite = sqlite3.connect('likes.db')
	sql_cursor = sqlite.cursor()
	sql_cursor.execute("SELECT * FROM users WHERE fb_id = " + str(fb_id))
	if sql_cursor.fetchone() == None:
		sql_cursor.execute("INSERT INTO users VALUES ("+str(fb_id)+", '"+fb_name+"', '"+tinder_id+"', '"+tinder_token+"', '"+tinder_created_date+"')")
	else:
		sql_cursor.execute("UPDATE  users SET fb_name = '"+fb_name+"', tinder_id = '"+tinder_id+
			"', tinder_token = '"+tinder_token+"', tinder_created_date = '"+tinder_created_date+"' WHERE fb_id = " + str(fb_id))
	sqlite.commit()
	sqlite.close()


def load_user(fb_id):
	sqlite = sqlite3.connect('likes.db')
	sql_cursor = sqlite.cursor()
	sql_cursor.execute("SELECT * FROM users WHERE fb_id = " + str(fb_id))
	row = sql_cursor.fetchone()
	sqlite.close()
	if row == None:
		print('User not found in db')
		raise Error(0)

	return {'email' : row[0], 'fb_name' : row[1], 'tinder_id' : row[2], 'tinder_token' : row[3], 'tinder_created_date' : row[4]}

def main():
	#users = get_fb_users()
	#pages = get_promoted_pages()
	messages = get_tinder_messages()
	# fb_user:fb_password
	global MAX_LIKES_RETRY
	global MAX_MESSAGES_RESPONSES
	global FORGET_LIKING
        global UPLOAD_PHOTOS
        global CHANGE_DATE
	parser = argparse.ArgumentParser(description='TinderBot 0.1')
	parser.add_argument('--fb', type=str,
	                   help='Facebook username and password separated with the : character',
	                   required=True)

	parser.add_argument('--lat', type=float, help='Tinder latitude', required=True)
	parser.add_argument('--lon', type=float, help='Tinder longitude', required=True)
	parser.add_argument('--page', type=str, help='Tinder promotion page', required=True)
	parser.add_argument('--max-likes', type=int, help='Tinder likes before answering', default=1300)
	parser.add_argument('--max-responses', type=int, help='Tinder messages responses before liking again', default=22)
	parser.add_argument('--forget-liking', type=bool, help='Dont like tinder users', default=False)
	parser.add_argument('--load-user', type=bool, help='Load previous user', default=False)
        parser.add_argument('--upload-photos', type=bool, help='Upload 2 photos', default=False)
        parser.add_argument('--change-date', type=bool, help='Change fb date', default=False)
	args = parser.parse_args()

	if len(args.fb.split(':')) != 2:
		sys.exit('Wrong format for the --fb parameter')
	user = {'email' : args.fb.split(':')[0], 'passwd' : args.fb.split(':')[1], 'lat' : args.lat,
		'lon' : args.lon}

	if args.load_user:
		user.update(load_user(user['email']))

	#message = {'init' : args['init'], 'first_reply' : args['first'], 'second_reply' : args['second']}
	MAX_LIKES_RETRY = args.max_likes
	MAX_MESSAGES_RESPONSES = args.max_responses
	FORGET_LIKING = args.forget_liking
        UPLOAD_PHOTOS = args.upload_photos
        CHANGE_DATE = args.change_date
	print('Started at :' + str(datetime.datetime.today()))
	try:
		#single_worker(user, messages['EN']['messages'], [args.page])
		new_worker(user, messages['EN']['messages'], args.page)
		print('Finished at: ' + str(datetime.datetime.today()))
	except Error as e:
		if e.value == 401:
                    print('Account blocked')
                else:
                    print('Error: ' + str(e.value))
		print('Finished at: ' + str(datetime.datetime.today()))
                sys.exit('Closing')

if __name__ == "__main__":
	main()
