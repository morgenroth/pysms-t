#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.web import resource
from twisted.words.xish import domish
from twisted.words.protocols.jabber.jid import JID
import configuration
import database
import exceptions

""" Beispiel URI: http://localhost:8888/status/user@host/2z8UDmyrcK9xCA6T?sender=0123456789&msg=Hallo+Welt """

class HTTPReceiver(resource.Resource):
    isLeaf = True
    def __init__(self, xmpp):
        self.xmpp = xmpp
    
    def render_GET(self, request):
        """ reveive http get requests from sms77.de """
        
        # get configuration
        conf = configuration.getConfig()
     
        # split the path into parameter
        params = request.path.rsplit("/")
        
        # catch wrong uri
        if len(params) < 4: return "WRONG URI"
        
        # check the httpkey for prevent spam
        if not database.checkHTTPGetKey(params[2], params[3]): return "WRONG KEY";
        
        # check first for incoming message or statusreport
        if params[1] == "message":
            return self.processMessage(params[2], request.args)
        elif params[1] == "status":
            return self.processReport(params[2], request.args)
        else:
            return "WRONG TYPE"

    def processMessage(self, jid, args):
        # get configuration
        conf = configuration.getConfig()

        # catch missing or empty sender string
        try:
            if len(args["from"][0]) <= 0: return "SENDER MISSING"
            
            # modify incoming phone number
            phonenumber = args["from"][0]
            if phonenumber.startswith("00"):
                phonenumber = "+" + phonenumber[2:]
        except exceptions.KeyError:
            return "SENDER MISSING"
        
        # create a new message
        status = domish.Element((None, "message"))
        status["to"] = jid        
        status["from"] = phonenumber + "@" + conf.jabberComponentName
        
        if database.getMessageAsChat(JID(jid)):
            status.attributes["type"] = "chat"
        else:
            status.addElement("subject", content="Eingehende SMS")

        try:
            body = args["text"][0].decode("latin1")
            status.addElement("body", content=body)
        except exceptions.KeyError:
            status.addElement("body")
        
        # send the message
        self.xmpp.send(status)
        
        # update the balance in the status
        self.xmpp.updateBalance(jid)

        return "OK"
    
    def processReport(self, jid, args):
        # get configuration
        conf = configuration.getConfig()

        # catch missing or empty msg_id string
        try:
            if len(args["msg_id"][0]) <= 0: return "MSGID MISSING"
            msgdata = database.getMessage(JID(jid), args["msg_id"][0])
        except exceptions.KeyError:
            return "MSGID MISSING"

        # create a new message
        status = domish.Element((None, "message"))
        status["to"] = jid
        
        if msgdata != None:
            status["from"] = msgdata["rcpt"] + "@" + conf.jabberComponentName
        
        # add subject
        status.addElement("subject", content=u"Statusbericht")

        try:
            # update message state in the database
            database.updateMessageState(JID(jid), args["msg_id"][0], args["status"][0])

            # create a message for notify the user
            msg = u"Der Status ihrer SMS hat sich geändert: " + unicode(args["status"][0])
	    if msgdata != None:
	        msg += u"\n\n-- Nachrichtentext --\n"
		msg += msgdata["content"]
            
            # add the message to the body
            status.addElement("body", content=msg)
        except exceptions.KeyError:
            status.addElement("body")
        
        if database.isReportRequested(JID(jid)):
            # send the message
            self.xmpp.send(status)
        
        # update the balance in the status
        self.xmpp.updateBalance(jid)

        return "OK"
