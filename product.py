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
    """añadimos varios campos para gestionar el uso del módulo por producto"""
    _inherit = "product.product"
    
    _columns = {
        'profit': fields.float('Profit %'),   
        'packaging_unit_cost': fields.float('Packaging unit cost'),
        'delivery_cost': fields.float('Delivery cost'),
    }

    _defaults = {
        'profit': 0,
        'packaging_unit_cost': 0,
        'delivery_cost': 0,
    }
product_product()

class product_product_costs(osv.osv):
    """añadimos un campo para gestionar el uso del módulo por producto"""
    _name = "product.product.costs"
    _inherit = "product.product"

    def _product_costs(self, cr, uid, ids, field_names, arg, context=None):

        if context is None:
            context = {}

        date_from = context.get('date_from', time.strftime('%Y-01-01'))
        date_to = context.get('date_to', time.strftime('%Y-12-31'))
        invoice_state = context.get('invoice_state', 'draft_open_paid')

        # calcular los costes indirectos
        total_indirect_costs = self._get_indirect_costs(cr, uid, 
            date_from, date_to, context=context)
        

        prod_costs_model = self.pool.get('product.costs')
        args = []
        prod_costs_ids = prod_costs_model.search(cr, uid, args, context=context)
        prod_costs_obj = prod_costs_model.browse(cr, uid, prod_costs_ids, context=context)[0]
        total_direct_costs = prod_costs_obj.total_direct_costs       

        # porcentaje costes indirectos 
        weight_ic = 0
        if total_direct_costs > 0:
            weight_ic = total_indirect_costs / total_direct_costs

        vals = {}
        prods = self.browse(cr, uid, ids, context=context)
        for prod in prods:
            vals[prod.id] = {}
            vals[prod.id]["indirect_cost"] = prod.direct_cost * weight_ic
            vals[prod.id]["product_cost"] = prod.direct_cost + vals[prod.id]["indirect_cost"]
            vals[prod.id]["product_sale_price"] = (1 + prod.profit / 100) * vals[prod.id]["product_cost"]     

            if prod.list_price > 0:
                vals[prod.id]["product_cost_tracking"] = round((prod.list_price-vals[prod.id]["product_sale_price"])/prod.list_price,2)*100
                margin = prod.actual_sale_price / prod.list_price
                vals[prod.id]["expected_sale_margin_rate"] = round((margin-1)*100,0)
            else:
                vals[prod.id]["product_cost_tracking"] = 0
                vals[prod.id]["expected_sale_margin_rate"] = 0

            if vals[prod.id]["product_sale_price"]> 0:                
                margin = prod.actual_sale_price / vals[prod.id]["product_sale_price"]
                vals[prod.id]["real_sale_margin_rate"] = round((margin-1)*100,0)
            else:                
                vals[prod.id]["real_sale_margin_rate"] = 0

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

    _columns = {
        'purchase_manpower': fields.float('Purchase Manpower'),
        'sale_manpower': fields.float('Sale Manpower'),
        'purchased_units': fields.float('Purchased units'),
        'manufactured_units' : fields.float('Manufactured units'),
        'procurement_units': fields.float('Procured units'),        
        'direct_cost' : fields.float('Direct costs'),
        'indirect_cost' : fields.function(_product_costs, type='float', string='Indirect costs', multi='product_costs'),
        'product_cost' : fields.function(_product_costs, type='float', string='Total cost', multi='product_costs'),
        'product_sale_price' : fields.function(_product_costs, type='float', string='Base sale price', multi='product_costs'), 
        'product_cost_tracking' : fields.function(_product_costs, type='float', string='Cost tracking (%)', multi='product_costs'),
        'actual_sale_price' : fields.float('Avg sale price'),
        'sold_units' : fields.float('Sold units'),
        'expected_sale_margin_rate': fields.function(_product_costs, type='float', string='Expected Margin (%)', multi='product_costs'),   
        'real_sale_margin_rate' : fields.function(_product_costs, type='float', string='Real Margin (%)', multi='product_costs'),
    }
    
product_product_costs()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: