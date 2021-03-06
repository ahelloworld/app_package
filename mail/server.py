import socket
import select
import errno
import re
import logging
import sys

import db

base_dir = sys.argv[1]
home_dir = base_dir + '/mail'
logpath = home_dir + '/mail.log'

logging.basicConfig(level = logging.DEBUG,
	format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
	datefmt = '%a %d %b %Y %H:%M:%S',
	filename = logpath,
	filemode = 'w')

class eml():
	def __init__(self):
		self.mfrom = None
		self.mto = None
		self.ip = None
		self.data = None
	def save(self):
		try:
			self.mfrom = self.mfrom.replace('"','\'')
			self.mto = self.mto.replace('"','\'')
			db.insert(self)
			return True
		except Exception, e:
			#print e
			return False

def r_hello(data, email):
	return '220 mail.wblog.top TMJ Personal Mail Server\r\n'

def r_protocol(data, email):
	if data.upper().find('HELO') == 0 or data.upper().find('EHLO') == 0:
		email.data = data
		return '250 OK\r\n'
	return '502 Error\r\n'

def r_fromok(data, email):
	logging.debug('from:\t%s' % data.strip())
	r = re.match(r'MAIL FROM:\s*<(.+?)>', data)
	if r:
		mfrom = r.group(1)
		print mfrom
		email.data += data
		email.mfrom = mfrom
		return '250 OK\r\n'
	return '502 Error\r\n'

def r_took(data, email):
	logging.debug('to:\t%s' % data.strip())
	r = re.match(r'RCPT TO:\s*<(.+?)>', data)
	if r:
		mto = r.group(1)
		print mto
		if mto.find('wblog.top') == -1:
			return '502 Error\r\n'
		email.data += data
		email.mto = mto
		return '250 OK\r\n'
	return '502 Error\r\n'

def r_start(data, email):
	if data.upper().find('DATA') == 0:
		email.data += '\r\n'
		return '354 Start\r\n'
	return '502 Error\r\n'

def r_data(data, email):
	if data.upper().find('\r\n.\r\n') != -1:
		email.data += data
		return '250 OK\r\n'
	return '502 Error\r\n'

def r_end(data, email):
	if data.upper().find('QUIT') == 0:
		return '221 Bye\r\n'
	return '502 Error\r\n'


def remove_client(fd, epoll, connections, state, rsn):
	epoll.unregister(fd)
	connections[fd].close()
	logging.info('removed[%d]:[%d]\t%s' % (fd, state, rsn))
	print 'removed[%d]:[%d]\t%s' % (fd, state, rsn)

def MailServer():
	switch = {1: r_hello,2: r_protocol,3: r_fromok,\
		4: r_took,5: r_start,6: r_data,7: r_end}
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	server.bind(('0.0.0.0', 25))
	server.listen(10)
	print 'server start!'

	epoll = select.epoll()
	epoll.register(server.fileno(), select.EPOLLIN)

	connections = {}
	mailbox_tmp = {}
	while True:
		elist = epoll.poll()
		#print elist
		for fd, events in elist:
			if fd == server.fileno():
				client, addr = server.accept()
				client.setblocking(0)
				epoll.register(client.fileno(), select.EPOLLOUT|select.EPOLLET)
				connections[client.fileno()] = client
				email = eml()
				email.ip = str(addr[0])
				mailbox_tmp[client.fileno()] = [email, '', 1]
				logging.info('connection[%d]:\t%s:%d' % (client.fileno(), addr[0], addr[1]))
				print 'connection:\t%s:%d' % (addr[0], addr[1])
			elif events & select.EPOLLHUP or events & select.EPOLLERR:
				remove_client(fd, epoll, connections, 0, 'socket error')
				continue
			elif events & select.EPOLLIN:
				datas = ''
				while True:
					try:
						state = mailbox_tmp[fd][2]
						data = connections[fd].recv(1024)
						if not data and not datas:
							if state == 6:
								if mailbox_tmp[fd][0].save():
									remove_client(fd, epoll, connections, state, 'mail save finish')
								else:
									remove_client(fd, epoll, connections, state, 'mail error')
							else:
								remove_client(fd, epoll, connections, state, 'connect break')
							break
						if len(data) == 0:
							e = socket.error
							e.errno == errno.EAGAIN
							raise e
						datas += data
						#print datas
					except socket.error, e:
						if e.errno == errno.EAGAIN:
							try:
								mailbox_tmp[fd][1] += datas
								if len(mailbox_tmp[fd][1]) > 1024 * 1024 * 5:
									remove_client(fd, epoll, connections, state, 'recv data too long')
									break
								if (state == 5 and mailbox_tmp[fd][1].find('\r\n.\r\n') != -1)\
									or (state != 5 and mailbox_tmp[fd][1].find('\r\n') != -1):
									mailbox_tmp[fd][2] += 1
									epoll.modify(fd, select.EPOLLOUT|select.EPOLLET)
							except:
								remove_client(fd, epoll, connections, state, 'recv data error')
						else:
							if state == 6:
								if mailbox_tmp[fd][0].save():
									remove_client(fd, epoll, connections, state, 'mail save finish')
								else:
									remove_client(fd, epoll, connections, state, 'mail error')
							else:
								print 'recv:' + str(e)
								remove_client(fd, epoll, connections, state, 'recv error')
						break
			elif events & select.EPOLLOUT:
				email = mailbox_tmp[fd][0]
				data = mailbox_tmp[fd][1]
				state = mailbox_tmp[fd][2]
				res = switch[state](data, email)
				#print [data]
				try:
					slen = connections[fd].send(res)
					if slen == len(res):
						epoll.modify(fd, select.EPOLLIN|select.EPOLLET)
						mailbox_tmp[fd][1] = ''
				except socket.error, e:
					if e.errno == errno.EAGAIN:
						epoll.modify(fd, select.EPOLLIN|select.EPOLLET)
					else:
						print 'send:' + str(e)
						remove_client(fd, epoll, connections, state, 'send error')
						break
				if int(res[0]) > 3:
					remove_client(fd, epoll, connections, state, 'format error')
					break
				if state == 7:
					if mailbox_tmp[fd][0].save():
						remove_client(fd, epoll, connections, state, 'mail save finish')
					else:
						remove_client(fd, epoll, connections, state, 'mail error')
	epoll.close()

MailServer()