# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import base64

class SignController(http.Controller):

    @http.route('/tvan/on-message', auth='public', csrf=False)
    def tvan_on_message(self, message):
        request.env['wg.tvan.log'].sudo().create({
            'user_id': 2,
            'TDiep': base64.b64encode(message.encode('utf-8')),
        })
        
    def tvan_check_account(self):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }
            else:
                return {
                    'status': 'Success',
                    'user_id': user.id,
                    'message': 'Xác thực thanh công',
                }
        except Exception as e:
            return {
                'status': 'Fail',
                'message': 'Đã có lỗi xảy ra',
            }
    
    # Lay MTDiep
    @http.route('/api/tvan/get-MTDiep', auth='public', csrf=False, type="json")
    def get_MTDiep(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        res = {
            'data': user.tvan_config_id.request_MTDiep(auth_res.get('user_id')),
        }
        print ('Controller1111111111111111111111111111111', res)
        return res

    # To khai 01
    @http.route('/api/tvan/get-xml-tk', auth='public', csrf=False, type="json")
    def get_xml_01_data(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
        print ('Controller1111111111111111111111111111111 get_xml_01_data', data)
        res = {
            'data': user.tvan_config_id.get_xml_01_data(data),
        }
        if data.get('include_text') == 'text':
            res['data_string'] = user.tvan_config_id.get_xml_01_data_text(data)
        print ('Controller1111111111111111111111111111111', res)
        return res

    # Hoa don
    @http.route('/api/tvan/get-xml-inv', auth='public', csrf=False, type="json")
    def get_xml_inv_data(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
        res = {
            'data': user.tvan_config_id.get_xml_inv_data(data),
        }
        if data.get('include_text') == 'text':
            res['data_string'] = user.tvan_config_id.get_xml_inv_data_text(data)
        return res

    # TBSS
    @http.route('/api/tvan/get-xml-tbss', auth='public', csrf=False, type="json")
    def get_xml_tb04_data(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
        res = {
            'data': user.tvan_config_id.get_xml_tb04_data(data),
        }
        if data.get('include_text') == 'text':
            res['data_string'] = user.tvan_config_id.get_xml_tb04_data_text(data)
        return res

    # Send XML
    @http.route('/api/tvan/send-xml', auth='public', csrf=False, type="json")
    def set_xml_to_send_tct(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        return {
            'data': user.tvan_config_id.set_xml_to_send_tct(auth_res.get('user_id'), data),

        }

    # Search with MTDiep
    @http.route('/api/tvan/search', auth='public', csrf=False, type="json")
    def tvan_search(self, **kwargs):
        auth_res = self.tvan_check_account()
        if auth_res.get('status') != 'Success':
            return auth_res
        data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
        user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
        return user.tvan_config_id.tvan_search(data.get('MTDiep'), data.get('pretty_print', False))    

