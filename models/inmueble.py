from odoo import models,fields,api

class Inmueble(models.Model):
    _name = 'lot.inmueble'

    name = fields.Char(string="Nombre",required=True)
    direccion = fields.Char(string="Direccion")
    numero_de_escritura = fields.Char(string="Numero de escritura")
    precio_a_publico = fields.Float(string="Precio a publico",required=True, default=0)
    precio_iva = fields.Float(string="Precio con IVA", readonly=True, compute="_precio_iva_")
    precio_minimo = fields.Float(string="Precio Minimo (Sin IVA)",required=True, default=0)
    reserva = fields.Float(string="Reserva",required=True, default=0)
    frente = fields.Float(string="Frente (metros)", default=0)
    lateral_izquierdo = fields.Float(string="Lateral Izquierdo (metros)", default=0)
    fondo = fields.Float(string="Fondo (metros)", default=0)
    lateral_derecho = fields.Float(string="Lateral (metros)", default=0)
    area = fields.Float(string="Area (metros²)", default=0)
    foto = fields.Binary(string="Foto")
    finca = fields.Char(string="Finca")
    folio = fields.Char(string="Folio")
    libro = fields.Char(string="Libro")

    _sql_constraints = [
        ('referencia_unica', 'unique(name)', "Ese inmueble ya existe especifica otro nombre")
    ]

    @api.onchange('precio_a_publico')
    def onchange_precio_a_publico(self):
        self._precio_iva_()


    def _precio_iva_(self):
        for inmueble in self:
            if inmueble.precio_a_publico != 0:
                iva_id = self.env['account.tax'].search([("type_tax_use", "=", "sale")])
                inmueble.precio_iva = round(round(iva_id.amount / 100 * inmueble.precio_a_publico, 2) + inmueble.precio_a_publico, 2)
            else:
                inmueble.precio_iva = 0

    def action_view_cotizaciones(self):
        action = self.env.ref('iit_lotificacion.cotizador_action').read()[0]
        action['domain'] = [('inmueble_id','=',self.id)]
        return action





