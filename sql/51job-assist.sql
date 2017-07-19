/*
Navicat MySQL Data Transfer

Source Server         : ZMInfo
Source Server Version : 
Source Host           : 
Source Database       : 51job-assist

Target Server Type    : MYSQL
Target Server Version : 
File Encoding         : 

Date: 2017-07-19 16:59:09
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `viewhistory`
-- ----------------------------
DROP TABLE IF EXISTS `viewhistory`;
CREATE TABLE `viewhistory` (
  `GUID` varchar(200) NOT NULL,
  `CreateTime` bigint(4) NOT NULL,
  `EmployerName` varchar(200) NOT NULL,
  `EmployerHomePage` varchar(100) NOT NULL,
  `EmployerSummary` varchar(200) NOT NULL,
  `EmployerOperation` varchar(100) NOT NULL,
  `SearchKeyword` varchar(100) NOT NULL,
  `ViewTime` bigint(4) NOT NULL,
  `VisitorSource` varchar(50) NOT NULL,
  `ViewCount` int(11) DEFAULT NULL,
  `ViewEmployerCount` int(11) DEFAULT NULL,
  PRIMARY KEY (`GUID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

