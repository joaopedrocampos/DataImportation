# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import pytz
import csv
import base64
import tempfile
import datetime

class ImportSaleOrders(models.Model):
    _name = 'import.sale.orders'

    type_importation = fields.Selection([('sale_orders', 'Sale Orders')], string="Importation Type", required=True)
    file = fields.Binary(string="Importation File", required=True)

    def validation_line(self, line, n_line):

        msg_error = []

        if not line['Cliente']:
            msg_error.append(_('Error on line %s: Field CNPJ/CPF is empty.') % n_line)

        if not line['Data']:
            msg_error.append(_('Error on line %s: Field Data is empty.') % n_line)
        else:
            self.validate_date(line['Data'], msg_error)

        if not line['Produto']:
            msg_error.append(_('Error on line %s: Field Produto is empty.') % n_line)

        if not line['Quantidade']:
            msg_error.append(_('Error on line %s: Field Quantidade is empty.') % n_line)
        else:
            try:
                float(line['Quantidade'])
            except:
                msg_error.append(_('Error on line %s: Field Quantidade is not an Integer.') % n_line)

        if not line['Preco Unitario']:
            msg_error.append(_('Error on line %s: Field Preco Unitario is empty.') % n_line)
        else:
            try:
                float(line['Preco Unitario'])
            except:
                msg_error.append(_('Error on line %s: Field Preco Unitario is not an Float.') % n_line)

        if not line['Medidas']:
            msg_error.append(_('Error on line %s: Field Medidas is empty.') % n_line)
        # if not line['Observacoes']:
        #     msg_error.append(_('Error on line %s: Field Observacoes is empty.') % n_line)

        return msg_error

    def validation_field(self, line):
        msg_error = []

        if 'Cliente' not in line:
            msg_error.append(_('Field Cliente not found!'))
        if 'Data' not in line:
            msg_error.append(_('Field Data not found!'))
        if 'Produto' not in line:
            msg_error.append(_('Field Produto not found!'))
        if 'Quantidade' not in line:
            msg_error.append(_('Field Quantidade not found!'))
        if 'Preco Unitario' not in line:
            msg_error.append(_('Field Preco Unitario not found!'))
        if 'Medidas' not in line:
            msg_error.append(_('Field Medidas not found!'))
        if 'Observacoes' not in line:
            msg_error.append(_('Field Observacoes not found!'))

        return msg_error

    def validate_date(self, date_str, msg_error):
        try:
            datetime.datetime.strptime(date_str, '%d/%m/%Y')
        except:
            msg_error.append(_('Invalid date!'))

        return msg_error

    def import_file(self):
        arq = base64.decodestring(self.file)

        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(arq)
        temp.close()

        with open(temp.name, 'r') as csvfile:
            csv_lines = csv.DictReader(csvfile, delimiter=';', lineterminator='\n')

            if self.type_importation == 'sale_orders':
                msg_error = []
                n_line = 1
                for line in csv_lines:
                    n_line += 1
                    validation_field = self.validation_field(line)
                    if validation_field:
                        msg_main = _('Problem with identifying line:\n\n')
                        for msg in validation_field:
                            msg_main += '- %s\n' % msg
                        raise ValidationError(msg_main)

                    validation = self.validation_line(line, n_line)
                    if validation:
                        for msg in validation:
                            msg_error.append(msg)
                        continue

                    customer_id = self.env['res.partner'].search([('cnpj_cpf', '=', line['Cliente'])])
                    if not customer_id:
                        msg_error.append(_('Error on line %s: Customer with the CNPJ/CPF %s is not registered.')
                                         % (n_line, line['Cliente']))
                        continue

                    product_id = self.env['product.template'].search([('name', '=', line['Produto'])])
                    if not product_id:
                        msg_error.append(_('Error on line %s: Product not registered.') % n_line)
                        continue
                    elif len(product_id) > 1:
                        msg_error.append(_('Error on line %s: There are more than one Product with the same name.')
                                         % n_line)
                        continue

                    confirm_date = datetime.datetime.strptime(line['Data'], u'%d/%m/%Y').replace(hour=12)

                    addr = customer_id.address_get(['delivery', 'invoice'])

                    observacoes = ""
                    if 'Observacoes' in line:
                        if line['Observacoes']:
                            observacoes = line['Observacoes']

                    vals_order = {
                        'partner_id': customer_id.id,
                        'pricelist_id': customer_id.property_product_pricelist and customer_id.property_product_pricelist.id or False,
                        'payment_term_id': customer_id.property_payment_term_id and customer_id.property_payment_term_id.id or False,
                        'partner_invoice_id': addr['invoice'],
                        'partner_shipping_id': addr['delivery'],
                        'user_id': customer_id.user_id.id or self.env.uid,
                        'state': 'sale',
                        'confirmation_date': confirm_date,
                        'note': observacoes
                    }

                    sale_order_id = self.env['sale.order'].create(vals_order)

                    vals_line = {
                        'order_id': sale_order_id.id,
                        'product_id': product_id.id,
                        'price_unit': line['Preco Unitario'],
                        'product_uom_qty': line['Quantidade'],
                        'product_uom': product_id.uom_id.id,
                        'band_type': 'normal',
                        'accordion_type': 'without_accordion',
                        'bags_per_package_qtd': 1,
                        'microsoft_weight': 1,
                        'product_type': 'Normal',
                        'liters_qtd': 1,
                        'customer_product_code': 123,
                        'measures': line['Medidas'],

                    }

                    self.env['sale.order.line'].create(vals_line)

        if msg_error:
            msgs = ''

            for msg in msg_error:
                msgs += '- %s\n' % msg

            error_id = self.env['import.sale.orders.error'].create({'errors': msgs})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'import.sale.orders.error',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': error_id.id,
                'views': [(False, 'form')],
                'target': 'new',
                'nodestroy': True,
            }

        return True

class ImportSaleOrdersError(models.Model):
    _name = "import.sale.orders.error"

    errors = fields.Text(string="Errors", readonly=True)
