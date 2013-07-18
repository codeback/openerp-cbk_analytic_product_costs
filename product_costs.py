# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 Codeback Software S.L. (www.codeback.es). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import math

from osv import fields, osv
from openerp.tools.translate import _

class product_costs(osv.osv_memory):
    """"""
    _name = "product.costs"

    def get_costs(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        product_costs_obj = self.browse(cr, uid, ids, context=context)[0]

        context.update(invoice_state = product_costs_obj.invoice_state)
        if product_costs_obj.from_date:
            context.update(date_from = product_costs_obj.from_date)
        if product_costs_obj.to_date:
            context.update(date_to = product_costs_obj.to_date)

        return self.redirect_view(cr, uid, context=context)
 
    def update_view(self, cr, uid, context=None):

        menu_mod = self.pool.get('ir.ui.menu')        
        args = [('name', '=', 'Product Cost Analysis')]
        menu_ids = menu_mod.search(cr, uid, args)
        
        return {
            'name': 'Product Cost Analysis',
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': menu_ids[0]},
        }    

    def redirect_view(self, cr, uid, context=None):
        mod_obj = self.pool.get('ir.model.data')
        result = mod_obj._get_id(cr, uid, 'product', 'product_search_form_view')
        id = mod_obj.read(cr, uid, result, ['res_id'], context=context)        
        cr.execute('select id,name from ir_ui_view where name=%s and type=%s', ('view.product.costs.form', 'form'))
        view_res2 = cr.fetchone()[0]
        cr.execute('select id,name from ir_ui_view where name=%s and type=%s', ('view.product.costs.tree', 'tree'))
        view_res = cr.fetchone()[0]

        return {
            'name': _('Product Cost Analysis'),
            'context': context,
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model':'product.product',
            'type': 'ir.actions.act_window',
            'views': [(view_res,'tree'), (view_res2,'form')],
            'view_id': False,
            'search_view_id': id['res_id']
        }    

    _columns = {
        'from_date': fields.date('From'),
        'to_date': fields.date('To'),
        'invoice_state':fields.selection([
           ('paid','Paid'),
           ('open_paid','Open and Paid'),
           ('draft_open_paid','Draft, Open and Paid'),
        ],'Invoice State', select=True, required=True),
    }
    _defaults = {
        'from_date': time.strftime('%Y-01-01'),
        'to_date': time.strftime('%Y-12-31'),
        'invoice_state': "draft_open_paid",
    } 
    
product_costs()