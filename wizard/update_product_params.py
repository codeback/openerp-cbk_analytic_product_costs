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

from openerp.osv import fields,osv
from openerp.tools.translate import _
import pdb

class cost_product_update_params_line (osv.TransientModel):
    """ Updates the cost-related fields of the selected products """

    _name = 'cost.product.update.params.line'
    _rec_name = 'product_id'
    _columns = {
        'product_id' : fields.many2one('product.product', string="Product", required=True, ondelete='CASCADE'),
        'product_name': fields.char('Product', size=128, required=True),    
        'packaging_unit_cost' : fields.float("Packaging cost", required=True),
        'delivery_cost': fields.float("Delivery cost", required=True),
        'profit' : fields.float("Profit", required=True),
        'wizard_id' : fields.many2one('cost.product.update.params.wizard', string="Wizard", ondelete='CASCADE'),
    }

class cost_product_update_params_wizard (osv.osv_memory):
    """Wizard for cost params update of a product"""

    _name = 'cost.product.update.params.wizard'
    _columns = {       
        'update_lines_ids' : fields.one2many('cost.product.update.params.line', 'wizard_id', 'Update lines'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(cost_product_update_params_wizard, self).default_get(cr, uid, fields, context=context)
        update_ids = context.get('active_ids', [])     

        prod_model = self.pool.get('product.product')
        prod_costs_model = self.pool.get('product.costs')
        prods = prod_costs_model.browse(cr, uid, update_ids, context=context)

        ids = [prod.product_id.id for prod in prods]

        update_objs = prod_model.browse(cr, uid, ids, context=context)   
    
        update_lines = []
        for update_obj in update_objs:
            update_line = {
                'product_id': update_obj.id,
                'product_name': update_obj.name,
                'packaging_unit_cost': update_obj.packaging_unit_cost,
                'delivery_cost': update_obj.delivery_cost,
                'profit': update_obj.profit,               
            }
            update_lines.append(update_line)
            
        res.update(update_lines_ids=update_lines)
        return res

    def update_product_params(self, cr, uid, ids, context=None):
        prod_model = self.pool.get('product.product')
        wizard = self.browse(cr, uid, ids[0], context=context)

        for line in wizard.update_lines_ids:
            prod = line.product_id
            val = {}            
            val["packaging_unit_cost"] = line.packaging_unit_cost
            val["delivery_cost"] = line.delivery_cost
            val["profit"] = line.profit

            prod_model.write(cr, uid, [prod.id], val)
        
        costs_model = self.pool.get('product.costs.manager')        
        return costs_model.redirect_view(cr, uid, context=context)

cost_product_update_params_wizard ()

