# -*- coding: utf-8 -*-
##############################################################################
########## OVERVIEW ####################
# This module, along with the other PEPPOL modules, are intended to allow a user to send and receive
#  PEPPOL financial messages using the l10n_se accounting module.
# These messages would be in the PEPPOL message format and sent via the PEPPOL-network.
# The current state of the modules is not complete and is addressing only converting to and from
#  PEPPOL for invoice type-of-messages, and even that has significant limitations,
#  with the steps which are estimated to need to be taken to remove these limitations listed below in the FUTURE DEVELOPMENT section.
# Note that these modules assume that ESAP 2.1 is used and that any user of this software is following it strictly,
#  in that they are keeping their partners, and their partners are keeping them fully up to date with any company, product, or price information.
# To read about ESAP 2.1 refer to here: https://gs1.se/wp-content/uploads/sites/2/2020/07/processdescription-esap-20.1-v1.7.pdf
# To read about PEPPOL invoices refer to here: https://docs.peppol.eu/poacc/billing/3.0/bis/
# To read about the elements of PEPPOL invoices, refer to here: https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/tree/
# To see the 'structure' of the existing modules, refer to this image: static/doc/PEPPOL_Class_Diagram.v2.png

########## HOW TO USE ##################
# To test the current modules you will need two databases, on the same virtual machine,
#  one for the 'sender'(seller/supplier) and one for the 'receiver'(buyer) of an invoice.

# Go to the sender database, install the EDI Peppol module, which should install the l10n_se and accounting modules too.
# Go into 'frakturering' and create a new 'kundfakturor' invoice.
# For an example of a invoice refer to: static/doc/Invoice.pdf
# Note that the company you are logged into the database as,
#  must be the same as the company which is supposed to be the 'seller' on the invoice.
# Click the 'Export to PEPPOL' button which should appear on the 'button bar' at the top,
#  to the far left. This will create/overwrite the XML file at edi_peppol/demo/output.xml.

# To validate the XML (which is not done automatically currently (read in FUTURE DEVELOPMENT on why)),
#  run the edi_peppol_validate/module/validate_test.py in the console with 'python3' command.
# This should spit out a small rapport if the validation was successful or a longer one if it failed.
# The raport will note what went wrong with the invoice if the validation failed.
# Correct the invoice, export it again, and run the validation again.
# Do not proceed to the next step, without a successful validation.

# Go to the receiver database, install the EDI Peppol module, which should install the l10n_se and accounting modules too.
# Fill out the database partner, and products so that the (sellers) partner information is the same as on the invoice.
# The product information must also be the same, with the partners id for a product being listed for them,
#  in the 'supplier', section of said products.
# Go into 'frakturering' and create a new 'leverantörsfakturor' invoice.
# Note that the company you are logged into the database as,
#  must be the same as the company which is supposed to be the 'buyer' on the invoice.
# Click the 'Import from PEPPOL' button which should appear on the 'button bar' at the top, to the far left.
# This should take the ouput.xml file and import it into the invoice you are currently looking at.
# If any error about mismatch is encountered at this stage,
#  ensure that the product/company information match between the two databases.
# The error message should tell you what specifically went wrong.
# Then attempt to import again.


########## FUTURE DEVELOPMENT ##########
# The EDI PEPPOL modules are not feature-complete at this time.
# The following is a list of further development which is judged to be the minimum needed steps
#  to make the EDI PEPPOL modules fit for purpose.

# 1.  Make the validation automated.
#	    Currently, the validation module does not function and is not automatically used.
#     What it should do is to take a given XML, and then validate it per PEPPOL Schematron files,
#      and then deliver a rapport to the user if this is done or not.
#     It currently crashes Odoo when attempted to be run within Odoo,
#      this appears to be due to unexplained memory problems related to the SaxonC library.
#     This must be fixed.
#     Currently, to validate an XML file, the validate_test.py program must be run, outside of Odoo,
#      using the console.
#     This program should be removed, when the peppol_validate.py file has been fixed.

# 2.  Fill out existing invoice conversion.
#     Fix all the 'simple' listed TODOs
#	    The Odoo-EDI workspace has been littered with many different TODO's of things that needs to be fixed.
#     These range from some smaller, quicker fixes, to larger issues mentioned elsewhere on this list.
#     All the smaller fixes should be gone through and fixed.

#     2.1 Fill out the peppol_to_invoice so that all elements of PEPPOL are handled.
#	        peppol_to_invoice, which is in charge of taking an Odoo Invoice and converting it to a PEPPOL XML invoice,
#	         has a long list of comments in it, listing possible elements in PEPPOL
#          which are currently not converted from Odoo to PEPPOL.
#	        These need to be tracked down to where in Odoo relevant information exists and
#          the comment turned into an appropriate 'convert_field()' function call.

#     2.2 Fill out the peppol_from_invoice so that all elements of the XML are handled.
#	        peppol_from_invoice currently does not handle every kind of element possible in PEPPOL.
#         This needs to be corrected in lockstep with the additions in peppol_to_invoice,
#          done during the previous step.
#
#     2.3 Fix EndpointID, which may require adding new columns in tables, and connecting to the PEPPOL network.
#         EndpointID is an 'electronic address' used within PEPPOL, which identifies, in simplified terms,
#          a 'post box number' to which messages can be delivered.
#         For peppol_to_invoice EndpointID exists once for the 'buyer' and once for the 'seller'.
#         The buyer’s EndpointID is 'my' address, which is where any response to this invoice should be sent.
#         The seller's EndpointID is 'their' address, which is where this invoice should be sent.
#         This EndpointID needs to be found somehow. It should possibly become part of res.company and
#          res.partner and be assumed to be communicated between the parties beforehand.
#         There is an official online directory to them at https://directory.peppol.eu. Unkown if it has an API.
#         In the above directory the types of PEPPOL messages which are supported are also listed.

#      2.4 Edit Interface.
#         Currently, a large button will appear whenever an l10n_se invoice is viewed,
#          or an incoming invoice is created. This should be changed to the desired UI solution.
#         When the PEPPOL message is to be sent, in step 4, further interface changes will likely be needed here.

#     2.5 Make less strict ESAP 2.1 adherence.
#         This step is optional, but current the modules are extremely strict that the information
#          between the invoice and the information in the database is strict, and if so much as the
#          phone number to the 'ourselves' on the invoice does not match, then the entire import
#          process will be aborted. Or if an item doesn't exactly appear as expected, it will fail.
#         Some user-friendliness might wish to be added here,
#          to ask what the user wants to do for a particular mismatch, rather than aborting everything.

#     2.6 Language conversion.
#         Currently the module is entierly in english.
#         There aught to be added to-swedish translation for all parts of it.

# 3.  Other PEPPOL messages.
#	    Currently, only 'Invoice' messages are handled. However, there are other types of messages
#      that PEPPOL can also handle, like Order, Order-response, price list and others.
#	    Judging by the https://directory.peppol.eu. the message types 'Invoice' and 'CreditNote'
#      are the most common and ‘CreditNote’ should then be implemented next.
#	    These should all be implemented by creating two new modules,
#      one being peppol_to_####  which inherits from peppol_to_peppol
#      and the other being peppol_from_#### which inherits from peppol_from_peppol.
#     Note that some functions currently in peppol_to_invoice and peppol_from_invoice
#      can be found to be useful and should then be moved to peppol_*_peppol so the new modules can use them.
#	    The interface in edi_peppol will need to be updated so that this new message type is handled.
#	    The validation will need a new validation function for this new message type.
#	     edi_peppol will also have to inherent from both peppol_to_#### and peppol_from_####.

# 4.  Create a system to send/receive a PEPPOL message through the PEPPOL network.
#	    This step involves connecting Odoo to the PEPPOL network so that messages are not just converted
#      from Odoo to PEPPOL (or visa versa), but are also sent on the PEPPOL network.
#	    There will likely have to be another company, one of the 'PEPPPOL access points' involved in this step.
#	    This step is the least researched and most unclear step, so no further guidance can be given.
##############################################################################


# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Enterprise Management Solution, third party addon
#    Copyright (C) 2014-2022 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'EDI PEPPOL',
    'summary': 'Module for sending and reciving PEPPOL',
    'author': 'Vertel AB',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'category': 'Accounting',
    'version': '14.0.0.0.0',
    # Version ledger: 14.0 = Odoo version. 1 = Major. Non regressionable code. 2 = Minor. New features that are regressionable. 3 = Bug fixes
    'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-edi/edi_peppol/',
    'description': """
        Implements a Framework for PEPPOL communication in Odoo.
        14.0.0.0.0 - Initial version
    """,
    'depends': ['base',
                'l10n_se',
                'purchase',
                'edi_peppol_validate',
                'edi_peppol_to_invoice',
                'edi_peppol_to_order',
                'edi_peppol_from_invoice'],
    'data': ['views/account_invoice_view.xml',
             'views/peppol_wizard_form.xml',
             'security/ir.model.access.csv',
             ],
    'installable': 'True',
    'application': 'False',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
