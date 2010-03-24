import MySQLdb
import xmpp
from sms77 import SMS77Client
from twisted.words.protocols.jabber.jid import JID, parse
import configuration
import string
from random import Random
import _mysql_exceptions

class Database:
    def __init__(self, host, username, password, database):
        self.__dbconn = MySQLdb.connect(host, username, password, database, use_unicode=True)
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        
    def __del__(self):
        self.__dbconn.close()

    def getCursor(self):
        return self.__dbconn.cursor()
    
    def commit(self):
        self.__dbconn.commit()

    def reconnect(self):
        self.__dbconn = MySQLdb.connect(self.host, self.username, self.password, self.database, use_unicode=True)
        
def checkMissingHttpKeys():
    cursor = db.getCursor() 
    cursor.execute("SELECT jid FROM users WHERE httpkey = %s", ("SECRET", ) )
    
    rows = cursor.fetchall()
    users = []
    
    for row in rows:
        httpkey = ''.join( Random().sample(string.letters+string.digits, 16) )
        users.append( (JID(row[0]), httpkey) )
        update = db.getCursor()
        update.execute("UPDATE users SET httpkey = %s WHERE jid = %s", (httpkey, row[0]) )
        update.close()
        
    cursor.close()
    db.commit()
    
    return users
    
def createUser(jid, username, phone, password = None):
    client = getSMS77Client(jid)
    cursor = db.getCursor()
    
    httpkey = ''.join( Random().sample(string.letters+string.digits, 16) )
    
    if password == None:
        if client == None:  
            sql = "INSERT INTO users (jid, username, phone, httpkey) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (jid.userhost(), username, phone, httpkey) )
        else:
            sql = "UPDATE users SET username = %s, phone = %s WHERE jid = %s"
            cursor.execute(sql, (username, phone, jid.userhost()) )
    else:
        if client == None:  
            sql = "INSERT INTO users (jid, username, password, phone, httpkey) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (jid.userhost(), username, password, phone, httpkey) ) 
        else:
            sql = "UPDATE users SET username = %s, password = %s, phone = %s WHERE jid = %s"
            cursor.execute(sql, (username, password, phone, jid.userhost()) )

    cursor.close()
    db.commit()
    
def getMessage(jid, msgid):
    cursor = db.getCursor()
    sql = "SELECT `rcpt`, `content`, `lastupdate`, `state` FROM statusmessages WHERE `jid` = %s AND `id` = %s;"
    cursor.execute(sql, (jid.userhost(), msgid,) )
    row = cursor.fetchone()
    if row == None: return None
    cursor.close()
    return { "jid": jid, "msgid": msgid, "rcpt": row[0], "content": row[1], "lastupdate": row[2], "state": row[3] }
    
def storeMessage(jid, msgid, rcpt, content):
    cursor = db.getCursor()
    sql = "INSERT INTO statusmessages (`jid`, `id`, `rcpt`, `content`, `lastupdate`) VALUES (%s, %s, %s, %s, NOW())" 
    cursor.execute(sql, (jid.userhost(), msgid, rcpt, unicode(content),))
    cursor.close()
    db.commit()
    
def updateMessageState(jid, msgid, state):
    cursor = db.getCursor()
    if state in [ "DELIVERED", "NOTDELIVERED" ]:
        sql = "DELETE FROM statusmessages WHERE `jid` = %s AND `id` = %s;"
        cursor.execute(sql, (jid.userhost(), msgid,))
    else:
        sql = "UPDATE statusmessages SET `state` = %s AND `lastupdate` = NOW() WHERE `jid` = %s AND `id` = %s;"
        cursor.execute(sql, (state, jid.userhost(), msgid,))
    
    cursor.close()
    db.commit()
    
    
def checkHTTPGetKey(userid, key):
    cursor = db.getCursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE jid = %s AND httpkey = %s", (userid, key) )
    row = cursor.fetchone()
    ret = False
    if row[0] > 0: ret = True
    cursor.close()
    return ret

def getHTTPGetKey(userid):
    cursor = db.getCursor()
    cursor.execute("SELECT httpkey FROM users WHERE jid = %s", (userid,))
    row = cursor.fetchone()
    cursor.close()
    if row == None: return None
    return row[0]
    
def removeUser(jid):
    cursor = db.getCursor()
    cursor.execute("DELETE FROM users WHERE jid = %s", (jid.userhost(),) )
    cursor.close()
    db.commit()
    
def isUserAvailable(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT COUNT(*) FROM roster WHERE jid = %s AND resource = %s", (jid.userhost(), xmpp.getResource(jid)) )
    row = cursor.fetchone()
    ret = False
    if row[0] > 0: ret = True
    cursor.close()
    return ret
    
def setUserAvailable(jid, priority = 0):
    if not isUserAvailable(jid):
        cursor = db.getCursor()
        try:
            cursor.execute("INSERT INTO roster (jid, resource, priority) values (%s, %s, %s);", (jid.userhost(), xmpp.getResource(jid), priority) )
            cursor.close()
            db.commit()
        except _mysql_exceptions.OperationalError:
            print "can't set status in roster for " + str(jid.userhost()) + ", user don't exists!"
            cursor.close()
            db.commit()

def setUserUnavailable(jid):
    cursor = db.getCursor()
    cursor.execute("DELETE FROM roster WHERE jid = %s AND resource = %s", (jid.userhost(), xmpp.getResource(jid)) )
    cursor.close()
    db.commit()
    
def getContacts(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT contact FROM contacts WHERE jid = %s", (jid.userhost(),) )
    
    ret = []
    row = cursor.fetchone()
    
    while (row != None):
        if row[0] != "":
            ret.append(JID(row[0] + "@" + configuration.getConfig().jabberComponentName))
            
        row = cursor.fetchone()
        
    cursor.close()
    
    return ret

def addContact(jid, contact):
    cursor = db.getCursor()
    try:
        cursor.execute("INSERT INTO contacts (jid, contact) values (%s, %s)", (jid.userhost(), xmpp.getUser(contact)) )
        cursor.close()
    except _mysql_exceptions.IntegrityError:
        cursor.close()
        db.commit()
        
def removeContact(jid, contact):
    cursor = db.getCursor()
    cursor.execute("DELETE FROM contacts WHERE jid = %s AND contact = %s", (jid.userhost(), xmpp.getUser(contact)))
    cursor.close()
    db.commit()
    
def getSMS77Client(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT jid, username, password, phone FROM users WHERE jid = %s" , (jid.userhost(),) )
    row = cursor.fetchone()
    if row == None: return None
    cursor.close()
    return SMS77Client(JID(row[0]), row[1], row[2])

def getDefaultMessageType(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT msgtype FROM users WHERE jid = %s" , (jid.userhost(),) )
    row = cursor.fetchone()
    cursor.close()
    if row == None:
        return None
    return row[0]

def setDefaultMessageType(jid, msgtype):
    cursor = db.getCursor()
    cursor.execute("UPDATE users SET msgtype = %s WHERE jid = %s" , (msgtype, jid.userhost(),) )
    cursor.close()
    db.commit()
    
def setPassword(jid, password):
    cursor = db.getCursor()
    cursor.execute("UPDATE users SET password = %s WHERE jid = %s" , (password, jid.userhost(),) )
    cursor.close()
    db.commit()

def getUsername(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT username FROM users WHERE jid = %s" , (jid.userhost(),) )
    row = cursor.fetchone()
    cursor.close()
    if row == None:
        return None
    return row[0]

def getPhone(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT phone FROM users WHERE jid = %s" , (jid.userhost(),) )
    row = cursor.fetchone()
    cursor.close()
    if row == None:
        return None
    return row[0]

def getBalance(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT balance FROM users WHERE jid = %s" , (jid.userhost(),) )
    row = cursor.fetchone()
    cursor.close()
    if row == None:
        return None
    return row[0]

def setBalance(jid, balance):
    cursor = db.getCursor()
    cursor.execute("UPDATE users SET balance = %s, lastupdate = NOW() WHERE jid = %s" , (balance, jid.userhost(),) )
    cursor.close()
    db.commit()
    
def isReportRequested(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE jid = %s AND report = 1", (jid.userhost(),) )
    row = cursor.fetchone()
    ret = False
    if row[0] > 0: ret = True
    cursor.close()
    return ret

def setReportRequested(jid, yesno):
    if yesno == True: yesno = 1
    else: yesno = 0
    
    cursor = db.getCursor()
    cursor.execute("UPDATE users SET report = %s WHERE jid = %s", (yesno, jid.userhost(),) )
    cursor.close()
    db.commit()
    
def getMessageAsChat(jid):
    cursor = db.getCursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE jid = %s AND aschat = 1", (jid.userhost(),) )
    row = cursor.fetchone()
    ret = False
    if row[0] > 0: ret = True
    cursor.close()
    return ret

def setMessageAsChat(jid, yesno):
    if yesno == True: yesno = 1
    else: yesno = 0
    
    cursor = db.getCursor()
    cursor.execute("UPDATE users SET aschat = %s WHERE jid = %s", (yesno, jid.userhost(),) )
    cursor.close()
    db.commit()
    
def init(host, username, password, database):
    global db
    db = Database(host, username, password, database)
