# -*- coding: utf-8 -*-
import uuid
import json
import requests
from odoo.http import request

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import secrets

class ResPartner(models.Model):
    _inherit = 'res.partner'

    api_rest_key = fields.Char()

class ResUsers(models.Model):
    _inherit = 'res.users'

    def generate_api_rest_key(self):
        self.ensure_one()
        if self.api_rest_key:
            return
        while True:
            api_rest_key = secrets.token_urlsafe(40)
            if not self.sudo().search([('api_rest_key', '=', api_rest_key)]):
                self.sudo().write({'api_rest_key': api_rest_key})
                return

    @api.model
    def get_api_rest_user(self, api_rest_key):
        return self.sudo().search([('api_rest_key', '=', api_rest_key)], limit=1)


    @api.model
    def get_tvan_conifg(self):
        user = self.get_api_rest_user(request.httprequest.headers.get('X-Api-Key'))
        if not user.tvan_config_id:
            raise ValidationError('Cấu hình Tvan chưa được thiết lập!')
        return user.tvan_config_id


    # Trả về XML Tờ khai Sử dụng hóa đơn điện tử text
    @api.model
    def get_xml_01_data(self, data):
        return {
            'data': self.get_tvan_conifg().get_xml_01_data(data),
        }

    # Trả về XML Tờ khai Sử dụng hóa đơn điện tử base64
    @api.model
    def get_xml_01_data_text(self, data):
        return {
            'data': self.get_tvan_conifg().get_xml_01_data_text(data),
        }

    # Trả về XML Hóa đơn Giá trị gia tăng text
    @api.model
    def get_xml_inv_data(self, data):
        print ('backend get_xml_inv_data', data, type(data))
        if type (data) == type('TGL'):
            res = json.loads(data)
        else:
            res = data
        return {
            'data': self.get_tvan_conifg().get_xml_inv_data(res),
        }

    # Trả về XML Hóa đơn Giá trị gia tăng base64
    @api.model
    def get_xml_inv_data_text(self, data={}):
        return {
            'data': self.get_tvan_conifg().get_xml_inv_data_text(data),
        }
    

    # Trả về XML Tờ khai Sử dụng hóa đơn điện tử text
    @api.model
    def get_xml_tb04_data(self, data):
        return {
            'data': self.get_tvan_conifg().get_xml_tb04_data(data),
        }

    # Trả về XML Tờ khai Sử dụng hóa đơn điện tử base64
    @api.model
    def get_xml_tb04_data_text(self, data):
        return {
            'data': self.get_tvan_conifg().get_xml_tb04_data_text(data),
        }        

    # Lấy mã thông điệp
    @api.model
    def request_MTDiep(self):
        user = self.get_api_rest_user(request.httprequest.headers.get('X-Api-Key'))
        return self.get_tvan_conifg().request_MTDiep(user.id)


    @api.model
    def set_xml_to_send_tct(self, data):
        user = self.get_api_rest_user(request.httprequest.headers.get('X-Api-Key'))
        return self.get_tvan_conifg().set_xml_to_send_tct(user.id, data)


class Partner(models.Model):
    _inherit = 'res.partner'

    tvan_config_id = fields.Many2one('wg.tvan.config', 'Môi trường TVAN')
