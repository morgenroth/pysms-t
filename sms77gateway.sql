-- phpMyAdmin SQL Dump
-- version 2.11.8.1deb5
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Erstellungszeit: 06. Januar 2009 um 09:22
-- Server Version: 5.0.51
-- PHP-Version: 5.2.6-0.1~lenny1

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Datenbank: `sms77gateway`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `contacts`
--

CREATE TABLE IF NOT EXISTS `contacts` (
  `jid` varchar(128) NOT NULL default '',
  `contact` varchar(64) NOT NULL default '',
  UNIQUE KEY `jid` (`jid`,`contact`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `roster`
--

CREATE TABLE IF NOT EXISTS `roster` (
  `jid` varchar(128) NOT NULL,
  `resource` varchar(255) NOT NULL,
  `priority` tinyint(4) NOT NULL,
  PRIMARY KEY  (`jid`,`resource`),
  KEY `priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `jid` varchar(128) NOT NULL default '',
  `username` varchar(255) NOT NULL default '',
  `password` varchar(255) NOT NULL default '',
  `phone` varchar(255) NOT NULL default '',
  `msgtype` enum('basicplus','standard','quality','festnetz','flash') NOT NULL default 'basicplus',
  `report` tinyint(1) NOT NULL default '0',
  `aschat` tinyint(1) NOT NULL default '0',
  `balance` double(5,3) default NULL,
  `lastupdate` datetime default NULL,
  `httpkey` varchar(128) NOT NULL default 'SECRET',
  PRIMARY KEY  (`jid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- 
-- Tabellenstruktur für Tabelle `statusmessages`
-- 

CREATE TABLE `statusmessages` (
  `jid` varchar(255) NOT NULL default '',
  `id` varchar(255) NOT NULL default '0',
  `state` enum('NO_STATUS','NONE','TRANSMITTED','DELIVERED','NOTDELIVERED','BUFFERED','ACCEPTED') NOT NULL default 'NONE',
  `rcpt` varchar(64) default NULL,
  `content` text,
  `lastupdate` datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (`jid`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- 
-- Constraints der exportierten Tabellen
-- 

-- 
-- Constraints der Tabelle `statusmessages`
-- 
ALTER TABLE `statusmessages`
  ADD CONSTRAINT `statusmessages_ibfk_1` FOREIGN KEY (`jid`) REFERENCES `users` (`jid`) ON DELETE CASCADE ON UPDATE CASCADE;


--
-- Constraints der exportierten Tabellen
--

--
-- Constraints der Tabelle `contacts`
--
ALTER TABLE `contacts`
  ADD CONSTRAINT `contacts_ibfk_1` FOREIGN KEY (`jid`) REFERENCES `users` (`jid`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints der Tabelle `roster`
--
ALTER TABLE `roster`
  ADD CONSTRAINT `roster_ibfk_1` FOREIGN KEY (`jid`) REFERENCES `users` (`jid`) ON DELETE CASCADE ON UPDATE CASCADE;
