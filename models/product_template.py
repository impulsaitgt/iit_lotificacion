from odoo import models, fields


class product_template(models.Model):
    _inherit = "product.template"

    lot_capital = fields.Boolean(string='Capital',default=False)
    lot_intereses = fields.Boolean(string='Intereses',default=False)
    lot_mora = fields.Boolean(string='Mora',default=False)
    lot_enganche = fields.Boolean(string='Enganche',default=False)



