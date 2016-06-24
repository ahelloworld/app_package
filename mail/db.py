import pymysql.cursors

def conn():
	global db_password
	connection = pymysql.connect(
		host='127.0.0.1',
		port=3306,
		user='root',
		password=db_password,
		db='mailbox',
		charset='utf8mb4',
		cursorclass=pymysql.cursors.DictCursor)
	return connection

def createMailBox():
	connection = conn()
	try:
		with connection.cursor() as cursor:
			sql = 'create table if not exists `mailbox` (`from` varchar(100) not null,`to` varchar(100) not null,`ip` varchar(20) not null,`data` text not null)'
			cursor.execute(sql)
		connection.commit()
	finally:
		connection.close()

def insert(data):
	connection = conn()
	try:
		with connection.cursor() as cursor:
			sql = 'insert into `mailbox` (`from`, `to`, `ip`, `data`) values (%s, %s, %s, %s)'
			cursor.execute(sql, (data.mfrom, data.mto, data.ip, data.data))
		connection.commit()
	finally:
		connection.close()

def select():
	connection = conn()
	try:
		with connection.cursor() as cursor:
			sql = 'select `from`, `to`, `ip`, `data` from `mailbox`'
			cursor.execute(sql)
			res = cursor.fetchall()
	finally:
		connection.close()
		return res

base_dir = sys.argv[1]
f = open(base_dir + '/mail/key.txt')
db_password = f.read()
f.close()
createMailBox()