import socket
import select
import errno
import multiprocessing
import urllib
import re
import sys
import os

path = os.path.split(sys.argv[0])[0]
sys.path.append(path + '/resume')
sys.path.append(path + '/mail')
import resume
import mail

def remove_client(fd, epoll, connections, rsn):
	epoll.unregister(fd)
	connections[fd].close()
	print 'removed:\t' + rsn

def proc():
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	server.bind(('0.0.0.0', 80))
	server.listen(10)
	print 'server start!'

	epoll = select.epoll()
	epoll.register(server.fileno(), select.EPOLLIN)

	connections = {}
	reqlist = {}
	sendlog = {}
	while True:
		elist = epoll.poll()
		#print elist
		for fd, events in elist:
			if fd == server.fileno():
				client, addr = server.accept()
				client.setblocking(0)
				epoll.register(client.fileno(), select.EPOLLIN|select.EPOLLET)
				connections[client.fileno()] = client
				print 'connection:\t%s:%d' % (addr[0], addr[1])
			elif events & select.EPOLLHUP or events & select.EPOLLERR:
				remove_client(fd, epoll, connections, 'socket error')
				continue
			elif events & select.EPOLLIN:
				datas = ''
				while True:
					try:
						data = connections[fd].recv(1024)
						if not data and not datas:
							remove_client(fd, epoll, connections, 'recv no data')
							break
						if len(data) == 0:
							e = socket.error
							e.errno == errno.EAGAIN
							raise e
						datas += data
					except socket.error, e:
						if e.errno == errno.EAGAIN:
							try:
								header = datas.split('\r\n')
								for h in header:
									if h.find('GET') != -1:
										req = h.split()[1]
									elif h.find('HOTS') != -1:
										host = re.search(r'(\w)\.', h).group(1)
								if req == '/':
									req = '/index.html'
								if host == 'resume':
									func = resume
								elif host == 'mail':
									func == mail
								req = urllib.unquote(req)
								reqlist[fd] = [func, req]
								sendlog[fd] = 0
								print 'request:\t%s' % req
								epoll.modify(fd, select.EPOLLOUT|select.EPOLLET)
							except:
								remove_client(fd, epoll, connections, 'recv data error')
						else:
							print 'recv:' + str(e)
							remove_client(fd, epoll, connections, 'recv error')
						break
			elif events & select.EPOLLOUT:
				slen = sendlog[fd]
				data, code = reqlist[fd][0].response(reqlist[fd][1])
				try:
					slen += connections[fd].send(data[slen:])
					print 'sending:\t%d' % slen
					if slen == len(data):
						#epoll.modify(fd, select.EPOLLIN|select.EPOLLET)
						print 'response:\t%d' % code
						remove_client(fd, epoll, connections, 'normal')
						continue
				except socket.error, e:
					if e.errno != errno.EAGAIN:
						print 'send:' + str(e)
						remove_client(fd, epoll, connections, 'send error')
						continue
					else:
						remove_client(fd, epoll, connections, 'normal')
						continue
				sendlog[fd] = slen
	epoll.close()

pl = []
for x in xrange(2):
	p = multiprocessing.Process(target = proc, args = ())
	p.daemon = True
	p.start()
	print 'process %d:start' % x
	pl.append(p)

for p in pl:
	p.join()