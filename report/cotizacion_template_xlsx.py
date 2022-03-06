import base64
import io

from odoo import models

class CotizadorXlsx(models.AbstractModel):
    _name = 'report.iit_lotificacion.report_cotizacion_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    def generate_xlsx_report(self, workbook, data, cotizador):
        for obj in cotizador:
            report_name = obj.name
            # One sheet by partner
            borde = 1
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'border': borde, 'bold': True})
            format_titulo = workbook.add_format({'border': borde, 'bold': True, 'align': 'center', 'bg_color': '#9DD18C'})
            format_titulo2 = workbook.add_format({'border': borde, 'bold': True })
            format_moneda = workbook.add_format({'border': borde, 'bold': True, 'num_format': 'Q#,##0.00'})
            format_mensaje = workbook.add_format({'border': borde, 'bold': True, 'text_wrap': True})
            format_titulo_centrado = workbook.add_format({'border': borde, 'bold': True, 'align': 'center'})


            sheet.set_column('B:B', 40)
            sheet.set_column('C:C', 12)
            sheet.set_column('C:C', 12)

            row = 1
            col = 1


            company = self.env['res.company'].search([('id','=', obj.env.company.id)])
            if company.logo:
                logo_image = io.BytesIO(base64.b64decode(company.logo))
                sheet.insert_image(row, col, "image.png", {'image_data': logo_image, 'x_scale': 0.50, 'y_scale': 0.50})

            row += 5

            sheet.merge_range(row, col, row, col+2, "COTIZACIÓN DE LOTIFICACIÓN PRADOS DE SAN FRANCISCO",  format_titulo)
            row += 1
            sheet.merge_range(row, col, row, col+2, "Nombre: "+obj.cliente_id.name, format_titulo2)
            row += 1
            sheet.merge_range(row, col, row, col+2, "Lote: " + obj.inmueble_id.name, format_titulo2)
            row += 1
            sheet.merge_range(row, col, row, col+2, "Area: " + str(obj.inmueble_id.area) + " metros", format_titulo2)
            row += 1
            sheet.merge_range(row, col, row, col + 2, "", format_titulo2)
            row += 1
            sheet.write(row, col, 'PRECIO DE VENTA', bold)
            sheet.merge_range(row, col+1, row, col+2, obj.precio, format_moneda)
            row += 1
            sheet.write(row, col, 'IVA', bold)
            iva_id = self.env['account.tax'].search([("type_tax_use", "=", "sale")])
            iva = round(iva_id.amount / 100 * obj.precio, 2)
            sheet.merge_range(row, col+1, row, col+2, iva, format_moneda)
            row += 1
            sheet.write(row, col, 'PRECIO DE VENTA CON IVA', bold)
            precio_iva = round(round(iva_id.amount / 100 * obj.precio, 2) + obj.precio, 2)
            sheet.merge_range(row, col+1, row, col+2, precio_iva, format_moneda)
            row += 1
            sheet.merge_range(row, col, row+1, col + 2,
                              "LOS HONORARIOS DEL REGISTRO DE LA PROPIEDAD QUE SE CANCELAN AL FIRMAR LA ESCRITURA DEPENDE DEL TAMAÑO DEL TERRENO",
                              format_mensaje)
            row += 2
            sheet.write(row, col, 'PRECIO DE VENTA SIN IVA', bold)
            sheet.merge_range(row, col+1, row, col+2, obj.precio, format_moneda)
            row += 1
            sheet.write(row, col, 'ENGANCHE', bold)
            sheet.merge_range(row, col+1, row, col+2, obj.enganche, format_moneda)
            row += 1
            sheet.write(row, col, 'SALDO A FINANCIAR', bold)
            sheet.merge_range(row, col+1, row, col+2, obj.monto_financiar, format_moneda)
            row += 1
            sheet.merge_range(row, col, row, col + 2, "", format_titulo2)
            row += 1
            sheet.write(row, col, '', bold)
            sheet.write(row, col+1, '1ra. Cuota', format_titulo_centrado)
            sheet.write(row, col+2, 'Cuotas', format_titulo_centrado)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 12 MESES', bold)
            if obj.plazo == 12:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 24 MESES', bold)
            if obj.plazo == 24:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 36 MESES', bold)
            if obj.plazo == 36:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 48 MESES', bold)
            if obj.plazo == 48:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 60 MESES', bold)
            if obj.plazo == 60:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.write(row, col, 'FINANCIAMIENTO POR 72 MESES', bold)
            if obj.plazo == 72:
                sheet.write(row, col+1, obj.cuota_uno, format_moneda)
                sheet.write(row, col+2, obj.cuota_normal, format_moneda)
            else:
                sheet.write(row, col+1, "", bold)
                sheet.write(row, col+2, "", bold)
            row += 1
            sheet.merge_range(row, col, row, col + 2,"", bold)
            row += 1
            sheet.merge_range(row, col, row, col + 2,
                              "HONORARIOS DEL ABOGADO ES DEL 3.36% SOBRE EL VALOR DEL LOTE",
                              format_mensaje)
            row += 1
            sheet.merge_range(row, col, row, col + 2,"", bold)
            row += 1
            sheet.merge_range(row, col, row, col + 2,"Asesor", bold)
            row += 1
            sheet.merge_range(row, col, row, col + 2,"Celular", bold)
            row += 1