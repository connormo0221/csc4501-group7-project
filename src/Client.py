import socket
import threading

username = input("choose a username: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#instead of binding a client to a host and port, we connect it to a host and port
client.connect(('127.0.0.1', 31103))


#Recieve function for data from the server

def receive():
	while True:
		try:
			message = client.recv(1024).decode('ascii') #the server uses a client to send messages which is why client is here
			if message == 'ID':
				client.send(username.encode('ascii'))
			else:
				print(message)
		except:
			print("An error occured, closing connection!")
			client.close()
			break


#Send messages to the server

def write():
	while True:
		message = (f'{username}: {input("")}')
		#constantly running user input function and as soon as enter is hit it sends a message and prompts for a new message
		client.send(message.encode('ascii'))
		
		
#These each need their own thread since it needs to send and receive simulatenously

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()