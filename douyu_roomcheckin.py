#! /usr/bin/env python
#coding=utf-8
#Author:nws0507
import requests
import re
import json
import time
import datetime
from douyu_authlogin import *
#proxy={'https':'127.0.0.1:8080'}

#构造token
def get_token(cookie):
	dic=cookie
	token=dic['acf_uid']+'_'+dic['acf_biz']+'_'+dic['acf_stk']+'_'+dic['acf_ct']+'_'+dic['acf_ltkid']
	#print(token)
	return token

#获取主播等级
def get_level(roomid):
	url='https://www.douyu.com/betard/%s'%roomid
	r=requests.get(url).text
	data=json.loads(r)
	#print(data['room']['levelInfo']['level'])
	return data['room']['levelInfo']['level']

#获取关注列表(flag为1时，获取符合签到条件的直播间)
def get_followlist(cookie,flag):
	url='https://www.douyu.com/wgapi/livenc/liveweb/follow/list?sort=0&cid1=0'
	html=requests.get(url,cookies=cookie).text
	#print(html)
	data=json.loads(html)
	if flag==1:
		followlist=[]
		for item in data['data']['list']:
			if item['show_time']>1569859200 and int(get_level(item['room_id']))>30:
				followlist.append(item)
	else:
		followlist=data['data']['list']
	return followlist

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
			#print('%s已开播'%item['room_id'])
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
	html=requests.post(url,data,headers=header).text
	print(html)

#签到
def checkin(token,roomid):
	url='https://apiv2.douyucdn.cn/japi/roomuserlevel/apinc/checkIn'
	data={'rid':roomid}
	header={'User-Agent': 'Mozilla/5.0 (Linux; Android 9; YAL-AL00 Build/HUAWEIYAL-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile Safari/537.36, Douyu_Android',
			'token':token}
	html=requests.post(url,data,headers=header).text
	print(html)

def piliangcheckin(list,token,followlist):
	for roomid in list:
		nickname,status=get_roomstatus(followlist,roomid)
		if status==1:
			print('%s已开播'%nickname)
			checkin(token,roomid)
			nobolist.remove(roomid)

if __name__ == '__main__':
#有LTP0的cookie可用，cookie时限理论上是半年
#没有LTP0的直接复制登录后cookie也行，确保存在acf_uid、acf_biz、acf_stk、acf_ct、acf_ltkid这几个，时效性好像是7天
	cookies=''    #将cookie复制到cookie=''里面
	if re.search('LTP0=',cookies) is not None:
		cookie=authlogin(cookies)
	else:
		cookie=get_cookies(cookies)
	start=time.time()
	followlist=get_followlist(cookie,1)
	onlinelist,nobolist=check(followlist)
	end=time.time()
	print('用时%.2s秒获取列表'%(end-start))
	print('统计：%s个主播已开播，%s个主播未开播'%(len(onlinelist),len(nobolist)))
	lastMinute = 0
	lastnum=0
	token=get_token(cookie)
	while True:
		#减少回显频率
		now = datetime.datetime.now()
		if now.minute != lastMinute and len(nobolist)!= lastnum:
			lastMinute = now.minute
			lastnum=len(nobolist)
			print(now.strftime("%Y-%m-%d %H:%M:%S"),'%s个主播未开播'%len(nobolist))
		#避免不必要时间的浪费，直接获取全部关注列表
		followlist=get_followlist(cookie,2)
		piliangcheckin(nobolist,token,followlist)
		time.sleep(5)
