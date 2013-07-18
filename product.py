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
import pdb
from osv import fields, osv

class product_product(osv.osv):
    """añadimos un campo para gestionar el uso del módulo por producto"""
    _inherit = "product.product"

    def _product_costs(self, cr, uid, ids, field_names, arg, context=None):

        res = {}
        if context is None:
            context = {}

        date_from = context.get('date_from', time.strftime('%Y-01-01'))
        date_to = context.get('date_to', time.strftime('%Y-12-31'))
        invoice_state = context.get('invoice_state', 'draft_open_paid')

        # calcular los costes indirectos
        total_indirect_costs = self._get_indirect_costs(cr, uid, 
            date_from, date_to, context=context)
        total_direct_costs = 0

        prod_obj = self.pool.get('product.product')
        args = []

        ids_all = prod_obj.search(cr, uid, args, context=context)
        prods_all = prod_obj.browse(cr, uid, ids_all, context=context)

        vals = {}
        for prod in prods_all:

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

        prods = prod_obj.browse(cr, uid, ids, context=context)
        
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

            if vals[prod.id]["product_sale_price"]> 0:                
                margin = vals[prod.id]["actual_sale_price"] / vals[prod.id]["product_sale_price"]
                vals[prod.id]["real_sale_margin_rate"] = round((margin-1)*100,0)
            else:                
                vals[prod.id]["real_sale_margin_rate"] = 0

            #prod_obj.write(cr, uid, [prod.id], vals[prod.id], context=None)

        # Devolver vista

        return vals

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
        'profit': fields.float('Profit %'),   
        'packaging_unit_cost': fields.float('Packaging unit cost'),
        'delivery_cost': fields.float('Delivery cost'),
        'purchase_manpower': fields.float('Purchase Manpower'),
        'sale_manpower': fields.float('Sale Manpower'),
        'purchased_units': fields.function(_product_costs, type='float', string='Purchased units', multi='product_margin'),
        'manufactured_units' : fields.function(_product_costs, type='float', string='Manufactured units', multi='product_margin'),
        'procurement_units': fields.function(_product_costs, type='float', string='Procured units', multi='product_margin'),        
        'direct_cost' : fields.function(_product_costs, type='float', string='Direct costs', multi='product_margin'),
        'indirect_cost' : fields.function(_product_costs, type='float', string='Indirect costs', multi='product_margin'),
        'product_cost' : fields.function(_product_costs, type='float', string='Total cost', multi='product_margin'),
        'product_sale_price' : fields.function(_product_costs, type='float', string='Base sale price', multi='product_margin'), 
        'product_cost_tracking' : fields.function(_product_costs, type='float', string='Cost tracking (%)', multi='product_margin'),
        'actual_sale_price' : fields.function(_product_costs, type='float', string='Avg sale price', multi='product_margin'),
        'sold_units' : fields.function(_product_costs, type='float', string='Sold units', multi='product_margin'),
        'expected_sale_margin_rate': fields.function(_product_costs, type='float', string='Expected Margin (%)', multi='product_margin'),   
        'real_sale_margin_rate' : fields.function(_product_costs, type='float', string='Real Margin (%)', multi='product_margin'),
    }
    
    _defaults = {
    	'profit': 0,
        'packaging_unit_cost': 0,
        'delivery_cost': 0,
    }
    
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: