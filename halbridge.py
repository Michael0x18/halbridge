#Private Messages

import sys
import string
import os
import socket

################CONFIGURATION################

#The server to connect to
HOST = "irc.efnet.org"
#Port to use
PORT = 6667

#Bot's nickname
NICK = "hal"
#Ident
IDENT = "Michael__"
#It's a bad joke
REALNAME = "Michael Michael0x18 the second"
#Control panel access (over ssh)
MASTER = "Michael0_"
#Channels to join
CHANNELS = ["#cemetech","#flood","#cemetechbot"]
#input buffer
readbuffer = ""
#Communication socket
s=socket.socket()

#For logging to.
log=open("log.txt","w");
#Context: dict of lists
last_messages=dict();
#Number of messages to save, per channel
last_messages_size=16;

#Attempt connection

##INITIAL CONNECTION##
s.connect((HOST, PORT))
s.send(bytes("NICK %s\n" % NICK, "UTF-8"))
s.send(bytes("USER %s %s join :%s\n" % (IDENT, HOST, REALNAME), "UTF-8"))
for CHANNEL in CHANNELS:
    s.send(bytes("JOIN %s\n" % (CHANNEL), "UTF-8"));
    last_messages[CHANNEL]=list()
s.send(bytes("PRIVMSG %s :Bot activated\n" % MASTER, "UTF-8"))
##INITIAL CONNECTION##

print("Finished navigating connection")

#Sends a message. Really just a quick thing.
def send_message(s,target,message):
    s.send(bytes("PRIVMSG %s :%s \n" % (target, message),"UTF-8"))
    print("(%s): %s: %s" % (target,NICK,message))
    log.write("(%s): %s: %s" % (target,NICK,message));
    log.write("\n");
    log.flush();

def send_message_nolog(s,target,message):
    s.send(bytes("PRIVMSG %s :%s \n" % (target, message),"UTF-8"))
    #print("(%s): %s: %s" % (target,NICK,message))


#indexed by the actual name, contains nicks
names=dict();
#indexed by the nick, contains actual name
nicks=dict();
#indexed by the actual name, contains channels connected
chans=dict();

###############/CONFIGURATION/###############



#Messages

#Handles a message sent in a channel (not privately)
def handle_message(s,channel,sender, message):
    print("(%s): %s: %s" % (channel,sender,message));
    log.write("(%s): %s: %s" % (channel,sender,message));
    log.write("\n")
    log.flush();
    #First, go around and forward it to people on the channel
    for name in names:
        if(chans[name]==channel):
            send_message_nolog(s,name,"("+channel+"): "+sender+": "+message)
    #Then stick it in the context queue.
    last_messages[channel].append(("(%s): %s: %s" % (channel,sender,message)));
    if len(last_messages[channel])>last_messages_size:
        last_messages[channel].pop(0);
    words = message.split(" ");
    if words[0].lower()=="%doc":
        if len(words)<2:
            send_message(s,channel,"Usage: %doc command")
        else:
            for i in range(1,len(words)):
                send_message(s,channel,search_doc(words[i]))
                return
    if words[0].lower()=="%shrug":
        send_message(s,channel,"¯\_(ツ)_/¯")
    return 0

#/messages

#actual name = thingy this script sends to
#nick = the thing in <these> while sending

#s is the socket, sender=sender, message=message string
def handle_pm(s,sender,message):
    global names
    global nicks
    global chans
    strings=message.split();
    size=len(strings);
    if sender in names:
        if message=="LOGOUT":
            chans.pop(sender);
            nicks.pop(names[sender]);
            names.pop(sender);
            send_message(s,sender,"Bye");
            return;
        #sender is logged in already
        #Just forward it to the channel
        send_message(s,chans[sender],"<"+names[sender]+"> "+message);
        #send it to other people who need to see it
        for n in names:
            if chans[n]==chans[sender] and n!=sender:
                send_message(s,n,"<"+names[sender]+"> "+message)
        #stick it in context queue
        last_messages[chans[sender]].append(("(%s): %s: %s" % (chans[sender],names[sender],message)));
        if len(last_messages[chans[sender]])>last_messages_size:
            last_messages[chans[sender]].pop(0);
    else:
        #Look at non-logged in message palette
        if strings[0]=='LOGIN':
            if(size!=4):
                send_message(s,sender,"Usage: LOGIN USERNAME PASSWORD CHANNEL");
            elif not os.path.isfile("logins/%s" % (strings[1])):
                send_message(s,sender,"Invalid username. Please register first");
            else:
                f1=open("logins/%s" % (strings[1]),"r");
                passwd=f1.read().split()[0];
                if(passwd!=strings[2]):
                    send_message(s,sender,"Invalid password.");
                else:
                    if(not (strings[3] in CHANNELS)):
                        send_message(s,sender,"Channel: Permission denied");
                        return;
                    if(strings[1] in nicks):
                        send_message(s,sender,"Invalid sign in detected: Did you LOGOUT?");
                        return;
                    names[sender]=strings[1];
                    nicks[strings[1]]=sender;
                    chans[sender]=strings[3];
                    send_message(s,sender,"Hello, %s!" % (names[sender]));
                    send_message(s,sender,"Joining channel %s" % (chans[sender]));
                    for st in last_messages[chans[sender]]:
                        send_message(s,sender,st);
#enter main loop
while 1:
    #Read the buffer and assume UTF-8
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    #Split into lines
    temp = str.split(readbuffer, "\n")
    #Stick the last (incomplete) line into the buffer again
    readbuffer=temp.pop()
    #Iterate the lines
    for linestr in temp:
        #Strip trailing stuff
        linestr = str.rstrip(linestr)
        #Tokenize
        line = str.split(linestr)
        if(line[0] == "PING"):
            s.send(bytes("PONG %s\n" % line[1], "UTF-8"))
        #Private Message
        if(line[1] == "PRIVMSG"):
            #Print the message to stdout
            #print(linestr);
            message = ""
            
            
            sender=""
            for c in line[0]:
                if c=="!":
                    break;
                if c!=":":
                    sender+=c;
            start=3
            if(sender=="saxjax"):
                #Keep parsing
                sender=""
                start=5
                while(line[4][-1]!=">"):
                    line[4]+=" "
                    line[4]+=line[5];
                    line.pop(5)
                for c in line[4]:
                    if c==">":
                        break;
                    if c!="<":
                        sender+=c
            for i in range(start,len(line)):
                message+=line[i];
                message+=" "
            message=str.rstrip(message)
            #message=str.lstrip(message,":")
            if(start==3):
                message=message[1:]
            #print("("+line[2]+"): "+sender+": "+message);
            #print(linestr);
            if(line[2] == NICK):
                #If private messaged - actually
                #Special if master?
                #if sender==MASTER:
                #    msg_out="Bot is active"
                #    s.send(bytes("PRIVMSG %s :%s \n" % (sender, msg_out), "UTF-8"))
                handle_pm(s,sender,message)

            else:
                #Channel wide message
                handle_message(s,line[2],sender,message)
        #Print stuff
        #print(linestr)
                    
