import sqlite3
import sys

def conn():
	global dbpath
	return sqlite3.connect(dbpath)

def createMailBox():
	connection = conn()
	try:
		connection.execute('create table if not exists mailbox ("from" text not null,"to" text not null,"ip" text not null,"data" text not null)')
		connection.commit()
	finally:
		connection.close()

def insert(data):
	connection = conn()
	try:
		connection.execute('insert into mailbox values ("%s", "%s", "%s", "%s")' % (data.mfrom, data.mto, data.ip, data.data))
		connection.commit()
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
dbpath = base_dir + '/mailbox.db'
createMailBox()