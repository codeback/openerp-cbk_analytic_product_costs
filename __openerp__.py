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

{
    'name': 'Manager for analytical accounting of products',
    'version': '0.1',
    'author': 'Codeback Software',
    'summary': 'analytical product costs',
    'description' : 'Manager for analytical accounting of products costs',
    'website': 'http://codeback.es',
    'images': [],
    'depends': ['product_cost_incl_bom', 'analytic'],
    'category': 'Analytical Accounting',
    'sequence': 23,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',            
        'product_view.xml',
        'product_costs_view.xml',
        'pricelist_view.xml',
        'analytic_account_view.xml',
        'wizard/new_list_price_view.xml',
        'wizard/update_list_price_view.xml',
        'wizard/update_product_params_view.xml',            
    ],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'css': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
