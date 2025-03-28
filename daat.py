# 关联文件：
# data_renew_method_1.xlsx：东方财富渠道数据（中国大陆）
# data_renew_method_2.xlsx：百度股市通渠道数据（）
import requests
import json
import csv
from datetime import datetime
import re
import pandas as pd
import time


print(1)
start_time = time.time()

class FeishuTalk:

    # 机器人webhook
    hdpbot_url = '在此输入您的飞书机器人webhook url～'

    # 发送文本消息
    def sendTextmessage(self, content):
        url = self.hdpbot_url
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        payload_message = {
            "msg_type": "text",
            "content": {
            	# @ 单个用户 <at user_id="ou_xxx">名字</at>
                "text": content # + "<at user_id=\"bf888888\">test</at>" #+ "<at user_id=\"bf888888\">test</at>"
            }
        }
        response = requests.post(url=url, data=json.dumps(payload_message), headers=headers)
        return response.json

def fetch_and_export_stock_data1(url, stock_names):
    try:

        # 发送HTTP GET请求
        headers = { # 输入您自己的相关信息～
            'Cookie': '',
            'User-Agent': ''
        }
        response = requests.get(url, headers = headers)
        response.raise_for_status()  # 检查HTTP请求是否成功

        # 打印响应内容
        # print("Response Text:", response.text[:500])  # 打印前500个字符以便检查内容

        # 使用正则表达式提取JSON部分
        match = re.search(r'\((.*?)\)', response.text)
        if not match:
            print("无法找到有效的JSON内容")
            return

        json_str = match.group(1)

        # 解析JSON响应
        data = json.loads(json_str)

        # 提取股票信息
        klines = data['data']['klines']

        # 定义要提取的信息字段
        fields = ["日期", "开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额", "振幅（%）", "涨跌幅（%）", "涨跌额",
                  "换手率（%）"]

        # 解析并整理每条K线数据
        stock_data = []
        for kline in klines:
            kline_data = kline.split(',')
            # 添加百分号
            kline_data[7] = kline_data[7] + '%'  # 振幅
            kline_data[8] = kline_data[8] + '%'  # 涨跌幅
            kline_data[10] = kline_data[10] + '%'  # 换手率
            stock_data.append(kline_data)

        # 按日期倒序排序
        stock_data.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)

        # 准备CSV文件名
        csv_file = f"market_data/{stock_names}.csv"

        # 打开CSV文件进行写入
        with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)

            # 写入表头
            writer.writerow(fields)

            # 写入排序后的每条K线数据
            for row in stock_data:
                writer.writerow(row)

        print(f"股票数据已导出为 {csv_file}")

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        raise  # 向外抛出异常
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        raise  # 向外抛出异常
    except Exception as e:
        print(f"其他错误: {e}")
        raise  # 向外抛出异常


def fetch_and_export_stock_data2(url, stock_names):
    try:
        headers =         headers = { # 输入您自己的相关信息～
            'Cookie': '',
            'User-Agent': ''
        }
        # 发送请求并获取JSON响应
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()

        market_data = data['Result']['newMarketData']['marketData']
        headers = data['Result']['newMarketData']['headers']
        keys = data['Result']['newMarketData']['keys']

        # 拆分每一行数据
        rows = market_data.split(';')

        # 存储所有股票信息的列表
        stock_info_s = []

        # 解析每行数据
        for row in rows:
            values = row.split(',')
            stock_info = {}
            for key in range(len(keys)):
                stock_info[keys[key]] = values[key] if values[key] != '--' else None
            stock_info_s.append(stock_info)

        # 按时间戳倒序排序
        stock_info_s.sort(key=lambda x: int(x['timestamp']), reverse=True)
        # 先获取涨跌幅的数值
        for info in stock_info_s:
            if 'ratio' in info and info['ratio'] is not None:
                info['ratio'] = info['ratio'] + '%'

        # 将格式化后的字符串存回到 stock_info_s 中
        csv_file = f"market_data/{stock_names}.csv"
        # 打开CSV文件进行写入
        with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)

            # 写入表头
            writer.writerow(headers)

            # 写入排序后的每条K线数据
            for row in stock_info_s:
                writer.writerow([row[key] for key in keys])

        print(f"股票数据已导出为 {csv_file}")

    except requests.exceptions.RequestException as e:
        print(f"请求数据时出错：{e}")
    except Exception as e:
        print(f"导出数据时出错：{e}")
        raise  # 向外抛出异常

print(1)

FeishuTalk().sendTextmessage(
    f"开始更新数据啦 <at user_id=\"94dae5e3\">test</at>")

renew_list1 = pd.read_excel("data_renew_method_1.xlsx", dtype={"code": str})
for i in range(len(renew_list1)):
    print(i)
    stock_name = f'{renew_list1["name"].iloc[i]}-{renew_list1["code"].iloc[i]}'
    fetch_and_export_stock_data1(renew_list1["url"][i], stock_name)

renew_list2 = pd.read_excel("data_renew_method_2.xlsx", dtype={"code": str})
for j in range(len(renew_list2)):
    stock_name = f'{renew_list2["name"].iloc[j]}-{renew_list2["code"].iloc[j]}'
    fetch_and_export_stock_data2(renew_list2["url"][j], stock_name)

print("搞掂！")
# 记录结束时间并计算运行时长
end_time = time.time()
duration = round(end_time - start_time, 2)
# 发送完成消息
FeishuTalk().sendTextmessage(
    f"今日市场数据已更新完毕！本次更新耗时 {int(duration//60)} 分 {round(duration%60, 2)} 秒" + " <at user_id=\"94dae5e3\">test</at>")
# raise Exception("测试错误")
