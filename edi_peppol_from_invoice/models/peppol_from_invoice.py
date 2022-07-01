import logging, inspect, datetime
from cffi import VerificationError

from lxml import etree, objectify
from numpy import percentile

from odoo.exceptions import ValidationError
from odoo import models, api, _, fields
from odoorpc import ODOO

_logger = logging.getLogger(__name__)


# This class handles spesificly the conversion of a Odoo Invoice, to a PEPPOL Invoice.
class Peppol_From_Invoice(models.Model):
    _name = 'peppol.frominvoice'
    _inherit = 'peppol.frompeppol'
    _description = 'Module for importing invoices from PEPPOL to Odoo'

    #Base function for importing a Odoo Invoice, from a PEPPOL Invoice.
    def import_invoice(self, tree):
        # TODO: Clear out all currently existing information from the account.move,
        #       which the export is to create itself.
        #       As a stop-gap mesure it currently only removed all account.move.lines.
        #       If there was any non-line information in the Odoo invoice,
        #        which the PEPPOL invoice does NOT have, then the old Odoo invoice value
        #        may still remain, when it should not!
        self.clear_old_data()

        # Checks that this invoice has the users current company as the 'Customer'
        #  and that the information the invoice has and the database
        #  has about the own company are the same.
        missmached_info = self.is_company_info_correct(
                                    tree,
                                    self.company_id, #'account.move.company_id',
                                    xmlpath='/ubl:Invoice/cac:AccountingCustomerParty/cac:Party')
        if missmached_info is not None:
            raise ValidationError('The company this invoice is made out to, ' +
                                  'contains missmatch to the information your company has. \n' +
                                  'The missmatch was between: ' + '\n' +
                                  f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
                                  '\n' + 'And' + '\n' +
                                  f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')

        # Checks that this invoice has the same info about the 'Supplying' company
        #  as the database has.
        #  Also imports the 'Supplying' companies ID.
        new_partner_id = self.find_company_id(
                                    tree,
                                    xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if new_partner_id is None:
            _logger.error(inspect.currentframe().f_code.co_name +
                          ':Could not find the selling company: ' +
                          f"{tree.xpft(tree, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')}")
            raise ValidationError('This invoice is convering the company: ' +
                                  self.xpft(tree, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
                                  + '\n' + 'But no such company could found in the database.')
        self.partner_id = new_partner_id

        missmached_info  = self.is_company_info_correct(
                                    tree,
                                    self.partner_id,
                                    xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if missmached_info is not None:
            _logger.error(inspect.currentframe().f_code.co_name +
                          'Found discrepency between the data of the selling company in the invoice, '
                          + 'and the selling company in the database.')
            raise ValidationError('The company this invoice is from, ' +
                                  'contains missmatch to the information ' +
                                  'of said company in the database. \n' +
                                  'The missmatch was between: ' + '\n' +
                                  f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
                                  '\n' + 'And' + '\n' +
                                  f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')

        # Go through each element in the XML, and convert each piece of data into Odoo, one by one.
        # Any element on the ignore list, should be ignored if found in the XML.
        # Any element that is not converted, and not ingored, should be stored in a pair-list,
        #  containing the ignored element name and its value,
        #  which will be given to the user in a warning box, at the end.
        # TODO: The 'warning box' is currently only a log prinout. A later TO-DO notes where this
        #  should be corrected.
        delayed_list = []

        for element in tree.iter(tag="{" + self.nsmapf().cbc + "}*"):

            if self.import_simple(element):
                continue
            if self.import_complex(element):
                continue
            was_done, missed_lines = self.import_function(element)
            if was_done:
                if missed_lines is not None:
                    _logger.warning(f"{missed_lines=}")
                    delayed_list.extend(missed_lines)
                continue
            if self.invoice_ignore(element):
                continue

            delayed_list.append(element)

        # Adds/updates the '2440 Leverantörskuld' which balances the invoice,
        #  as well as the tax line due to 'True' being inputet.
        # _recompute_dynamic_lines is run twice, to ensure that the account validity is tested
        #  once all numbers have been generated.
        self.with_context({'check_move_validity': False})._recompute_dynamic_lines(True)
        self._recompute_dynamic_lines(True)

        skipped_list = []
        for element in delayed_list:
            was_found, missmached_info = self.check_dynamic_lines(element)
            if was_found:
                if missmached_info is not None:
                    _logger.error(inspect.currentframe().f_code.co_name + ': '
                                'Found a discrepency between the incomming Invoice, '
                                + 'and what Odoo dynamically generated.')
                    raise ValidationError( 'Found a discrepency between the incomming Invoice, '
                                        + 'and what Odoo dynamically generated.' + '\n' +
                                        'The missmatch was between: ' + '\n' +
                                        f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
                                        '\n' + 'And' + '\n' +
                                        f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')
                continue
            skipped_list.append([element, element.text])

        # Print a warning in the logs,
        #  if any line of the XML is not considered to have been 'handeled'
        # TODO: This is currently only written out in the logs. The list should be
        #  displayed to the user and the the created invoice should be removed!
        #  Alternatively the user given a question if they want the invoice to be created anyway,
        #  despite the non-handled lines.
        if len(skipped_list) != 0:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " +
                            "Be aware that the following tags where not converted " +
                            "from PEPPOL into Odoo:")
            ordered_list = ''
            for s in skipped_list:
                ordered_list = ordered_list + '\n' + self.get_full_parent_path(s[0]) + ": '" + s[1] + "'"

            _logger.warning(ordered_list)# + " with the value of: " + s[1])


    # This function should clear out 'self', which is to be a account.move,
    #  and clear out all data in it.
    # Currently, as a stop-gap messure, it removes all account.move.line.
    def clear_old_data(self):
        for line in self.line_ids:
            line.with_context({'check_move_validity': False}).unlink()

    ###############################################################################################
    # Help functions ##############################################################################
    ###############################################################################################

    # Builts and returns a string containing a elements name
    #  which is proceded by their parents and all ancestors, seperated by a '/'
    def get_full_parent_path(self, element):
        path = element.tag.split('}')[1]
        for e in element.iterancestors():
            path = e.tag.split('}')[1] + "/" + path
        return path

    # Returns true if a element is on either ignore lists, else returns false.
    def invoice_ignore(self, element):
        if self.ignore_simple(element):
            return True
        if self.ignore_complex(element):
            return True
        return False

    # A list of element names which should be ignored,
    #  along with a comment on why they are to be ignored.
    def ignore_simple(self, element):
        simple_ignore_list ={
            'CustomizationID', # Should not be convertet
            'ProfileID', # Should not be convertet
            'InvoiceTypeCode', # Should always be a invoice in this case, so ignore it.
                               # This is not directly checked anywhere though.
            #'BuyerReference', #TODO: Should possible be converted?
        }
        return element.tag.split('}')[1] in simple_ignore_list

    # A list of element+(grand)parent(s) names which should be ignored,
    #  along with a comment on why they are to be ignored.
    def ignore_complex(self, element):
        complex_ignore_list ={
            '/PartyLegalEntity/RegistrationName', # Is checked by is_company_info_correct(....)
            '/PartyTaxScheme/CompanyID', # Is checked by is_company_info_correct(....)
            '/EndpointID', # Is checked by is_company_info_correct(....)
                           # TODO: This assumed EndpointID is a VAT number,
                           #  this is not nessesarily true.
            '/Party/PostalAddress/', # Is checked by is_company_info_correct(....)
            '/Contact/Telephone', # Is checked by is_company_info_correct(....)
            '/Contact/ElectronicMail', # Is checked by is_company_info_correct(....)
            '/TaxScheme/ID', # Should allways be 'VAT' except for one case.
                             # TODO: Make an exception for that one case?
            '/DeliveryLocation/Address/', # Is ignored, due to this being a Invoice.

            # TODO: Write a more explicit test of TaxSubtotal
            'Invoice/TaxTotal/TaxSubtotal/', # Is effectively checked by check_dynamic_lines(..)
            'Invoice/InvoiceLine/' #All invoiceLine's are handeled seperately

        }
        return any(s in self.get_full_parent_path(element) for s in complex_ignore_list)

    # A list of invoice.line element names which should be ignored,
    #  along with a comment on why they are to be ignored.
    def invoiceline_ignore(self, element):
        ingore_list ={
            # Invoice/InvoiceLine/ID', # DO NOT INGORE THIS!
            #  ID should be let through, 'un-used', to aid with debugging of lines.
            #  If it is the only thing that was not ignored, it will not be displayed.

            'Invoice/InvoiceLine/LineExtensionAmount', # Is handeled by the is_product_info_correct(...)
            'Invoice/InvoiceLine/Item/ClassifiedTaxCategory/Percent', # Is handeled by the get_oddo_tax(..)
            'Invoice/InvoiceLine/Item/Name', # Is handeled by the is_product_info_correct(...)
            'Invoice/InvoiceLine/Item/Description', #Should not be checked
            'InvoiceLine/Item/ClassifiedTaxCategory/TaxScheme/ID', # Should allways be 'VAT' except for one case.
                                                                   # TODO: Make an exception for that one case?
        }
        return any(s in self.get_full_parent_path(element) for s in ingore_list)

    # Check if element name is in the internal dict,
    #  if so convert the elements value into the dict-assigned place in Odoo.
    def import_simple(self, element):
        simpledict = {
            'IssueDate': 'invoice_date',
            'DueDate': 'invoice_date_due'
        }

        try:
            nm = simpledict[element.tag.split('}')[1]]
        except:
            return False
        else:
            self[nm] = element.text
            return True

    # Check if element name+(grand)parent(s) is in the internal dict,
    #  if so convert the elements value into the dict-assigned place in Odoo.
    def import_complex(self, element):
        complexdict = {
            'Invoice/PaymentTerms/Note': 'narration',
            'Invoice/ID' : 'ref',
        }

        try:
            e = complexdict[self.get_full_parent_path(element)]
        except:
            return False
        else:
            self[e] = element.text
            return True

    # Check if element name+(grand)parent(s) is in the internal elif-'list',
    #  if so call a spesific function which converts that elements value into the correct place in Odoo.
    # The first return parameter returns True if a match was found, else False.
    # The second return parameter is used to indicate missed lines.
    def import_function(self, element):
        path = self.get_full_parent_path(element)
        if path == 'Invoice/InvoiceLine/ID':
            missed_lines = self.import_invoiceline(element)
            if len(missed_lines) == 1:
                missed_lines = None
            return True, missed_lines
        elif path == 'Invoice/DocumentCurrencyCode':
            self.currency_id = self.get_currency_by_name()
            return True, None

        return False, None

    # This function handles a invoice line, doing the creating of a new line,
    #  the filling it with data, imporing product data from the database
    #  and some checking that the values match up.
    # The return value is a list of pairs, containing the names and value
    #  of any XML element which was not handeled by this function.
    def import_invoiceline(self, element):
            missed_lines = []
            element = element.getparent()
            try:
                quantity = None
                unit_price = None
                sellers_item = None
                odoo_tax_id = None

                for ele in element.iter(tag="{" + self.nsmapf().cbc + "}*"):
                    full_path = self.get_full_parent_path(ele)
                    if full_path == 'Invoice/InvoiceLine/InvoicedQuantity':
                        quantity = float(ele.text)
                        continue
                    if full_path == 'Invoice/InvoiceLine/Price/PriceAmount':
                        unit_price = float(ele.text)
                        continue
                    if full_path == 'Invoice/InvoiceLine/Item/SellersItemIdentification/ID':
                        sellers_item = ele.text
                        continue
                    if full_path == 'Invoice/InvoiceLine/Item/ClassifiedTaxCategory/ID':
                        odoo_tax_id = self.get_oddo_tax(ele.getparent())
                        continue
                    if self.invoiceline_ignore(ele):
                        continue

                    missed_lines.append(ele)

                # TODO: Only products that have no variants are handled by this code.
                #  It should be changed to be able to handle products with multible variants.
                supplierinfo = self.env['product.supplierinfo'].search([
                                            ('name', '=', self.partner_id.id),
                                            ('product_code', '=', sellers_item)])
                product = self.env['product.product'].search([
                                        ('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id)])
                if len(product) == 0:
                    raise ValidationError('Could not find the item from the invoice ' +
                                        'in the products database.\n' +
                                        'Please ensure there the product with ' +
                                        'the sellers id of: ' +
                                        '\'' + f'{sellers_item}' + '\'' + '\n' +
                                        'Is buyable from the company: ' +
                                        f'{self.partner_id.name}')
                if len(product) > 1:
                    raise ValidationError('More then one products with ' +
                                        'the matching product code was found.' + '\n' +
                                        'Are varient products used? These are not yet handled.')

                # Creates the new line, with 'simple' fields filled in
                line = self.env['account.move.line'].with_context({'check_move_validity': False}).create(
                                                        {'move_id': self.id,
                                                        #TODO: For quantity:
                                                        # Add the 'type' of quantity.
                                                        # (For example: It coudl be 'hours',
                                                        #  or 'liters' or anything like that.)
                                                        'quantity': quantity,
                                                        'price_unit': supplierinfo.price,
                                                        #'tax_ids': odoo_tax_id,
                                                        #TODO: For account_id
                                                        # This is hard coded to be intra-sweden
                                                        #  item purchases. Should be made dynamic.
                                                        'account_id': 1253,
                                                        'recompute_tax_line': True,
                                                        'product_id': product.id
                                                        })
                # Imports item information from the database, relying on the 'product_id'.
                line.with_context({'check_move_validity': False})._onchange_product_id()
                line.price_unit = supplierinfo.price
                # Checks that there is no missmatch between what is in the database about a item
                #  and what is actually writen in the incomming invoice
                # TODO: Add a check that the VAT-taxes are the same in the database and the invoice!
                product_correct, missmached_info = self.is_product_info_correct(line, element)
                if not product_correct:
                    raise ValidationError('The product: ' + line.name +
                                        ' had a missmatch between the database, ' +
                                        'and the invoice. \n' +
                                        'The missmatch was between: ' + '\n' +
                                        f'{missmached_info[0][0]}' + ': ' + '\'' +
                                        f'{missmached_info[0][1]}' + '\'' +
                                        '\n' + 'And' + '\n' +
                                        f'{missmached_info[1][0]}' + ': ' + '\'' +
                                        f'{missmached_info[1][1]}' + '\'')
            except Exception as e:
                _logger.exception(e)
                raise
            else:
                return missed_lines

    # A helper function which checks that the dynamically created values in the lines,
    # matches up with the values in the XML Invoice.
    # If these don't match up, it probably indicates a missmatch between Odoo's database,
    #  and what the invoice expected it to be.
    def check_dynamic_lines(self, element):
        checkdict = {
            'Invoice/TaxTotal/TaxAmount': [True, 'amount_tax'],
            'Invoice/LegalMonetaryTotal/LineExtensionAmount': [False, 'get_line_extension_amount'],
            'Invoice/LegalMonetaryTotal/TaxExclusiveAmount': [True, 'amount_untaxed'],
            'Invoice/LegalMonetaryTotal/TaxInclusiveAmount': [True, 'amount_total'],
            'Invoice/LegalMonetaryTotal/PayableAmount': [True, 'amount_residual'],
        }

        try:
            nm = checkdict[self.get_full_parent_path(element)]
        except:
            #_logger.warning("Could not find in dict: " + self.get_full_parent_path(element))
            return False, None
        else:
            name = element.tag.split('}')[1]
            if nm[0]:
                db = str(self[nm[1]])
            else:
                db = str(getattr(self, nm[1])())
            xml = str(element.text)
            if str(db) == str(xml):
                return True, None
            else:
                return True, [['Database ' + name, '\'' + f"{db}" + '\''],
                              ['Invoice     ' + name, '\'' + f"{xml}" + '\'']]

    # Gets the tax id in Odoo, for a given XML item element.
    def get_oddo_tax(self, element):
        tax_type = self.xpft(element, './cbc:ID')
        tax_percent = self.xpft(element, './cbc:Percent')

        tax_name = self.translate_tax_category_from_peppol(tax_type, tax_percent)
        tax_id = self.env['account.tax'].search([('name', '=', tax_name)])

        try:
            return tax_id
        except:
            raise ValidationError('The tax with the name: ' + "'" + f"{tax_name}" + "' " +
                                  'could not be found in the database.')