import requests as rq
import json
from datetime import datetime

class FeishuBot:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_card_message(self, content, title="通知", tag_text="🔔通知", tag_color="indigo", template_color="blue"):
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

        card_content = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "subtitle": {
                    "tag": "plain_text",
                    "content": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                "text_tag_list": [
                    {
                        "tag": "text_tag",
                        "text": {
                            "tag": "plain_text",
                            "content": tag_text
                        },
                        "color": tag_color  # 用于标签小角标（不是背景）
                    }
                ],
                "template": template_color  # 这里设置标题栏背景颜色
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }

        response = rq.post(
            url=self.webhook_url,
            data=json.dumps({
                "msg_type": "interactive",
                "card": card_content
            }),
            headers=headers
        )
        return response.json()
