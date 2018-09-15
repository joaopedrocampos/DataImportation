# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Data Importation',
    'summary': "Importation of data files",
    'description': """
    This module creates the feature of custom importation for Odoo.

    Functionalities:
        - Imports a CSV file of sale orders in a default template.
    """,
    'version': '1.0.0',
    'category': 'Extra Tools',
    'author': 'João Pedro Campos',
    'license': 'AGPL-3',
    'website': 'https://github.com/joaopedro-campos',
    'contributors': [
        'João Pedro Campos'
    ],
    'depends': [
        'sale',
    ],
    'data': [
        'views/crm_sale_views.xml',
        'wizard/import_sale_orders.xml',
    ],
    'auto_install': False,
    'application': True,
}