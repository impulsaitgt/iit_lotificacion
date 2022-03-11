from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import math

class Cotizador(models.Model):
    _name = 'lot.cotizador'

    name = fields.Char(string='Cotizacion', copy=False, readonly=True, default='Nuevo')
    inmueble_id = fields.Many2one(comodel_name='lot.inmueble', required=True)
    enganche = fields.Float(string="Enganche",required=True)
    fecha_inicial = fields.Date(string="Fecha inicial",required=True)
    fecha_generacion = fields.Date(string="Fecha generacion", readonly=True)
    plazo = fields.Integer(string="Plazo",required=True)
    tasa_de_interes = fields.Float(string="Tasa de interes",required=True)
    cliente_id = fields.Many2one(comodel_name='res.partner', string="Cliente", required=True)
    cotizador_lines = fields.One2many(comodel_name='lot.cotizador.lines', inverse_name='cotizador_id')
    cotizador_enganche_lines = fields.One2many(comodel_name='lot.cotizador.enganche.lines', inverse_name='cotizador_id')

    state = fields.Selection([('draft', 'Borrador'), ('published', 'Publicado'), ('cancelled', 'Cancelado')],
                             string='Estado', default='draft')
    precio = fields.Float(string="Precio", default=0)
    monto_financiar = fields.Float(string="Monto a financiar", readonly=True, compute="_montof_")
    suma_capital = fields.Float(string="Total Capital", readonly=True, compute="_montof_")
    suma_intereses = fields.Float(string="Total Interes", readonly=True, compute="_montof_")
    suma_cuotas = fields.Float(string="Total", readonly=True, compute="_montof_")
    cuota_uno = fields.Float(string="Cuota 1", readonly=True, default=0)
    cuota_normal = fields.Float(string="Cuota Normal", readonly=True, default=0)
    enganche_pagado = fields.Float(string="Enganche Pagado", readonly=True, compute="_montof_")
    valor_pagado = fields.Float(string="Valor Pagado", readonly=True, compute="_montof_")
    cuota_final = fields.Float(string="Cuota Normal", readonly=True, default=0)
    state_payment = fields.Char(string="Estado de Pago", readonly=True)

    _sql_constraints = [
        ('referencia_unica', 'unique(name)', "Ese cotizador ya existe revisa la secuencia")
    ]

    @api.model
    def create(self, vals):
        if vals.get('name','Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('lot.cotizador.numero') or 'Nuevo'

        result = super(Cotizador,self).create(vals)
        return result

    @api.onchange('inmueble_id')
    def onchange_inmueble_id(self):
        self.precio = self.inmueble_id.precio_a_publico

    @api.onchange('precio')
    def onchange_precio(self):
        if self.precio < self.inmueble_id.precio_minimo:
            self.precio = self.inmueble_id.precio_a_publico

    def action_genera_cuotas(self):
        # elimino cuotas anteriores
        lineas = self.cotizador_lines
        for linea in lineas:
            linea.unlink()

        # genero cuotas
        tasa_mensual = self.tasa_de_interes / 100 / 12
        factor1 = 1 - ((1 + tasa_mensual) ** (self.plazo * -1))
        factor2 = factor1 / tasa_mensual
        cuota_base = round(self.monto_financiar / factor2, 2)
        cbd10 = cuota_base / 10
        truncado = math.trunc(cbd10) * 10
        valsnormal = {
            'cuota_normal': truncado,
            'fecha_generacion': datetime.today()
        }
        self.write(valsnormal)
        delta = round(cuota_base - truncado, 2)
        financiamiento = self.monto_financiar
        fecha_cuota = self.fecha_inicial
        delta_mes = relativedelta(months=1)


        i = 0
        while i < self.plazo:
            if (i == 0):
                interes = round(financiamiento * tasa_mensual, 2)
                capital = round(cuota_base - interes + (delta * (self.plazo - 1)), 2)
                financiamiento = financiamiento - capital

                vals1 = {
                    'cuota_uno': round(interes + capital, 2)
                }
                self.write(vals1)


            elif (i == self.plazo - 1):
                capital = financiamiento
                interes = round(financiamiento * tasa_mensual, 2)

                valsfinal = {
                    'cuota_final': round(interes + capital, 2)
                }
                self.write(valsfinal)
            else:
                interes = round(financiamiento * tasa_mensual, 2)
                capital = round(truncado - interes, 2)
                financiamiento = financiamiento - capital

            i += 1
            valscuota = {
                'cuota': i,
                'fecha': fecha_cuota,
                'capital': capital,
                'intereses': interes,
                'cotizador_id': self.id
            }
            # cotizador = self.env["lot.cotizador"].search([("id", "=", self.id)])
            # cotizador.cotizador_lines.create(valscuota)
            # self.env["lot.cotizador"].search([("id", "=", self.id)]).cotizador_lines.create(valscuota)
            self.cotizador_lines.create(valscuota)

            fecha_cuota = fecha_cuota + delta_mes

    def action_confirma_cuotas(self):
        self.state="published"

    def action_reestablece_borrador(self):
        self.state="draft"

    def action_cancela(self):
        for linea in self.cotizador_lines:
            if linea.recibo_id:
                linea.recibo_id.action_draft()
                linea.recibo_id.action_cancel()
            if linea.cargo_capital_id:
                linea.cargo_capital_id.button_draft()
                linea.cargo_capital_id.button_cancel()
            if linea.cargo_intereses_id:
                linea.cargo_intereses_id.button_draft()
                linea.cargo_intereses_id.button_cancel()
            if linea.cargo_mora_id:
                linea.cargo_mora_id.button_draft()
                linea.cargo_mora_id.button_cancel()

        for linea_enganche in self.cotizador_enganche_lines:
            if linea_enganche.recibo_id:
                linea_enganche.recibo_id.action_draft()
                linea_enganche.recibo_id.action_cancel()
            if linea_enganche.cargo_enganche_id:
                linea_enganche.cargo_enganche_id.button_draft()
                linea_enganche.cargo_enganche_id.button_cancel()


        self.state="cancelled"

    def action_registrar_pago(self):
        action = self.env.ref('iit_lotificacion.action_registra_pago').read()[0]
        action['domain'] = [('lot.registra.pago.wizard.cotizador_id', '=', self.id)]
        return action

    # def action_imprime_cotizacion(self):
    #     print("aqui imprimo cotizacion: ", self)
    #
    # def action_imprime_estado_cuenta(self):
    #     print("aqui imprimo estado de cuenta: ", self)

    def _montof_(self):
        for cotizador in self:
            cotizador.monto_financiar = cotizador.precio - cotizador.enganche
            capital = 0
            intereses = 0
            cuotas = 0
            valor_pagado = 0
            state_payment = "Normal"
            for linea in cotizador.cotizador_lines:
                capital = capital + linea.capital
                intereses = intereses + linea.intereses
                cuotas = cuotas + linea.cuota_total
                valor_pagado = valor_pagado + linea.valor_pagado
                if (round(linea.cuota_total,2) > round(linea.valor_pagado, 2)):
                    if (linea.fecha < date.today()):
                        state_payment = "Pagos pendientes"
                        linea.estado = "Atrasado"
                    else:
                        linea.estado = 'Normal'
                else:
                    linea.estado = 'Pagado'
            cotizador.suma_capital = capital
            cotizador.suma_intereses = intereses
            cotizador.suma_cuotas = cuotas
            cotizador.valor_pagado = valor_pagado
            if round(capital, 2) <= round(valor_pagado, 2):
                state_payment = "Completamente Pagado"

            if cotizador.state == 'draft':
                state_payment = "Borrador"

            if cotizador.state == 'cancelled':
                state_payment = "Cancelado"
            enganche_pagado = 0
            for eng in cotizador.cotizador_enganche_lines:
                enganche_pagado = enganche_pagado + eng.valor_pagado
            cotizador.enganche_pagado = enganche_pagado

            cotizador.state_payment = state_payment


class CotizadorLines(models.Model):
    _name = 'lot.cotizador.lines'

    cotizador_id = fields.Many2one(comodel_name='lot.cotizador')
    inmueble_name = fields.Char(string="Inmueble", related="cotizador_id.inmueble_id.name")

    fecha = fields.Date(string="Fecha", required=True)
    fecha_pago = fields.Date(string="Fecha Pagado")
    capital = fields.Float(string="Capital", default=0)
    intereses = fields.Float(string="Intereses", default=0)
    cuota = fields.Integer(string="Cuota", default=0)
    cuota_total = fields.Float(string="Cuota total", compute="_cuota_total_")
    valor_pagado = fields.Float(string="Valor Pagado", default=0)
    boleta = fields.Char(string='Boleta')
    cargo_capital_id = fields.Many2one(string="Cargo capital", comodel_name='account.move', readonly=True)
    cargo_intereses_id = fields.Many2one(string="Factura Interes", comodel_name='account.move', readonly=True)
    cargo_mora_id = fields.Many2one(string="Factura Mora", comodel_name='account.move', readonly=True)
    recibo_id = fields.Many2one(string="Recibo de Pago", comodel_name='account.payment', readonly=True)
    estado = fields.Char(string="Estado", readonly=True, default='Normal')

    def _cuota_total_(self):
        for linea in self:
            linea.cuota_total = linea.capital + linea.intereses

class CotizadorEngancheLines(models.Model):
    _name = 'lot.cotizador.enganche.lines'

    cotizador_id = fields.Many2one(comodel_name='lot.cotizador')
    fecha = fields.Date(string="Fecha", required=True)
    valor_pagado = fields.Float(string="Valor Pagado", default=0)
    boleta = fields.Char(string='Boleta')
    cargo_enganche_id = fields.Many2one(string="Cargo Enganche", comodel_name='account.move', readonly=True)
    recibo_id = fields.Many2one(string="Recibo de Pago", comodel_name='account.payment', readonly=True)


