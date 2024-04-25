import threading
import socket
import os

# TODO: add proper type checking for host & port variables
# TODO: add error handling to failed connections
# TODO: fix formatting; submitted messages are inserted between unsent messages

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')
if username == 'admin':
	password = input('Type in a password: ')

# Allow client to set server host IP & port number
host = '127.0.0.1'
port = 29170

# Connect the client to a host IP & port number; dependent on previous user input
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

stop_thread = False

helpPG = 'Valid commands are as follows' #TODO: Write these two
adminPG = 'ADMINISTRATOR COMMANDS:'

# function Receive
# Receives & decodes data from the server; if data can't be decoded, client disconnects
def receive():
	while True:
		global stop_thread
		if stop_thread == True:
			# [for debugging thread closure]
			# print('breaking receive loop')
			break
		try:
			message = client.recv(1024).decode('ascii')
			# the server uses a client to send messages which is why client is here
			if message == 'ID':
				client.send(username.encode('ascii'))
				next_msg = client.recv(1024).decode('ascii')
				if next_msg == 'PASS':
					client.send(password.encode('ascii'))
					if client.recv(1024).decode('ascii') == 'REFUSE':
						print('Connection was refused, incorrect password')
						stop_thread = True
				elif next_msg == 'BAN':
					print('Connection refused: you have been banned by an administrator')
					client.close()
					stop_thread = True
			elif message == 'KICKED':
				client.close()
				stop_thread = True
			elif message == 'EXIT':
				print('You have left the room succesfully')
				stop_thread = True

			elif message.startswith('FTP_REQ'):
				content = message.split()
				print(f'{content[1]} would like to transfer file [{content[2]}]. Will you accept? (y/n)')
				resp = input("")
				client.send(resp.encode('ascii'))
				if resp == 'y':
					file_name = client.recv(1024).decode()
					file_size = client.recv(1024).decode() # just here if we decide to implement a progress bar
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
			client.close()
	# [for debugging thread closure]
	# print('receive loop broken')

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	# User input function is always running in order to catch input
	while True:
		if stop_thread:
			# [for debugging thread closure]
			#print('breaking write loop')
			break
		try:
			content = input("")
			isAdmin = False
			if username == 'admin':
				isAdmin = True

			if content.startswith('/'): #indicates a command
				if (content.startswith('/help')):
					print(helpPG)
					if isAdmin:
						print(adminPG)
				
				elif (content.startswith('/kick') & isAdmin):
					print(f'kicking {content[6:]}')
					client.send(f'KICK {content[6:]}'.encode('ascii'))

				elif (content.startswith('/ban') & isAdmin):
					print(f'banning {content[5:]}')
					client.send(f'BAN {content[5:]}'.encode('ascii'))

				elif (content.startswith('/unban') & isAdmin):
					print(f'unbanning {content[7:]}')
					client.send(f'UNBAN {content[7:]}'.encode('ascii'))

				elif (content.startswith('/make') & isAdmin):
					client.send(f'MAKE {content[6:]}'.encode('ascii'))

				elif (content.startswith('/close') & isAdmin):
					client.send(f'CLOSE {content[7:]}'.encode('ascii'))

				elif (content.startswith('/exit')):
					print('Exiting')
					client.send('EXIT'.encode('ascii'))
				
				elif(content.startswith('/w')):
					print(f'whispering')
					client.send(f'WHISPER {content[3:]}'.encode('ascii'))

				elif(content.startswith('/online')):
					client.send('USERS'.encode('ascii'))

				elif(content.startswith('/channels')):
					client.send('CHANNELS'.encode('ascii'))

				elif (content.startswith('/join')):
					client.send(f'JOIN {content[6:]}'.encode('ascii'))
				
				elif(content.startswith('/transfer')):
					command = content.split()
					target = command[1]
					file = command[2:]
					client.send(f'REQ {target} {file}'.encode('ascii'))
					response = client.recv(1204).decode('ascii')
					if response == 'FTP CONF':
						f = open(file, 'rb')
						f_size = os.path.getsize(file)
						client.send(file.encode())
						client.send(str(f_size).encode())
						data = f.read()
						client.sendall(data)
						client.send(b"<END>")
						f.close()
					elif response == 'FTP DENY':
						print(f'{target} has declined your file transfer request')
					else:
						print('Server has sent an unknown response. File transfer was likely unsuccesful or incomplete')

					
				else:
					print('invalid command')
			else:
				message = (f'{username}: {content}')
				client.send(message.encode('ascii'))

		except:
			print('unable to send message')
	# [for debugging thread closure]
	# print('write loop broken')
		
# Both functions need their own thread since we need to be able to send & recieve messages simultaneously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()