# -*- coding: utf-8 -*-
import base64

from odoo import http
from odoo.http import request
import json
from pprint import pprint


class APIAll(http.Controller):

    @http.route('/api/account/database-request', auth='public', csrf=False, type="json")
    def api_account_database_request(self, **kwargs):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            # print ('333333333333333333333333333333333, Authorization', Authorization)
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }
            company_data = request.jsonrequest.get('data')
            res = request.env['res.company'].sudo().kt_database_request(company_data)
            return {
                'data': res,
            }
        except Exception as e:
            return {
                'status': 'Fail',
                'message': 'Đã có lỗi xảy ra ' + str(e),
            }

    