# -*- encoding: utf-8 -*-
import odoo.osv.osv
from odoo.tools.translate import _

__all__ = [
    'check_deps',
]

def check_deps(check_list):
    error = False
    import_errors = []
    for imp in check_list:
        try:
            exec(imp in {})
        except ImportError as e:
            error = True
            import_errors.append(str(e))
    if error:
        raise odoo.osv.osv.except_osv(_('Warning!')+' '+_('Unmet python dependencies!'), '\n'.join(import_errors))

