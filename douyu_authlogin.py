#! /usr/bin/env python
#coding=utf-8
import requests
import re
import json
#proxy={'https':'127.0.0.1:8080'}
def get_cookies(s):
    s=s.replace('=',':')
    l=s.split('; ')
    d=[]
    for i in range(len(l)):
        l1=l[i].split(':')
        #print l1
        d.append(l1)
    return dict(d)

def get_302(cookie):
	url='https://passport.douyu.com/lapi/passport/iframe/safeAuth?client_id=1&callback=axiosJsonpCallback1'
	header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
			'Referer':'https://www.douyu.com/directory/myFollow'}
	r=requests.get(url,cookies=cookie,headers=header)
	reditList = r.history
	#print(reditList)
	lastcookie=r.cookies.get_dict()
	#lasturl=reditList[len(reditList)-1].headers["location"]
	#print(lasturl)
	return lastcookie

def authlogin(ltp0):
	cookies=get_cookies(ltp0)
	cookie=get_302(cookies)
	return cookie


if __name__ == '__main__':
	cookie=''
	cookies=get_cookies(cookie)
	#print(cookies)
	get_302(cookies)
