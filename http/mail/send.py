import socket
import base64
import re
import datetime

#dnspython
import dns.resolver

def stmpS(ss, req):
	for i in xrange(0, 5):
		try:
			#print req
			ss.sendall(req)
			return True
		except Exception, e:
			print e
			#print 'try:%d' % i
	return False

def stmpR(ss, code):
	for i in xrange(0, 5):
		try:
			res = ss.recv(1024)
			#print res
			if code == res.split()[0]:
				return res.strip()
			else:
				return False
		except Exception, e:
			print e
			#print 'try:%d' % i
	return False

def getMailHost(server):
	mx = dns.resolver.query(server, 'MX')
	rdict = {}
	for rdata in mx:
		rdict[rdata.exchange] = rdata.preference
	return str(min(rdict.items(), key=lambda x: x[1])[0])

def sendMail(email, name, title, text, fname, admin):
	server = email.split('@')[1]

	ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	ss.connect((getMailHost(server), 25))


	if stmpR(ss, '220') == False:
		print 'connect mail server failed!'
		return False

	if stmpS(ss, 'EHLO mail.wblog.top\r\n') == False:
		print 'send ehlo failed!'
		return False

	stmpR(ss, '250-mail')

	if stmpS(ss, 'MAIL FROM: <%s@wblog.top>\r\n' % admin) == False:
		print 'send mail from failed!'
		return False

	if stmpR(ss, '250') == False:
		print 'can not accept mail from!'
		return False

	if stmpS(ss, 'RCPT TO: <%s>\r\n' % email) == False:
		print 'send rcpt to failed!'
		return False

	if stmpR(ss, '250') == False:
		print 'can not accept rcpt to!'
		return False

	if stmpS(ss, 'DATA\r\n') == False:
		print 'send data start failed!'
		return False

	if stmpR(ss, '354') == False:
		print 'can not accept data!'
		return False

	data = 'FROM: =?utf-8?B?%s?=<%s@wblog.top>\r\nTO: %s\r\n' % (base64.b64encode(name), admin, email)
	data += 'Subject: =?utf-8?B?%s?=\r\n' % base64.b64encode(title)
	data += 'MIME-Version: 1.0\r\n'
	data += 'Content-Type: multipart/mixed;\r\n\tboundary="Part_Boundary_Mixed"\r\n\r\n'
	
	data += '--Part_Boundary_Mixed\r\n'
	data += 'Content-Type: multipart/alternative;\r\n\tboundary="Part_Boundary_Alternative"\r\n'
	data += 'Content-Transfer-Encoding: 8Bit\r\n\r\n'
	
	data += '--Part_Boundary_Alternative\r\n'
	data += 'Content-Type: text/plain;\r\n\tcharset="utf-8"\r\nContent-Transfer-Encoding: base64\r\n\r\n'

	data += '--Part_Boundary_Alternative\r\n'
	data += 'Content-Type: text/html;\r\n\tcharset="utf-8"\r\nContent-Transfer-Encoding: base64\r\n\r\n'

	data += base64.b64encode(text) + '\r\n\r\n'

	if fname != None:
		data += '--Part_Boundary_Alternative--\r\n\r\n'
		base_fname = base64.b64encode(fname)
		data += '--Part_Boundary_Mixed\r\n'
		data += 'Content-Type: application/octet-stream;\r\n\tname="=?utf-8?B?%s?="\r\n' % base_fname
		data += 'Content-Disposition: attachment; filename="=?utf-8?B?%s?="\r\n' % base_fname
		data += 'Content-Transfer-Encoding: base64\r\n\r\n'

		if stmpS(ss, data) == False:
			print 'send data failed!'
			return False

		f = open(fname.decode('utf-8'), 'rb')
		data = f.read()
		f.close()
		dlist = re.findall(r'.{4096}|.+', base64.b64encode(data))
		total = len(dlist)
		diff = total / 10 + 1
		d1 = datetime.datetime.now()
		stime = 0
		for i, data in enumerate(dlist):
			if stmpS(ss, data) == False:
				print 'send data failed!'
				return False
			d2 = datetime.datetime.now()
			d = d2 - d1
			stime = float(d.microseconds) / 1000000 + d.seconds
			if stime > 0 and ((i + 1) % diff == 0 or (i + 1) == total):
				print '%.2f%%\t%.2fkb/s' % (float(i + 1) / total * 100, float(4) * (i + 1) / stime)
		print 'finish:%.2fs' % stime
		data = '\r\n\r\n--Part_Boundary_Mixed--\r\n'
	else:
		data += '--Part_Boundary_Alternative--\r\n--Part_Boundary_Mixed--\r\n'

	if stmpS(ss, data) == False:
		print 'send data failed!'
		return False
	if stmpS(ss, '\r\n.\r\n') == False:
		print 'send data failed!'
		return False

	res = stmpR(ss, '250')
	if res == False:
		print 'send mail failed!'
		return False
	else:
		print res
	stmpS(ss, 'QUIT\r\n')
	stmpR(ss, '221')
	ss.close()