# -*- coding: utf-8 -*-

import json
from confluent_kafka import Consumer
from odoo import api, tools
from odoo.addons.base.models.ir_default import IrDefault


def post_load_hook():
    print (11111111111111111111111111111111111, 'post_load_hook')
    # conf = {
    #     'bootstrap.servers': '27.74.253.50:19092',
    #     'security.protocol': 'SASL_PLAINTEXT',
    #     'sasl.mechanisms': 'PLAIN',
    #     'sasl.username': 'vinaclient2022009',
    #     'sasl.password': '6jIZzxCJiJnoM5',
    #     'group.id': '0307633556',
    # }
    # consumer = Consumer(conf) 
    # running = True

    # msg_index = 0
    # try:
    #     topics = consumer.list_topics().topics.get('0307633556_out')
    #     print ('topics', topics)
    #     consumer.subscribe(['0307633556_out'])
    #     while running:
    #         msg = consumer.poll(timeout=1.0)
    #         if msg is None: continue

    #         if msg.error():
    #             print('KAFKA error:', msg.error())
    #         else:
    #             msg_index += 1
    #             print ('KAFKA message', msg_index, ':', msg.value(), type(msg.value()))
    # finally:
    #     # Gửi mail báo lỗi
    #     consumer.close()