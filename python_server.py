""" Basic Python 3 HTTP server without the HTTP library

	La question:
		Write an HTTP server, in Python, using only the standard lib (excluding the `http` module).
		The server should serve static files (its own code for example), and be able to list files like
		Apache does when serving a directory.

		Please spend about 2 hours on this. The goal is obviously not to re-create Apache with all its functionalities
		but try to implement all the use-cases that you can think of and can cover in those 2 hours.

	J'ai utilisé la porte 8000 par défaut. Pour tester le serveur, executer le fichier main.py, et 
	ouvrez un navigateur, dans mon cas, google chrome, et puis naviguez vers http://localhost:8000
"""

import os, socket, mimetypes

class TCPServer:
	"""Base server class for handling TCP connections.
	The HTTP server will inherit from this class.
	"""
	def __init__(self, host='127.0.0.1', port = 8000):
		self.host = host
		self.port = port

	def start(self):
		"""Method for starting the server"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((self.host, self.port))
		s.listen(5)

		print("Listening at", s.getsockname())

		# generate an html page that lists the other files in the server directory on server start
		files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]
		self.generate_directory_list_page(files)

		while True:
			conn, addr = s.accept()
			print("Connected by", addr)
			data = conn.recv(4096)
			response = self.handle_request(data)
			conn.sendall(response)
			conn.close()

	# Handles incoming data and returns a response.
	def handle_request(self, data):
		return data

	# Generate a directory html page at index.html
	def generate_directory_list_page(self, filenames):
		print("Generating directory page at index.html")
		with open('index.html', 'w') as myFile:
			myFile.write('<!DOCTYPE html> ')
			myFile.write('<html>')
			myFile.write('<head>')
			myFile.write('</head>')
			myFile.write('<body>')
			myFile.write('<h1>Server Directory</h1>')
			for filename in filenames:
				myFile.write('<div>')
				myFile.write("<a href="+filename+">" + filename + "</a>")
				myFile.write('</div>')
			myFile.write('</body>')
			myFile.write('</html>')
		print("DONE")

class HTTPServer(TCPServer):
	"""The actual HTTP server class."""
	headers = {
		'Server': 'StaticServer',
		'Content-Type': 'text/html',
	}

	status_codes = {
		200: 'OK',
		404: 'Not Found',
		501: 'Not Implemented',
	}

	# Handles incoming requests
	def handle_request(self, data):
		request = HTTPRequest(data) # Get a parsed HTTP request
		try:
			# Call the corresponding handler method for the current
			# request's method
			handler = getattr(self, 'handle_%s' % request.method)
		except AttributeError:
			handler = self.HTTP_501_handler
		response = handler(request)
		return response

	# Returns response line (as bytes)
	def response_line(self, status_code):
		reason = self.status_codes[status_code]
		response_line = 'HTTP/1.1 %s %s\r\n' % (status_code, reason)
		return response_line.encode() # convert from str to bytes

	# Returns headers as bytes. Extra headers can be used as a dict for sending extra headers with response
	def response_headers(self, extra_headers=None):
		headers_copy = self.headers.copy() # make a local copy of headers
		if extra_headers:
			headers_copy.update(extra_headers)
		headers = ''
		for h in headers_copy:
			headers += '%s: %s\r\n' % (h, headers_copy[h])
		return headers.encode() # convert str to bytes

	# Handle options http method
	def handle_OPTIONS(self, request):
		response_line = self.response_line(200)
		extra_headers = {'Allow': 'OPTIONS, GET'}
		response_headers = self.response_headers(extra_headers)
		blank_line = b'\r\n'
		return b''.join([response_line, response_headers, blank_line])

	# Handle GET http method
	def handle_GET(self, request):
		path = request.uri.strip('/') # remove slash from URI

		if not path:
			# if path is empty, serve index.html by default
			path = 'index.html'

		if os.path.exists(path) and not os.path.isdir(path): # don't serve directories
			response_line = self.response_line(200)

			# find out a file's MIME type if nothing is found, just send `text/html`
			content_type = mimetypes.guess_type(path)[0] or 'text/html'
			extra_headers = {'Content-Type': content_type}
			response_headers = self.response_headers(extra_headers)

			with open(path, 'rb') as f:
				response_body = f.read()
		else:
			response_line = self.response_line(404)
			response_headers = self.response_headers()
			response_body = b'<h1>404 Not Found</h1>'

		blank_line = b'\r\n'
		response = b''.join([response_line, response_headers, blank_line, response_body])
		return response

	# 501 if method is not yet implemented
	def HTTP_501_handler(self, request):
		response_line = self.response_line(status_code=501)
		response_headers = self.response_headers()
		blank_line = b'\r\n'
		response_body = b'<h1>501 Not Implemented</h1>'
		return b"".join([response_line, response_headers, blank_line, response_body])

class HTTPRequest:
	"""Parser for HTTP requests.

	It takes raw data and extracts information about the incoming request.
	Instances of this class have the following attributes:
		self.method: The current HTTP request method sent by client (string)
		self.uri: URI for the current request (string)
		self.http_version = HTTP version used by  the client (string)
	"""

	def __init__(self, data):
		self.method = None
		self.uri = None
		self.http_version = '1.1' # default to HTTP/1.1 if request doesn't provide a version

		# call self.parse method to parse the request data
		self.parse(data)

	def parse(self, data):
		lines = data.split(b'\r\n')
		request_line = lines[0] # request line is the first line of the data
		words = request_line.split(b' ') # split request line into seperate words
		self.method = words[0].decode() # call decode to convert bytes to string

		if len(words) > 1:
			# we put this in if block because sometimes browsers
			# don't send URI with the request for homepage
			self.uri = words[1].decode() # call decode to convert bytes to string python3

		if len(words) > 2:
			# we put this in if block because sometimes browsers
			# don't send HTTP version
			self.http_version = words[2]

if __name__ == '__main__':
	server = HTTPServer()
	server.start()
