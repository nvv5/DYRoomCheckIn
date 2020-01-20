#! /usr/bin/env python
# coding=utf-8
import requests
import re
import json
import time
import datetime
from douyu_authlogin import authlogin, get_cookies
# proxy={'https':'127.0.0.1:8080'}


class Request(object):
    """docstring for Request"""

    def __init__(self):
        self._session = requests.Session()

    def _requests(self, method, url, decode_level=2, retry=3, timeout=15, **kwargs):
        # proxy={'https':'127.0.0.1:8080'}
        if method in ["get", "post"]:
            for _ in range(retry + 1):
                try:
                    #response = getattr(self._session, method)(url, timeout=timeout, **kwargs,proxies=proxy,verify=False)
                    response = getattr(self._session, method)(
                        url, timeout=timeout, **kwargs)
                    return response.json() if decode_level == 2 else response.content if decode_level == 1 else response
                except Exception as e:
                    print(datetime.datetime.now(), '报错：', e)
                    time.sleep(10)
        return None


class DyCheckin():
    def __init__(self, cookies):
        self.cookie = self.str2cookie(cookies)
        self.req = Request()
        self.lastMinute = 0
        self.lastnum = 0
        self.onlinelist = []
        self.nobolist = []

    #server酱
    def wx_reply(self, desp):
        text = '主人斗鱼签到又挂掉啦~'
        secret_key = ''  # server酱的token
        url = 'https://sc.ftqq.com/%s.send?text=%s&desp=%s' % (
            secret_key, text, desp)
        res = self.req._requests("get", url)
        print(res)

    def str2cookie(self, cookies):
        if re.search('LTP0=', cookies) is not None:
            cookie = authlogin(cookies)
        else:
            cookie = get_cookies(cookies)
        return cookie

    def get_token(self):
        dic = self.cookie
        token = dic['acf_uid']+'_'+dic['acf_biz']+'_' + \
            dic['acf_stk']+'_'+dic['acf_ct']+'_'+dic['acf_ltkid']
        # print(token)
        return token

    def initrun(self):
        print('正在初始化~~~~~~~~~~')
        start = time.time()
        followlist = self.get_followlist(1)
        if len(followlist) == 0:
            print('cookie失效，请重新登录')
        else:
            followlist = self.get_sign(followlist)
            self.onlinelist, self.nobolist = self.check(followlist)
            end = time.time()
            print('用时%.2s秒获取列表' % (end-start))
            print('统计：%s个主播已开播，%s个主播未开播' %
                  (len(self.onlinelist), len(self.nobolist)))
            self.token = self.get_token()
            self.piliangcheckin(self.onlinelist, followlist)

    def start(self):
        self.main()

    def main(self):
        self.initrun()
        while True:
            # 减少回显频率
            now = datetime.datetime.now()
            if now.minute != self.lastMinute and len(self.nobolist) != self.lastnum:
                self.lastMinute = now.minute
                self.lastnum = len(self.nobolist)
                print(now.strftime("%Y-%m-%d %H:%M:%S"),
                      '%s个主播未开播' % len(self.nobolist))
            elif now.hour == 3 and now.minute == 59:
                start = time.time()
                followlist = self.get_followlist(1)
                self.onlinelist, self.nobolist = self.check(followlist)
                end = time.time()
                print('用时%.2s秒获取列表' % (end-start))
                print('统计：%s个主播已开播，%s个主播未开播' %
                      (len(self.onlinelist), len(self.nobolist)))
                while True:
                    now = datetime.datetime.now()
                    print(now)
                    if now.hour == 4 and now.minute == 0:
                        self.piliangcheckin(self.onlinelist, followlist)
                        # print(onlinelist)
                        break
                    time.sleep(0.1)
            # 避免不必要时间的浪费，直接获取全部关注列表
            followlist = self.get_followlist(2)
            if len(followlist) == 0:
                break
            self.piliangcheckin(self.nobolist, followlist)
            time.sleep(5)

    # 获取关注列表(flag为1时，获取符合签到条件的直播间)
    def get_followlist(self, flag):
        url = 'https://www.douyu.com/wgapi/livenc/liveweb/follow/list?sort=0&cid1=0'
        data = self.req._requests("get", url, cookies=self.cookie)
        try:
            if data.get('error') == 0:
                if flag == 1:
                    followlist = []
                    for item in data['data']['list']:
                        if item['show_time'] > 1569859200 and int(self.get_level(item['room_id'])) > 30:
                            followlist.append(item)
                else:
                    followlist = data['data']['list']
                return followlist
            else:
                print('获取直播列表失败：', data)
                if re.search('LTP0=', cookies) is not None:
                    print('检测到cookie为ltp0，重新登录中~~~')
                    self.cookie = authlogin(cookies)
                    followlist = self.get_followlist(flag)
                    self.token = self.get_token()
                    return followlist
                else:
                    followlist = []
                    return followlist
        except Exception as e:
            print(datetime.datetime.now(), e)
            print(data)
            # server酱微信通知
            #desp = e+'++%0D%0A'+data
            # self.wx_reply(desp)

    def get_level(self, roomid):
        url = 'https://www.douyu.com/betard/%s' % roomid
        data = self.req._requests("get", url)
        return data['room']['levelInfo']['level']

    def get_sign(self, followlist):
        print('符合签到条件的总共有%s个房间' % len(followlist))
        print('开始获取今天的签到情况~~~~~~')
        for item in followlist[::-1]:
            roomid = item['room_id']
            signstatus = self.get_signstatus(roomid)
            # print(roomid,signstatus)
            if signstatus == 1:
                print('%s今天已签到,签到排名为%s' %
                      (item['nickname'], self.get_signrank(roomid)))
                followlist.remove(item)
        print('还有%s个房间未签到' % len(followlist))
        return followlist

    def get_signstatus(self, roomid):
        url = 'https://www.douyu.com/japi/roomuserlevel/apinc/levelInfo?rid=%s' % roomid
        data = self.req._requests("get", url, cookies=self.cookie)
        signstatus = data['data']['signInInfo']['done']
        return signstatus

    def get_signrank(self, roomid):
        url = 'https://www.douyu.com/japi/roomuserlevel/apinc/getSignInRankInfoList?rid=%s' % roomid
        data = self.req._requests("get", url, cookies=self.cookie)
        rank = '100+'
        for item in data['data']:
            if item['uid'] == int(self.cookie['acf_uid']):
                rank = item['rank']
                # print(rank)
        return rank

    # 检测关注列表中是否开播
    def check(self, followlist):
        list1 = []
        list2 = []
        for item in followlist:
            if item['show_status'] == 1:
                # print('%s已开播'%item['room_id'])
                list1.append(item['room_id'])
            else:
                list2.append(item['room_id'])
        return list1, list2

    def piliangcheckin(self, list, followlist):
        for roomid in list[::-1]:
            nickname, status = self.get_roomstatus(followlist, roomid)
            if status == 1:
                print('%s已开播' % nickname)
                self.checkin(roomid)
                list.remove(roomid)

    # 获取直播状态
    def get_roomstatus(self, followlist, roomid):
        for item in followlist:
            if item['room_id'] == int(roomid):
                return item['nickname'], item['show_status']

    # 签到
    def checkin(self, roomid):
        url = 'https://apiv2.douyucdn.cn/japi/roomuserlevel/apinc/checkIn'
        data = {'rid': roomid}
        header = {'User-Agent': 'Mozilla/5.0 (Linux; Android 9; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile Safari/537.36, Douyu_Android',
                  'token': self.token}
        html = self.req._requests("post", url, data=data, headers=header)
        print(html)


if __name__ == '__main__':
    # 有LTP0的cookie可用，cookie时限理论上是半年
    # 没有LTP0的直接复制登录后cookie也行，确保存在acf_uid、acf_biz、acf_stk、acf_ct、acf_ltkid这几个，时效性好像是7天
    cookies = ''
    qiandao = DyCheckin(cookies)
    qiandao.start()
