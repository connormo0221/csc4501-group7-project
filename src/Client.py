import threading
import socket
import os

# TODO: check that all features are working as intended
# TODO: check that common errors are handled properly
# TODO: specify the exceptions we want to catch in try-except statements (it's best practice)

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')
if username == 'admin':
	password = input('Type in a password: ')

# Server host IP & port number manually set to localhost for this project
host = '127.0.0.1'
port = 29170

# Open new socket and connect using host IP and port number defined above
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

stop_thread = False

# Add client commands to the help message here
help_msg = 'Valid commands:\n/help, /exit, /w [user] [message], /online, /channels, /join #[channel name], /transfer [user] [path to file]'
# Add admin commands to the help message here
admin_help_msg = 'Additional commands for admins:\n/kick [user], /ban [user], /unban [user], /make #[channel name], /close #[channel name]'

# function Receive
# Receives & decodes data from the server; if data can't be decoded, client disconnects
def receive():
	while True:
		global stop_thread
		# Use the following line for debugging thread closure
		print(f'DEBUG_CLIENT: stop_thread == {stop_thread}')
		if stop_thread:
			# Use the following line for debugging thread closure
			print('DEBUG_CLIENT: Breaking receive() loop.')
			client.close()
			break

		try:
			message = client.recv(1024).decode('ascii') # Server uses a client to send messages
			if message == 'ID':
				client.send(username.encode('ascii'))
				next_msg = client.recv(1024).decode('ascii')
				if next_msg == 'PASS': # Using PASS keyword to ask for password
					client.send(password.encode('ascii'))
					if client.recv(1024).decode('ascii') == 'REFUSE':
						print('ERROR: Connection refused due to invalid password.')
						stop_thread = True
				elif next_msg == 'BAN': # Using BAN keyword to disconnect user
					print('ERROR: Connection refused due to being banned by an administrator.')
					stop_thread = True
			elif message == 'KICKED': # Using KICKED keyword to disconnect user
				print('ERROR: Connection to server refused.')
				stop_thread = True
			elif message == 'EXIT': # Using EXIT keyword to disconnect user
				print('Now disconnecting from the server.')
				stop_thread = True
			elif message.startswith('FTP_REQ'): # Using FTP_REQ keyword to request file transfer
				content = message.split()
				print(f'{content[1]} would like to transfer file [{content[2]}]. Will you accept? (y/n)')
				resp = input("")
				client.send(resp.encode('ascii'))
				if resp == 'y':
					file_name = client.recv(1024).decode()
					#file_size = client.recv(1024).decode() # Uncomment this if we want to implement a progress bar
					file = open(file_name, 'wb')
					file_bytes = b""
					done = False
					while not done:
						data = client.recv(1024)
						if file_bytes[-5:] == b"<END>":
							done = True
						else:
							file_bytes += data
					file.write(file_bytes)
					file.close()

			else:
				print(message)
		except:
			print('Data transfer stopped, closing connection.')
			client.close() # Close socket connected to the server
			break
	
	# This line is only reached if the receive() loop has been broken
	print('Press ENTER to exit.') # Force the user to submit input in order to close the write() thread

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	while True: # Always running in order to catch input
		try:
			content = input("")
			isAdmin = False
			if username == 'admin': # Change this if we decide to add support for multiple admins
				isAdmin = True

			if content.startswith('/'): # Forward slash indicates a command is being used; check which command
				if (content.startswith('/help')):
					print(help_msg)
					if isAdmin:
						print(admin_help_msg)
				
				elif (content.startswith('/kick') & isAdmin): # Kicks a user temporarily
					print(f'Kicking user {content[6:]}')
					client.send(f'KICK {content[6:]}'.encode('ascii'))

				elif (content.startswith('/ban') & isAdmin): # Bans a user
					print(f'Banning user {content[5:]}')
					client.send(f'BAN {content[5:]}'.encode('ascii'))

				elif (content.startswith('/unban') & isAdmin): # Unbans a user
					print(f'Unbanning user {content[7:]}')
					client.send(f'UNBAN {content[7:]}'.encode('ascii'))

				elif (content.startswith('/make') & isAdmin): # Make a new server channel
					client.send(f'MAKE {content[6:]}'.encode('ascii'))

				elif (content.startswith('/close') & isAdmin): # Closes an existing server channel
					client.send(f'CLOSE {content[7:]}'.encode('ascii'))

				elif (content.startswith('/exit')): # Exits the server
					print('Exiting server.')
					client.send('EXIT'.encode('ascii'))
				
				elif (content.startswith('/w')): # Sends a private message to another user
					print('Whispering to another user.')
					client.send(f'WHISPER {content[3:]}'.encode('ascii'))

				elif (content.startswith('/online')): # Lists all users that are currently online
					client.send('USERS'.encode('ascii'))

				elif (content.startswith('/channels')): # Lists all available server channels
					client.send('CHANNELS'.encode('ascii'))

				elif (content.startswith('/join')): # Moves user to another server channel
					client.send(f'JOIN {content[6:]}'.encode('ascii'))
				
				elif (content.startswith('/transfer')): # Sends a request for file transfer to another user
					command = content.split()
					target = command[1]
					file = command[2:]
					client.send(f'REQ {target} {file}'.encode('ascii'))
					response = client.recv(1204).decode('ascii')
					if response == 'FTP_CONF':
						f = open(file, 'rb')
						f_size = os.path.getsize(file)
						client.send(file.encode())
						client.send(str(f_size).encode())
						data = f.read()
						client.sendall(data)
						client.send(b"<END>")
						f.close()
					elif response == 'FTP_DENY':
						print(f'{target} has declined your file transfer request.')
					else:
						print('ERROR: Unknown response from server. File transfer attempt unsuccessful or incomplete.')

				else:
					print('ERROR: Invalid command. Use /help to list all valid commands.')
			else:
				message = (f'{username}: {content}')
				client.send(message.encode('ascii'))

		except:
			if receive_thread.is_alive(): # Only send error message if receive thread is still active
				print('ERROR: Unable to send message to server.')
			break
	# Use the following line for debugging thread closure
	print('DEBUG_CLIENT: Broke write() loop successfully.')
		
# Both functions need their own thread since we need to be able to send & receive messages simultaneously
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()

if receive_thread.is_alive() == False & write_thread.is_alive() == False:
	os._exit(0) # Exit client if both threads have been closed