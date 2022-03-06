# -*- coding: utf-8 -*-
{
    'name' : 'Especializacion Lotificacion ',
    'summary':"""
        Especializacion Lotificacion
    """,
    'author':'Alexander Paiz/Lester Paiz',
    'category': 'General',
    'version' : '1.0.0',
    'depends': [
        "account",
        "report_xlsx"
    ],
    'data': [
        'security/lotificacion_security.xml',
        'security/ir.model.access.csv',
        'views/menu_view.xml',
        'views/inmueble_view.xml',
        'views/mora_view.xml',
        'views/cotizador_view.xml',
        'views/product_template_view.xml',
        'views/account_journal_view.xml',
        'views/account_journal_view.xml',
        'views/sequences.xml',
        'wizard/registra_pago.xml',
        'report/report.xml',
        'report/cotizacion_template.xml',
        'report/estado_cuenta_template.xml'
    ]
}