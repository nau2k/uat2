from odoo import fields, models, tools, _


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    ae_no = fields.Integer(compute='_compute_aeroo_number_order', string='Order Number')

    def _compute_aeroo_number_order(self):
        for count, r in enumerate(self):
            r.ae_no = count + 1

    def _get_aeroo_report(self, fmodel,fres_id, fname, print_report_name, rptype, template_path=None, ae_context=None):
        return {
            'name': 'dynamic_aeroo',
            'type': 'ir.actions.act_url',
            'url': f'/dynamic_aeroo?res_model={self._name}&res_id={self.id}&'
                f'fmodel={fmodel}&fres_id={fres_id}&fname={fname}&print_report_name={print_report_name}&rptype={rptype}&template_path={template_path}&ae_context={ae_context}',
            'target': 'new',
        }  

    # def get_aeroo_report_docx(self, fmodel,fres_id, fname, print_report_name, template_path=None, ae_context=None):
    #     rptype = 'docx'
    #     return self._get_aeroo_report(fmodel,fres_id, fname, print_report_name, rptype, template_path, ae_context)

    # def get_aeroo_report_pdf(self, fmodel,fres_id, fname, print_report_name, template_path=None, ae_context=None):
    #     rptype = 'pdf'
    #     return self._get_aeroo_report(fmodel,fres_id, fname, print_report_name, rptype, template_path, ae_context)

    def get_des_sel(self, fname):
        f = self._fields[fname]
        f_des = dict(f.get_description(self.env)['selection'])
        val = self[fname]
        return f_des[val] if val else False

    def aedf(self, dt, fm="%d/%m/%Y"):
        if dt:
            return dt.strftime(fm)
        return ''
