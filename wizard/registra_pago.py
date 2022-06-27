from odoo import models,fields,api
from odoo.exceptions import ValidationError
from datetime import datetime


class RegistraPagoWizard(models.TransientModel):
    _name = 'lot.registra.pago.wizard'
    _description = 'Registra Pago wizard'

    tipo_pago = fields.Selection([('0', 'Cuotas'), ('1', 'Enganche')],string='Tipo de Pago', default='0')
    boleta = fields.Char(string='Boleta')
    monto = fields.Float(string="Monto", default=0)
    fecha = fields.Date(string="Fecha", default=datetime.today())
    journal_id = fields.Many2one(string="Diario", comodel_name='account.journal')
    cotizador_id = fields.Many2one(string="Cotizador", comodel_name='lot.cotizador')
    cuota_id = fields.Many2one(string="Cuota", comodel_name='lot.cotizador.lines')
    mora = fields.Float(string="Mora", default=0)

    @api.onchange('tipo_pago')
    def onchange_tipo_pago(self):
        cotizador_id = self.env['lot.cotizador'].search([('id','=',self.env.context['active_id'])])
        if self.tipo_pago == '0':
            self.cuota_id = self.env['lot.cotizador.lines'].search([('cotizador_id','=',self.env.context['active_id']),
                                                                   ('valor_pagado','=',0)],
                                                                   order='cuota')[0]
            self.monto = round(self.cuota_id.capital + self.cuota_id.intereses, 2)

            if self.fecha > self.cuota_id.fecha:
                mora = self.env['lot.mora'].search([('fecha_de_vigencia','<=', self.fecha)], order='fecha_de_vigencia desc')[0]
                self.mora = round(mora.porcentaje_de_mora/100 * self.monto , 2)

        elif self.tipo_pago == '1':
            self.monto = round(cotizador_id.enganche - cotizador_id.enganche_pagado, 2)
            self.mora = 0

        self.cotizador_id = cotizador_id


    def paga_cargo(self, cargo, abono, full_reconcile):
        for line in cargo.line_ids:
            if line.debit > 0:
                for linec in abono.line_ids:
                    if linec.credit > 0:
                        vals_pr = {
                            "debit_move_id": line.id,
                            "credit_move_id": linec.id,
                            "full_reconcile_id": full_reconcile.id,
                            "debit_currency_id": cargo.currency_id.id,
                            "credit_currency_id": abono.currency_id.id,
                            "amount": line.debit,
                            "debit_amount_currency": line.debit,
                            "credit_amount_currency": linec.credit
                        }

                        self.env['account.partial.reconcile'].create(vals_pr)

                        vals_cargo_pago = {
                            'payment_id': abono.id,
                            'amount_residual': 0,
                            'amount_residual_signed': 0,
                            'payment_state': 'paid'

                        }

                        cargo.write(vals_cargo_pago)

                        vals_linea = {
                            'reconciled': True,
                            'full_reconcile_id': full_reconcile.id,
                            'matching_number': full_reconcile.name,
                        }

                        linec.write(vals_linea)

                        line.write(vals_linea)

        return self

    def action_pagar(self):
        cotizador_id = self.env['lot.cotizador'].search([('id','=',self.env.context['active_id'])])
        diario_capital = self.env['account.journal'].search([('lot_tipo_registro', '=', '2')]).id
        diario_intereses = self.env['account.journal'].search([('lot_tipo_registro', '=', '3')]).id
        diario_mora = self.env['account.journal'].search([('lot_tipo_registro', '=', '4')]).id
        diario_enganche = self.env['account.journal'].search([('lot_tipo_registro', '=', '5')]).id
        producto_capital = self.env['product.template'].search([('lot_capital', '=', True)]).id
        producto_intereses = self.env['product.template'].search([('lot_intereses', '=', True)]).id
        taxes_intereses = self.env['product.template'].search([('lot_intereses', '=', True)]).taxes_id
        producto_mora = self.env['product.template'].search([('lot_mora', '=', True)]).id
        taxes_mora = self.env['product.template'].search([('lot_mora', '=', True)]).taxes_id
        producto_enganche = self.env['product.template'].search([('lot_enganche', '=', True)]).id

        if self.tipo_pago == '0':
            if round(cotizador_id.enganche - cotizador_id.enganche_pagado,2) > 0:
                raise ValidationError('No se pueden registrar pagos a Cuotas si no se ha completado el pago del enganche')
            else:
                self.cuota_id = self.env['lot.cotizador.lines'].search([('cotizador_id', '=', self.env.context['active_id']),
                                                                        ('valor_pagado', '=', 0)],
                                                                           order='cuota')[0]
                if self.monto != round(self.cuota_id.capital + self.cuota_id.intereses,2):
                    raise ValidationError('No se puede registrar un pago de cuota diferente a su valor ' + str(round(self.cuota_id.capital + self.cuota_id.intereses, 2)))
                else:
                    vals_cargo_capital = {
                        'move_type': 'out_invoice',
                        'state': 'draft',
                        'partner_id': cotizador_id.cliente_id.id,
                        'inmueble_id': cotizador_id.inmueble_id.id,
                        'journal_id': diario_capital,
                        'payment_reference': cotizador_id.name,
                        'invoice_line_ids': [(0, 0, {'product_id': producto_capital, 'price_unit': self.cuota_id.capital})]
                    }

                    cargo_capital = self.env['account.move'].create(vals_cargo_capital)
                    cargo_capital.action_post()

                    vals_cargo_intereses = {
                        'move_type': 'out_invoice',
                        'state': 'draft',
                        'partner_id': cotizador_id.cliente_id.id,
                        'inmueble_id': cotizador_id.inmueble_id.id,
                        'journal_id': diario_intereses,
                        'payment_reference': cotizador_id.name,
                        'invoice_line_ids': [(0, 0, {'product_id': producto_intereses, 'price_unit': self.cuota_id.intereses, 'tax_ids': taxes_intereses})]
                    }

                    cargo_intereses = self.env['account.move'].create(vals_cargo_intereses)

                    cargo_intereses.action_post()

                    vals_cuota = {
                        'valor_pagado': round(self.monto, 2),
                        'cotizador_id': cotizador_id.id,
                        'fecha_pago': self.fecha,
                        'boleta': self.boleta,
                        'cargo_capital_id': cargo_capital.id,
                        'cargo_intereses_id': cargo_intereses.id
                    }

                    if self.mora > 0:
                        vals_cargo_mora = {
                            'move_type': 'out_invoice',
                            'state': 'draft',
                            'partner_id': cotizador_id.cliente_id.id,
                            'inmueble_id': cotizador_id.inmueble_id.id,
                            'journal_id': diario_mora,
                            'payment_reference': cotizador_id.name,
                            'invoice_line_ids': [(0, 0,
                                                  {'product_id': producto_mora, 'price_unit': self.mora,
                                                   'tax_ids': taxes_mora})]
                            }

                        cargo_mora = self.env['account.move'].create(vals_cargo_mora)

                        cargo_mora.action_post()

                        vals_cuota['cargo_mora_id'] = cargo_mora.id


                    vals_pago = {
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'state': 'draft',
                        'partner_id': cotizador_id.cliente_id.id,
                        'amount': round(self.monto + self.mora, 2),
                        'journal_id': self.journal_id.id,
                        'date': self.fecha,
                        'ref': self.cotizador_id.name
                    }

                    pago_cuota = self.env['account.payment'].create(vals_pago)
                    pago_cuota.action_post()

                    vals_fr = {
                    }

                    full_reconcile = self.env['account.full.reconcile'].create(vals_fr)

                    self.paga_cargo(cargo_capital, pago_cuota, full_reconcile)
                    self.paga_cargo(cargo_intereses, pago_cuota, full_reconcile)
                    if self.mora:
                        self.paga_cargo(cargo_mora, pago_cuota, full_reconcile)

                    vals_cuota['recibo_id'] = pago_cuota.id
                    self.cuota_id.write(vals_cuota)


        elif self.tipo_pago == '1':
            if self.monto > round(cotizador_id.enganche - cotizador_id.enganche_pagado,2):
                raise ValidationError('No se puede registrar un pago de Enganche mayor a el monto de Enganche Pendiente '+str(round(cotizador_id.enganche - cotizador_id.enganche_pagado,2)))
            else:
                vals_cargo_enganche = {
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'partner_id': cotizador_id.cliente_id.id,
                    'inmueble_id': cotizador_id.inmueble_id.id,
                    'journal_id': diario_enganche,
                    'payment_reference': cotizador_id.name,
                    'invoice_line_ids': [(0, 0, {'product_id': producto_enganche, 'price_unit': self.monto})]
                }

                cargo_enganche = self.env['account.move'].create(vals_cargo_enganche)
                cargo_enganche.action_post()

                vals_pago = {
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'state': 'draft',
                    'partner_id': cotizador_id.cliente_id.id,
                    'amount': round(self.monto,2),
                    'journal_id': self.journal_id.id,
                    'date': self.fecha,
                    'ref': self.cotizador_id.name
                }

                pago_enganche = self.env['account.payment'].create(vals_pago)
                pago_enganche.action_post()

                vals_fr = {

                }

                full_reconcile = self.env['account.full.reconcile'].create(vals_fr)

                self.paga_cargo(cargo_enganche, pago_enganche, full_reconcile)

                vals_enganche = {
                        'valor_pagado': round(self.monto, 2),
                        'cotizador_id': cotizador_id.id,
                        'fecha': self.fecha,
                        'boleta': self.boleta,
                        'cargo_enganche_id': cargo_enganche.id,
                        'recibo_id': pago_enganche.id
                        }

                cotizador_id.cotizador_enganche_lines.create(vals_enganche)

