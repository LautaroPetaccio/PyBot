import re
import json, time, re, sys, datetime, random
import requests
from error import Error


generic_facebook_headers = {"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
 "Accept-Encoding" : "gzip, deflate", "Accept-Language" : "en-US,en;q=0.5",
 "User-Agent" : "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19",
 "Connection" : "Keep-Alive"}

#Compiled regex
lsd_regex = re.compile('.*name="lsd" value="(.*?)".*', re.DOTALL)
nh_regex = re.compile('.*name="nh" value="(.*?)".*', re.DOTALL)
access_token_regex = re.compile('.*access_token=(.*?)&expires.*', re.DOTALL)
captcha_persist_data_regex = re.compile('.*captcha_persist_data" value="(.*?)".*', re.DOTALL)
li_regex = re.compile('.*"li" value="(.*?)".*', re.DOTALL)
fb_dtsg_regex = re.compile('.*name="fb_dtsg" value="(.*?)".*', re.DOTALL)
mobile_fb_dtsg_regex = re.compile('.*name=\\\\\"fb_dtsg\\\\" value=\\\\"(\w*)', re.DOTALL)
access_token_regex = re.compile('.*access_token=(.*?)&expires.*',re.DOTALL)
#name_regex = re.compile('.*</a> \((.*)\)</span>.*',re.DOTALL)
name_regex = re.compile('.*profilePicture profpic\\\\" aria-label=\\\\"(\w+\s\w+)', re.DOTALL)  
revision_regex = re.compile('.*{"revision":(\d*),.*', re.DOTALL)
user_id_regex = re.compile('.*{"USER_ID":\"(\d.*)\","ACCOUNT_ID":', re.DOTALL)
user_page_regex = re.compile('.*<a href="/(.*)?v=photos', re.DOTALL)

class facebook():
	MAX_RETRY = 10
	web_session = requests.Session()
	base_url_mobile = "https://m.facebook.com"
	base_url_desktop = "https://www.facebook.com"
        base_url_upload = 'https://upload.facebook.com'
        #base_url_upload = 'http://httpbin.org/post'
	name = ''
	def __init__(self, id, password):
                print('Logging in')
		self.name = self.auth(id, password)
                print('Got name: ' + str(self.name))

        def get_user_name(self):
            return self.name

	def post(self, url, payload, headers={}, mobile=True, allow_redirects=True, upload=False):
		for i in range(self.MAX_RETRY):
			try:
				post_headers = generic_facebook_headers
				#post_headers.update({"Content-Type" : "application/x-www-form-urlencoded"})
				post_headers.update(headers)
				if(mobile):
					req_url = self.base_url_mobile + url
				else:
					req_url = self.base_url_desktop + url
                                if not upload:
				    return self.web_session.post(self.base_url_mobile + url, data=payload, headers=post_headers, 
				        allow_redirects=allow_redirects, verify=False, timeout=120)
                                else:
				    return self.web_session.post(self.base_url_upload + url, data=payload, files=upload, headers=post_headers, 
				        allow_redirects=allow_redirects, verify=False, timeout=120)

			except (requests.exceptions.ConnectionError,requests.exceptions.Timeout) as e:
				if i == (self.MAX_RETRY-1):
					raise e
				else:
					print('Server connection problem, sleeping and retrying')
					time.sleep(SLEEP_FORBIDDEN)
					continue

	def get(self, url, headers={}, mobile=True):
		for i in range(self.MAX_RETRY):
			try:
				get_headers = generic_facebook_headers
				get_headers.update(headers)
				if(mobile):
					req_url = self.base_url_mobile + url
				else:
					req_url = self.base_url_desktop + url
				return self.web_session.get(self.base_url_mobile + url, headers=get_headers, verify=False, timeout=120)

			except (requests.exceptions.ConnectionError,requests.exceptions.Timeout) as e:
				if i == (self.MAX_RETRY-1):
					raise e
				else:
					print('Server connection problem, sleeping and retrying')
					time.sleep(SLEEP_FORBIDDEN)
					continue

	def __login(self, email, password):
		home_response = self.get('', mobile=True)
		if home_response.status_code != 200:
			raise Error(home_response.status_code)

		#Prepare headers
		headers = {"Referer" : "https://m.facebook.com/"}

		home_response_content = home_response.text
	 	lsd_match = lsd_regex.match(home_response_content)
	 	li_match = li_regex.match(home_response_content)
	 	#Get the content from the home page to send
	 	if lsd_match and li_match:
			payload = {'lsd' : lsd_match.group(1), 'charset_test' : '%E2%82%AC%2C%C2%B4%2C%E2%82%AC%2C%C2%B4%2C%E6%B0%B4%2C%D0%94%2C%D0%84',
			'version' : '1', 'ajax' : '0', 'width' : '0', 'pxr' : '0', 'gps' : '0', 'm_ts' : str(int(time.time())), 'li' : li_match.group(1), 'trynum' : '1',
			'spw' : '0', 'email' : email, 'pass' : password, 'login' : 'Log+In'}
			login_response = self.post("/login.php?refsrc=https://m.facebook.com/&refid=8", payload, headers=headers, mobile=True)
			if login_response.status_code == 200:
				return login_response.text
			else:
				raise Error(login_response.status_code)
		else:
			raise Error('Could not retrieve lsd and li from home page')

	def __get_oauth(self):
		oauth_response = self.get('/v1.0/dialog/oauth?redirect_uri=fbconnect://' \
			'success&scope=user_interests,user_likes,email,user_about_me,user_birthday,user_education_history,' \
			'user_location,user_activities,user_relationship_details,user_photos,' \
			'user_status&type=user_agent&client_id=464891386855067&_rdr', mobile=False)
		if oauth_response.status_code == 200:
			return oauth_response.text
		else:
			raise Error(oauth_response.status_code)

	def __get_tinder_token(self, verification):
		headers = {"Referer" : "https://www.facebook.com/v1.0/dialog/oauth?redirect_uri=fbconnect://" \
		'success&scope=user_interests,user_likes,email,user_about_me,user_birthday,' \
		"user_education_history,user_location,user_activities,user_relationship_details," \
		"user_photos,user_status&type=user_agent&client_id=464891386855067&_rdr", "Host" : "www.facebook.com"}

		ttstamp = self.__generate_ttstamp(verification['fb_dtsg'])

		payload = {'__CONFIRM__' : 1, '__a' : 1, '__dyn' : '', '__req' : 1, '__rev' : verification['revision'], '__user' : verification['user_id'],
		'access_token' : '', 'app_id' : '464891386855067', 'auth_nonce' : '', 'auth_token' : '', 'auth_type' : '', 'confirm' : '', 'default_audience' : '',
		'display' : 'page', 'domain' : '', 'extended' : '', 'fb_dtsg' : verification['fb_dtsg'], 'from_post' : 1, 'gdp_version' : 3,
		'login' : '', 'private' : '', 'public_info_nux' : 1, 'read' : 'user_interests,user_likes,email,user_about_me,'
		'user_birthday,user_education_history,user_location,user_activities,user_relationship_details,user_photos,user_status,public_profile,user_friends,baseline',
		'readwrite' : '', 'redirect_uri' : 'fbconnect://success', 'ref' : 'Default', 'return_format' : 'access_token', 'sdk' : '',
		'seen_scopes' : 'user_interests,user_likes,email,user_about_me,user_birthday,user_education_history,user_location,user_activities,'
		'user_relationship_details,user_photos,user_status,public_profile,user_friends,baseline', 'social_confirm' : '', 'sso_device' : '',
		'ttstamp' : ttstamp, 'write' : ''}

		tinder_token_response = self.post('/v1.0/dialog/oauth/read', payload,
		 headers=headers, allow_redirects=False, mobile=False)

		if tinder_token_response.status_code == 200:
			return tinder_token_response.text
		else:
			raise Error(tinder_token_response.status_code)

	def __generate_ttstamp(self, fb_dtsg):
		ttstamp = ''
		u = ''
		for c in fb_dtsg:
			u = u + str(ord(c))
		ttstamp = '2' + u
		return ttstamp

	def auth(self, id, password):
		login_response = self.__login(id, password)
		if 'notifications.php' in login_response:
			name_match = name_regex.match(login_response)
			if name_match:
				return name_match.group(1)
			else:
				raise Error('Error getting name')
		#Check if the account asks for phone security, skip it
		# if login_response.find('Help Secure Your Account') != -1:
		# 	login_response = facebook_phonesecure(requests_session)

	def get_token(self):
		oauth_response = self.__get_oauth()
		#fb = open('oauth_response.html', 'w')
		#fb.write(oauth_response.encode('utf-8'))
		#fb.close()
		fb_dstg_match = fb_dtsg_regex.match(oauth_response)
		user_id_match = user_id_regex.match(oauth_response)
		revision_match = revision_regex.match(oauth_response)
		if fb_dstg_match and user_id_match and revision_match:
			verification = {'fb_dtsg' : fb_dstg_match.group(1), 'user_id' : user_id_match.group(1), 'revision' : revision_match.group(1)}
			facebook_tinder_token_response = self.__get_tinder_token(verification)
			#fd = open('facebook_tinder_token_response.html', 'w')
			#fd.write(facebook_tinder_token_response.encode('utf-8'))
			#fd.close()
			access_token_match = access_token_regex.match(facebook_tinder_token_response)
			if access_token_match:
				return access_token_match.group(1)
			else:
				#Raiseo error si no lo encunetra
				raise Error('Error, access token was not found')
				#fd = open('facebook_tinder_token_response.html', 'w')
				#fd.write(facebook_tinder_token_response.encode('utf-8'))
				#fd.close()
		else:
			raise Error('Error getting the information for the tinder token')
        def upload_picture(self, path):
            home_response = self.get('', mobile=True)
            if home_response.status_code != 200:
                raise Error(home_response.status_code)
            home_response_content = home_response.text
            #f = open('home_verification.html', 'w')
            #f.write(home_response_content.encode('utf-8'))
            #f.close()
	    fb_dstg_match = mobile_fb_dtsg_regex.match(home_response_content)
            if fb_dstg_match: 
                payload = {'fb_dtsg' : fb_dstg_match.group(1), 'charset_test' : '%E2%82%AC%2C%C2%B4%2C%E2%82%AC%2C%C2%B4%2C%E6%B0%B4%2C%D0%94%2C%D0%84'}
                files = {'pic' : open(path, 'rb')}
                upload_response = self.post('/_mupload_/composer/?profile&domain=m.facebook.com&ref=m_upload_pic'
                        '&waterfall_source=m_upload_pic&return_uri=https%3A%2F%2Fm.facebook.com%2Fdagmar.beal'
                        '&return_uri_error=https%3A%2F%2Fm.facebook.com%2Fdagmar.beal&pp_source=timeline', payload, mobile=True, upload=files)
                
                if(upload_response.status_code != 200):
                    print('Error uploading file')
                    raise Error(upload_response.status_code)
            else:
                print('Error verification')
                raise Error('Error finding the verification for the file upload')

	def change_date(self, day, month, year):
            print('Set date to ' + str(day) + '/' + str(month) + '/' + str(year))
            editbirthday_response = self.get('/editprofile.php?type=basic&edit=birthday&ref=bookmark', mobile=True)
            if editbirthday_response.status_code != 200:
                raise Error(editbirthday_response.status_code)

            editbirthday_text_response = editbirthday_response.text
            privacy_regex = re.compile('.*privacy\[(\d+)\]" value="(\d+)', re.DOTALL)
            privacy_regex_match = privacy_regex.match(editbirthday_text_response)
            if not privacy_regex_match:
                f = open('editbirthday.html', 'w')
                f.write(editbirthday_text_response.encode('utf-8'))
                f.close()
                raise Error('Privacy regex was not found changing date')

            privacy = 'privacy[' + privacy_regex_match.group(1) + ']'
            privacy_val = privacy_regex_match.group(2)

            fb_dtsg_regex_match = fb_dtsg_regex.match(editbirthday_text_response)
            if not fb_dtsg_regex_match:
                raise Error('Error getting fb_dstg while changing date')

            dstg = fb_dtsg_regex_match.group(1)
            payload = {'charset_test' : '%E2%82%AC%2C%C2%B4%2C%E2%82%AC%2C%C2%B4%2C%E6%B0%B4%2C%D0%94%2C%D0%84',
                    'day' : day, 'month' : month, 'year' : year, 'fb_dtsg' : dstg, 'type' : 'basic', 'edit' :'birthday',
                    privacy : privacy_val}

            editbirthday_response = self.post('/a/editprofile.php?ref=bookmark', payload, mobile=True)
            if editbirthday_response.status_code != 200:
                print('Error changing the birthday date')
                raise Error(editbirthday_response.status_code)
