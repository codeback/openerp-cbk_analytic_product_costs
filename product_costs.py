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
from openerp.tools.translate import _

class product_costs(osv.osv):

    _name = "product.costs"
    
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'default_code': fields.related('product_id', 'default_code', type='char', relation="product.product", string='Ref.', readonly=True, store=False),
        'name': fields.related('product_id', 'name', type='char', relation="product.product", string='Name', readonly=True, store=False),
        'list_price': fields.related('product_id', 'list_price', type='float', relation="product.product", string='Catalog Price', readonly=True, store=False),
        'cost_price': fields.related('product_id', 'cost_price', type='float', relation="product.product", string='Avg. price', readonly=True, store=False),

        'packaging_unit_cost': fields.related('product_id', 'packaging_unit_cost', type='float', relation="product.product", string='PUC', readonly=True, store=False),        
        'profit': fields.related('product_id', 'profit', type='float', relation="product.product", string='Profit', readonly=True, store=False),

        'avg_delivery_cost': fields.float('Avg. Deliv. cost'),
        'avg_rappel': fields.float('Avg. rappel'),

        'purchased_units': fields.float('Purchased units'),
        'manufactured_units' : fields.float('Manufactured units'),
        'procurement_units': fields.float('Procured units'),        
        'direct_cost' : fields.float('Direct costs'),
        'indirect_cost' : fields.float('Indirect costs'),
        'product_cost' : fields.float('Total cost'),
        'product_sale_price' : fields.float('Base sale price'),
        'fixed_sale_price' : fields.float('Fixed sale price'),
        'calculated_sale_price': fields.float('Calcultated sale price'),
        'product_cost_tracking' : fields.float('Cost tracking (%)'),
        'actual_sale_price' : fields.float('Avg sale price'),
        'sold_units' : fields.float('Sold units'),
        'expected_sale_margin_rate': fields.float('Expected Margin (%)'),   
        'real_sale_margin_rate' : fields.float('Real Margin (%)'),
    }

    def clear_objects(self, cr, uid, args=[], ids=None):
        """
        Elimina los objetos de forma permanente
        """
        if not ids:
            ids = self.search(cr, uid, args)
        self.unlink(cr, uid, ids)

class product_costs_manager(osv.osv_memory):
    """"""
    _name = "product.costs.manager"

    def get_costs(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        #Eliminar los datos existentes
        prod_costs_model = self.pool.get('product.costs')
        prod_costs_model.clear_objects(cr, uid)

        # DATOS DE CONFIGURACIÓN
        #get the current product.costs object to obtain the values from it
        prod_costs_mgr_obj = self.browse(cr, uid, ids, context=context)[0]
        date_from = prod_costs_mgr_obj.from_date
        date_to = prod_costs_mgr_obj.to_date
        invoice_state = prod_costs_mgr_obj.invoice_state

        # calcular los costes indirectos
        total_indirect_costs = self._get_indirect_costs(cr, uid, 
            date_from, date_to, context=context)

        prod_model = self.pool.get('product.product')
        args = []
        ids = prod_model.search(cr, uid, args, context=context)
        prods = prod_model.browse(cr, uid, ids, context=context)

        total_direct_costs = 0
        vals = {}
        # Primer paso para hallar los costes directos
        for prod in prods:
            vals[prod.id] = {}

            invoiced_data = self._get_invoiced_data(cr, uid, prod.id, 
                date_from, date_to, invoice_state)

            vals[prod.id]["product_id"] = prod.id

            vals[prod.id]["actual_sale_price"] = invoiced_data['sale_avg_price']
            vals[prod.id]["sold_units"] = invoiced_data['sale_num_invoiced']            
            vals[prod.id]["purchased_units"] = invoiced_data['purchase_num_invoiced']
            vals[prod.id]["avg_rappel"] = invoiced_data['avg_rappel']
            vals[prod.id]["avg_delivery_cost"] = invoiced_data['avg_delivery_cost']

            vals[prod.id]["manufactured_units"] = self._get_manufactured_units(cr, uid,
                prod, date_from, date_to, context=context)

            vals[prod.id]["procurement_units"] = vals[prod.id]["purchased_units"] + \
                vals[prod.id]["manufactured_units"]

            vals[prod.id]["direct_cost"] = prod.cost_price + prod.packaging_unit_cost
            sold_costs = vals[prod.id]["avg_rappel"] + vals[prod.id]["avg_delivery_cost"]
            
            vals[prod.id]["product_cost"] = vals[prod.id]["direct_cost"] + sold_costs

            total_direct_costs += vals[prod.id]["direct_cost"] * vals[prod.id]["procurement_units"]

        # porcentaje costes indirectos 
        weight_ic = 0
        if total_direct_costs > 0:
            weight_ic = total_indirect_costs / total_direct_costs
                
        # Segundo paso      
        for prod in prods:
            value = vals[prod.id]
            value["indirect_cost"] = value["direct_cost"] * weight_ic
            value["product_cost"] = value["product_cost"] + value["indirect_cost"]
            value["product_sale_price"] = (1 + prod.profit / 100) * value["product_cost"]

            value["calculated_sale_price"]  = value["product_sale_price"] + value["avg_delivery_cost"] + value["avg_rappel"]
            value["fixed_sale_price"]  =  prod.list_price + value["avg_delivery_cost"] + value["avg_rappel"]

            if prod.list_price > 0:
                value["product_cost_tracking"] = round((prod.list_price-value["product_sale_price"])/prod.list_price,2)*100
                margin = value["actual_sale_price"] / value["fixed_sale_price"]
                value["expected_sale_margin_rate"] = round((margin-1)*100,0)
            else:
                value["product_cost_tracking"] = 0
                value["expected_sale_margin_rate"] = 0

            if value["calculated_sale_price"]> 0:                
                margin = value["actual_sale_price"] / value["calculated_sale_price"]
                value["real_sale_margin_rate"] = round((margin-1)*100,0)
            else:                
                value["real_sale_margin_rate"] = 0

            prod_costs_model.create(cr, uid, value)

        return self.redirect_view(cr, uid, context=context)
     
    def _get_indirect_costs(self, cr, uid, date_from, date_to, context=None):
        
        line_obj = self.pool.get("account.analytic.line")
        args = [('date', '>=', date_from), ('date', '<=', date_to)]
        ids = line_obj.search(cr, uid, args)
        acc_lines = line_obj.browse(cr, uid, ids)

        total_amount = 0
        for line in acc_lines:
            # Se comprueba si el asiento pertenece a una cuenta al que se deb imputar costes
            if line.account_id.assign_product_cost:
                total_amount += line.amount

        return math.fabs(total_amount)

    def _compute_costs(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        prod_costs_mgr_obj = self.browse(cr, uid, ids, context=context)[0]

        context.update(invoice_state = prod_costs_mgr_obj.invoice_state)
        if prod_costs_mgr_obj.from_date:
            context.update(date_from = prod_costs_mgr_obj.from_date)
        if prod_costs_mgr_obj.to_date:
            context.update(date_to = prod_costs_mgr_obj.to_date)

        return self.redirect_view(cr, uid, context=context)
    
    def _get_invoiced_data(self, cr, uid, prod_id, date_from, date_to, invoice_state):
        invoice_types = ()
        states = ()
        if invoice_state == 'paid':
            states = ('paid',)
        elif invoice_state == 'open_paid':
            states = ('open', 'paid')
        elif invoice_state == 'draft_open_paid':
            states = ('draft', 'open', 'paid')
        
        sqlstr="""select
                l.price_unit as unit_price,
                l.quantity as qty,
                i.partner_id as partner            
            from account_invoice_line l
            left join account_invoice i on (l.invoice_id = i.id)
            left join product_product product on (product.id=l.product_id)
            left join product_template pt on (pt.id=product.product_tmpl_id)
            where l.product_id = %s and i.state in %s and i.type IN %s and (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))
            """
        res = {}
        invoice_types = ('out_invoice', 'in_refund')
        cr.execute(sqlstr, (prod_id, states, invoice_types, date_from, date_to))
        lines = cr.fetchall()

        total_price = 0.0
        total_qty = 0.0
        rappel = 0.0
        delivery_cost = 0.0
        for line in lines:
            unit_price = line[0]
            qty = line[1]
            partner_id = line[2]
            total_price = total_price + unit_price * qty
            total_qty = total_qty + qty

            partner_mod = self.pool.get("res.partner")
            partner = partner_mod.browse(cr, uid, partner_id)   
            
            pricelist = partner.property_product_pricelist
            
            sale_costs = self._get_pricelist_sale_costs(cr, uid, pricelist, 
                prod_id, qty, partner_id)
            
            if sale_costs and sale_costs.get("TE") and sale_costs.get("TI"):
                rappel = rappel + (sale_costs["TI"] - sale_costs["TE"]) * qty

            if sale_costs and sale_costs.get("TE") and sale_costs.get("Base"):
                delivery_cost = delivery_cost + (sale_costs["TE"] - sale_costs["Base"]) * qty
        
        if total_qty > 0:
            res['sale_avg_price'] = total_price / total_qty
            res['sale_num_invoiced'] = total_qty
            res['avg_rappel'] = rappel / total_qty
            res['avg_delivery_cost'] = delivery_cost / total_qty
        else:
            res['sale_avg_price'] = 0.0
            res['sale_num_invoiced'] = 0.0
            res['avg_rappel'] = 0.0
            res['avg_delivery_cost'] = 0.0
        
        sqlstr="""select
                sum(l.price_unit * l.quantity)/sum(l.quantity) as avg_unit_price,
                sum(l.quantity) as num_qty
            from account_invoice_line l
            left join account_invoice i on (l.invoice_id = i.id)
            left join product_product product on (product.id=l.product_id)
            left join product_template pt on (pt.id=product.product_tmpl_id)
            where l.product_id = %s and i.state in %s and i.type IN %s and (i.date_invoice IS NULL or (i.date_invoice>=%s and i.date_invoice<=%s))
            """
        invoice_types = ('in_invoice', 'out_refund')
        cr.execute(sqlstr, (prod_id, states, invoice_types, date_from, date_to))
        result = cr.fetchall()[0]
        res['purchase_avg_price'] = result[0] and result[0] or 0.0
        res['purchase_num_invoiced'] = result[1] and result[1] or 0.0      

        return res

    def _get_pricelist_sale_costs(self, cr, uid, pricelist, prod_id, qty, partner_id, res=None, last=False):
        """
        Para que funcione bien las tarifas que dependan de [TI] y [TE] (que estén a 
        su derecha), deben tener una única regla
        
        La función tiene que llamar varias veces (de forma recursiva) a 
        price_get_multi de "product.pricelist" porque hay un bug en esta función
        """

        if not res:
            res={}

        if not pricelist:
            prod_mod = self.pool.get("product.product")
            res["Base"] = prod_mod.browse(cr, uid, [prod_id])[0].list_price
        else:
            pricelist_mod = self.pool.get("product.pricelist")
            pricelist_item_mod = self.pool.get("product.pricelist.item")

            pricelist_info = pricelist_mod.price_get_multi(cr, uid, pricelist_ids=[pricelist.id], 
                products_by_qty_by_partner=[(prod_id, qty, partner_id)])

            if pricelist_info and pricelist_info[prod_id] and pricelist_info[prod_id][pricelist.id]:

                if last == True:
                    res["Base"] = pricelist_info[prod_id][pricelist.id]
                else:
                    if pricelist.name[:2] == "TI":
                        res["TI"] = pricelist_info[prod_id][pricelist.id]
                    if pricelist.name[:2] == "TD":
                        res["TE"] = pricelist_info[prod_id][pricelist.id]
                        last=True           

                    pricelist_item = pricelist_item_mod.browse(cr, uid, [pricelist_info['item_id']])

                    if pricelist_item and pricelist_item[0]:            
                        pricelist = pricelist_item[0].base_pricelist_id
                        res = self._get_pricelist_sale_costs(cr, uid, pricelist, prod_id, qty, 
                            partner_id, res=res, last=last)

        return res

    def _get_pricelists(self, pricelist, res={}):
        """
        Función que devuelve los ids de las tarifas de "impuesto de venta" (TI), 
        "coste de envío a cliente" (TE) y la anterior a la TE (Base)
        """

        pdb.set_trace()
        if (pricelist_version and pricelist_version.items_id[0]):
            
            pricelist = pricelist_version.pricelist_id
            if pricelist.name[:4] == "[TI]":
                res["TI"] = pricelist.id
            
            if pricelist.name[:4] == "[TE]":
                res["TE"] = pricelist.id
                res["Base"] = pricelist_version.items_id[0].base_pricelist_id
                return res

            pricelist_version = pricelist_version.items_id[0].base_pricelist_id
            return self._get_pricelists(pricelist_version, res=res)

        return res



    def _get_pricelist_sale_costs2(self, pricelist_item, price, sale_costs):
        """
        Para que funcione bien las tarifas que dependan de [TI] y [TD] (que estén a 
        su derecha), deben tener una única regla
        """

        discount = pricelist_item.price_discount
        surcharge = pricelist_item.price_surcharge
        base_price = (price - surcharge) / (1 + discount)
        
        if pricelist_item.name[:2] == "[TI]":
            sale_costs['discount'] = discount
        
        if pricelist_item.name[:2] == "[TD]":
            sale_costs['surcharge'] = surcharge
            return sale_costs

        base_pricelist = pricelist_item.base_pricelist_id
        if (base_pricelist and base_pricelist.version_id[0] and 
            base_pricelist.version_id[0].items_id[0]):

            pricelist_item = base_pricelist.version_id[0].items_id[0]
            return self._get_pricelist_sale_costs(pricelist_item, base_price, sale_costs)

        return sale_costs

    def _get_manufactured_units(self, cr, uid, prod, date_from, date_to, context=None):
        
        obj = self.pool.get("mrp.production")
        args = [('date_finished', '>=', date_from), ('date_finished', '<=', date_to), ('product_id', '=', prod.id)]
        ids = obj.search(cr, uid, args)
        prod_orders = obj.browse(cr, uid, ids)

        total_qty = 0
        for order in prod_orders:
            total_qty += order.product_qty

        return total_qty

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
        #mod_obj = self.pool.get('ir.model.data')
        #result = mod_obj._get_id(cr, uid, 'product', 'product_search_form_view')
        #id = mod_obj.read(cr, uid, result, ['res_id'], context=context)        
        cr.execute('select id,name from ir_ui_view where name=%s and type=%s', ('view.product.costs.form', 'form'))
        view_res2 = cr.fetchone()[0]
        cr.execute('select id,name from ir_ui_view where name=%s and type=%s', ('view.product.costs.tree', 'tree'))
        view_res = cr.fetchone()[0]

        return {
            'name': _('Product Cost Analysis'),
            'context': context,
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model':'product.costs',
            'type': 'ir.actions.act_window',
            'views': [(view_res,'tree'), (view_res2,'form')],
            'view_id': False
            #'search_view_id': id['res_id']
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
