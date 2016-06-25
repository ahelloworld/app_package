import os
import sys
import gzip
import StringIO

base_dir = sys.argv[1]
home_dir = base_dir + '/resume'

def readfile(dirn, resdict, slen):
	for parent, dnames, fnames in os.walk(dirn):
		for dname in dnames:
			readfile(os.path.join(parent,dname), resdict, slen)
		for fname in fnames:
			fpath = os.path.join(parent,fname)
			f = open(fpath, 'r')
			data = f.read()
			f.close()
			zbuf = StringIO.StringIO()
			gziper = gzip.GzipFile(mode = 'wb', compresslevel = 9, fileobj = zbuf)
			gziper.write(data)
			gziper.close()
			text = zbuf.getvalue()
			data = 'HTTP/1.1 200 OK\r\nServer: ResumeServer\r\nConnection: keep-alive\r\nContent-Encoding: gzip\r\nContent-Length: '
			data += str(len(text)) + '\r\n'
			if fpath[-4:] == 'html':
				data += 'Content-Type: text/html;charset=utf-8\r\n\r\n'
			else:
				data += 'Content-Type: application/octet-stream\r\nAccept-Ranges: bytes\r\n\r\n'
			data += text
			resdict[fpath[slen:]] = data

def make404(resdict):
	text = '<p>Page Not Found</p>'
	data = 'HTTP/1.1 404 NotFound\r\nServer: ResumeServer\r\nConnection: keep-alive\r\nContent-Length: '
	data += str(len(text)) + '\r\nContent-Type: text/html;charset=utf-8\r\n\r\n'
	data += text
	resdict['404'] = data

def response(req, cookie):
	global resdict
	if req != None and resdict.has_key(req):
		data = resdict[req]
		code = 200
	else:
		data = resdict['404']
		code = 404
	return data, code

resdict = {}
make404(resdict)
readfile(home_dir, resdict, len(home_dir))
for x, y in resdict.items():
	print x