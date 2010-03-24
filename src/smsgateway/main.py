import configuration
from xmlconfig import *
from twisted.application import service, internet
from twisted.web import server

from wokkel import generic, disco
from wokkel.component import Component

from httpreceiver import HTTPReceiver
from xmpp import XMPPComponent, DiscoResponder, PresenceHandler, RegisterHandler, VCardHandler, GatewayHandler
import database
import messages

from twisted.words.xish import domish

application = service.Application("smsgateway")
sc = service.IServiceCollection(application)

# read configuration
configuration.init()
conf = configuration.getConfig()
readXmlConfig("/opt/smsgateway/config.xml", configuration.getConfig())

# initialize database
database.init(conf.mysqlHost, conf.mysqlUsername, conf.mysqlPassword, conf.mysqlDatabase)

# start xmpp component
xmpp = Component(conf.jabberHost, conf.jabberPort, conf.jabberComponentName, conf.jabberPassword)
xmpp.logTraffic = False
handler = XMPPComponent()
handler.setHandlerParent(xmpp)

# fallback handling
generic.FallbackHandler().setHandlerParent(xmpp)

# version handling
generic.VersionHandler("SMS.de Gateway", "1.0").setHandlerParent(xmpp)

# allow disco handling
disco.DiscoHandler().setHandlerParent(xmpp)
DiscoResponder().setHandlerParent(xmpp)

# add handler for gateway requests
GatewayHandler().setHandlerParent(xmpp)

# add handler for vcards
VCardHandler().setHandlerParent(xmpp)

# add handler for registering
RegisterHandler().setHandlerParent(xmpp)

# PresenceHandler
PresenceHandler().setHandlerParent(xmpp)

xmpp.setServiceParent(sc)

# fire up the HTTP Server
site = server.Site(HTTPReceiver(handler))
i = internet.TCPServer(conf.inboundPort, site)
i.setServiceParent(sc)

# check for missing httpkeys
users = database.checkMissingHttpKeys()

for user in users:
    # create welcome message
    updatemsg = messages.getInfoMessage("update", user[0].userhost(), user[1])
    
    # send welcome message
    update = domish.Element((None, "message"))
    update["to"] = user[0].userhost()
    update.addElement("subject", content=updatemsg[0])
    update.addElement("body", content=updatemsg[1])
    xmpp.send(update)

# send status to admin
#status = domish.Element((None, "message"))
#status["to"] = conf.serverAdmin
#status.addElement("subject", content="status of " + conf.serverName)
#status.addElement("body", content="we're online!")
#xmpp.send(status)
