# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime, timezone, timedelta
import base64
import pandas as pd
import requests as rq
import re
import os
import csv
from notify_util import FeishuBot

# 获取当前时间
current_time = datetime.now().astimezone(timezone(timedelta(hours=8)))

# 格式化为 "YYYYMMDDHHMMSS"
formatted_time = current_time.strftime("%Y%m%d%H%M%S")

testt = str(f"""<span class="red" style="color:#ff0000;">下跌了0.9%</span>""")


# 封装读取日期并生成邮件主题的函数
def generate_subject():
    # GitHub Actions 是 UTC 时间，这里手动加8小时变成北京时间

    # 先获取 UTC 时间（有时区意识的）
    utc_now = datetime.now(timezone.utc)
    # 转为北京时间（UTC+8）
    bj_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    current_date = bj_now.strftime("%Y-%m-%d")
    current_hour = bj_now.hour
    current_minute = bj_now.minute

    # 简单逻辑判断，如果早于中午 12 点，就认为是“开盘速报”，否则是“收盘速报”
    if current_hour < 12:
        report_type = "开盘速报"
    else:
        report_type = "收盘速报"

    return f'{current_date} {report_type}'


# 对昵称进行 base64 编码
def encode_nickname(nickname, charset='utf-8'):
    nickname_bytes = nickname.encode(charset)
    encoded_nickname = base64.b64encode(nickname_bytes).decode(charset)
    return f'=?{charset}?B?{encoded_nickname}?='


# 创建邮件内容
def create_email_content(mail_msg, subject, sender_nickname, sender_email, receiver_nickname, receiver_email):
    message = MIMEText(mail_msg, 'html', 'utf-8')

    encoded_sender_nickname = encode_nickname(sender_nickname)
    message['From'] = formataddr((encoded_sender_nickname, sender_email))

    encoded_receiver_nickname = encode_nickname(receiver_nickname)
    message['To'] = formataddr((encoded_receiver_nickname, receiver_email))

    message['Subject'] = Header(subject, 'utf-8')

    return message


# 发送邮件
def send_email(sender_email, sender_password, receivers, message):
    smtpobj = smtplib.SMTP_SSL("smtp.feishu.cn", 465)
    smtpobj.login(sender_email, sender_password)
    smtpobj.sendmail(sender_email, receivers, message.as_string())
    smtpobj.quit()
    print('邮件发送成功')


# 交易时间获取 Trade Time Get
def ttg(name):
    headers = {
        # 'Cookie': 'SE_LAUNCH=5%3A28688665; BA_HECTOR=a1242l0520ah840k80aga5a11nes201j9igf91v; BDORZ=AE84CDB3A529C0F8A2B9DCDD1D18B695; H_WISE_SIDS=110085_287279_299591_603326_298697_604101_301026_607111_607725_307086_307654_277936_610004_609973_610265_609499_610845_610981_604787_611257_611020_611207_611317_611313_611307_611320_611770_611855_611877_611874_609580_610630_611720_610812_612052_612160_612199_612271_610605_612314_612274_612312_107318_609087_611512_295151_612496_612043_612558_612557_612581_612512_612562_611447_611448_612648_282466_611384_611388_612947_611385_612957_612870_613019_613053_613123_613176_613319_613336; ZFY=oZibowksA2xwHV8SdgOXrcK0V3P:B:AVd34Vy2Q0A:BqY0:C; rsv_i=80aeIeuFsz44uKifqBcR3UVZws9/8c1Xvu9JQUsZUIbZsFjhesb+RAjCyc48rLBsKAsGd4AJyR2EB/vW+eJfUXBBmPAaG/Q; BAIDUID=5B9890EA595509E38E7ED9BF4D8FFB98:FG=1',
        'Cookie': 'BAIDUID=70A14469CBE38E4A5624A7612EC1289D:FG=1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'}
    judge_xls = pd.read_excel("main_info_judge.xlsx")
    index = judge_xls[judge_xls['指标名称'] == name].index[0]
    ttg_url = judge_xls.loc[index, '时区信息']
    # print(ttg_url)
    a = rq.get(ttg_url, headers=headers)
    # print(a)
    b = a.text
    c = "".join(b)
    d = c.split('"update":{')
    # print("---------------------------")
    # print(d)
    e = d[1].split('},')
    # 定义一个正则表达式，匹配每个键值对
    pattern = r'"([^"]+)":"([^"]+)"'

    # 使用正则表达式进行匹配
    matches = re.findall(pattern, e[0])

    # 将匹配结果存放到一个字典中
    result = {}
    for key, value in matches:
        # 使用 unicode_escape 解码器处理中文字符
        result[key] = bytes(value, 'utf-8').decode('unicode_escape')

    return f"""{result["stockStatus"]} {result["text"]} {result["timezone"]}"""


# 涨跌判断 Info + Up Down Judgement
def m(name):
    judge_xls = pd.read_excel("main_info_judge.xlsx")
    index = judge_xls[judge_xls['指标名称'] == name].index[0]
    code = judge_xls.loc[index, '对应代码']
    find_the_file = pd.read_csv(f"market_data/{name}-{code}.csv")

    if judge_xls.loc[index, '爬取方式'] == 1:
        today_info_close = find_the_file.loc[0, "收盘价"]
        today_info_rate = find_the_file.loc[0, "涨跌幅（%）"]
        if float(today_info_rate.rstrip('%')) < 0:
            today_info_rate_output = f"""<span class="green">{today_info_rate}</span>"""
        elif float(today_info_rate.rstrip('%')) > 0:
            today_info_rate_output = f"""<span class="red"  >+{today_info_rate}</span>"""
        else:
            today_info_rate_output = "持平"
    elif judge_xls.loc[index, '爬取方式'] == 2:
        today_info_close = find_the_file.loc[0, "收盘"]
        today_info_rate = find_the_file.loc[0, "涨跌幅"]
        if float(today_info_rate.rstrip('%')) < 0:
            today_info_rate_output = f"""<span class="green">{today_info_rate}</span>"""
        elif float(today_info_rate.rstrip('%')) > 0:
            today_info_rate_output = f"""<span class="red"  >{today_info_rate}</span>"""
        else:
            today_info_rate_output = "持平"

    # 格式化输出
    name_op = "{: <12}".format(name)
    today_info_close_op = "{: ^40}".format(today_info_close)
    today_info_rate_output_op = "{: >10}".format(today_info_rate_output)
    output = f"{name_op} {today_info_close_op} {today_info_rate_output_op}"
    # print(output)
    return output

def log_push_event_csv(subject, receivers, error_message=None):
    # 北京时间
    # 先获取 UTC 时间（有时区意识的）
    utc_now = datetime.now(timezone.utc)
    # 转为北京时间（UTC+8）
    bj_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    timestamp = bj_now.strftime("%Y-%m-%d %H:%M:%S")

    log_path = "push_log.csv"
    new_rows = []

    for receiver in receivers:
        new_rows.append([timestamp, receiver, subject, error_message or "None"])

    # 如果文件不存在，先写入表头
    file_exists = os.path.exists(log_path)

    # 读取旧数据（为了把新记录放在前面）
    existing_rows = []
    if file_exists:
        with open(log_path, "r", encoding="utf-8", newline='') as csvfile:
            reader = list(csv.reader(csvfile))
            if reader:
                existing_rows = reader[1:]  # 跳过表头

    # 写入新日志（新记录在上面）
    with open(log_path, "w", encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["时间（北京时间）", "接收人", "标题", "错误状态"])
        writer.writerows(new_rows + existing_rows)

def load_receivers_from_file(filepath="email_list.txt"):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换换行为逗号，再按逗号分割
    raw_emails = content.replace('\n', ',').split(',')

    # 去除空格、空项
    cleaned_emails = [email.strip() for email in raw_emails if email.strip()]
    return cleaned_emails



if __name__ == "__main__":
    # 用户输入
    sender_nickname = '曲径推送'
    # sender_email = '1624070280@qq.com'
    sender_email = 'qjgr_gz@huangdapao.com'
    # sender_password = 'xafmaduaahdqejih'
    sender_password = 'eIey9NsyqT34otTH'

    receiver_nickname = 'Clients_Mainland'
    receiver_email = '1624070280@qq.com'

    # 邮件内容
    styles = """    
    <style>
        :root {
            color-scheme: light only;
        }

        body {
            background-color: #000001 !important;
            color: #fefefe !important;
        }

        .email-body {
            font-size: 12px;
            line-height: 1.5;
            color: #fefefe !important;
            background-color: #000001 !important;
        }

        .red {
            color: #ff1a1a !important;
        }

        .green {
            color: #00b300 !important;
        }

        .main-table,
        .card-content,
        .title,
        .header,
        .content-section {
            background-color: #000001 !important;
            color: #fefefe !important;
        }
    </style>
    """

    mail_msg = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Market Update</title>
        {styles}
    </head>
    <body style="background-color:#000001 !important; color:#fefefe !important;">
        <center>
            <table class="main-table" style="width:690px;border-spacing:0;border-collapse:collapse;">
                <tbody>
                    <!-- Header Section -->
                    <tr>
                        <td style="text-align:center; background:#000001 !important;">
                            <div style="display:inline-block; width:100%;">
                                <img style="max-width:100%; width:100%; height:auto;" src="https://huangdapao.com/images/header_of_email.png" alt="Header Image">
                            </div>
                        </td>
                    </tr>

                    <!-- Content Section -->
                    <tr>
                        <td colspan="2" style="background:#000001 !important;">
                            <div class="content-outer" style="background:#000001 !important; border-radius:4px; max-width:600px; margin:0 auto; border:2px solid #333333;">
                                <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%; border-radius:4px;">
                                    <tbody>
                                        <tr><td height="30" style="height:30px;"></td></tr>
                                        <tr>
                                            <td style="text-align:center;">
                                                <div class="content-section" style="max-width:600px; margin:0 auto;">
                                                    <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
                                                        <tbody>
                                                            <tr>
                                                                <td style="padding-left:40px; padding-right:40px; text-align:center;">
                                                                    <div style="max-width:520px; margin:0 auto;">
                                                                        <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td style="padding-top:30px; text-align:center;">
                                                                                        <div style="text-align:left; width:100%;">
                                                                                            <!-- Incident Header -->
                                                                                            <div class="title" style="position:relative;">
                                                                                                <span class="title-inner" style="color:#f48120; font-weight:bold; line-height:21px; font-size:14px;">
                                                                                                    全球市场 · Global Market
                                                                                                </span>
                                                                                            </div>
                                                                                            <div class="header" style="margin:10px 0px; padding:0;">
                                                                                                <a style="text-decoration:none; color:#ffffff; font-family:Arial; font-weight:bold; line-height:26px; font-size:22px;">
                                                                                                    重要指数与数据 · Important Indexes & Data
                                                                                                </a>
                                                                                            </div>
                                                                                            <div class="card-content" style="color:#ffffff; font-family:Arial; font-weight:normal; line-height:21px; font-size:14px; margin:10px 0px; padding:0;">
                                                                                                <span style="font-weight:bold;font-size:16px">中国市场</span><br>
                                                                                                {m("上证指数")}<br>
                                                                                                {m("深证成指")}<br>
                                                                                                {m("沪深300")}<br>
                                                                                                {m("北证50")}<br>
                                                                                                {m("创业板指")}<br>
                                                                                                {m("科创50")}<br>
                                                                                                {m("B股指数")}<br>
                                                                                                {m("国债指数")}<br>
                                                                                                {m("基金指数")}<br>
                                                                                                {m("恒生指数")}<br>
                                                                                                {m("香港100")}<br>
                                                                                                {m("红筹指数")}<br>

                                                                                                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                                                                                    <tbody>
                                                                                                        <tr><td height="35" style="height:35px;"></td></tr>
                                                                                                    </tbody>
                                                                                                </table>

                                                                                                <span style="font-weight:bold;font-size:16px">美洲市场</span><br>
                                                                                                {m("纳斯达克")}<br>
                                                                                                {m("道琼斯")}<br>
                                                                                                {m("标普500")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("纳斯达克")}
                                                                                                </h3>
                                                                                                {m("富时加拿大")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("富时加拿大")}
                                                                                                </h3>
                                                                                                {m("富时巴西")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("富时巴西")}
                                                                                                </h3>
                                                                                                {m("富时墨西哥")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("富时墨西哥")}
                                                                                                </h3>

                                                                                                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                                                                                    <tbody>
                                                                                                        <tr><td height="35" style="height:35px;"></td></tr>
                                                                                                    </tbody>
                                                                                                </table>

                                                                                                <span style="font-weight:bold;font-size:16px">欧洲市场</span><br>
                                                                                                英国{m("富时AIM全股")}<br>
                                                                                                {m("英国富时100")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("英国富时100")}
                                                                                                </h3>
                                                                                                {m("法国CAC40")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("法国CAC40")}
                                                                                                </h3>
                                                                                                {m("德国DAX")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("德国DAX")}
                                                                                                </h3>
                                                                                                {m("瑞士SMI")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("瑞士SMI")}
                                                                                                </h3>
                                                                                                {m("意大利MIB")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("意大利MIB")}
                                                                                                </h3>
                                                                                                {m("荷兰AEX")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("荷兰AEX")}
                                                                                                </h3>

                                                                                                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                                                                                    <tbody>
                                                                                                        <tr><td height="35" style="height:35px;"></td></tr>
                                                                                                    </tbody>
                                                                                                </table>

                                                                                                <span style="font-weight:bold;font-size:16px">亚洲市场</span><br>
                                                                                                {m("日经225")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("日经225")}
                                                                                                </h3>
                                                                                                {m("印度孟买SENSEX")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("印度孟买SENSEX")}
                                                                                                </h3>
                                                                                                {m("韩国KOSPI")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("韩国KOSPI")}
                                                                                                </h3>
                                                                                                {m("泰国SET")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("泰国SET")}
                                                                                                </h3>
                                                                                                {m("富时马来西亚KLCI")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("富时马来西亚KLCI")}
                                                                                                </h3>

                                                                                                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                                                                                    <tbody>
                                                                                                        <tr><td height="35" style="height:35px;"></td></tr>
                                                                                                    </tbody>
                                                                                                </table>

                                                                                                <span style="font-weight:bold;font-size:16px">大洋洲市场</span><br>
                                                                                                {m("澳大利亚普通股")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("澳大利亚普通股")}
                                                                                                </h3>
                                                                                                {m("富时新西兰")}<br>
                                                                                                <h3 style="margin:0; font-weight:normal; font-size:14px; line-height:1.5; color:#AAAAAA;">
                                                                                                    {ttg("富时新西兰")}
                                                                                                </h3>
                                                                                            </div>
                                                                                            <div style="color:#757575; font-family:Arial; font-weight:normal; line-height:12px; font-size:10px; margin:10px 0 0; padding:0; text-align:right;">
                                                                                                时间戳：{formatted_time}
                                                                                            </div>
                                                                                            <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                                                                                <tbody>
                                                                                                    <tr><td height="30" style="height:30px;"></td></tr>
                                                                                                </tbody>
                                                                                            </table>
                                                                                        </div>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer Section -->
                    <tr>
                        <td class="mail-footer" colspan="2" style="padding:25px; font-family:Arial; font-weight:normal; line-height:21px; font-size:14px; background-color:#000001 !important; color:#fefefe !important;">
                            <div style="display:inline-block; width:100%;">
                                <img style="margin-bottom:10px; max-width:100%; width:100%; height:auto;" src="https://huangdapao.com/images/end_of_email_logo.png" alt="Footer Image">
                            </div>
                            <center>
                                <span style="color:#888888;">您会收到这封邮件是因为您订阅了曲径共融的邮件推送。</span><br>
                                <span style="color:#888888;">You are receiving this email because you have subscribed to Curveway Confluence email notifications.</span><br><br>
                                <span style="color:#888888;">本邮件由曲径共融（广州）大数据投资中心数据部与信息部共同制作推送。</span><br>
                                <span style="color:#888888;">This email is jointly generated and sent by the Data Dep. and the IT Dep. of Curveway Confluence (Guangzhou) Big Data Investment Center.</span><br>
                            </center>
                        </td>
                    </tr>
                </tbody>
            </table>
        </center>
    </body>
    </html>
    """

    message = MIMEText(mail_msg, 'html', 'utf-8')

    subject = generate_subject()

    message = create_email_content(mail_msg, subject, sender_nickname, sender_email, receiver_nickname, receiver_email)

    receivers = load_receivers_from_file("email_list.txt")

    bot = FeishuBot('在此输入您的飞书机器人webhook url～')

    try:
        send_email(sender_email, sender_password, receivers, message)
        log_push_event_csv(subject, receivers)

        bot.send_card_message(
            content=f"祝您有美好的一天~✅",
            title=f"✅ {subject} 已成功推送",
            tag_text="成功",
            tag_color="green",
            template_color="green"  # 标题栏为绿色背景
        )
    except Exception as e:
        # print("邮件发送失败：", e)
        log_push_event_csv(subject, receivers, error_message=str(e))
        bot.send_card_message(
            content=f"{subject}的推送出现错误。\n程序运行报错：\n```{str(e)}```",
            title="🚨 报错警告",
            tag_text="错误",
            tag_color="red",
            template_color = "red"
        )
