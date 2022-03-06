from odoo import models, fields



class AccountJournal(models.Model):
    _inherit = 'account.journal'

    lot_tipo_registro = fields.Selection([ ('1','Otro'),('2','Capital'),('3','Interes'),('4','Mora'),('5', 'Enganche')],string='Tipo de Registro',default='1',required=True)
