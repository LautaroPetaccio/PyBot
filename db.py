from error import Error
import sqlite3

class db():
	sqlite = None
	def __init__(self):
		self.sqlite = sqlite3.connect('likes.db')

	def __del__(self):
		self.sqlite.close()

	def save_like(self, id):
		sql_cursor = self.sqlite.cursor()
		sql_cursor.execute("INSERT OR IGNORE INTO likes VALUES ('"+id+"')")
		self.sqlite.commit()

	def save_user(self, fb_id, fb_name, tinder_id, tinder_token, tinder_created_date):
		sql_cursor = self.sqlite.cursor()
		sql_cursor.execute("SELECT * FROM users WHERE fb_id = " + str(fb_id))
		if sql_cursor.fetchone() == None:
			sql_cursor.execute("INSERT INTO users VALUES ("+str(fb_id)+", '"+fb_name+"', '"+tinder_id+"', '"+tinder_token+"', '"+tinder_created_date+"')")
		else:
			sql_cursor.execute("UPDATE  users SET fb_name = '"+fb_name+"', tinder_id = '"+tinder_id+
				"', tinder_token = '"+tinder_token+"', tinder_created_date = '"+tinder_created_date+"' WHERE fb_id = " + str(fb_id))
		self.sqlite.commit()

	def load_user(self, fb_id):
		sql_cursor = self.sqlite.cursor()
		sql_cursor.execute("SELECT * FROM users WHERE fb_id = " + str(fb_id))
		row = sql_cursor.fetchone()
		if row == None:
			print('User not found in db')
			raise Error(0)

		return {'email' : row[0], 'fb_name' : row[1], 'tinder_id' : row[2], 'tinder_token' : row[3], 'tinder_created_date' : row[4]}

	def has_liked_before(self, id):
		sql_cursor = self.sqlite.cursor()
		sql_cursor.execute("SELECT COUNT(id) FROM likes WHERE id = ?",(id,))
		if sql_cursor.fetchone()[0] == 1:
			return True
		else:
			return False
