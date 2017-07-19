#coding=utf-8

from datetime import *
from enum import Enum
from xml.dom import minidom
from email.mime.text import MIMEText
from email.header import Header
from DBOperator import DBOperator
import http.cookiejar
import urllib
import urllib.request, re, codecs, os, os.path, smtplib, configparser, time, sys, uuid

XML_FILE_NAME = 'Lufax.xml'
SOURCE_NODE_NAME = 'Source'

PATH_CONFIG = 'config/'
CONFIG_FILE_NAME = 'config.ini'
CONFIG_FIELD_EMAIL = 'email'
CONFIG_FIELD_DATABASE = 'database'
CONFIG_FIELD_51JOB = '51job'

PATH_LOG = 'log/'
LOG_FILE_NAME = 'log.txt'

#'(button type.*?)'
VIEW_MY_RESUME_REGEX = '近60天内简历被浏览<span class="c_orange">(\d+?)</span>[\S\s]*?<span class="c_orange">(\d+?)</span>[\S\s]*?(<div class="e qy">[\S\s]*?<div class="h1"><a href="([\S\s]*?)"[\S\s]*?title="([\S\s]*?)">([\S\s]*?)<[\S\s]*?<em>([\S\s]*?)</em>[\S\s]*?<label>([\S\s]*?)</label>[\S\s]*?<p title="([\S\s]*?)"[\S\s]*?<label><span>([\S\s]*?)<[\S\s]*?title="([\S\s]*?)"[\S\s]*?</div>[\S\s]*?</div>)'
NEED_INPUT_VERIFYCODE_REGEX = '<div class="lr_e e2" style="display:" id="verifypic">'

URL_WHO_VIEW_MY_RESUME = 'http://i.51job.com/userset/resume_browsed.php?lang=c'
URL_LOGIN = 'http://login.51job.com'

#读ini文件
def ReadConfig(field, key):
    cf = configparser.ConfigParser()
    try:
    	cf.read(GetConfigPath() + CONFIG_FILE_NAME)
    	result = cf.get(field, key)
    except:
    	Log('Read config file wrong: field=%s,key=%s', (field, key))
    	sys.exit(1)
    return result

#写ini文件
def WriteConfig(field, key, value):
    cf = configparser.ConfigParser()
    try:
        cf.read(CONFIG_FILE_NAME)
        cf.set(field, key, value)
        cf.write(open(GetConfigPath() + CONFIG_FILE_NAME,'w'))
    except:
        sys.exit(1)
    return True

def IsNum(str):	
	try:
		float(str)
		return True
	except ValueError as e:
		return False

def IsInt(str):	
	try:
		int(str)
		return True
	except ValueError as e:
		return False

def GetAbsPath():
	'''
	sys.argv为执行该python脚本时的命令行参数
	sys.argv[0]为该python脚本的路径
	'''	
	if len(os.path.dirname(sys.argv[0])) < 1:
		return ''
	else:
		return os.path.dirname(sys.argv[0]) + '/'

def GetLogPath():
	return GetAbsPath() + PATH_LOG

def GetConfigPath():
	return GetAbsPath() + PATH_CONFIG

def Log(logStr):
	logPath = GetLogPath()
	if not os.path.exists(logPath):
		os.mkdir(logPath)
	logFile =logPath + LOG_FILE_NAME
	fpLog = open(logFile, 'a')
	nowTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
	fpLog.write('%s  %s\n' % (nowTime, logStr))
	fpLog.close()


#邮件通知类
class Notify():
	def __init__(self):
		self.smtp = ReadConfig(CONFIG_FIELD_EMAIL, 'smtp')
		self.sendFrom = ReadConfig(CONFIG_FIELD_EMAIL, 'from')
		self.sendTo = ReadConfig(CONFIG_FIELD_EMAIL, 'to')
		self.port = ReadConfig(CONFIG_FIELD_EMAIL, 'port')
		self.password = ReadConfig(CONFIG_FIELD_EMAIL, 'password')

	def Send(self, subject, content):
		message = MIMEText(content, 'html', 'utf-8')
		message['From'] = "ZMInfo" + "<" + self.sendFrom +">"
		message['To'] = "farrell" + "<" + self.sendTo +">"

		nowTime = time.strftime("%Y-%m-%d %H:%M", time.localtime())
		subject = nowTime + subject
		message['Subject'] = Header(subject, 'utf-8')
		try:
			print ('prepare send mail To: %s' % self.sendTo)
			#print ('smtp: %s port: %s from: %s to: %s password: %s' % (self.smtp, self.port, self.sendFrom, self.sendTo, self.password))
			smptObj = smtplib.SMTP(self.smtp, self.port)
			#smptObj.set_debuglevel(1)
			smptObj.login(self.sendFrom, self.password)
			smptObj.sendmail(self.sendFrom, [self.sendTo], message.as_string())
			smptObj.quit()
			print ('send mail success')
			return True
		except smtplib.SMTPException:
			print ('send mail fail')
			return False
		return False

class EmployerInfo():
	def __init__(self):
		self.data = {}

class ResumeAssist():
	def __init__(self, username, psd):
		self.notifyMgr = Notify()
		self.loginname = username
		self.password = psd

	def WhoViewMyResume(self):
		content = self.Login(URL_LOGIN)
		if self.NeedInputVerifyCode(content):
			return None
		employer = EmployerInfo()
		matchList = re.findall(VIEW_MY_RESUME_REGEX, content)
		#print('Regex:' + VIEW_MY_RESUME_REGEX)
		if len(matchList) != 1:
			print ('No Employer View My Resume')
		else:
			employer.data['viewCount'] = matchList[0][0]
			employer.data['viewEmployerCount'] = matchList[0][1]
			employer.data['employerHomePage'] = matchList[0][3]
			employer.data['employerName'] = matchList[0][5]
			employer.data['visitorSource'] = matchList[0][6]
			employer.data['viewTime'] = datetime.strftime(datetime.strptime(matchList[0][7], '%Y-%m-%d %H:%M'), '%Y%m%d%H%M')
			employer.data['employerSummary'] = matchList[0][8]
			employer.data['employerOperation'] = matchList[0][9]
			employer.data['searchKeyword'] = matchList[0][10]
			if self.IsNewly(employer):
				employer.data['createTime'] = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
				employer.data['guid'] = str(uuid.uuid1())
				#print (employer.data)
				self.notifyMgr.Send(' 简历被浏览:%s家,%s次' % (employer.data['viewEmployerCount'], employer.data['viewCount']), matchList[0][2])
				self.AddToDatabase(employer)
				return employer
		return None

	def NeedInputVerifyCode(self, content):
		matchList = re.findall(NEED_INPUT_VERIFYCODE_REGEX, content)
		if len(matchList) > 0:
			Log('Please Input Verifycode')
			self.notifyMgr.Send(' 51job需要输入验证码', '51job需要输入验证码') 
			return True
		else:
			return False

	def AddToDatabase(self, employer):
		if employer == None:
			return
		if len(employer.data.keys()) < 0:
			return
		formatStr = ''
		for i in range(0, len(employer.data.keys())):
			formatStr = formatStr + '%s,'
		formatStr = formatStr[0: len(formatStr) - 1]
		keyList = str(tuple(employer.data.keys()))
		keyList = keyList.replace('\'', '')
		keyList = keyList.replace('(', '')
		keyList = keyList.replace(')', '')
		sqlInsert = 'INSERT INTO viewhistory(%s) VALUES(%s)' % (keyList, formatStr)
		records = []
		param = list(employer.data.values())
		records.append(param)
		db.ExecuteMany(sqlInsert, records)

	def Login(self, url):
		cj = http.cookiejar.CookieJar()
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
		opener.addheaders = [('User-agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')]
		data = {'loginname':self.loginname,
				'password':self.password,
				'action': 'save',
				'from_domain': 'i',
				'lang': 'c',
				'verifycode': ''
				}
		#print (data)
		op = opener.open(url, urllib.parse.urlencode(data).encode())
		content = op.read()
		#print (content.decode('gbk'))
		#html = content.decode("gbk").encode('utf-8')
		#print(html)
		print (len(content))
		return content.decode('gbk')

	#是否为新的企业
	def IsNewly(self, employer):
		#print (employer.data['employerName'])
		#for field in house.data.keys():
		#	print (field + ':');
		#	print (house.data[field])
		row = db.Execute('SELECT * FROM viewhistory ORDER BY CreateTime DESC LIMIT 0,1')
		if row < 1:
			return True
		records = db.GetLastRecords()
		firshRecord = records[0]
		if employer.data['employerName'] != firshRecord['EmployerName']:
			return True
		else:
			#print ('Existed')
			return False

#reload(sys)
#sys.setdefaultencoding('utf8')
Log('=============================')
Log('Application Start')
#print (sys.getdefaultencoding())

dbHost = ReadConfig(CONFIG_FIELD_DATABASE, 'host')
dbPort = int(ReadConfig(CONFIG_FIELD_DATABASE, 'port'))
dbName = ReadConfig(CONFIG_FIELD_DATABASE, 'dbName')
dbUser = ReadConfig(CONFIG_FIELD_DATABASE, 'user')
dbPassword = ReadConfig(CONFIG_FIELD_DATABASE, 'password')
db = DBOperator(dbHost, dbPort, dbUser, dbPassword, dbName)
Log('Connect Database Successful')

assist = ResumeAssist(ReadConfig(CONFIG_FIELD_51JOB, 'loginname'), ReadConfig(CONFIG_FIELD_51JOB, 'password'))
assist.WhoViewMyResume()

Log('Application Closed')
