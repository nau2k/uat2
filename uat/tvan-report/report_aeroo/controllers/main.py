# -*- encoding: utf-8 -*-
import logging
import json
from multiprocessing.sharedctypes import Value
from odoo.addons.web.controllers import main
from odoo import http
from odoo.http import route, request, content_disposition, serialize_exception as _serialize_exception
from odoo.tools import html_escape
_logger = logging.getLogger(__name__)


class ReportController(main.ReportController):

    MIMETYPES = {
        'txt': 'text/plain',
        'html': 'text/html',
        'doc': 'application/vnd.ms-word',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'zip': 'application/zip',
    }

    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter not in ['aeroo', 'qweb-aeroo']:
            return super(ReportController, self).report_routes(reportname, docids, converter, **data)

        context = dict(request.env.context)

        report = request.env['ir.actions.report']._get_report_from_name(
            reportname)
        context.update({'preview': 'ABC'})

        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])

        file_data, out_code, filename = report.with_context(
            context).render_aeroo(docids, data=data)
        httpheaders = [
            ('Content-Type', self.MIMETYPES.get(out_code, 'application/octet-stream')),
            ('Content-Length', len(file_data)),
            ('Content-Disposition', content_disposition(filename))]
        return request.make_response(file_data, headers=httpheaders)

    @route()
    def report_download(self, data, token):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        if type not in ['aeroo', 'qweb-aeroo']:
            return super(ReportController, self).report_download(data, token)
        try:
            reportname = url.split('/report/aeroo/')[1].split('?')[0]
            reportname, docids = reportname.split('/')
            return self.report_routes(reportname=reportname, docids=docids, converter=type)
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

    @http.route('/dynamic_aeroo', auth='public')
    def index(self, **kw):
        ae_context = json.loads(kw['ae_context'])
        context = dict(request.env.context, ae_context = ae_context)
        fres_id = kw['fres_id']
        fmodel = kw['fmodel']
        obj = request.env[fmodel].browse(int(fres_id))
        template_data = obj[kw['fname']]
        template_path = kw['template_path']
        template_path = None if template_path in ('None','False') else template_path
        tml_source =  'database' if template_data else 'file' if template_path else None
        if not tml_source:
            raise ValueError('path hoặc template data không hợp lệ')
        rptype = kw['rptype']
        out_format = request.env['report.mimetypes'].search([('code','=',f'oo-{rptype}')], limit=1).id
        report_data = { 
            # 'name': 'dump', 
            'type': 'ir.actions.report',
            'model': kw['res_model'],
            # 'report_name':'dump',
            'report_type':'aeroo',
            'in_format':'oo-odt',
            'out_format': out_format,
            'tml_source': tml_source,
            # 'report_data': template_data,
            'print_report_name':kw['print_report_name']
        }

        if template_data:
            report_data['report_data'] =  template_data
            # if not template_data:
            #     raise ValueError(f'Không tồn tại template_data ở record:{fres_id} của model {fmodel}')
        else:
            report_data['report_file'] =  template_path
           
        report = request.env['ir.actions.report'].new(report_data)
        docids = [int(kw['res_id'])]
        # context.update({'preview': 'ABC'})
        data = {}
        # if docids:
        #     docids = [int(i) for i in docids.split(',')]
        # if data.get('options'):
        #     data.update(json.loads(data.pop('options')))
        # if data.get('context'):
        #     data['context'] = json.loads(data['context'])
        #     if data['context'].get('lang'):
        #         del data['context']['lang']
        #     context.update(data['context'])

        file_data, out_code, filename = report.with_context(
            context).render_aeroo(docids, data=data)
        httpheaders = [
            ('Content-Type', self.MIMETYPES.get(out_code, 'application/octet-stream')),
            ('Content-Length', len(file_data)),
            ('Content-Disposition', content_disposition(filename))]
        return request.make_response(file_data, headers=httpheaders)