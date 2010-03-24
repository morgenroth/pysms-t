#!/usr/bin/python
# -*- coding: utf-8 -*-

subject = {}
message = {}
    
subject["update"] = u"Eine neue Gateway Software!"
message["update"] = u"""Das SMS77.de-zu-XMPP Gateway wurde komplett überarbeitet und sollte bezüglich Performance und Stabilität nun keine Probleme mehr bereiten. Ihr registrierter Account bleibt natürlich erhalten.

## Was ist neu? ##

+ Deutlich performanter und stabiler
+ Inbound SMS und Statusübermittlung in Echtzeit
+ Konfigurationsparameter (erreichbar über das Gateway-Registrierungsformular)
    * Standard SMS Typ
    * Eingehender Nachrichten Typ (chat/message)
    * SMS Berichte empfangen
+ Aktueller Kontostand als Statusnachricht des Gateways


## Wichtig ##

Für die eingehenden BasicPlus SMS und die SMS Berichte muss das SMS77.de Konto entsprechend eingerichtet werden. Das neue Gateway verwendet die Push-Technologie um über eingehende Nachrichten und Berichte von SMS77.de informiert zu werden. Dazu müssen Einstellungen in dem Bereich für die "HTTP-API" vorgenommen werden. Um in diesen Bereich zu gelangen melden Sie sich auf der Seite www.sms77.de mit Ihrem Konto an. Wählen Sie aus der oberen Leiste die Schaltfläche "Mein SMS" aus. Anschließend klicken Sie auf der linken Leiste die Option "HTTP API" an und modifizieren die folgenden Parameter:

"HTTP API aktivieren"
Diese Option muss angewählt (Haken gesetzt) sein.

"BasicPlus Antworten an URL weiterleiten"
Hier muss die URL des SMS-Gateway eingesetzt werden. Jeder Benutzer bekommt eine eindeutige URI zugewiesen, in die auch ein persönlicher Schlüssel eingearbeitet ist. Bitte tragen Sie in das Eingabefeld folgende URL ein:
<<<URI1>>>

"Statusbericht per HTTP GET an URL senden"
Auch hier muss die URL des SMS-Gateway eingesetzt werden. Es handelt sich dabei nicht um die selbe wie für die BasicPlus Antworten! Bitte tragen Sie in das Eingabefeld folgende URL ein:
<<<URI2>>>
"""

subject["welcome"] = u"Willkommen / Anleitung"
message["welcome"] = u"""Gratulation!

Sofern Ihr SMS77.de Konto aufgeladen ist, kann Ihr Messenger nun SMS versenden. Für die Rückmeldungen von Nachrichten zu Ihnen sind allerdings noch ein paar Schritte nötig, die in dem folgenden Absatz beschrieben sind.

## Wichtig ##

Für die eingehenden BasicPlus SMS und die SMS Berichte muss das SMS77.de Konto entsprechend eingerichtet werden. Das neue Gateway verwendet die Push-Technologie um über eingehende Nachrichten und Berichte von SMS77.de informiert zu werden. Dazu müssen Einstellungen in dem Bereich für die "HTTP-API" vorgenommen werden. Um in diesen Bereich zu gelangen melden Sie sich auf der Seite www.sms77.de mit Ihrem Konto an. Wählen Sie aus der oberen Leiste die Schaltfläche "Mein SMS" aus. Anschließend klicken Sie auf der linken Leiste die Option "HTTP API" an und modifizieren die folgenden Parameter:

"HTTP API aktivieren"
Diese Option muss angewählt (Haken gesetzt) sein.

"BasicPlus Antworten an URL weiterleiten"
Hier muss die URL des SMS-Gateway eingesetzt werden. Jeder Benutzer bekommt eine eindeutige URI zugewiesen, in die auch ein persönlicher Schlüssel eingearbeitet ist. Bitte tragen Sie in das Eingabefeld folgende URL ein:
<<<URI1>>>

"Statusbericht per HTTP GET an URL senden"
Auch hier muss die URL des SMS-Gateway eingesetzt werden. Es handelt sich dabei nicht um die selbe wie für die BasicPlus Antworten! Bitte tragen Sie in das Eingabefeld folgende URL ein:
<<<URI2>>>
"""

baseurl = {}
baseurl["message"] = u"http://sms.localhost:8888/message/<<<JID>>>/<<<KEY>>>"
baseurl["status"] = u"http://sms.localhost:8888/status/<<<JID>>>/<<<KEY>>>"

def getInfoMessage(type, jid, key):
    uri = { "message": baseurl["message"].replace("<<<JID>>>", jid).replace("<<<KEY>>>", key),
    "status": baseurl["status"].replace("<<<JID>>>", jid).replace("<<<KEY>>>", key) }
    
    return { 0: subject[type], 1: message[type].replace("<<<URI1>>>", uri["message"]).replace("<<<URI2>>>", uri["status"]) }
