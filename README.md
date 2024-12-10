# 天猫商品评论获取

> 本项目用于获取天猫商城的某个商品的评论区信息，限于时间，本脚本仅为一个半自动化脚本。
> 
> 原则上淘宝商品评论亦可通过此脚本获取

## 使用
本脚本通过模拟浏览器访问，从浏览器内获取网络信息来得到评论，调用了天猫api接口

1. 要使用本脚本，首先安装selenium，并配置对应的webdriver
   
`pip install selenium`

3. 配置main.py里的商品链接地址和输出文件名

4. 依次完成登录和跳转，手动点击评论区按钮，弹出评论区，脚本会自动开始寻找对应api
5. 在评论区向下滑动，脚本会自动检测获取新评论的位置，并记录新的评论
6. 收集完毕后，直接结束脚本的运行，在你设定的位置打开csv文件即可

## 联系

如有任何问题，可通过issue与我取得联系。
