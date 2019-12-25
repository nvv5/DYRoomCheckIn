#! /usr/bin/env python
#coding=utf-8
import requests
import re
import json
import time
import datetime
from douyu_authlogin import *
#proxy={'https':'127.0.0.1:8080'}

class Request(object):
	"""docstring for Request"""
	def __init__(self):
		self._session = requests.Session()
		
	def _requests(self, method, url, decode_level=2, retry=3, timeout=15, **kwargs):
		#proxy={'https':'127.0.0.1:8080'}
		if method in ["get", "post"]:
			for _ in range(retry + 1):
				try:
					#response = getattr(self._session, method)(url, timeout=timeout, **kwargs,proxies=proxy,verify=False)
					response = getattr(self._session, method)(url, timeout=timeout, **kwargs)
					return response.json() if decode_level == 2 else response.content if decode_level == 1 else response
				except Exception as e:
					print('报错：',e)
					time.sleep(10)
		return None
#构造token
def get_token(cookie):
	dic=cookie
	token=dic['acf_uid']+'_'+dic['acf_biz']+'_'+dic['acf_stk']+'_'+dic['acf_ct']+'_'+dic['acf_ltkid']
	#print(token)
	return token

#获取主播等级
def get_level(roomid):
	url='https://www.douyu.com/betard/%s'%roomid
	data=req._requests("get",url)
	return data['room']['levelInfo']['level']

#获取关注列表(flag为1时，获取符合签到条件的直播间)
def get_followlist(cookie,flag):
	url='https://www.douyu.com/wgapi/livenc/liveweb/follow/list?sort=0&cid1=0'
	while True:
		data=req._requests("get",url,cookies=cookie)
		if data!=None:
			if flag==1:
				followlist=[]
				for item in data['data']['list']:
					if item['show_time']>1569859200 and int(get_level(item['room_id']))>30:
						followlist.append(item)
			else:
				followlist=data['data']['list']
			return followlist
		else:
			print('获取直播列表失败：',data)
			time.sleep(60)

#获取直播状态
def get_roomstatus(followlist,roomid):
	for item in followlist:
		if item['room_id']==int(roomid):
			return item['nickname'],item['show_status']

#检测关注列表中是否开播
def check(followlist):
	list1=[]
	list2=[]
	for item in followlist:
		if item['show_status']==1:
			list1.append(item['room_id'])
		else:
			list2.append(item['room_id'])
	return list1,list2

#获取直播间房间等级，此脚本未用
def get_roomlevel(token,roomid):
	url='https://apiv2.douyucdn.cn/japi/roomuserlevel/apinc/levelInfo'
	data={'rid':roomid}
	header={'User-Agent': 'Mozilla/5.0 (Linux; Android 9; YAL-AL00 Build/HUAWEIYAL-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile Safari/537.36, Douyu_Android',
			'token':token,}
	html=req._requests("post",url,data=data,headers=header)
	print(html)

#签到
def checkin(token,roomid):
	url='https://apiv2.douyucdn.cn/japi/roomuserlevel/apinc/checkIn'
	data={'rid':roomid}
	header={'User-Agent': 'Mozilla/5.0 (Linux; Android 9; YAL-AL00 Build/HUAWEIYAL-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile Safari/537.36, Douyu_Android',
			'token':token}
	html=req._requests("post",url,data=data,headers=header)
	print(html)

def piliangcheckin(list,token,followlist):
	for roomid in list[::-1]:
		nickname,status=get_roomstatus(followlist,roomid)
		if status==1:
			print('%s已开播'%nickname)
			checkin(token,roomid)
			list.remove(roomid)

def get_sign(followlist,cookie):
	print('符合签到条件的总共有%s个房间'%len(followlist))
	for item in followlist[::-1]:
		roomid=item['room_id']
		signstatus=get_signstatus(cookie, roomid)
		if signstatus==1:
			print('%s今天已签到,签到排名为%s'%(item['nickname'],get_signrank(cookie,roomid)))
			followlist.remove(item)
	print('还有%s个房间未签到'%len(followlist))
	return followlist

def get_signstatus(cookie,roomid):
	url='https://www.douyu.com/japi/roomuserlevel/apinc/levelInfo?rid=%s'%roomid
	data=req._requests("get",url,cookies=cookie)
	signstatus=data['data']['signInInfo']['done']
	return signstatus

def get_signrank(cookie,roomid):
	url='https://www.douyu.com/japi/roomuserlevel/apinc/getSignInRankInfoList?rid=%s'%roomid
	data=req._requests("get",url,cookies=cookie)
	rank='100+'
	for item in data['data']:
		if item['uid']==int(cookie['acf_uid']):
			rank=item['rank']
			#print(rank)
	return rank

if __name__ == '__main__':
#有LTP0的cookie可用，cookie时限理论上是半年
#没有LTP0的直接复制登录后cookie也行，确保存在acf_uid、acf_biz、acf_stk、acf_ct、acf_ltkid这几个，时效性好像是7天
	cookies=''
	if re.search('LTP0=',cookies) is not None:
		cookie=authlogin(cookies)
	else:
		cookie=get_cookies(cookies)
	req=Request()
	start=time.time()
	followlist=get_followlist(cookie,1)
	followlist=get_sign(followlist,cookie)
	onlinelist,nobolist=check(followlist)
	end=time.time()
	print('用时%.2s秒获取列表'%(end-start))
	print('统计：%s个主播已开播，%s个主播未开播'%(len(onlinelist),len(nobolist)))
	lastMinute = 0
	lastnum=0
	token=get_token(cookie)
	piliangcheckin(onlinelist,token,followlist)
	while True:
		#减少回显频率
		now = datetime.datetime.now()
		if now.minute != lastMinute and len(nobolist)!= lastnum:
			lastMinute = now.minute
			lastnum=len(nobolist)
			print(now.strftime("%Y-%m-%d %H:%M:%S"),'%s个主播未开播'%len(nobolist))
		elif now.hour==3 and now.minute==59:
			followlist=get_followlist(cookie,1)
			onlinelist,nobolist=check(followlist)
			print('用时%.2s秒获取列表'%(end-start))
			print('统计：%s个主播已开播，%s个主播未开播'%(len(onlinelist),len(nobolist)))
			while True:
				now = datetime.datetime.now()
				print(now)
				if now.hour==4 and now.minute==0:
					piliangcheckin(onlinelist,token,followlist)
					#print(onlinelist)
					break
				time.sleep(0.1)
		#避免不必要时间的浪费，直接获取全部关注列表
		followlist=get_followlist(cookie,2)
		piliangcheckin(nobolist,token,followlist)
		time.sleep(5)