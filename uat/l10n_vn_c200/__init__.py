# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# This module is Copyright (c) 2009-2013 General Solutions (http://gscom.vn) All Rights Reserved.

from odoo import api, SUPERUSER_ID


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('l10n_vn_c200.vn_template').process_coa_translations()
    env.ref('account.group_account_user').write({
        'category_id': env.ref('base.module_category_usability').id,
    })
