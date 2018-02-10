# m.weibo.cn

## 流程

```sh
https://m.weibo.cn/api/container/getIndex
- web, 登陆获取 1005056069778559 = 100505 + 6069778559
- 传入 'containerid': '1005056069778559' 获取 `2302836069778559` 和 `1076036069778559`
- 传入 `1076036069778559` 获取所有微博
- 传入 `2302836069778559` 获取个人配置
- cards -show_type == 2, 基本资料, 进入个人详细资料
- containerid = 2302836069778559_-_INFO 获取个人信息
- 解析上步的 itemid: 2306186069778559_-_likes, 获取个人点赞内容
	请求url: https://m.weibo.cn/api/container/getItem?itemid=2306186069778559_-_likes
	会返回 获取个人点赞综合所需的containerid	2308696069778559_-_mix
- 使用 containerid	2308696069778559_-_mix 就可以获取所有信息了
```

## web登陆

## mobile登陆

- 目标
  - 获取 `cookie`
  - 获取 `uid` 


- url: `post`

  `https://passport.weibo.cn/sso/login`

- 参数

  ```python
  username = ''
  password = ''

  form = {
      'username': username,
      'password': password,
      'savestate': '1',
      'ec': '0',
      'entry': 'mweibo',
      'wentry': '',
      'loginfrom': '',
      'client_id': '',
      'code': '',
      'qq': '',
      'mainpageflag': '1',
      'hff': '',
      'hfp': '',
  }
  ```

- 响应

  ```python
  {
  	'crossdomainlist': {
  		'weibo.com': '...',
  		'sina.com.cn': '...',
  		'weibo.cn': '...'
  	},
  	'loginresulturl': '',
  	'uid': '6069778559'
  }
  ```

## 个人配置

- 目标
  - 获取后续操作所需要的 `st值`: 类似于`token`作用


- url: `GET`

  `https://m.weibo.cn/api/config`

- 响应

  ```python
  {
  	"data": {
  		"login": true,
  		"st": "----", # 主要使用值, 用于之后操作时使用, 每 5min 更新一次
  		"uid": "6069778559"
  	},
  	"ok": 1
  }
  ```

- 说明

  主要使用的是返回的`st`值, 作为以后查询及操作的`token`

## 微博入口

- 目标
  - 获取微博`containerid`
  - 获取个人信息`containerid`


- [url](https://m.weibo.cn/p/1005056069778559) 

  `https://m.weibo.cn/api/container/getIndex`

- params

  ```python
  # method 1
  {
  	'containerid': '1005056069778559' # web登陆后获取的 pid/domain + uid
  }

  # method 2
  params = {
      'type': 'uid',
      'value': '6069778559',	# uid 为登陆后获取的 uid
  }
  ```

- response

  ```python
  {
  	"ok": 1,
  	"data": {
  		"userInfo": {
  			"id": 6069778559,
  			"statuses_count": 9,
  			"followers_count": 83,
  			"follow_count": 57,
  		},
  		...
  		"tabsInfo": {
  			"selectedTab": 1,
  			"tabs": [{
  				"title": "主页",
  				"tab_type": "profile",
  				"containerid": "2302836069778559"	# 
  			}, {
  				"title": "微博",
  				"tab_type": "weibo",
  				"containerid": "1076036069778559",	# 微博内容的入口
  			}]
  		},
  		...
  	}
  }
  ```

- 说明

  `userInfo.id`: 为账号 uid

  `tabsInfo.tabs.containerid`: 为账号接下来信息的所有功能的入口`containerid`

## 微博内容

- 个人微博内容展示页


- url: `GET`

  `https://m.weibo.cn/api/container/getIndex`

- 参数

  ```python
  {
    'containerid': '1076036069778559',
    'page': 1
  }
  ```

- 响应

  ```python
  {
  	"ok": 1,
  	"data": {
  		"cardlistInfo": {
  			"containerid": "1076036069778559",
  			"v_p": 42,
  			"show_style": 1,
  			"total": 9,
  			"page": None
  		},
  		"cards": [...],	# 实际微博内容
  		"showAppTips": 0,
  		"scheme": ""
  	}
  }
  ```

- 说明

  `data.cardlistInfo.page`: 当前页数

  `data.cardlistInfo.total`: 总微博数

## 微博主页

- 个人基础信息页


- url: `GET`

  `https://m.weibo.cn/api/container/getIndex`

- 参数

  ```python
  {
    'containerid': '2302836069778559',	#
  }
  ```

- 响应

  ```python
  {
  	"ok": 1,
  	"data": {
  		"cardlistInfo": {
  			"v_p": "42",
  			"cardlist_title": "",
  			"desc": "",
  			"show_style": 1,
  			"can_shared": 0,
  			"containerid": "2302836069778559",
  		},
  		"cards": [...],
  		"showAppTips": 0,
  		"scheme": ""
  	}
  }
  ```

## 更多资料

- 个人更多信息

- url: `GET`

  `https://m.weibo.cn/api/container/getIndex`

- 参数

  ```python
  {
    'containerid': '2302836069778559_-_INFO',
  }
  ```

  ​