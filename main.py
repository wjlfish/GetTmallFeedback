import json  # 导入 JSON 模块，用于解析 JSON 数据
import csv  # 导入 CSV 模块，用于处理 CSV 文件
from selenium import webdriver  # 从 selenium 导入 webdriver 模块，用于驱动浏览器
from selenium.webdriver.chrome.options import Options  # 从 selenium.webdriver.chrome.options 导入 Options 类，用于配置 Chrome 浏览器选项
import time  # 导入 time 模块，用于处理时间相关操作
import os  # 导入 os 模块，用于处理操作系统相关操作

chrome_options = Options()  # 创建 Chrome 浏览器选项对象
chrome_options.add_argument("--no-sandbox")  # 添加无沙盒模式参数
chrome_options.add_argument("--enable-logging")  # 启用日志记录
chrome_options.add_argument("--v=1")  # 设置日志记录级别
chrome_options.add_argument("--log-level=3")  # 设置日志记录级别
chrome_options.add_argument("--enable-automation")  # 启用自动化控制
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 排除日志记录开关
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # 设置性能日志记录选项
driver = webdriver.Chrome(options=chrome_options)  # 创建 Chrome 浏览器驱动对象，并应用配置选项

def parse_comment_data(jsonp_data):  # 定义解析 JSONP 数据的函数
    """解析 JSONP 数据"""
    json_str = jsonp_data[jsonp_data.find("(") + 1: jsonp_data.rfind(")")]  # 提取 JSON 字符串
    data = json.loads(json_str)  # 解析 JSON 字符串为 Python 字典

    # 提取评论内容
    if "data" in data and "rateList" in data["data"]:  # 检查数据中是否包含评论列表
        comments = []  # 初始化评论列表
        for rate in data["data"]["rateList"]:  # 遍历评论列表
            comment = {  # 提取每条评论的相关信息
                "user": rate.get("reduceUserNick", "匿名用户"),  # 用户名
                "feedback": rate.get("feedback", "无评论"),  # 评论内容
                "reply": rate.get("reply", "无回复"),  # 商家回复
                "createTime": rate.get("feedbackDate", "未知时间"),  # 评论时间
                "appendedFeedback": rate.get("appendedFeed", {}).get("appendedFeedback", "无追评"),  # 追评内容
                "appendedCreateTime": rate.get("appendedFeed", {}).get("createTime", "无追评时间"),  # 追评时间
            }
            comments.append(comment)  # 将评论添加到评论列表中
        return comments  # 返回评论列表
    return []  # 如果没有评论，返回空列表

def save_comments_to_csv(comments, csv_filename):  # 定义将评论保存到 CSV 文件的函数
    """将评论保存到 CSV 文件"""
    if not os.path.exists(csv_filename):  # 如果 CSV 文件不存在
        with open(csv_filename, mode="w", encoding="utf-8", newline="") as file:  # 创建并打开 CSV 文件
            writer = csv.writer(file)  # 创建 CSV 写入对象
            writer.writerow(["用户名", "评价内容", "商家回复", "留言时间", "追评内容", "追评时间"])  # 写入表头

    existing_comments = set()  # 初始化已存在评论的集合
    with open(csv_filename, mode="r", encoding="utf-8") as file:  # 打开 CSV 文件
        reader = csv.reader(file)  # 创建 CSV 读取对象
        next(reader)  # 跳过表头
        for row in reader:  # 遍历 CSV 文件中的每一行
            existing_comments.add((row[0], row[1]))  # 将用户名和评价内容作为唯一标识添加到集合中

    with open(csv_filename, mode="a", encoding="utf-8", newline="") as file:  # 以追加模式打开 CSV 文件
        writer = csv.writer(file)  # 创建 CSV 写入对象
        for comment in comments:  # 遍历评论列表
            unique_key = (comment["user"], comment["feedback"])  # 生成唯一标识
            if unique_key not in existing_comments:  # 如果评论不在已存在评论集合中
                writer.writerow([  # 写入评论到 CSV 文件
                    comment["user"],
                    comment["feedback"],
                    comment["reply"],
                    comment["createTime"],
                    comment["appendedFeedback"],
                    comment["appendedCreateTime"],
                ])
                print(f"新增评论: {comment}")  # 打印新增评论信息

def listen_for_comments(product_url, csv_filename):  # 定义监听新的评论 API 请求并保存到 CSV 的函数
    """监听新的评论 API 请求并保存到 CSV"""
    try:
        driver.get("https://login.tmall.com")  # 打开天猫登录页面
        time.sleep(70)  # 等待用户登录
        driver.get(product_url)  # 打开商品详情页
        print("等待用户手动滑动页面加载新的评论...")  # 提示用户手动滑动页面加载新的评论

        captured_requests = set()  # 初始化已捕获请求的集合
        while True:  # 无限循环监听新的评论请求
            logs = driver.get_log("performance")  # 获取性能日志
            for log_entry in logs:  # 遍历日志条目
                message = json.loads(log_entry["message"])["message"]  # 解析日志消息

                if message["method"] == "Network.responseReceived":  # 如果是网络响应接收事件
                    response_url = message["params"]["response"]["url"]  # 获取响应 URL
                    if "mtop.taobao.rate.detaillist.get" in response_url and response_url not in captured_requests:  # 如果是评论请求且未捕获过
                        print(f"捕获到新的评论请求: {response_url}")  # 打印捕获到的新评论请求
                        captured_requests.add(response_url)  # 将请求 URL 添加到已捕获请求集合中
                        request_id = message["params"]["requestId"]  # 获取请求 ID

                        response_body = driver.execute_cdp_cmd(  # 通过 DevTools 协议获取响应体
                            "Network.getResponseBody", {"requestId": request_id}
                        )

                        jsonp_data = response_body["body"]  # 获取 JSONP 数据
                        comments = parse_comment_data(jsonp_data)  # 解析评论数据
                        save_comments_to_csv(comments, csv_filename)  # 将评论保存到 CSV 文件

                        print("等待新的 API 请求...")  # 提示等待新的 API 请求
            time.sleep(1)  # 适当延迟，不然可能有点卡
    finally:
        driver.quit()  # 关闭浏览器驱动

product_url = "https://detail.tmall.com/item.htm?xxx"  # 商品详情页 URL
csv_filename = "comments.csv"  # 导出的文件名，默认在同级目录下
listen_for_comments(product_url, csv_filename)  # 调用函数监听评论并保存到 CSV 文件