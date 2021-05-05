""" 
Mohammad Rifat Arefin
ID: 1001877262  
"""
import socket
import threading
import re
import tkinter as tk
import os
import pickle
import time

""" create a TCP socket """
server_port = 12100
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost',server_port))    #create server on a port
server_socket.listen()                          
print ('The server is ready to receive')

bk_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #create socket to connect to backup
poll_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #create socket for polling clients
poll_socket.bind(('localhost',12105))    #create server on a port
poll_socket.listen()

lexicon = set(open('lexicon.txt').read().split())   #read lexicon from file
client_name = set()                            #currently connected clients
name2 = set(client_name)                       #for checking arriving or leaving clients

""" thread for each client """
def listen(connection_socket, username):

    while(True):
        try:
            header = connection_socket.recv(1024).decode()        #check header for data or polling req
            if (header =="data"):
                connection_socket.send("send data".encode())        #send ack
                
                break
            elif (len(header) == 0):                                #break if client disconnect 
                break
            elif (header == "lexicon"):
                print("header lexicon")
                connection_socket.send("send_lexicon".encode())     #send ack
                lex = connection_socket.recv(1024)                  #recv lexicon
                
                lex = pickle.loads(lex)
                global lexicon
                lexicon = lexicon.union(lex)
                print(lexicon)
        except Exception as e:
            print(e)
            print("prob")
            continue

    
    data = b''
    while(True):                                #receive file in chunks
        chunk = connection_socket.recv(1024)
        data += chunk
        if len(chunk)<1024:
            break

    print(data.decode()+username)
    st = data.decode()                          #convert binary to text
    for i in lexicon:                           #replace misspelled words
        word = r'\b' +i +r'\b'
        pattern = re.compile(word,re.IGNORECASE)
        for m in re.findall(pattern, st):

            st = st.replace(m,'['+m+']')
    connection_socket.send(st.encode())         #send checked file
        
    connection_socket.close()                   #close socket
    client_name.remove(username)                #remove from list
    

""" refresh client names real time
master -> frame to refresh """
def real_time(master, client_label):
    client_label['text'] = str(len(client_name))+" client(s) connected\n"+ str([x for x in client_name])+"\n"
    global name2                                    #compare with older client names
    if(len(client_name)<len(name2)):                #check leaving clients
        client_label['text']+=str(name2.difference(client_name)) +" has left"
    elif(len(client_name)>len(name2)):              #check arriving clients
        client_label['text']+=str(client_name.difference(name2)) +" has arrived"
    name2 = set(client_name)
    master.after(3000, real_time, master, client_label)#calls itself every 3 secs

""" thread for real time GUI """
def show_clients():
    master = tk.Tk()                                            # draw server window
    master.title("Server")
    master.geometry("500x200")
    tk.Label(master, text="Server started").grid()
    client_label = tk.Label(master, text=[x for x in client_name])
    client_label.grid()
    tk.Button(master, text = "Quit",command=lambda: quit_app(master)).grid()
    real_time(master, client_label)                            #refresh client names real time
    
    
    tk.mainloop()
    server_socket.close()
    os._exit(1)

""" thread for polling """
def polling(poll):                                                  
    # print("addr")
    while(1):
        try:
            time.sleep(10)
            print("sending")
            poll.send("polling".encode())                               #send polling request to client
        except:
            break
        
        
""" Try to connect to backup every 10 seconds """
def connect_backup():
    flag = 0
    while(1):
        time.sleep(10)
        if(flag == 0):
                try:
                    bk_socket.connect(('localhost', 12102))               #connect with backup server
                    bk_socket.send("server connected".encode())
                    flag = 1
                    print("connected")
                    
                except Exception as e:
                    
                    print("Backup not connected")
        try:
            print(bk_socket.recv(1024).decode())
            lex = pickle.dumps(lexicon)                                 #send lexicon to backup
            bk_socket.send(lex)
        except:
            flag=0

    
""" Quit button action """
def quit_app(master):
    master.destroy()
    server_socket.close()
    os._exit(1)

threading.Thread(target=show_clients).start()       #start thread for real time GUI
threading.Thread(target=connect_backup).start()
while 1: 
    
    connection_socket, addr = server_socket.accept()        #accept new clients
    username = connection_socket.recv(1024).decode()        #receive username
    if username not in client_name and len(client_name)<3:  #send ok msg if no conflict
        client_name.add(username)
        
        connection_socket.send("ok".encode())
        poll, p_addr = poll_socket.accept()                 #poll client on a different socket

        print(poll.recv(1024).decode())
        threading.Thread(target=polling, args= (poll,)).start()            #start thread for polling

    
    else:                                                   #reject with a msg
        if username in client_name:
            connection_socket.send("duplicate".encode())
        else:
            connection_socket.send("full_capacity".encode())

        connection_socket.close()
        continue

    # new threads will be forked for each connected client
    threading.Thread(target=listen, args= (connection_socket, username)).start()
