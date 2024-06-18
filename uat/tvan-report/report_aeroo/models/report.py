# -*- encoding: utf-8 -*-
import encodings
import importlib
import sys
import os
import odoo
import binascii
from base64 import b64decode
import zipimport
from lxml import etree
import logging

import time
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _
from odoo.modules import module
from odoo.addons.report_aeroo.docs_client_lib import DOCSConnection

AEROO_CONVERSION_GENERATE_PARAMETER = 'aeroo.conversion_generate'
_logger = logging.getLogger(__name__)

mime_dict = {'oo-odt': 'odt',
             'oo-ods': 'ods',
             'oo-pdf': 'pdf',
             'oo-doc': 'doc',
             'oo-docx': 'docx',
             'oo-xls': 'xls',
             'oo-xlsx': 'xlsx',
             'oo-csv': 'csv', }


# ------------------------------------------------------------------------------
class ReportStylesheets(models.Model):
    '''
    Aeroo Report Stylesheets
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'

    ### Fields
    name = fields.Char('Name', size=64, required=True)
    report_styles = fields.Binary('Template Stylesheet',
                                  help='OpenOffice.org / LibreOffice stylesheet (.odt)')
    ### ends Fields


# ------------------------------------------------------------------------------
class ResCompany(models.Model):
    _inherit = 'res.company'

    ### Fields
    stylesheet_id = fields.Many2one('report.stylesheets',
                                    'Aeroo Reports Global Stylesheet')
    ### ends Fields


# ------------------------------------------------------------------------------
class ReportMimetypes(models.Model):
    '''
    Aeroo Report Mime-Type
    '''
    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'

    ### Fields
    name = fields.Char('Name', size=64, required=True, readonly=True)
    code = fields.Char('Code', size=16, required=True, readonly=True)
    compatible_types = fields.Char('Compatible Mime-Types', size=128,
                                   readonly=True)
    filter_name = fields.Char('Filter Name', size=128, readonly=True)
    ### ends Fields


# ------------------------------------------------------------------------------
class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def render_aeroo(self, docids, data=None):
        report_model_name = 'report.%s' % self.report_name
        if not data:
            data = {
                'ids': docids
            }
        report_parser = self.env.get(report_model_name)
        context = dict(self.env.context)
        if report_parser is None:
            report_parser = self.env['report.report_aeroo.abstract']

        context.update({
            'active_model': self.model,
            'report_name': self.report_name,
        })
        file_data, out_code, filename = report_parser.with_context(context).sudo().aeroo_report(docids, data, new_instance_report = not self.id and self)
        return file_data, out_code, filename

    @api.model
    def _get_report_from_name(self, report_name):
        res = super(IrActionsReport, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env['ir.actions.report']
        conditions = [('report_type', 'in', ['aeroo']), ('report_name', '=', report_name)]
        context = self.env['res.users'].context_get()
        return report_obj.with_context(context).search(conditions, limit=1)

    def _get_generate_doc(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            AEROO_CONVERSION_GENERATE_PARAMETER, 'aeroo_docs',
        )

    @api.model
    def get_docs_conn(self):
        if self._get_generate_doc() != 'aeroo_docs':
            return
        icp = self.env.get('ir.config_parameter')
        icpgp = icp.get_param
        docs_host = icpgp('aeroo.docs_host') or 'localhost'
        docs_port = icpgp('aeroo.docs_port') or '8989'
        # docs_auth_type = icpgp('aeroo.docs_auth_type') or False
        docs_username = icpgp('aeroo.docs_username') or 'anonymous'
        docs_password = icpgp('aeroo.docs_password') or 'anonymous'
        docs_client = DOCSConnection(docs_host, docs_port, username=docs_username, password=docs_password)

        fp = file_open('report_aeroo/test_temp.odt', mode='rb')
        file_data = fp.read()
        token = docs_client.upload(file_data)
        return docs_client.convert(identifier=token, out_mime='pdf')

    def _read_template(self):
        self.ensure_one()
        fp = None
        data = None
        try:
            fp = file_open(self.report_file, mode='rb')
            data = fp.read()
        except IOError as e:
            if e.errno == 13:  # Permission denied on the template file
                raise UserError(_(e.strerror), e.filename)
            else:
                _logger.exception(
                    "Error in '_read_template' method", exc_info=True)
        except Exception as e:
            _logger.exception(
                "Error in '_read_template' method", exc_info=True)
            fp = False
            data = False
        finally:
            if fp is not None:
                fp.close()
        return data

    @api.model
    def _get_encodings(self):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)

    @api.model
    def _get_default_outformat(self):
        res = self.env['report.mimetypes'].search([('code', '=', 'oo-odt')])
        return res and res[0].id or False

    def _get_extras(self):
        result = []
        if self.aeroo_docs_enabled():
            result.append('aeroo_ooo')
        ##### Check deferred_processing module #####
        self.env.cr.execute("SELECT id, state FROM ir_module_module WHERE \
                             name='deferred_processing'")
        deferred_proc_module = self.env.cr.dictfetchone()
        if deferred_proc_module and deferred_proc_module['state'] in ('installed', 'to upgrade'):
            result.append('deferred_processing')
        ############################################
        result = ','.join(result)
        for rec in self:
            rec.extras = result

    @api.model
    def aeroo_docs_enabled(self):
        '''
        Check if Aeroo DOCS connection is enabled
        '''
        icp = self.env['ir.config_parameter'].sudo()
        enabled = icp.get_param('aeroo.docs_enabled')
        return enabled == 'True' and True or False

    @api.model
    def _get_in_mimetypes(self):
        mime_obj = self.env['report.mimetypes']
        domain = self.env.context.get('allformats') and [] or [('filter_name', '=', False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]

    report_type = fields.Selection(selection_add=[('aeroo', _('Aeroo Reports'))], ondelete={'aeroo': 'cascade'})
    ### Fields
    charset = fields.Selection('_get_encodings', string='Charset', required=True, default='utf_8')

    styles_mode = fields.Selection([
        ('default', 'Not used'),
        ('global', 'Global'),
        ('specified', 'Specified'),
    ], string='Stylesheet', default='default')
    stylesheet_id = fields.Many2one('report.stylesheets', 'Template Stylesheet', ondelete='set null')

    preload_mode = fields.Selection([
        ('static', _('Static')),
        ('preload', _('Preload')),
    ], string='Preload Mode', default='static')
    tml_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
        ('parser', 'Parser'),
    ], string='Template source', default='database', index=True)
    parser_def = fields.Text('Parser Definition',
                             default="""from odoo import api, models
class Parser(models.AbstractModel):
    _inherit = 'report.report_aeroo.abstract'
    _name = 'report.thisismyparserservicename'"""
                             )
    parser_loc = fields.Char('Parser location', size=128,
                             help="Path to the parser location. Beginning of the path must be start \
              with the module name!\n Like this: {module name}/{path to the \
              parser.py file}")

    # Kim: parser_state dung de khai bao cao hinh parser cho report, mac dinh nen su dung parser_state = default.
    # Y nghia cua cac loai parser_state:
    # default: gia tri khai bao object se duoc su ly trong khai bao module mac dinh, _name = 'report.thisismyparserservicename' can duoc thay the bang name cua report.
    # def: gia tri khai bao object se do dev dinh nghia theo cau truc tuong tu parser_def mac dinh.
    # loc: gia tri khai bao object se lay tu duong dan cua file
    parser_state = fields.Selection([
        ('default', _('Default')),
        ('def', _('Definition')),
        ('loc', _('Location')),
    ], 'State of Parser', index=True, default='default')

    process_sep = fields.Boolean('Process Separately',
                                 help='Generate the report for each object separately, then merge reports.')

    in_format = fields.Selection(selection='_get_in_mimetypes', string='Template Mime-type')  # , default='oo-odt'
    out_format = fields.Many2one('report.mimetypes', 'Output Mime-type')  # , default=_get_default_outformat
    preview = fields.Boolean('Preview before printing', default=False)

    report_wizard = fields.Boolean('Report Wizard',
                                   help='Adds a standard wizard when the report gets invoked.')

    copies = fields.Integer(string='Number of Copies', default=1)
    disable_fallback = fields.Boolean('Disable Format Fallback',
                                      help='Raises error on format convertion failure. Prevents returning \
              original report file type if no convertion is available.')

    extras = fields.Char('Extra options', compute='_get_extras', size=256)
    deferred = fields.Selection([
        ('off', _('Off')),
        ('adaptive', _('Adaptive')),
    ], 'Deferred',
        help='Deferred (aka Batch) reporting, for reporting on large amount of data.', default='off')
    deferred_limit = fields.Integer('Deferred Records Limit',
                                    help='Records limit at which you are invited to start the deferred process.',
                                    default=80)

    replace_report_id = fields.Many2one('ir.actions.report', 'Replace Report',
                                        help='Select a report that should be replaced.', ondelete='set null')
    wizard_id = fields.Many2one('ir.actions.act_window', 'Wizard Action', ondelete='set null')
    report_data = fields.Binary(string='Template Content', attachment=True)

    ### ends Fields

    @api.onchange('in_format')
    def onchange_in_format(self):
        self.out_format = False

    def unlink(self):
        trans_obj = self.env['ir.translation']
        trans_ids = trans_obj.search([('type', '=', 'report'), ('res_id', 'in', self.ids)])
        trans_ids.unlink()
        res = super(IrActionsReport, self).unlink()
        return res

    def unregister_report(self):
        for rec in self:
            report_name = 'report.%s' % rec.report_name
            if rec.env.get(report_name):
                rep_model = self.env['ir.model'].search(
                    [('model', '=', report_name)])
                rep_model.with_context(_force_unlink=True).unlink()

    @api.model
    def load_from_file(self, path, key):
        class_inst = None
        expected_class = 'Parser'

        try:
            for mod_path in odoo.addons.__path__:
                if os.path.lexists(mod_path + os.path.sep + path.split(os.path.sep)[0]):
                    filepath = mod_path + os.path.sep + path
                    filepath = os.path.normpath(filepath)
                    sys.path.append(os.path.dirname(filepath))
                    mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
                    mod_name = '%s_%s_%s' % (self.env.cr.dbname, mod_name, key)

                    if file_ext.lower() == '.py':
                        py_mod = importlib.load_source(mod_name, filepath)

                    elif file_ext.lower() == '.pyc':
                        py_mod = importlib.load_compiled(mod_name, filepath)

                    if expected_class in dir(py_mod):
                        class_inst = py_mod.Parser
                    return class_inst
                elif os.path.lexists(mod_path + os.path.sep + path.split(os.path.sep)[0] + '.zip'):
                    zimp = zipimport.zipimporter(mod_path + os.path.sep + path.split(os.path.sep)[0] + '.zip')
                    return zimp.load_module(path.split(os.path.sep)[0]).parser.Parser
        except SyntaxError as e:
            _logger.error(_('Syntax Error !'), e)
        except Exception as e:
            _logger.error('Error loading report parser: %s' + (filepath and ' "%s"' % filepath or ''), e)
            return None
        return True

    @api.model
    def create(self, vals):
        res = super(IrActionsReport, self).create(vals)
        if res.report_type != 'aeroo':
            return res
        self.clear_caches()
        ir_model = self.env['ir.model']
        model_data = {
            'model': res.report_name,
            'name': res.name,
            'parser_def': res.parser_def,
        }

        parser = ir_model._default_aeroo_parser(model_data)
        if res.parser_state == 'loc' and res.parser_loc:
            parser = self.load_from_file(res.parser_loc, res.name.lower().replace(' ', '_'))
            parser._build_model(self.pool, self._cr)
        elif res.parser_state == 'def' and res.parser_def:
            parser = ir_model._custom_aeroo_parser(model_data)
            parser._build_model(self.pool, self._cr)
        parser._build_model(self.pool, self._cr)
        return res

    def write(self, vals):
        if 'report_data' in vals and vals['report_data']:
            try:
                b64decode(vals['report_data'])
            except binascii.Error:
                vals['report_data'] = False
        res = super(IrActionsReport, self).write(vals)
        self.clear_caches()
        for rec in self.filtered(lambda x: x.report_type == 'aeroo'):
            try:
                rec.unregister_report()
            except Exception:
                _logger.exception(_("Error unregistering Aeroo Reports report"))
                raise UserError(_("Error unregistering Aeroo Reports report"))

            ir_model = rec.env['ir.model']
            model_data = {'model': rec.report_name, 'name': rec.name, 'parser_def': rec.parser_def}

            parser = ir_model._default_aeroo_parser(model_data)
            if rec.parser_state == 'def':
                parser = ir_model._custom_aeroo_parser(model_data)
            elif rec.parser_state == 'loc':
                parser = rec.load_from_file(rec.parser_loc, rec.id)
            parser._build_model(rec.pool, rec.env.cr)
        return res

    # Kim: tao button print bang report_action nhu khai bao cua odoo,
    # def print_quotation(self):
    #    return self.env.ref('report_aeroo_sample.aeroo_sample_report_id').report_action(self)

    # @api.noguess
    def report_action(self, docids, data=None, config=True):
        if self.report_type != 'aeroo':
            return super(IrActionsReport, self).report_action(docids, data=data, config=config)
        context = self.env.context
        if docids:
            if isinstance(docids, models.Model):
                active_ids = docids.ids
            elif isinstance(docids, int):
                active_ids = [docids]
            elif isinstance(docids, list):
                active_ids = docids
            context = dict(self.env.context, active_ids=active_ids)
        out_format = mime_dict[self.out_format.code] or mime_dict[self.in_format]
        preview = self.preview if out_format == 'pdf' else False
        try:
            self.get_docs_conn()
        except Exception as e:
            _logger.exception(_("Aeroo DOCS error!\n%s") % str(e))
            out_format = mime_dict[self.in_format]
            preview = False

        filename = "%s.%s" % (self.name, out_format)
        # obj = self.env[self.model].browse(docids.ids)
        # if self.print_report_name and not len(obj) > 1:
        #     report_name = safe_eval(self.print_report_name, {'object': obj, 'time': time})
        #     filename = ("%s.%s" % (report_name, out_format)).replace('/','_')

        return {
            'context': context, 'data': data,
            'type': 'ir.actions.report',
            'report_name': self.report_name,
            'report_type': self.report_type,
            'report_file': self.report_file,
            'name': self.name,
            'filename': filename,
            'preview': preview,
            'out_format': out_format}
