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

class cost_product_new_catalog(osv.osv_memory):
    """ Create new list_price of selected products """

    _name = 'cost.product.new.catalog'
    _columns = {
        'name': fields.char('ListPrice Name', size=64, required=True),
    }

    def new_list_price(self, cr, uid, ids, context=None):                        
        prod_costs_model = self.pool.get('product.costs')
        prods = prod_costs_model.browse(cr, uid, context['active_ids'], context=context)

        data_obj = self.browse(cr, uid, ids, context=context)[0]

        # Crear tarifa
        pl_model = self.pool.get('product.pricelist')
        args =[('type', '=', 'sale')]
        id = pl_model.search(cr, uid, args, context=context)[0]
        pl = pl_model.browse(cr, uid, [id], context=context)[0]
        
        vals = {}
        vals["name"] = data_obj.name
        vals["active"] = True
        vals["type"] = pl.type
        vals["currency_id"] = pl.currency_id.id
        vals["company_id"] = pl.company_id.id

        pl_id = pl_model.create(cr, uid, vals, context=context)

        # Crear version
        pl_version_model = self.pool.get('product.pricelist.version')
        vals = {}
        vals["name"] = data_obj.name
        vals["active"] = True
        vals["company_id"] = pl.company_id.id
        vals["pricelist_id"] = pl_id

        pl_version_id = pl_version_model.create(cr, uid, vals, context=context)

        # Crear reglas
        pl_item_model = self.pool.get('product.pricelist.item')
        pl_items = []
        for prod in prods:
            vals = {}
            vals["name"] = prod.default_code or prod.name
            vals["price_version_id"] = pl_version_id            
            vals["product_id"] = prod.product_id.id
            vals["base"] = 1 #Precio al público
            vals["price_discount"] = (prod.product_sale_price - prod.list_price) / prod.list_price
            vals["company_id"] = pl.company_id.id

            pl_items.append(pl_item_model.create(cr, uid, vals))

        return True

cost_product_new_catalog()

