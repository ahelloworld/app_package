def response(req, cookie):
	data = req
	data += '\r\n'
	data += cookie
	code = 404
	return data, code