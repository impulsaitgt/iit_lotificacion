from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    inmueble_id = fields.Many2one(comodel_name='lot.inmueble')
