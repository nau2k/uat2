# -*- coding: utf-8 -*-
import uuid
import json
import base64
import requests
from xml.dom import minidom
from lxml import etree
from confluent_kafka import Consumer
import dicttoxml
import re

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

    type = fields.Selection([('uat', 'UAT'), ('producttion', 'Production')], 'Môi trường', default='uat')
    tvan_code = fields.Char('Mã TCGP', default='G0307633556')

    tct_template_id = fields.Many2one('wg.tvan.template', 'Định dạng TCT')

    template_01_id = fields.Many2one('wg.tvan.template', 'Tờ khai')
    template_cks_id = fields.Many2one('wg.tvan.template', 'Chữ ký số')

    template_inv_id = fields.Many2one('wg.tvan.template', 'Hóa đơn')
    template_inv_adjust_id = fields.Many2one('wg.tvan.template', 'Điều chỉnh/Thay thế')
    template_inv_line_id = fields.Many2one('wg.tvan.template', 'Sản phẩm/dịch vụ')
    template_tax_line_id = fields.Many2one('wg.tvan.template', 'Chi tiết thuế suất')

    template_tb04_id = fields.Many2one('wg.tvan.template', 'Thông báo sai sót')
    template_tb04_line_id = fields.Many2one('wg.tvan.template', 'Chi tiết TBSS')

    @api.model
    def get_MTDiep(self):
        MTDiep = 'G0307633556' + str(uuid.uuid4()).upper().replace('-', '')
        if self.env['wg.tvan.log'].sudo().search([('MTDiep', '=', MTDiep)], limit=1):
            return self.get_MTDiep()
        return MTDiep

    def request_MTDiep(self, user_id): 
        MTDiep = self.get_MTDiep()   
        print ('MTDiep', MTDiep)
        self.env['wg.tvan.log'].sudo().create({
            'user_id': user_id,
            'MTDiep': MTDiep,
        })
        return {
            'data': MTDiep,
        }

    def get_xml_01_body_data(self, DSCTSSDung):
        template_line = self.template_cks_id.xml_data
        return ''.join([template_line.format(**line) for line in DSCTSSDung])


    # Trả về XML Tờ khai text
    def get_xml_01_data_text(self, value):
        xml_data = self.template_01_id.xml_data
        value.update({
            'DSCTSSDung': self.get_xml_01_body_data(value.get('DSCTSSDung', []))
        })
        xml_str = xml_data.format(**value)
        parser = etree.XMLParser(remove_blank_text=True)
        elem = etree.XML(xml_str, parser=parser)
        res = etree.tostring(elem).decode('ascii')
        return res

    # Trả về XML Tờ khai base64
    def get_xml_01_data(self, value):
        res = self.get_xml_01_data_text(value)
        return base64.b64encode(res.encode('utf-8')) 


    def get_inv_xml_adjust_data(self, LHDCLQuan):
        if not LHDCLQuan:
            return ''
        if self.template_inv_adjust_id:
            template = self.template_inv_adjust_id.xml_data
            res = template.format(**LHDCLQuan)
            return res

        xml = self.convert_json_to_xml(LHDCLQuan)
        return xml
    # def get_inv_xml_adjust_data(self, LHDCLQuan):
    #     if not LHDCLQuan:
    #         return ''
    #     template = self.template_inv_adjust_id.xml_data
    #     res = template.format(LHDCLQuan) 
    #     print ('get_inv_xml_adjust_data', res)      
    #     return res

    def get_inv_xml_body_data(self, DSHHDVu):
        if not DSHHDVu:
            return ''
        if self.template_inv_line_id:
            template = self.template_inv_line_id.xml_data 
            res = ''.join([template.format(**line) for line in DSHHDVu])
            return res
        xml = self.convert_json_to_xml(DSHHDVu)
        return xml
    # def get_inv_xml_body_data(self, DSHHDVu):
    #     template = self.template_inv_line_id.xml_data
    #     res = ''.join([template.format(**line) for line in DSHHDVu])
    #     print ('get_inv_xml_body_data', res)      
    #     return res

    def get_inv_xml_footer_data(self, THTTLTSuat):
        if not THTTLTSuat:
            return ''
        if self.template_tax_line_id:
            template = self.template_tax_line_id.xml_data 
            res = ''.join([template.format(**line) for line in THTTLTSuat])        
            return res
        xml = self.convert_json_to_xml(THTTLTSuat)
        return xml

    # def get_inv_xml_footer_data(self, THTTLTSuat):
    #     template = self.template_inv_line_id.xml_data
    #     res = ''.join([template.format(**line) for line in THTTLTSuat])        
    #     print ('get_inv_xml_footer_data', res)      
    #     return res

    # Trả về XML Hóa đơn Giá trị gia tăng text
    def get_xml_inv_data_text(self, data):
        xml_data = self.template_inv_id.xml_data
        data.update({
            'LHDCLQuan': self.get_inv_xml_adjust_data(data.get('LHDCLQuan', {})),
            'body_data': self.get_inv_xml_body_data(data.get('DSHHDVu', [])),            
            'footer_data': self.get_inv_xml_footer_data(data.get('THTTLTSuat', [])),
        })
        xml_str = xml_data.format(**data)
        parser = etree.XMLParser(remove_blank_text=True)
        elem = etree.XML(xml_str, parser=parser)
        res = etree.tostring(elem).decode('ascii')
        return res

    # Trả về XML Hóa đơn Giá trị gia tăng Base64
    def get_xml_inv_data(self, data):
        if not self.template_inv_id:
            raise ValueError(('Chưa cấu hình biểu mẫu'))
        xml_data = self.template_inv_id.xml_data
        data.update({
            'LHDCLQuan': self.get_inv_xml_adjust_data(data.get('LHDCLQuan', {})),
            'body_data': self.get_inv_xml_body_data(data.get('DSHHDVu', [])),            
            'footer_data': self.get_inv_xml_footer_data(data.get('THTTLTSuat', [])),
        })
        xml_str = xml_data.format(**data)
        parser = etree.XMLParser(remove_blank_text=True)
        elem = etree.XML(xml_str, parser=parser)
        res = etree.tostring(elem).decode('ascii')
        return base64.b64encode(res.encode('utf-8'))        


    def get_xml_tb04_body_data(self, DSHDon):
        template_line = self.template_tb04_line_id.xml_data
        return ''.join([template_line.format(**line) for line in DSHDon])


    # Trả về XML TBSS text
    def get_xml_tb04_data_text(self, value):
        xml_data = self.template_tb04_id.xml_data
        value.update({
            'DSHDon': self.get_xml_tb04_body_data(value.get('DSHDon', []))
        })
        xml_str = xml_data.format(**value)
        parser = etree.XMLParser(remove_blank_text=True)
        elem = etree.XML(xml_str, parser=parser)
        res = etree.tostring(elem).decode('ascii')
        return res

    # Trả về XML TBSS base64
    def get_xml_tb04_data(self, value):
        res = self.get_xml_tb04_data_text(value)
        print (res)
        return base64.b64encode(res.encode('utf-8'))         


    def set_xml_to_send_tct(self, user_id, data):
        log_value = {
            'user_id': user_id,
            'MTDiep': data.get('MTDiep'),
            'type': data.get('type'),
            'inv_number': data.get('inv_number'),
            'vat': data.get('vat'),
            'company_name': data.get('company_name'),
            'datas': data.get('datas'),
            'tvan_config_id': self.id,
        }
        log = self.env['wg.tvan.log'].sudo().search([('MTDiep', '=', data.get('MTDiep'))], limit=1)
        if log:
            if log.state == '2':
                log.write(log_value)
                log.gen_xml_to_send_tct()
            else:
                return {
                    'MTDiep': data.get('MTDiep'),
                    'status': 'fail',
                    'message': 'Thông điệp đã được gửi đi!',
                }
        else:
            log = self.env['wg.tvan.log'].sudo().create(log_value)
        return {
            'MTDiep': data.get('MTDiep'),
            'status': 'success',
            'message': 'Thông điệp đang được xử lý!',
        }

    def get_tvan_api_token(self):
        # requests.post
        headers = {
            'content-type': 'application/json',
            # 'Authorization': 'token ' + tvan_config.api_token,
        }
        data = {
            'UserName': self.api_username, 
            'Password': self.api_password,
        }
        res = requests.post(self.api_link + self.api_auth_url, data=json.dumps(data), headers=headers)
        try:
            res = json.loads(res.text)
            self.write({
                'api_token': res.get('Token'),
            })
        except Exception as e:
            raise e


    def tvan_send_message(self, TDiep):
        # requests.post
        headers = {
            'content-type': 'application/json',
            'Authorization': 'token ' + self.api_token,
        }
        data = {
            'TDiep': TDiep, 
        }
        res = requests.post(self.api_link + self.api_send_url, data=json.dumps(data), headers=headers)
        try:
            res = json.loads(res.text)
            return res
        except Exception as e:
            return {
                'status': 'Fail',
                'message': str(e),
            }

    # KAFKA service
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

    def convert_json_to_xml(self, data_json=None):
        if not data_json:
            return
        xml_data = dicttoxml.dicttoxml(data_json, custom_root='root', attr_type=False)
        # autoregex
        res = re.sub(r'<\?xml.*?\?><root>|</?root>|</?item>', '', xml_data.decode('utf-8'))
        return res
    