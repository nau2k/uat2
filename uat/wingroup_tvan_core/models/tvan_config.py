# -*- coding: utf-8 -*-
import json
import requests
# from confluent_kafka import Consumer

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class TvanConfig(models.Model):
    _name = 'wg.tvan.config'
    _description = 'Thông số kết nối Tvan'
    _order = 'sequence'

    sequence = fields.Integer('sequence')
    name = fields.Char('Tên TVan', required=True)
    api_username = fields.Char('API username')
    api_password = fields.Char('API password')
    api_link = fields.Char('Link API')
    api_auth_url = fields.Char('Route auth')
    api_send_url = fields.Char('Route send')
    api_token = fields.Char('API token')
    note = fields.Text('Mô tả')

    mq_url = fields.Char('MQ URL')
    mq_protocol = fields.Char('MQ protocol', default='SASL_PLAINTEXT')
    mq_mechanisms = fields.Char('MQ mechanisms', default='PLAIN')
    mq_username = fields.Char('MQ username')
    mq_password = fields.Char('MQ password')
    mq_group = fields.Char('MQ group')
    mq_topic = fields.Char('MQ topic')

    def get_tvan_api_token(self):
        res = requests.post(self.api_link + self.api_auth_url, json={
            'UserName': self.api_username,
            'Password': self.api_password,
        })
        
        try:
            self.write({
                'api_token': json.loads(res.text).get('Token')
            })
        except Exception as e:
            raise e

    def tvan_on_message(self):
        conf = {
            'bootstrap.servers': self.mq_url,
            'security.protocol': self.mq_protocol,
            'sasl.mechanisms': self.mq_mechanisms,
            'sasl.username': self.mq_username,
            'sasl.password': self.mq_password,
            'group.id': self.mq_topic,
        }
        consumer = Consumer(conf) 
        running = True

        msg_index = 0
        try:
            topics = consumer.list_topics().topics.get('0307633556_out')
            print ('topics', topics)
            consumer.subscribe(['0307633556_out'])

            while running:
                msg = consumer.poll(timeout=1.0)
                if msg is None: continue

                if msg.error():
                    print('error:', msg.error())
                else:
                    msg_index += 1
                    print ('Message', msg_index, ':', msg.value(), type(msg.value()))
        finally:
            # Gửi mail báo lỗi
            consumer.close()

