nohup python "/app/http/server.py" "/docker" > "/docker/log/http.log" 2>&1 &
nohup python "/app/mail/server.py" "/docker" > "/docker/log/mail.log" 2>&1 &