# -*- encoding: utf-8 -*-
from io import BytesIO
from PIL import Image
from base64 import b64decode

from .barcode.code128 import get_code
from .barcode.code39 import create_c39
from .barcode.EANBarCode import EanBarCode
import re
import time
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from aeroolib.plugins.opendocument import Template, OOSerializer, _filter
from aeroolib import __version__ as aeroolib_version
from currency2text import supported_language, currency_to_text
from .docs_client_lib import DOCSConnection
from .exceptions import ConnectionError

from genshi.template.eval import StrictLookup

from odoo import release as odoo_release
from odoo import api, models, fields
from odoo.tools import file_open, frozendict
from odoo.tools.translate import translate, _
from odoo.tools.misc import formatLang, format_date, find_in_path
from odoo.tools.safe_eval import safe_eval
from odoo.modules import load_information_from_description_file
from odoo.exceptions import MissingError
from num2words import num2words
import pytz

import logging
_logger = logging.getLogger(__name__)
AEROO_CONVERSION_COMMAND_PARAMETER = 'aeroo.conversion_command'
AEROO_CONVERSION_GENERATE_PARAMETER = 'aeroo.conversion_generate'
import subprocess
import tempfile
import os

mime_dict = {'oo-odt': 'odt',
             'oo-ods': 'ods',
             'oo-pdf': 'pdf',
             'oo-doc': 'doc',
             'oo-docx': 'docx',
             'oo-xls': 'xls',
             'oo-xlsx': 'xlsx',
             'oo-csv': 'csv', }

filters = {'pdf':'writer_pdf_Export',   # PDF - Portable Document Format
           'odt':'writer8', #ODF Text Document
           'ods':'calc8',   # ODF Spreadsheet
           'doc':'MS Word 97',  # Microsoft Word 97/2000/XP
           'docx':'MS Word 2007 XML',
           'xls':'MS Excel 97', # Microsoft Excel 97/2000/XP
           'xlsx':'Calc Office Open XML',
           'csv':'Text - txt - csv (StarCalc)', # Text CSV
          }

class Parser(models.AbstractModel):
    _name = 'report.report_aeroo.abstract'
    docs_client = None

    def __filter(self, val):
        if isinstance(val, models.BaseModel):
            return val and val.name_get()[0][1] or ''
        return _filter(val)

    # Extra Functions ==========================================================
    def _asarray(self, attr, field):
        """Returns named field from all objects as a list."""
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects': attr, 'value_list': []}
        exec(expr, localspace)
        return localspace['value_list']

    def _average(self, attr, field):
        """
        Returns average (arithmetic mean) of fields from all objects in a list.
        """
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects': attr, 'value_list': []}
        exec(expr, localspace)
        x = sum(localspace['value_list'])
        y = len(localspace['value_list'])
        return float(x)/float(y)
    
    def _barcode(self, code, code_type='ean13', rotate=None, height=50, xw=1):
        if code:
            if code_type.lower()=='ean13':
                bar=EanBarCode()
                im = bar.getImage(code,height)
            elif code_type.lower()=='code128':
                im = get_code(code, xw, height)
            elif code_type.lower()=='code39':
                im = create_c39(height, xw, code)
        else:
            return BytesIO(), 'image/png'
        tf = BytesIO()
        try:
            if rotate!=None:
                im=im.rotate(int(rotate))
        except Exception as e:
            pass
        im.save(tf, 'png')
        size_x = str(im.size[0]/96.0)+'in'
        size_y = str(im.size[1]/96.0)+'in'
        return tf, 'image/png', size_x, size_y

    
    def _asimage(self, field_value, rotate=None, size_x=None, size_y=None, uom='px', hold_ratio=False):
        """
        Prepare image for inserting into OpenOffice.org document
        """
        def size_by_uom(val, uom, dpi):
            if uom == 'px':
                result = str(val/dpi)+'in'
            elif uom == 'cm':
                result = str(val/2.54)+'in'
            elif uom == 'in':
                result = str(val)+'in'
            return result
        ##############################################
        if not field_value:
            return BytesIO(), 'image/png'
        field_value = b64decode(field_value)
        tf = BytesIO(field_value)
        tf.seek(0)
        im = Image.open(tf)
        format = im.format.lower()
        dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))
        try:
            if rotate != None:
                im = im.rotate(int(rotate))
                tf.seek(0)
                im.save(tf, format)
        except Exception as e:
            _logger.exception("Error in '_asimage' method")

        if hold_ratio:
            img_ratio = im.size[0] / float(im.size[1])
            if size_x and not size_y:
                size_y = size_x / img_ratio
            elif not size_x and size_y:
                size_x = size_y * img_ratio
            elif size_x and size_y:
                size_y2 = size_x / img_ratio
                size_x2 = size_y * img_ratio
                if size_y2 > size_y:
                    size_x = size_x2
                elif size_x2 > size_x:
                    size_y = size_y2

        size_x = size_x and size_by_uom(size_x, uom, dpi_x) \
            or str(im.size[0]/dpi_x)+'in'
        size_y = size_y and size_by_uom(size_y, uom, dpi_y) \
            or str(im.size[1]/dpi_y)+'in'
        return tf, 'image/%s' % format, size_x, size_y

    def _currency_to_text(self, currency):
        def c_to_text(sum, currency=currency, language=None):
            lang = supported_language.get(language or self._get_lang())
            return str(lang.currency_to_text(sum, currency), "UTF-8")
        return c_to_text
    
    def _vn_num2words(self, val):
        res = num2words(val, lang='vi_VN') + ' đồng'
        return res[0].upper() + res[1:]

    def _get_tick(self, obj, fname, val):
        lookup = {obj.fname.id: '☒'}
        return lookup.get(val, '☐')

    def _get_selection(self, obj, field=None, value=None):
        """Chuc nang nay cho phep lay gia tri display cua filed selection
            + obj: la object dang print
            + field: ten filed selection
            + value: gia tri noi dung selection
        """
        try:
            if isinstance(obj, models.AbstractModel):
                obj = obj[0]
            if isinstance(obj, str):
                model = obj
                field_val = value
            else:
                model = obj._name
                field_val = getattr(obj, field)
            val = self.env[model].fields_get(allfields=[field])[field]['selection']
            if field_val:
                return dict(val)[field_val]        
            return ''
        except Exception:
            _logger.exception("Error in '_get_selection' method", exc_info=True)
        return ''

    def _get_log(self, obj, field=None):
        if field:
            return obj.get_metadata()[0][field]
        else:
            return obj.get_metadata()[0]

    #TODO : comemnt check after Duong
    def _translate_text(self, source):
        return source
        # trans_obj = self.env['ir.translation']
        # lang = self._get_lang()
        # name = 'ir.actions.report'
        # conds = [('res_id', '=', self.report.id),
        #          ('type', '=', 'report'),
        #          ('src', '=', source),
        #          ('lang', '=', lang)
        #          ]
        # trans = trans_obj.search(conds)
        # if not trans:
        #     vals = {
        #         'src': source,
        #         'type': 'report',
        #         'lang': self._get_lang(),
        #         'res_id': self.report.id,
        #         'name': name,
        #     }
        #     trans_obj.create(vals)
        # return translate(self.env.cr, name, 'report', lang, source) or source

    def get_docs_conn(self):
        if self._get_generate_doc() != 'aeroo_docs':
            return
        if self.docs_client:
            return
        icp = self.env.get('ir.config_parameter')
        icpgp = icp.get_param
        docs_host = icpgp('aeroo.docs_host') or 'localhost'
        docs_port = icpgp('aeroo.docs_port') or '8989'
        # docs_auth_type = icpgp('aeroo.docs_auth_type') or False
        docs_username = icpgp('aeroo.docs_username') or 'anonymous'
        docs_password = icpgp('aeroo.docs_password') or 'anonymous'
        docs_client = DOCSConnection(
            docs_host, docs_port, username=docs_username,
            password=docs_password)
        self.docs_client = docs_client

    def _get_lo_bin(self):
        lo_bin = self.env['ir.config_parameter'].sudo().get_param(
            AEROO_CONVERSION_COMMAND_PARAMETER, 'soffice',
        )
        try:
            lo_bin = find_in_path(lo_bin)
        except IOError:
            lo_bin = None
        if not lo_bin:
            try:
                lo_bin = find_in_path('libreoffice')
            except IOError:
                lo_bin = None
        return lo_bin
    
    def _get_generate_doc(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            AEROO_CONVERSION_GENERATE_PARAMETER, 'aeroo_docs',
        )

    def _convert_single_report_cmd(self, report, result_path, format_type):
        lo_bin = self._get_lo_bin()
        if not lo_bin:
            raise RuntimeError(
                _('Libreoffice runtime not available. '
                  'Please contact your administrator.')
            )
        in_mime = mime_dict[report.in_format]
        out_filters = filters.get(format_type, False)
        if out_filters:
            out_mime = '%s:%s' % (format_type, out_filters)
        else:
            out_mime = format_type
        command = [lo_bin, '--headless',
                   '--convert-to', out_mime, result_path]
        subprocess.check_output(command, cwd=os.path.dirname(result_path))
        result_path = result_path.replace('.' + in_mime, '.' + format_type)
        # THANH 15072020 - using while to check template file created from subprocess exists on directory /tmp/
        # before return result_path because subprocess runs slower and causes return file ods instead of converted file
        i = 0
        while not os.path.exists(result_path):
            i += 1
        return result_path

    def _cleanup_tempfiles(self, temporary_files):
        # Manual cleanup of the temporary files
        for temporary_file in temporary_files:
            try:
                os.unlink(temporary_file)
            except (OSError, IOError):
                _logger.error('Error when trying to remove file %s' %
                             temporary_file)
    
    def _generate_doc_cmd(self, data, report):
        in_mime = mime_dict[report.in_format]
        out_mime = mime_dict[report.out_format.code]
        file_path = tempfile.mktemp(
            suffix='.%s' % in_mime, prefix='aeroo-%s-tmp-%s-' % (in_mime, report.id))
        with open(file_path, 'wb') as f:
            f.write(data)
        filedata = self._convert_single_report_cmd(
            report, file_path, out_mime)
        with open(filedata, 'r+b') as fd:
            data = fd.read()
        self._cleanup_tempfiles([file_path, filedata])
        return data
    
    def _generate_doc(self, data, report):
        docs = self.docs_client
        token = docs.upload(data)
        if report.out_format.code == 'oo-dbf':
            data = docs.convert(identifier=token)  # TODO What format?
        else:
            data = docs.convert(
                identifier=token, out_mime=mime_dict[report.out_format.code], in_mime=mime_dict[report.in_format])
        return data

    def _get_lang(self, source='current'):
        if source == 'current':
            return self.env.context['lang'] or self.env.context['user_lang']
        elif source == 'company':
            return self.env.user.company_id.partner_id.lang
        elif source == 'user':
            return self.env.context['user_lang']

    def _set_lang(self, lang, obj=None):
        self.localcontext.update(lang=lang)
        if obj is None and 'objects' in self.localcontext:
            obj = self.localcontext['objects']
        if obj and obj.env.context['lang'] != lang:
            ctx_copy = dict(self.env.context)
            ctx_copy.update(lang=lang)
            obj.env.context = frozendict(ctx_copy)
            obj.invalidate_cache()

    def _format_lang(self, value, digits=None, grouping=True, monetary=False, dp=False, currency_obj=False, date=False, date_time=False):
        """Chuc nang nay cho phep formart cac gia tri: float datetime, date
            + float: co the formart chuoi so thap phan bang digits, currency_obj hoac convert thanh field monetary
            + date va date_time: de duoc dua ve dinh dang theo ngon ngu hien tai cua nguoi dung 
        """
        if date or date_time:
            return format_date(self.env, value, lang_code=self.env.user.lang or 'vi_VN')
        return formatLang(self.env, value, digits, grouping, monetary, dp, currency_obj)
    
    def _format_ddmmyyy(self, date, field_type='date'):
        if not date:
            return ''
        tz_utc = pytz.utc
        tz_user = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        if field_type == 'date':
            # date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).astimezone(tz_user)
            #Hieu sua lai ham cu
            date = tz_user.localize(datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)).astimezone(tz_user)
        else:
            # date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT).astimezone(tz_user)
            #Hieu sua lai ham cu
            date = tz_user.localize(datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(tz_user)
        if self.env.user.lang == 'vi_VN':
            string = (_('Ngày %s tháng %s năm %s')%(str(date.strftime('%d')), str(date.strftime('%m')), str(date.strftime('%Y'))))
        else:
            string = (_('Day %s month %s year %s')%(str(date.strftime('%d')), str(date.strftime('%m')), str(date.strftime('%Y'))))
        return string

    def _set_objects(self, model, docids, lctx):
        # lctx = self.localcontext
        lang = lctx['lang']
        objects = None
        if self.env.context['lang'] != lang:
            ctx_copy = dict(self.env.context)
            ctx_copy.update(lang=lang)
            objects = self.env.get(model).with_context(**ctx_copy).browse(docids)
        else:
            objects = self.env.get(model).browse(docids)
        lctx['objects'] = objects
        lctx['o'] = objects and objects[0] or None

    def test(self, obj):
        _logger.exception(
            'AEROO TEST1======================= %s - %s' %
            (type(obj),
             id(obj)))
        _logger.exception('AEROO TEST2======================= %s' % (obj,))

    def get_other_template(self, model, rec_id):
        if not hasattr(self, 'get_template'):
            return False
        record = self.env.get(model).browse(rec_id)
        template = self.get_template(record)
        return template

    def get_stylesheet(self, report):
        style_io = None
        if report.styles_mode != 'default':
            if report.styles_mode == 'global':
                styles = self.company.stylesheet_id
            elif report.styles_mode == 'specified':
                styles = report.stylesheet_id
            if styles:
                style_io = b64decode(styles.report_styles or False)
        return style_io
    
    def _set_company(self, model, docids):
        '''Kim: - Fix loi lay mac dinh lay company theo cau hinh cua user
                - Khong nen su dung gia tri company lay du lieu khi in hang loat record
        '''
        company = self.env.user.company_id
        if model and docids:
            try:
                objects = self.env.get(model).browse(docids)
                if objects[0] and objects[0].company_id:
                    company = objects[0].company_id
            except Exception as e:
                _logger.exception(_("%s") % str(e))
        return company

    
    def _set_localcontext(self):
        return {}

    def _aeroo_date_format(self, dt, fm="%d/%m/%Y"):
        if dt:
            return dt.strftime(fm)
        return ''

    def _format_dt_ngay_thang_nam(self, dt):
        return self._aeroo_date_format(dt, fm='Ngày %d tháng %m năm %Y')

    def _format_dt_gio_phut_ngay_thang_nam(self, dt):
        return self._aeroo_date_format(dt, fm='%H giờ %M phút, ngày %d tháng %m năm %Y')

    def _format_currency_vnd_has_symbol(self, val):
        return self._format_currency_vnd_without_symbol(val)

    def _format_currency_vnd_without_symbol(self, val):
        self = self.with_context(lang='vi_VN')
        return formatLang(self.env, val, 0)
    
    def _format_vn_digit(self, val, digits):
        self = self.with_context(lang='vi_VN')
        return formatLang(self.env, val, digits)
    
    def vnpercent(self, val):
        return self._format_vn_digit(val, 3)

    
    def _bool2char(self, val, chr='X', false_char=''):
        return chr if val else false_char
    
    def _bool2tick(self, val):
        return self._bool2char(val,'☒','☐')

    def _get_ae_main_obj(self):
        return self._context.get('ae_main_obj')


    def complex_report(self, docids, data, report, ctx):
        """ Returns an aeroo report generated by aeroolib"""
        model = ctx.get('active_model', False)
        # tmpl_type = 'odt'
        record_ids = docids
        ctx = ctx
        company = self.env.user.company_id

        #=======================================================================
        localcontext = {
            'data':     data,
            '__filter': self.__filter,
            'ae_main_obj': self._get_ae_main_obj(),
            'ae_context':self._context.get('ae_context'),
            'aedf':self._aeroo_date_format,
            'aentn':self._format_dt_ngay_thang_nam,
            'aegpntn':self._format_dt_gio_phut_ngay_thang_nam,
            'aecf': self._format_currency_vnd_has_symbol,
            'aecfw': self._format_currency_vnd_without_symbol,
            'ae_vn_digit': self._format_vn_digit,
            'bool2char': self._bool2char,
            'vn_num2words': self._vn_num2words,
            'get_tick': self._get_tick,
            'bool2tick': self._bool2tick,
            'vnpercent':self.vnpercent,
            're':re,
            'formatLang': self._format_lang,
            '_': self._translate_text,
            
            'time': time,
            'today': fields.Date.context_today(self),
            'format_ddmmyyy': self._format_ddmmyyy,
            
            'user': self.env.user,
            'user_lang': self.env.user.lang,
            'company': self._set_company(model, docids),
            
            'asarray':  self._asarray,
            'average':  self._average,
            
            'currency_to_text': self._currency_to_text,
            
            'asimage': self._asimage,
            'barcode': self._barcode,
            
            'get_selection': self._get_selection,
            
            'get_log': self._get_log,
            'getLang':  self._get_lang,
            # 'setLang':  self._set_lang,
            
            'gettext': self._translate_text,
#             'test':     self.test,
            'fields':     fields}
        ae_context = self._context.get('ae_context', {})
        obj_context = {}
        for k,v in ae_context.items():
            if isinstance(v, dict) and v.get('ae_model'):
                obj = self.env[v.get('ae_model')].browse(v.get('ae_res_id'))
                obj_context[k] = obj


        localcontext.update(ctx)
        localcontext.update(obj_context)
        # localcontext = self._set_localcontext()
        # if localcontext:
        #     localcontext.update(localcontext)
        
        # self._set_lang(company.partner_id.lang)
        self._set_objects(model, docids, localcontext)

        file_data = None
        if report.tml_source == 'database':
            if not report.report_data or report.report_data == 'False':
                # TODO log report ID etc.
                raise MissingError(_("Aeroo Reports could'nt find report template"))
            file_data = b64decode(report.report_data)
        elif report.tml_source == 'file':
            if not report.report_file or report.report_file == 'False':
                # TODO log report ID etc.
                raise MissingError(
                    _("No Aeroo Reports template filename provided"))
            file_data = report._read_template()
        else:
            rec_id = ctx.get('active_id', data.get('id')) or data.get('id')
            file_data = self.get_other_template(model, rec_id)

        if not file_data:
            # TODO log report ID etc.
            raise MissingError(_("Aeroo Reports could'nt find report template"))

        template_io = BytesIO(file_data)
        if report.styles_mode == 'default':
            serializer = OOSerializer(template_io)
        else:
            style_io = BytesIO(self.get_stylesheet(report))
            serializer = OOSerializer(template_io, oo_styles=style_io)

        basic = Template(source=template_io, serializer=serializer, lookup=StrictLookup)

        # Add metadata
        ser = basic.Serializer
        model_obj = self.env.get('ir.model')
        model_name = model_obj.search([('model', '=', model)])[0].name
        ser.add_title(model_name)

        user_name = self.env.user.name
        ser.add_creation_user(user_name)

        module_info = load_information_from_description_file('report_aeroo')
        version = module_info['version']
        ser.add_generator_info('Aeroo Lib/%s Aeroo Reports/%s'% (aeroolib_version, version))
        ser.add_custom_property('Aeroo Reports %s' % version, 'Generator')
        ser.add_custom_property('Odoo %s' % odoo_release.version, 'Software')
        ser.add_custom_property(module_info['website'], 'URL')
        ser.add_creation_date(time.strftime('%Y-%m-%dT%H:%M:%S'))

        file_data = basic.generate(**localcontext).render().getvalue()
        #=======================================================================
        code = mime_dict[report.in_format]
        #_logger.info("End process %s (%s), elapsed time: %s" % (self.name, self.model, time.time() - aeroo_print.start_time), logging.INFO) # debug mode

        return file_data, code

    def simple_report(self, docids, data, report, ctx, output='raw'):
        pass

    def single_report(self, docids, data, report, ctx):
        code = report.out_format.code or 'oo-pdf'
        ext = mime_dict[code]
        if code.startswith('oo-'):
            return self.complex_report(docids, data, report, ctx)
        elif code == 'genshi-raw':
            return self.simple_report(docids, data, report, ctx, output='raw')
        
    def assemble_tasks(self, docids, data, report, ctx):
        file_data, out_code = self.single_report(docids, data, report, ctx)
        
        obj = self.env[report.model].browse(docids)
        print_report_name = safe_eval(report.print_report_name, {'object': obj})
        if report.in_format == report.out_format.code:
            out_code = mime_dict[report.in_format]
        else:
            try:
                if self._get_generate_doc() == 'py3o':
                    file_data = self._generate_doc_cmd(file_data, report)
                else:
                    self.get_docs_conn()
                    file_data = self._generate_doc(file_data, report)
                out_code = mime_dict[report.out_format.code]
            except Exception as e:
                _logger.exception(_("Aeroo DOCS error!\n%s") % str(e))
                if report.disable_fallback:
                    file_data = None
                    out_code = None
                    _logger.exception(e[0])
                    raise ConnectionError(_('Could not connect Aeroo DOCS!'))
        
        filename = '%s.%s' % (print_report_name, out_code) if out_code else ''
        return file_data, out_code, filename

    @api.model
    def aeroo_report(self, docids, data, new_instance_report=None):
        report = new_instance_report or self.env['ir.actions.report']._get_report_from_name(self._context.get('report_name'))
        if 'tz' not in self._context:
            self = self.with_context(tz=self.env.user.tz or 'UTC')
        file_data, out_code, filename = self.assemble_tasks(docids, data, report, self._context)
        return file_data, out_code, filename
