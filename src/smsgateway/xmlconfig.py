from configuration import Configuration

import sha
import xml.dom.minidom
from xml.dom.minidom import Node
 
def readXmlConfig(filename, config):
    doc = xml.dom.minidom.parse(filename)
    e_config = doc.documentElement
    
    for subElement in e_config.childNodes:
        if subElement.nodeType != Node.TEXT_NODE:
            for serverElement in subElement.childNodes:
                if serverElement.nodeType != Node.TEXT_NODE:
                    setConfigParam(config, subElement.nodeName, serverElement.nodeName, serverElement.firstChild.data) 
    
    # clean-up
    doc.unlink()
    
def setConfigParam(config, section, param, value):
    if section == "server":
        if param == "admin":
            config.serverAdmin = value
        elif param == "name":
            config.serverName = value
        elif param == "description":
            config.serverDescription = value
        elif param == "contacticon":
            config.contactIcon = file(value).read()
	    config.contactIconHash = sha.new(config.contactIcon).hexdigest()
    elif section == "jabber":
        if param == "server":
            config.jabberHost = value
        elif param == "port":
            config.jabberPort = int(value)
        elif param == "name":
            config.jabberComponentName = value
        elif param == "password":
            config.jabberPassword = value
    elif section == "mysql":
        if param == "server":
            config.mysqlHost = value
        elif param == "database":
            config.mysqlDatabase = value
        elif param == "username":
            config.mysqlUsername = value
        elif param == "password":
            config.mysqlPassword = value
