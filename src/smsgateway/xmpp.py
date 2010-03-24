#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.words.xish import domish
from wokkel.xmppim import MessageProtocol, AvailablePresence, PresenceClientProtocol, Presence

from wokkel import disco
from wokkel.subprotocols import XMPPHandler
from zope.interface import implements
from twisted.internet import defer
import database
import exceptions

from wokkel.subprotocols import IQHandlerMixin, XMPPHandler
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber import *

import messages 
import configuration
import binascii

NS_REGISTER = 'jabber:iq:register'
NS_VCARD = 'vcard-temp'
NS_VCARD_UPDATE = 'vcard-temp:x:update'
NS_JABBER_AVATAR = 'jabber:x:avatar'
NS_GATEWAY = 'jabber:iq:gateway'
NS_XDATA = 'jabber:x:data'
IQ_GET = '/iq[@type="get"]'
IQ_SET = '/iq[@type="set"]'
IQ_REGISTER_GET = IQ_GET + '/query[@xmlns="' + NS_REGISTER + '"]'
IQ_REGISTER_SET = IQ_SET + '/query[@xmlns="' + NS_REGISTER + '"]'
IQ_VCARD_GET = IQ_GET + '/vCard[@xmlns="' + NS_VCARD + '"]'
IQ_GATEWAY_GET = IQ_GET + '/query[@xmlns="' + NS_GATEWAY + '"]'
IQ_GATEWAY_SET = IQ_SET + '/query[@xmlns="' + NS_GATEWAY + '"]'

def getResource(jabberid):
    return jid.parse(jabberid.full())[2]

def getUser(jabberid):
    return jabberid.user

class XMPPComponent(MessageProtocol):
    def __init__(self):
        MessageProtocol.__init__(self)

    def connectionMade(self):
        print "Connected!"

    def connectionLost(self, reason):
        print "Disconnected!"

    def onMessage(self, msg):
        # return is there is no body or body is empty
        if not hasattr(msg, "body"):    return
        if msg.body == None:            return
        
        # don't react on messages with type 'error'
        try:
            if msg["type"] == "error":
                return
        except exceptions.KeyError:
            pass

        client = database.getSMS77Client(jid.JID(msg["from"]))
        
        # if a error is happened, then send a error message
        reply = domish.Element((None, "message"))
        reply["to"] = msg["from"]
        reply["from"] = msg["to"]
        
        # only send if the sms-account is available
        if client != None:
            types = [ 'basicplus', 'standard', 'quality', 'festnetz', 'flash' ]
            number = jid.parse(msg["to"])[0]
            
            # return if there is no number
            if number == None:  return
            if number == "":    return
            
            if str(msg.subject) in types:
                ret = client.sendMessage(msg.body, number, str(msg.subject))
            else:
                ret = client.sendMessage(msg.body, number)
                
            # store the sms for status reports
            if ret[2] != None:
                try:
                    database.storeMessage(JID(msg["from"]), ret[2], number, msg.body)
                except exceptions.KeyError:
                    pass
                
            reply.addElement("subject", content="Nachricht an " + number)
            reply.addElement("body", content=ret[1])
            
            if ret[0] != "100":
                reply["type"] = 'error'
                self.send(reply)
            else:
                if database.isReportRequested(jid.JID(msg["from"])):
                    self.send(reply)
        else:
            reply["type"] = 'error'
            reply.addElement("subject", content="Benutzerdaten nicht vorhanden")
            reply.addElement("body", content="Es konnten keine Benutzerdaten gefunden werden. Bitte registrieren Sie sich zuerst am Gateway!")
            self.send(reply)
        
        # update the balance in the status
        self.updateBalance(JID(msg["from"]).userhost()) 
            
    def updateBalance(self, jid):
        client = database.getSMS77Client(JID(jid))
        if client != None:
            balance = client.getBalance()
            if balance != None:
                status = { None: "Kontostand EUR " + balance,
                           "de": "Kontostand EUR " + balance,
                           "en": "account balance EUR " + balance }
                
                if balance != database.getBalance(JID(jid)):
                    self.send(AvailablePresence(JID(jid), None, status, 0))
                    database.setBalance(JID(jid), balance)
            
class GatewayHandler(XMPPHandler, IQHandlerMixin):
    iqHandlers = { IQ_GATEWAY_GET: '_onGetGateway',
                   IQ_GATEWAY_SET: '_onSetGateway' }
    
    def connectionInitialized(self):
        self.xmlstream.addObserver(IQ_GATEWAY_GET, self.handleRequest)
        self.xmlstream.addObserver(IQ_GATEWAY_SET, self.handleRequest)
        
    def _onGetGateway(self, iq):
        reply = domish.Element((NS_GATEWAY, "query"))
        reply.addElement("desc", content="Mobiltelefonnummer angeben (z.B. +4932112345678)")
        reply.addElement("prompt")
        return reply
    
    def _onSetGateway(self, iq):
        reply = domish.Element((NS_GATEWAY, "query"))
        reply.addElement("prompt", content=str(iq.query.prompt) + "@" + configuration.getConfig().jabberComponentName)
        return reply
            
class VCardHandler(XMPPHandler, IQHandlerMixin):
    iqHandlers = { IQ_VCARD_GET: '_onGetVCard' }
    
    def connectionInitialized(self):
        self.xmlstream.addObserver(IQ_VCARD_GET, self.handleRequest)
        
    def _onGetVCard(self, iq):
        tojid = jid.internJID(iq["to"])
        reply = domish.Element((NS_VCARD, "vCard"))
        
        if tojid.user == None:
            reply.addElement("FN", content=configuration.getConfig().serverName)
        else:
            reply.addElement("FN", content=getUser(tojid))
            reply.addElement("NICKNAME", content=getUser(tojid))
            reply.addElement("TEL").addElement("NUMBER", content=getUser(tojid))
            
            contactIcon = configuration.getConfig().contactIcon
            
            if contactIcon != None:
                photo = reply.addElement("PHOTO")
                photo.addElement("TYPE", content="image/png")
                
                photo_data = binascii.b2a_base64(contactIcon)
                photo.addElement("BINVAL", content=photo_data)
        
        return reply
                
class RegisterHandler(XMPPHandler, IQHandlerMixin):
    iqHandlers = { IQ_REGISTER_GET: '_onGetRegister', 
                   IQ_REGISTER_SET: '_onSetRegister' }

    def connectionInitialized(self):
        self.xmlstream.addObserver(IQ_REGISTER_GET, self.handleRequest)
        self.xmlstream.addObserver(IQ_REGISTER_SET, self.handleRequest)
        
    def _onGetRegister(self, iq):
        fromjid = jid.internJID(iq["from"])
        username = database.getUsername(fromjid)
        phone = database.getPhone(fromjid)
        smstyp = database.getDefaultMessageType(fromjid)
        
        reply = domish.Element((NS_REGISTER, "query"))
        xdata = reply.addElement("x", NS_XDATA)
        xdata.addElement("title", content=u"SMS77.de Gateway Registrierung")
        xdata.attributes["type"] = "form"
        
        instructions = u"Hier können Sie Ihren sms77.de Account mit dem Gateway\nregistrieren. Geben Sie dazu ihren sms77.de Benutzernamen\nsowie das dazugehörige Passwort an."
        
        xdata.addElement("instructions", content=instructions)
        reply.addElement("instructions", content=instructions)
        
        field = xdata.addElement("field")
        field.attributes["type"] = "hidden"
        field.attributes["var"] = "FORM_TYPE"
        field.addElement("value", content=NS_GATEWAY)
        
        field = xdata.addElement("field")
        field.attributes["type"] = "text-single"
        field.attributes["label"] = "Benutzername"
        field.attributes["var"] = "username"
        field.addElement("required")
        
        if username == None:
            reply.addElement("username")
        else:
            reply.addElement("username", content=username)
            field.addElement("value", content=username)
        
        field = xdata.addElement("field")
        field.attributes["type"] = "text-private"
        field.attributes["label"] = "Passwort"
        field.attributes["var"] = "password"
        field.addElement("required")
        reply.addElement("password")
        
        field = xdata.addElement("field")
        field.attributes["type"] = "text-single"
        field.attributes["label"] = "Telefonnummer"
        field.attributes["var"] = "phone"
        field.addElement("required")
        
        if username == None:
            reply.addElement("phone")
        else:
            reply.addElement("phone", content=phone)
            field.addElement("value", content=phone)
            
        field = xdata.addElement("field")
        field.attributes["type"] = "list-single"
        field.attributes["label"] = "Standard SMS Typ"
        field.attributes["var"] = "smstype"
        if smstyp != None: field.addElement("value", content=smstyp)
        
        option = field.addElement("option")
        option.attributes["label"] = "BasicPlus"
        option.addElement("value", content="basicplus")
        
        option = field.addElement("option")
        option.attributes["label"] = "Standard"
        option.addElement("value", content="standard")
        
        option = field.addElement("option")
        option.attributes["label"] = "Quality"
        option.addElement("value", content="quality")
        
        option = field.addElement("option")
        option.attributes["label"] = "Festnetz"
        option.addElement("value", content="festnetz")
        
        option = field.addElement("option")
        option.attributes["label"] = "Flash"
        option.addElement("value", content="flash")
        
        field = xdata.addElement("field")
        field.attributes["type"] = "list-single"
        field.attributes["label"] = "Eingehende SMS als"
        field.attributes["var"] = "msgtype"
        if database.getMessageAsChat(fromjid): field.addElement("value", content="chat")
        else: field.addElement("value", content="message")
        
        option = field.addElement("option")
        option.attributes["label"] = "Chat"
        option.addElement("value", content="chat")
        
        option = field.addElement("option")
        option.attributes["label"] = "Nachricht"
        option.addElement("value", content="message")
        
        field = xdata.addElement("field")
        field.attributes["type"] = "list-single"
        field.attributes["label"] = "Status Berichte"
        field.attributes["var"] = "report"
        if database.isReportRequested(fromjid): field.addElement("value", content="yes")
        else: field.addElement("value", content="no")
        
        option = field.addElement("option")
        option.attributes["label"] = "Ja"
        option.addElement("value", content="yes")
        
        option = field.addElement("option")
        option.attributes["label"] = "Nein"
        option.addElement("value", content="no")

        return reply

    def _onSetRegister(self, iq):
        fromjid = jid.internJID(iq["from"])
        data = iq.query
        
        username = None
        password = None
        phone = None
        msgtype = "message"
        report = False
        
        if data.x == None:
            """ use standard form if no xdata is returned """
            username = data.username
            password = data.password
            phone = data.phone
        else:
            """ xdata available, take it! """
            for field in data.x.elements():
                if field.name == "field":
                    if field.getAttribute("var") == "username": username = str(field.value)
                    if field.getAttribute("var") == "smstype": smstyp = str(field.value)
                    if field.getAttribute("var") == "password": password = str(field.value)
                    if field.getAttribute("var") == "phone": phone = str(field.value)
                    if field.getAttribute("var") == "msgtype": msgtype = str(field.value)
                    if field.getAttribute("var") == "report": report = str(field.value)
        
        # set password to None if there isn't one
        if password == "": password = None

        # remove or register?
        if data.remove == None:
            # register new account
            database.createUser(fromjid, username, phone, password)
            
            # set the default message type if set
            if smstyp != None:
                database.setDefaultMessageType(fromjid, smstyp)
                
            database.setMessageAsChat(fromjid, (msgtype == "chat"))
            database.setReportRequested(fromjid, (report == "yes"))
            
            # send own subscribe
            self.send(Presence(to=fromjid, type='subscribe'))
            
            # create welcome message
            httpkey = database.getHTTPGetKey(fromjid.userhost())
            welcomemsg = messages.getInfoMessage("welcome", str(fromjid.userhost()), httpkey)
            
            # send welcome message
            welcome = domish.Element((None, "message"))
            welcome["to"] = iq["from"]
            welcome.addElement("subject", content=welcomemsg[0])
            welcome.addElement("body", content=welcomemsg[1])
            self.send(welcome)
        else:
            # remove the account
            database.removeUser(fromjid)

class DiscoResponder(XMPPHandler):
    implements(disco.IDisco)
    
    def getDiscoItems(self, requestor, target, node):
        return defer.succeed([])

    def getDiscoInfo(self, requestor, target, nodeIdentifier):
        if not nodeIdentifier:
            return defer.succeed([
                disco.DiscoIdentity('sms', 'generic', 'SMS77.de Gateway'),
                disco.DiscoFeature('jabber:iq:version'),
                disco.DiscoFeature('jabber:iq:register'),
                #disco.DiscoFeature('jabber:iq:search'),
                disco.DiscoFeature('jabber:iq:gateway'),
                disco.DiscoFeature('vcard-temp'),
                disco.DiscoFeature('http://jabber.org/protocol/disco#info'),
                disco.DiscoFeature('http://jabber.org/protocol/disco#items')
            ])
        else:
            return defer.succeed([])

class UserPresence(Presence):
    def __init__(self, user=None, to=None, type=None):
        Presence.__init__(self, to, type)

        if user is not None:
            self["from"] = user.full()
                    
class UserAvailablePresence(UserPresence):
    def __init__(self, user=None, to=None, show=None, statuses=None, priority=0):
        UserPresence.__init__(self, user, to, type=None)

        if show in ['away', 'xa', 'chat', 'dnd']:
            self.addElement('show', content=show)

        if statuses is not None:
            for lang, status in statuses.iteritems():
                s = self.addElement('status', content=status)
                if lang:
                    s[(NS_XML, "lang")] = lang

        if priority != 0:
            self.addElement('priority', content=unicode(int(priority)))
        
        if configuration.getConfig().contactIcon != None:
            x = self.addElement('x', defaultUri=NS_VCARD_UPDATE)
            x.addElement("photo", content=configuration.getConfig().contactIconHash)
	    x = self.addElement('x', defaultUri=NS_JABBER_AVATAR)
            x.addElement("hash", content=configuration.getConfig().contactIconHash)

class UserUnavailablePresence(UserPresence):
    def __init__(self, user=None, to=None, statuses=None):
        UserPresence.__init__(self, user, to, type='unavailable')

        if statuses is not None:
            for lang, status in statuses.iteritems():
                s = self.addElement('status', content=status)
                if lang:
                    s[(NS_XML, "lang")] = lang
        
class PresenceHandler(PresenceClientProtocol):
    def _onPresenceSubscribed(self, presence):
        tojid = jid.internJID(presence["to"])
        self.subscribedReceived(tojid, jid.JID(presence["from"]))

    def _onPresenceUnsubscribed(self, presence):
        tojid = jid.internJID(presence["to"])
        self.unsubscribedReceived(tojid, jid.JID(presence["from"]))

    def _onPresenceSubscribe(self, presence):
        tojid = jid.internJID(presence["to"])
        self.subscribeReceived(tojid, jid.JID(presence["from"]))

    def _onPresenceUnsubscribe(self, presence):
        tojid = jid.internJID(presence["to"])
        self.unsubscribeReceived(tojid, jid.JID(presence["from"]))

    def _onPresenceAvailable(self, presence):
        entity = jid.JID(presence["from"])

        show = unicode(presence.show or '')
        if show not in ['away', 'xa', 'chat', 'dnd']:
            show = None

        statuses = self._getStatuses(presence)

        try:
            priority = int(unicode(presence.priority or '')) or 0
        except ValueError:
            priority = 0
        
        tojid = jid.internJID(presence["to"])
        self.availableReceived(tojid, entity, show, statuses, priority)
            
    def _onPresenceUnavailable(self, presence):
        entity = jid.JID(presence["from"])

        statuses = self._getStatuses(presence)

        tojid = jid.internJID(presence["to"])
        self.unavailableReceived(tojid, entity, statuses)

    def subscribeReceived(self, user, entity):
        if user.user != None:
            if database.getSMS77Client(entity) != None:
                self.send(UserPresence(user=user, to=entity, type='subscribed'))
                self.send(UserAvailablePresence(user, entity, None, None, 0))
                database.addContact(entity, user)
        else:
            self.subscribed(entity)
            self.subscribe(entity)

    def unsubscribeReceived(self, user, entity):
        if user.user != None:
            if database.getSMS77Client(entity) != None:
                self.send(UserUnavailablePresence(user, entity, None))
                self.send(UserPresence(user=user, to=entity, type='unsubscribed'))
                database.removeContact(entity, user)
        else:
            self.unsubscribed(entity)
            self.unsubscribe(entity)
            
    def subscribedReceived(self, user, entity):
        PresenceClientProtocol.subscribedReceived(self, entity)

    def unsubscribedReceived(self, user, entity):
        PresenceClientProtocol.unsubscribedReceived(self, entity)
        
    def availableReceived(self, user, entity, show=None, statuses=None, priority=0):
        if user.user != None:
            pass
        else:
            client = database.getSMS77Client(entity)
            if client == None:
                self.available(entity)
            else:
                balance = client.getBalance()
                if balance != None:
                    status = { None: "Kontostand EUR " + balance,
                               "de": "Kontostand EUR " + balance,
                               "en": "account balance EUR " + balance }
                    self.available(entity, None, status, 0)
                    
                    if balance != database.getBalance(entity):
                        database.setBalance(entity, balance)
                
            if not database.isUserAvailable(entity):                
                contacts = database.getContacts(entity)
                for contact in contacts:
                    self.send(UserAvailablePresence(contact, entity, None, None, 0))
                    
            database.setUserAvailable(entity, priority)
        
    def unavailableReceived(self, user, entity, statuses=None):
        if user.user != None:
            """ presence for a user """
            pass
        else:
            self.unavailable(entity)

            if database.isUserAvailable(entity):               
                contacts = database.getContacts(entity)
                for contact in contacts:
                    self.send(UserUnavailablePresence(contact, entity, None))
            
            database.setUserUnavailable(entity)
        
    
