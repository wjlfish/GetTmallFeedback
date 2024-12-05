import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--enable-logging")
chrome_options.add_argument("--v=1")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--enable-automation")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(options=chrome_options)
def parse_comment_data(jsonp_data):
    """解析 JSONP 数据"""
    json_str = jsonp_data[jsonp_data.find("(") + 1: jsonp_data.rfind(")")]
    data = json.loads(json_str)

    # 提取评论内容
    if "data" in data and "rateList" in data["data"]:
        comments = []
        for rate in data["data"]["rateList"]:
            comment = {
                "user": rate.get("reduceUserNick", "匿名用户"),
                "feedback": rate.get("feedback", "无评论"),
                "reply": rate.get("reply", "无回复"),
                "createTime": rate.get("feedbackDate", "未知时间"),
                "appendedFeedback": rate.get("appendedFeed", {}).get("appendedFeedback", "无追评"),
                "appendedCreateTime": rate.get("appendedFeed", {}).get("createTime", "无追评时间"),
            }
            comments.append(comment)
        return comments
    return []


def save_comments_to_csv(comments, csv_filename):
    """将评论保存到 CSV 文件"""
    if not os.path.exists(csv_filename):
        with open(csv_filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["用户名", "评价内容", "商家回复", "留言时间", "追评内容", "追评时间"])

    existing_comments = set()
    with open(csv_filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # 跳过表头
        for row in reader:
            existing_comments.add((row[0], row[1]))  # 用户名和评价内容作为唯一标识

    with open(csv_filename, mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        for comment in comments:
            unique_key = (comment["user"], comment["feedback"])
            if unique_key not in existing_comments:
                writer.writerow([
                    comment["user"],
                    comment["feedback"],
                    comment["reply"],
                    comment["createTime"],
                    comment["appendedFeedback"],
                    comment["appendedCreateTime"],
                ])
                print(f"新增评论: {comment}")
def listen_for_comments(product_url, csv_filename):
    """监听新的评论 API 请求并保存到 CSV"""
    try:
        driver.get("https://login.tmall.com")
        time.sleep(70)
        driver.get(product_url)
        print("等待用户手动滑动页面加载新的评论...")

        captured_requests = set()
        while True:
            # 遍历 performance 日志
            logs = driver.get_log("performance")
            for log_entry in logs:
                message = json.loads(log_entry["message"])["message"]

                if message["method"] == "Network.responseReceived":
                    response_url = message["params"]["response"]["url"]
                    if "mtop.taobao.rate.detaillist.get" in response_url and response_url not in captured_requests:
                        print(f"捕获到新的评论请求: {response_url}")
                        captured_requests.add(response_url)
                        request_id = message["params"]["requestId"]

                        # 通过 DevTools 协议获取响应体
                        response_body = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": request_id}
                        )

                        jsonp_data = response_body["body"]
                        comments = parse_comment_data(jsonp_data)
                        save_comments_to_csv(comments, csv_filename)

                        print("等待新的 API 请求...")
            time.sleep(1)  # 适当延迟，不然可能有点卡
    finally:
        driver.quit()

product_url = "https://detail.tmall.com/item.htm?xxx" # 商品详情页
csv_filename = "comments.csv" # 导出的文件名，默认在同级目录下
listen_for_comments(product_url, csv_filename)