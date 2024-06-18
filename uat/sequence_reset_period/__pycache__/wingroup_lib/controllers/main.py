# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import base64

class SignController(http.Controller):

    @http.route('/sign', auth='public')
    def sign_record_view(self, portal_token):
        all_model = ['wg.inv.registry']
        record = False
        for model in all_model:
            record = request.env[model].sudo().search([('portal_token', '=', portal_token)], limit=1)
            if record:
                break
        if not record.attachment_origin_id:
            return 'Hợp đồng chưa được khởi tạo!'   
        data = record.wg_get_portal_sign_data()
        return request.render('wingroup_lib.portal_sign_view', data)


    @http.route('/post-sign', auth='public', csrf=False, methods=['POST'])
    def sign_record_post(self, portal_token, **data):
        model = data.get('model')
        record = request.env[model].sudo().search([('portal_token', '=', portal_token)], limit=1)
        res = record.sudo().wg_handle_signed_data(data)
        return json.dumps(res)

