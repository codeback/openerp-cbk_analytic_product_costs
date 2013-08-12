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

class cost_product_update_catalog (osv.osv_memory):
    """ Updates the list_price field of selected products """

    _name = 'cost.product.update.catalog'
    _columns = {}

    def update_list_price(self, cr, uid, ids, context=None):
        
        prod_model = self.pool.get('product.product.costs')
        prods = prod_model.browse(cr, uid, context['active_ids'], context=context)

        for prod in prods:
            val = {}
            val["list_price"] = prod.product_sale_price
            prod_model.write(cr, uid, [prod.id], val)

        costs_model = self.pool.get('product.costs')        
        return costs_model.redirect_view(cr, uid, context=context)

cost_product_update_catalog ()

