""" 
Mohammad Rifat Arefin
ID: 1001877262  
"""
import os
import tkinter as tk
import socket
import threading
import pickle
from orderedset import OrderedSet               #FIFO data structure for lexicon
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfile
import time

server_port = 12100                             #primary server
polling_port = 12105                            #polling on primary server
client_socket = None
lexicon = OrderedSet()
polled = ""                                    #keep track of polled contents
send_start = 0                                  #keep track when file transfer starts
disconnected = False                            #check if primary server disconnected
backup = 0                                      #check if connected to backup
lock = threading.Lock()                         #for isolation
username = None
poll_socket = None   

""" Prompt user to choose file to send """
def open_file(root):
    global send_start

    lock.acquire()
    send_start = 1
    client_socket.send("data".encode())                 #send header
    ack = client_socket.recv(1024).decode()             #recv ack
    print("ack "+ ack + str(len(ack)))

    # client_socket.send("Got it!".encode())    
    

    path = open(askopenfilename(),'rb')                 #file chooser 
    client_socket.sendfile(path)                        #send file for spell check
    

    root.grid_remove()

    root = tk.Frame(master, width=500, height=200)
    root.grid()


    get = client_socket.recv(1024).decode()             #recv checked file
    # while(get==""):
    #     get = client_socket.recv(1024).decode()         #reattempt if data not received
    lock.release()
    print("get "+get)
    lexicon.clear()
    client_socket.close()
    tk.Label(root, text="Upload complete\nSpell checking complete").grid()
    tk.Button(root, text = "Save as",command=lambda: save_file(root,get)).grid()
    root.tkraise()

""" Prompt user for destination location of spell checked file """
def save_file(root, data):

    print("data"+data)
    file = asksaveasfile()              #destination location
    file.write(data)
    file.close()
    root.grid_remove() 
    root = tk.Frame(master, width=500, height=200)
    root.grid()
    tk.Label(root,text="Spell checking complete").grid()
    tk.Label(root,text="Successfully saved").grid()
    tk.Button(root, text = "Quit",command=lambda: quit_app()).grid()
    tk.Button(root, text = "Start over", command=lambda: restart(root)).grid()
    root.tkraise()

""" Show lexicon to user """
def show_lexicon(frame, label):
    global disconnected
    if disconnected == True:                                        #notify user if primary server disconnected
        label['text'] = "SERVER DISCONNECTED\n"
        disconnected = False
    else:
        label['text'] = ""
    label['text'] += "Lexicon Queue " + str(lexicon)
    global polled
    if (polled != ""):                                                  #check if server polled
        label['text'] += "\nPolled content by server:" + polled
    
    polled = ""                                                     #reset GUI content
    master.after(2000, show_lexicon, frame, label)                  #refresh GUI

""" add lexicon to queue """
def add_lexicon(entry):
    lexicon.add(entry.get())
    entry.delete(0,'end')

""" receive polling req """
def polling_req(frame):
    while(1):
        

        req = poll_socket.recv(1024).decode()         #recv header
        print(req+" req "+str(len(req)))
        
        if(len(req)==0):                                #if primary server disconnects
           
            global disconnected, backup
            disconnected = True
            
            global server_port, polling_port
            server_port = 12101
            polling_port = 12106
            send_username(frame)                        #check with backup port no.
            break
        
        elif(req=="polling"):
            try:
                lock.acquire()
                client_socket.send("lexicon".encode())      #send header
                print(client_socket.recv(1024).decode())                    #recv ack
                lex = pickle.dumps(lexicon)                 
                client_socket.send(lex)                     #send lexicon
                lock.release()
                global polled
                if len(lexicon)>0:
                    polled = str(lexicon)
                lexicon.clear()                             #clear after being polled
            except:
                lock.release()
                break

    print("break")
        
    

""" connect with the server and register a username """
def send_username(root_frame, entry = None):
    
    if entry != None:
        global username
        username = entry.get()
    print("username: %s" % (username))
    global client_socket, server_port, poll_socket, polling_port
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #create socket
    poll_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect(('localhost', server_port))               #connect with server
        client_socket.send(username.encode())
        
        root_frame.grid_remove()

        msg = client_socket.recv(1024).decode()               #receive server status

        frame2 = tk.Frame(master)
        frame2.grid()

        if(msg == "ok"):                          #servers sends ok if name available
            tk.Label(frame2, text="Welcome "+username).grid()
            if entry == None:
                tk.Label(frame2, text="Connected to Backup Server").grid()
            tk.Button(frame2, text="Choose file", command=lambda:open_file(frame2)).grid()
            dummy = tk.Label(frame2, text="")
            dummy.grid()
            lex_input = tk.Entry(frame2, bd=5)
            lex_input.grid()
            tk.Button(frame2, text="Insert lexicon", command=lambda:add_lexicon(lex_input)).grid()      #add lexicon through GUI
            tk.Button(frame2, text = "Quit",command=quit_app).grid()

            show_lexicon(frame2, dummy)                                                        #GUI for lexicon
            frame2.tkraise()
            
            poll_socket.connect(('localhost', polling_port))
            poll_socket.send("hello".encode())
            threading.Thread(target=polling_req, args= (frame2,)).start()                                        #new thread for checking polling req
            
            
        
        else:                                      #server rejects if name not available
            if(msg == "duplicate"):
                tk.Label(frame2, text="Name not available").grid()
                
            elif(msg == "full_capacity"):           #server rejects if already 3 clients running
                tk.Label(frame2, text="Already 3 clients running").grid()

            tk.Button(frame2, text = "Quit",command=quit_app).grid()
            tk.Button(frame2, text = "Retry", command=lambda: restart(frame2)).grid()
            frame2.tkraise()
    except:                                     
        global backup
        if backup == 0:
            server_port = 12101
            polling_port = 12106
            backup = 1
            send_username(root_frame, entry)
            return
        root_frame.grid_remove()                                #Notify username if server not connected
        frame2 = tk.Frame(master)
        frame2.grid()
        tk.Label(frame2, text="Server not connected").grid()
        tk.Button(frame2, text="Quit", command=quit_app).grid()
        tk.Button(frame2, text = "Retry", command=lambda: restart(frame2)).grid()
        
""" restart client """        
def restart(root):
    root.grid_remove()
    client_socket.close()
    poll_socket.close()
    global send_start, disconnected, backup, server_port, polling_port
    server_port = 12100
    polling_port = 12105
    backup = 0
    send_start = 0
    disconnected = False

    landing()

""" quit application """
def quit_app():
    master.destroy()
    client_socket.close()
    os._exit(1)

"""Prompt user for username  """
def landing():
    
    root_frame = tk.Frame(master, width=300, height=100)
    root_frame.grid()
    tk.Label(root_frame, text="Username").grid(row=0, column=0)
    entry = tk.Entry(root_frame, bd=5)
    entry.grid(row=0, column=1)
    tk.Button(root_frame, text="confirm",
            command=lambda: send_username(root_frame, entry = entry)).grid(row=1)

    


master = tk.Tk()                    # draw client window
master.title("client")
master.geometry("500x200")
landing()                           #prompt for username
tk.mainloop()

client_socket.close()
