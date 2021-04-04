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

lexicon = set(open('lexicon.txt').read().split())   #read lexicon from file
client_name = set()                            #currently connected clients
name2 = set(client_name)                       #for checking arriving or leaving clients
client_addr = {}

""" thread for each client """
def listen(connection_socket, username):

    while(True):
        try:
            header = connection_socket.recv(1024).decode()
            if (header =="data"):
                connection_socket.send("send data".encode())
                break
            elif (len(header) == 0):
                break
            elif (header == "lexicon"):
                print("header lexicon")
                connection_socket.send("send_lexicon".encode())
                lex = connection_socket.recv(1024)
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
    print(data.decode())
    st = data.decode()                          #convert binary to text
    for i in lexicon:                           #replace misspelled words
        pattern = re.compile(i,re.IGNORECASE)
        for m in re.findall(pattern, st):

            st = st.replace(m,'['+m+']')
    connection_socket.send(st.encode())         #send checked file
        
    connection_socket.close()                   #close socket
    client_name.remove(username)                #remove from list
    client_addr.pop(username)

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

def polling():
    # print("addr")
    while(1):
        time.sleep(15)
        for k in client_addr.keys():
            try:
                client_addr[k].send("polling".encode())
            except:
                del client_addr[k]
    
""" Quit button action """
def quit_app(master):
    master.destroy()
    server_socket.close()
    os._exit(1)

threading.Thread(target=show_clients).start()       #start thread for real time GUI
threading.Thread(target=polling).start()
while 1: 
    
    connection_socket, addr = server_socket.accept()        #accept new clients
    username = connection_socket.recv(1024).decode()        #receive username
    if username not in client_name and len(client_name)<3:  #send ok msg if no conflict
        client_name.add(username)
        client_addr[username] = connection_socket
        connection_socket.send("ok".encode())
    
    else:                                                   #reject with a msg
        if username in client_name:
            connection_socket.send("duplicate".encode())
        else:
            connection_socket.send("full_capacity".encode())

        connection_socket.close()
        continue

    # new threads will be forked for each connected client
    threading.Thread(target=listen, args= (connection_socket, username)).start()
