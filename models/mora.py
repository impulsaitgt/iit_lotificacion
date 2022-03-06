from odoo import models,fields,api

class Mora(models.Model):
    _name= 'lot.mora'

    fecha_de_vigencia = fields.Date(string="Fecha de Vigencia",required=True)
    porcentaje_de_mora = fields.Float(string="Porcentaje de mora",required=True)

