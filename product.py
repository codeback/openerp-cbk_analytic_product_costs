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
    _name = "product.product"
    _inherit = "product.product"
    
    _columns = {
        'profit': fields.float('Profit %'),   
        'packaging_unit_cost': fields.float('Packaging unit cost'),
    }

    _defaults = {
        'profit': 0,
        'packaging_unit_cost': 0,
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: