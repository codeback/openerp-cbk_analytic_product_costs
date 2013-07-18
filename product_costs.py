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
        # DATOS DE CONFIGURACIÓN
        #get the current product.costs object to obtain the values from it
        product_costs_obj = self.browse(cr, uid, ids, context=context)[0]
        date_from = product_costs_obj.from_date
        date_to = product_costs_obj.to_date
        invoice_state = product_costs_obj.invoice_state

        # calcular los costes indirectos
        total_indirect_costs = self._get_indirect_costs(cr, uid, 
            date_from, date_to, context=context)
        total_direct_costs = 0

        prod_obj = self.pool.get('product.product')
        args = []
        ids = prod_obj.search(cr, uid, args, context=context)
        prods = prod_obj.browse(cr, uid, ids, context=context)

        vals = {}
        for prod in prods:
            vals[prod.id] = {}

            invoiced_data = self._get_invoiced_data(cr, prod.id, 
                date_from, date_to, invoice_state)

            vals[prod.id]["actual_sale_price"] = invoiced_data['sale_avg_price']
            vals[prod.id]["sold_units"] = invoiced_data['sale_num_invoiced']            
            vals[prod.id]["purchased_units"] = invoiced_data['purchase_num_invoiced']

            vals[prod.id]["manufactured_units"] = self._get_manufactured_units(cr, uid,
                prod, date_from, date_to, context=context)

            vals[prod.id]["procurement_units"] = vals[prod.id]["purchased_units"] + \
                vals[prod.id]["manufactured_units"]

            sale_cost = prod.packaging_unit_cost + prod.delivery_cost
            vals[prod.id]["direct_cost"] = prod.cost_price + sale_cost
             
            total_direct_costs += vals[prod.id]["direct_cost"] * \
                (vals[prod.id]["purchased_units"] + vals[prod.id]["manufactured_units"])

        # porcentaje costes indirectos 
        weight_ic = 0
        if total_direct_costs > 0:
            weight_ic = total_indirect_costs / total_direct_costs

        for prod in prods:
            vals[prod.id]["indirect_cost"] = vals[prod.id]["direct_cost"] * weight_ic
            vals[prod.id]["product_cost"] = vals[prod.id]["direct_cost"] + vals[prod.id]["indirect_cost"]
            vals[prod.id]["product_sale_price"] = (1 + prod.profit / 100) * vals[prod.id]["product_cost"]     

            if prod.list_price > 0:
                vals[prod.id]["product_cost_tracking"] = round((prod.list_price-vals[prod.id]["product_sale_price"])/prod.list_price,2)*100
                margin = vals[prod.id]["actual_sale_price"] / prod.list_price
                vals[prod.id]["expected_sale_margin_rate"] = round((margin-1)*100,0)
            else:
                vals[prod.id]["product_cost_tracking"] = 0
                vals[prod.id]["expected_sale_margin_rate"] = 0

            if prod.product_sale_price > 0:                
                margin = vals[prod.id]["actual_sale_price"] / prod.product_sale_price
                vals[prod.id]["real_sale_margin_rate"] = round((margin-1)*100,0)
            else:                
                vals[prod.id]["real_sale_margin_rate"] = 0

            prod_obj.write(cr, uid, [prod.id], vals[prod.id], context=None)

        # Devolver vista
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

    def _get_indirect_costs(self, cr, uid, date_from, date_to, context=None):
        line_obj = self.pool.get("account.analytic.line")
        args = [('date', '>=', date_from), ('date', '<=', date_to)]
        ids = line_obj.search(cr, uid, args)
        acc_lines = line_obj.browse(cr, uid, ids)

        total_amount = 0
        for line in acc_lines:
            total_amount += line.amount

        return math.fabs(total_amount)

    def _get_invoiced_data(self, cr, id, date_from, date_to, invoice_state):
        invoice_types = ()
        states = ()
        if invoice_state == 'paid':
            states = ('paid',)
        elif invoice_state == 'open_paid':
            states = ('open', 'paid')
        elif invoice_state == 'draft_open_paid':
            states = ('draft', 'open', 'paid')

        sqlstr="""select
                sum(l.price_unit * l.quantity)/sum(l.quantity) as avg_unit_price,
                sum(l.quantity) as num_qty
            from account_invoice_line l
            left join account_invoice i on (l.invoice_id = i.id)
            left join product_product product on (product.id=l.product_id)
            left join product_template pt on (pt.id=product.product_tmpl_id)
            where l.product_id = %s and i.state in %s and i.type IN %s and (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))
            """
        res = {}
        invoice_types = ('out_invoice', 'in_refund')
        cr.execute(sqlstr, (id, states, invoice_types, date_from, date_to))
        result = cr.fetchall()[0]
        res['sale_avg_price'] = result[0] and result[0] or 0.0
        res['sale_num_invoiced'] = result[1] and result[1] or 0.0

        invoice_types = ('in_invoice', 'out_refund')
        cr.execute(sqlstr, (id, states, invoice_types, date_from, date_to))
        result = cr.fetchall()[0]
        res['purchase_avg_price'] = result[0] and result[0] or 0.0
        res['purchase_num_invoiced'] = result[1] and result[1] or 0.0      

        return res

    def _get_manufactured_units(self, cr, uid, prod, date_from, date_to, context=None):
        obj = self.pool.get("mrp.production")
        args = [('date_finished', '>=', date_from), ('date_finished', '<=', date_to), ('product_id', '=', prod.id)]
        ids = obj.search(cr, uid, args)
        prod_orders = obj.browse(cr, uid, ids)

        total_qty = 0
        for order in prod_orders:
            total_qty += order.product_qty

        return total_qty

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