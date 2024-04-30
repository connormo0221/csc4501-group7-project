import socket
import threading
import tkinter
from tkinter import simpledialog, messagebox, Label, Text, Scrollbar


host = '127.0.0.1'
port = 29170

background_gray = '#ABB2B9'
background_color = '#17202A'
background_msg = '#2C3E50'
text_color = '#EAECEE'
main_font = 'Helvetica 14'
font_bold = 'Helvitica 13 bold'


help_msg = 'Valid commands:\n/help, /exit, /w [user] [message], /online, /channels, /join #[channel name], /transfer [user] [path to file]'

admin_help_msg = 'Additional commands for admins:\n/kick [user], /ban [user], /unban [user], /make #[channel name], /close #[channel name]'

class Client:

    def __init__(self, host, port):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
                
        msg = tkinter.Tk()
        msg.withdraw()

        self.username = simpledialog.askstring("Username", "Please choose a username", parent = msg)
        if self.username == 'admin':
            self.password = simpledialog.askstring("Password", "Enter the admin password")

        self.gui_done = False
        self.running = True

        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)

        if self.running:
            gui_thread.start()
            receive_thread.start()
            

    def gui_loop(self):
        
        self.window = tkinter.Tk()
        self.window.title("Chat")
        self.window.configure(width=470, height=550, bg=background_color)
        self.window.iconbitmap('favicon.ico')
        
        head_label = Label(self.window, bg=background_color, fg=text_color, text="Welcome", font=font_bold, pady=10)
        head_label.place(relwidth=1)
        
        line = Label(self.window, width=450, bg=background_gray)
        line.place(relwidth=1, rely=0.07, relheight=0.012)
        
        self.text_area = Text(self.window, width=20, height=2, bg=background_color, fg=text_color, font=main_font, padx=5, pady=5)
        self.text_area.place(relheight=0.745, relwidth=1, rely=0.08)
        self.text_area.configure(cursor='arrow', state='disabled')
        
        scrollbar = Scrollbar(self.text_area)
        scrollbar.place(relheight=1, relx=0.974)
        scrollbar.configure(command=self.text_area.yview)
        
        bottom_label = Label(self.window, bg=background_gray, height=80)
        bottom_label.place(relwidth=1, rely=0.825)
        
        self.input_area = tkinter.Text(bottom_label, bg=background_msg, fg=text_color, font=main_font)
        self.input_area.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        self.input_area.focus()
        
        send_button = tkinter.Button(bottom_label, text='Send', font=font_bold, width=20, bg=background_gray, command=self.write)
        send_button.place(relx=0.77, rely=0.008, relheight=0.06, relwidth=0.22)
        
        self.gui_done = True

        self.window.protocol("WM_DELETE_WINDOW", self.stop)

        self.window.mainloop()

    def write(self):
        message = ("{}: {}".format(self.username, self.input_area.get('1.0', 'end')))
        isAdmin = False
        if(self.username == 'admin'):
            isAdmin = True
        usermsg = self.input_area.get('1.0', 'end')
        if usermsg.startswith('/'):
            if(usermsg.startswith('/help')):
                self.sock.send(help_msg.encode('utf-8'))
                if isAdmin:
                    self.sock.send(admin_help_msg)     
            else:
                self.socket.send('ERROR: Invalid command. Use /help to list all valid command.')   
        else:
            self.sock.send(message.encode('utf-8'))
            
        self.input_area.delete('1.0', 'end')


    def stop(self):
        self.running = False
        self.window.destroy()
        self.sock.close()
        exit(0)

    
    

    def receive(self):
        while self.running:
                        
            try:
                message = self.sock.recv(1024).decode('utf-8') 

                if message == 'USER':
                    self.sock.send(self.username.encode('utf-8'))
                    next_msg = self.sock.recv(1024).decode('utf-8')
                    if next_msg == 'PASS': 
                        self.sock.send(self.password.encode('utf-8'))
                        if self.sock.recv(1024).decode('utf-8') == 'REFUSE':
                            print('ERROR: Connection refused due to invalid password.')
                            messagebox.showerror("ERROR", "Connection refused due to invalid password.")
                            self.stop()
                            client.close()
                    elif next_msg == 'BAN': 
                        print('ERROR: Connection refused due to being banned by an administrator.')
                        messagebox.showerror("ERROR", "Connection refused due to being banned by an administrator.")
                        self.stop()
                        client.close()
                elif message == 'EXIT': 
                    self.stop()
                    client.close()                        
                else:
                    if self.gui_done:
                        self.text_area.config(state='normal')
                        self.text_area.insert('end', message)
                        self.text_area.yview('end')
                        self.text_area.config(state='disabled')
            except:
                print('Data transfer stopped, closing connection.')
                self.sock.close()
                break
        
client = Client(host,port)