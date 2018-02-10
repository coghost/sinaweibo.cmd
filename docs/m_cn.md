## urls

```sh
# post login
https://passport.weibo.cn/sso/login

# msg
https://m.weibo.cn/msg/index?format=cards

# unread
https://m.weibo.cn/unread

# @me
https://m.weibo.cn/msg/atme?subtype=allWB

# 关注: followers
https://m.weibo.cn/api/container/getSecond?containerid=1005056069778559_-_FOLLOWERS
containerid: 1005056069778559_-_FOLLOWERS
page: 2

# 粉丝: fans
https://m.weibo.cn/api/container/getSecond?containerid=1005056069778559_-_FANS
containerid: 1005056069778559_-_FANS
page: 2

# 照片: 
https://m.weibo.cn/api/container/getIndex?containerid=107803_6069778559

# 收藏:
https://m.weibo.cn/api/container/getIndex?containerid=2302596069778559

# 赞:
https://m.weibo.cn/api/container/getIndex?containerid=2302576069778559


```



## ContainerId

```sh
赞: 2308696069778559
收藏: 2308696069778559
```



## follow

```sh
# 1. create -> post
https://m.weibo.cn/api/friendships/create
uid: user_uid, st: token_st

# 2. groups -> get 设置分组, 可跳过
https://m.weibo.cn/friendships/groups?uid=2714280233
uid: user_uid

# 3. add to groups -> post
https://m.weibo.cn/friendships/groupsMemberAdd
gid, uid, st

# 4. destroy
https://m.weibo.cn/api/friendships/destory
uid, st

```







## TODO

- [x] 关注bug, 切换账号关注未改变

