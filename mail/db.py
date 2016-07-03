import sqlite3
import sys
import time

def conn():
	global dbpath
	return sqlite3.connect(dbpath)

def save(fname, data):
	global home_dir
	f = open(home_dir + '/mailbox/eml/' + fname, 'w')
	f.write(data)
	f.close()

def createMailBox():
	connection = conn()
	try:
		connection.execute('create table if not exists mailbox ([from] text not null,[to] text not null,[ip] text not null,[name] text not null,[date] datetime default (datetime(\'now\', \'+8 hour\')))')
		connection.commit()
	finally:
		connection.close()

def insert(data):
	connection = conn()
	try:
		fname = data.mfrom + '_' + str(int(time.time() * 1000)) + '.eml'
		connection.execute('insert into mailbox ([from], [to], [ip], [name]) values ("%s", "%s", "%s", "%s")' % (data.mfrom, data.mto, data.ip, fname))
		connection.commit()
		save(fname, data.data)
	finally:
		connection.close()

def select():
	connection = conn()
	cu = connection.cursor()
	try:
		cu.execute('select * from mailbox')
		res = cu.fetchall()
		cu.close()
	finally:
		connection.close()
		return res

base_dir = sys.argv[1]
home_dir = base_dir + '/mail'
dbpath = home_dir + '/mailbox.db'
createMailBox()