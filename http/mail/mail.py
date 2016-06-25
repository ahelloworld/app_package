import random
import gzip
import sys
import sqlite3
import json
import StringIO

base_dir = sys.argv[1]
home_dir = base_dir + '/mail'
f = open(home_dir + '/key.txt', 'r')
user = f.readline().strip()
passwd = f.readline().strip()
f.close()

key = str(random.randint(0,100000000000))

def login(u, p):
	global user
	global passwd
	global key
	if u.strip() == user and p.strip() == passwd:
		return key
	else:
		return None

def check(k):
	global key
	if k == key:
		return True
	else:
		return False

def rfile(fpath):
	global home_dir
	if fpath.find('..') != -1:
		return None
	try:
		f = open(home_dir + '/mailbox' + fpath, 'r')
		data = f.read()
		f.close()
		zbuf = StringIO.StringIO()
		gziper = gzip.GzipFile(mode = 'wb', compresslevel = 9, fileobj = zbuf)
		gziper.write(data)
		gziper.close()
		text = zbuf.getvalue()
		data = 'HTTP/1.1 200 OK\r\nServer: MailServer\r\nConnection: keep-alive\r\nContent-Encoding: gzip\r\nContent-Length: '
		data += str(len(text)) + '\r\n'
		if fpath[-4:] == 'html':
			data += 'Content-Type: text/html;charset=utf-8\r\n\r\n'
		else:
			data += 'Content-Type: application/octet-stream\r\nAccept-Ranges: bytes\r\n\r\n'
		data += text
		return data
	except:
		return None

def errjson():
	text = json.dumps({'res':-1})
	data = 'HTTP/1.1 200 OK\r\nServer: MailServer\r\nConnection: keep-alive\r\nContent-Length: '
	data += str(len(text)) + '\r\n'
	data += 'Content-Type: application/json;charset=utf-8\r\n\r\n'
	data += text
	return data

def mailbox():
	global home_dir
	dbpath = home_dir + '/mailbox.db'
	connection = sqlite3.connect(dbpath)
	cu = connection.cursor()
	try:
		cu.execute('select * from mailbox')
		text = cu.fetchall()
		cu.close()
		dt = {}
		dt['res'] = 0
		dt['data'] = text
		dt = json.dumps(dt)
		zbuf = StringIO.StringIO()
		gziper = gzip.GzipFile(mode = 'wb', compresslevel = 9, fileobj = zbuf)
		gziper.write(dt)
		gziper.close()
		text = zbuf.getvalue()
		data = 'HTTP/1.1 200 OK\r\nServer: MailServer\r\nConnection: keep-alive\r\nContent-Encoding: gzip\r\nContent-Length: '
		data += str(len(text)) + '\r\n'
		data += 'Content-Type: application/json;charset=utf-8\r\n\r\n'
		data += text
	finally:
		connection.close()
		return data


def make404():
	text = '<p>Page Not Found</p>'
	data = 'HTTP/1.1 404 NotFound\r\nServer: MailServer\r\nConnection: keep-alive\r\nContent-Length: '
	data += str(len(text)) + '\r\nContent-Type: text/html;charset=utf-8\r\n\r\n'
	data += text
	return data

def response(req, cookie):
	if req.find('/lib/') == 0:
		try:
			r = req.split('/')[2]
			p = r.split('?')
			if p[0] == 'login':
				data = p[1].split('&')
				user = data[0].split('=')[1]
				passwd = data[1].split('=')[1]
				key = login(user, passwd)
				if key != None:
					text = '<div>login success!</div>'
					data = 'HTTP/1.1 302 Moved Permanently\r\nServer: MailServer\r\nConnection: keep-alive\r\nLocation: http://mail.wblog.top/index.html\r\nContent-Length: '
					data += str(len(text)) + '\r\n'
					data += 'Set-Cookie: UUID=%s\r\n' % key
					data += 'Content-Type: text/html;charset=utf-8\r\n\r\n'
					code = 302
				else:
					text = '<div>login failed!</div>'
					data = 'HTTP/1.1 302 Moved Permanently\r\nServer: MailServer\r\nConnection: keep-alive\r\nLocation: http://mail.wblog.top/login.html\r\nContent-Length: '
					data += str(len(text)) + '\r\n'
					data += 'Content-Type: text/html;charset=utf-8\r\n\r\n'
					code = 302
				return data, code
			elif p[0] == 'mailbox':
				if check(cookie):
					data = mailbox()
					if data:
						code = 200
						return data, code
				else:
					data = errjson()
					code = 200
					return data, code
		except:
			pass
	else:
		data = rfile(req)
		if data != None:
			code = 200
			return data, code
	data = make404()
	code = 404
	return data, code