# -*- coding: utf-8 -*-
import base64

from odoo import http
from odoo.http import request
import json
from pprint import pprint


class APIAll(http.Controller):


    @http.route(['/view/pdf',
        '/view/pdf/<string:xmlid>',
        '/view/pdf/<string:xmlid>/<string:filename>',
        '/view/pdf/<int:id>',
        '/view/pdf/<int:id>/<string:filename>',
        '/view/pdf/<string:model>/<int:id>/<string:field>',
        '/view/pdf/<string:model>/<int:id>/<string:field>/<string:filename>'], type='http', auth="public")
    def view_pdf(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename=None, filename_field='name', unique=None, mimetype=None,
                       download=None, data=None, token=None, access_token=None, **kw):
        return request.env['ir.http']._get_content_common(xmlid=xmlid, model=model, res_id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype, access_token=access_token, token=token)


    @http.route('/api/report/create', auth='public', csrf=False, type="json")
    def api_report_create(self, **kwargs):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }

            ReportObj = request.env['wg.report.template.odt']
            report_data = {key: request.jsonrequest.get(key) for key in request.jsonrequest if key in ReportObj._fields}
            template_code = request.jsonrequest.get('template_code')
            if template_code:
	            old_report = ReportObj.with_user(user).search([('code', '=', template_code)], limit=1)
	            if old_report:
	            	old_report.unlink()
            report = ReportObj.with_user(user).create(report_data)
            return {
                'data': report.code,
            }
        except Exception as e:
            raise e

    # https://uat.latido.vn/api/view/pdf?code=tmp0307633556B36039F958F34FD384B7A68F256087FB
    @http.route('/api/view/pdf', auth='public', csrf=False, type="http")
    def api_view_pdf(self, **kwargs):            
        # Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
        # user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
        # if not user:
        #     return {
        #         'status': 'Fail',
        #         'message': 'Xác thực không chính xác',
        #     }
        code = kwargs.get('code')
        if code.startswith('tmp'):
            model_name = 'wg.report.pdf.tmp'
        elif code.startswith('store'):
            model_name = 'wg.report.pdf.store'
        else:
            return {
                'status': 'Fail',
                'message': 'Không tìm thấy tập tin!',
            }
        link = request.env[model_name].get_view_link_by_code(code)
        return request.redirect(link)
        return {
            'status': 'Success',
            'link': link,
        }


    @http.route('/api/create/pdf', auth='public', csrf=False, type="json")
    def api_create_pdf(self, **kwargs):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }
            report_data = {key: request.jsonrequest.get(key) for key in request.jsonrequest}
            new_url = request.env['wg.report.template.odt'].with_user(user).action_print(
                template_code=report_data.get('template_code'), data=report_data)
            return {
                'status': 'Success',
                'message': new_url,
            }
        except Exception as e:
            raise e