#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
from urllib import urlencode
import database
from twisted.words.protocols.jabber.jid import JID

class SMS77Client:
    
    def __init__(self, jid, username, password):
        """ initialize the sms77 client """
        self.__url = "https://gateway.sms77.de/"
        self.__jid = jid
        self.__username = username
        self.__password = password
        
    def __getUrl(self, type = 'default'):
        """ returns the correct url with encoded username and password """
        #params = urlencode({ "u": self.__username, "p": self.__password, "debug": 1 })
        params = urlencode({ "u": self.__username, "p": self.__password })
        
        if type == 'default':
            return self.__url + "?" + params
        elif type == 'status':
            return self.__url + "status.php?" + params
        elif type == 'balance':
            return self.__url + "balance.php?" + params
        elif type == 'address':
            return self.__url + "adress.php?" + params
        elif type == 'gatewaystatus':
            return "https://www.sms77.de/gateway/gateway-status.php"
    
    def sendMessage(self, message, receiver, type = None, sender = None):
        """ sends a message """
        
        # get default message type from database
        if type == None:
            type = database.getDefaultMessageType(self.__jid)
            
        if sender == None:
            sender = database.getPhone(self.__jid)
        
        # convert the encoding
        text = unicode(message).encode('latin_1', "replace")
        
        # prepare the url
        actionurl = self.__getUrl() + "&" + urlencode({ "text": text,
                                                       "to": self.__transformNumber(receiver),
                                                       "type": type,
                                                       "from": self.__transformNumber(sender),
                                                       "status": "1",
                                                       "return_msg_id": "1" })
        
        # send message
        try:
            ret = self.__doAction( actionurl )
        except urllib2.URLError:
            return { 0: "1001", 1: self.__decodeError("1001"), 2: None }
        
        if ret == "":
            return { 0: "1001", 1: self.__decodeError("1001"), 2: None }
            
        ret = ret.split("\n")
        
        if len(ret) > 1:
            return { 0: ret[0], 1: self.__decodeError(ret[0]), 2: ret[1] }
        else:
            return { 0: ret[0], 1: self.__decodeError(ret[0]), 2: None }
        
    def getBalance(self):
        """ returns the balance of the account """
        try:
            return self.__doAction( self.__getUrl('balance') )
        except urllib2.URLError:
            return None
    
    def __doAction(self, url):
        """ executes a command via http """
        usock = urllib2.urlopen(url)
        data = usock.read()
        usock.close()
        return data 
    
    def __decodeError(self, code):
        """ decode the error from the provider into text """
        codes = { "100": u"SMS wurde erfolgreich verschickt",
                  "101": u"Versand an mindestens einen Empfänger fehlgeschlagen",
                  "201": u"Ländercode für diesen SMS-Typ nicht gültig. Bitte als Basic SMS verschicken.",
                  "202": u"Empfängernummer ungültig",
                  "300": u"Bitte Benutzer/Passwort angeben",
                  "301": u"Variable to nicht gesetzt",
                  "304": u"Variable type nicht gesetzt",
                  "305": u"Variable text nicht gesetzt",
                  "306": u"Absendernummer ungültig (nur bei Standard SMS). Diese muss vom Format 0049... sein und eine gültige Handynummer darstellen.",
                  "307": u"Variable url nicht gesetzt",
                  "400": u"type ungültig. Siehe erlaubte Werte oben.",
                  "401": u"Variable text ist zu lang",
                  "402": u"Reloadsperre – diese SMS wurde bereits innerhalb der letzten 90 Sekunden verschickt",
                  "500": u"Zu wenig Guthaben vorhanden.",
                  "600": u"Carrier Zustellung misslungen",
                  "700": u"Unbekannter Fehler",
                  "801": u"Logodatei nicht angegeben",
                  "802": u"Logodatei existiert nicht",
                  "803": u"Klingelton nicht angegeben",
                  "900": u"Benutzer/Passwort-Kombination falsch",
                  "902": u"http API für diesen Account deaktiviert",
                  "903": u"Server IP ist falsch",
                  "": u"Der Server lieferte eine unbekannte Antwort.",
                  "1001": u"Der SMS77.de Server ist nicht erreichbar oder reagiert nicht.",
                  "1002": u"Der Server lieferte eine unbekannte Antwort." }
        
        return codes[code]
        
    def __transformNumber(self, number):
        """ checks the phone number an replaces the + with 00 """
        if number[:1] == "+":
            return "00" + number[1:] 
        
        return number
