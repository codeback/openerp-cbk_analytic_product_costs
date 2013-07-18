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

from osv import fields, osv

class product_product(osv.osv):
    """añadimos un campo para gestionar el uso del módulo por producto"""
    _inherit = "product.product"

    _columns = {
        'profit': fields.float('Profit %'),   
        'packaging_unit_cost': fields.float('Packaging unit cost'),
        'delivery_cost': fields.float('Delivery cost'),
        'purchase_manpower': fields.float('Purchase Manpower'),
        'sale_manpower': fields.float('Sale Manpower'),
        'purchased_units': fields.float('Purchased units'),
        'manufactured_units' : fields.float('Manufactured units'),
        'procurement_units': fields.float('Procured units'),        
        'direct_cost' : fields.float('Direct costs'),
        'indirect_cost' : fields.float('Indirect costs'),
        'product_cost' : fields.float('Total cost'),
        'product_sale_price' : fields.float('Base sale price'), 
        'product_cost_tracking' : fields.float('Cost tracking (%)'),
        'actual_sale_price' : fields.float('Avg sale price'),
        'sold_units' : fields.float('Sold units'),
        'expected_sale_margin_rate': fields.float('Expected Margin (%)'),   
        'real_sale_margin_rate' : fields.float('Real Margin (%)'),
    }
    
    _defaults = {
    	'profit': 0,
        'packaging_unit_cost': 0,
        'delivery_cost': 0,
    }

product_product()

class product_ul(osv.osv):
    """añadimos un campo para gestionar el uso del módulo por producto"""
    _inherit = "product.ul"
    _columns = {
        'unit_price': fields.float('Unit price'),
        'delivery_cost': fields.float('Delivery cost'),
    }

    _defaults = {
        'unit_price': 0,
        'delivery_cost': 0,
    }

product_ul()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: