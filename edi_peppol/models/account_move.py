import logging, traceback, subprocess
from multiprocessing import Process, queues
from odoo import models, api, _, fields

from lxml import etree, objectify
from lxml.etree import Element, SubElement, QName, tostring

_logger = logging.getLogger(__name__)


"""
The EDI PEPPOL modules are not feature-complete at this time.
The following is a list of further development which is judged to be the minimum needed steps
to make the EDI PEPPOL modules fit for purpose.

1.  Make the validation automated.
	Currently, the validation module does not function and is not automatically used.
  What it should do is to take a given XML, and then validate it per PEPPOL Schematron files,
   and then deliver a rapport to the user if this is done or not.
	It currently crashes Odoo when attempted to be run within Odoo,
   this appears to be due to unexplained memory problems related to the SaxonC library.
  This must be fixed.
	Currently, to validate an XML file, the validate_test.py program must be run, outside of Odoo,
   using the console.
  This program should be removed, when the peppol_validate.py file has been fixed.

2. Fill out existing invoice conversion.
  Fix all the 'simple' listed TODOs
	The Odoo-EDI workspace has been littered with many different TODO's of things that needs to be fixed.
  These range from some smaller, quicker fixes, to larger issues mentioned elsewhere on this list.
  All the smaller fixes should be gone through and fixed.

  2.1 Fill out the peppol_to_invoice so that all elements of PEPPOL are handled.
	  peppol_to_invoice, which is in charge of taking an Odoo Invoice and converting it to a PEPPOL XML invoice,
	   has a long list of comments in it, listing possible elements in PEPPOL
     which are currently not converted from Odoo to PEPPOL.
	  These need to be tracked down to where in Odoo relevant information exists and
     the comment turned into an appropriate 'convert_field()' function call.

  2.2 Fill out the peppol_from_invoice so that all elements of the XML are handled.
	  peppol_from_invoice currently does not handle every kind of element possible in PEPPOL.
    This needs to be corrected in lockstep with the additions in peppol_to_invoice,
     done during the previous step.

  2.3 Fix EndpointID, which may require adding new columns in tables, and connecting to the PEPPOL network.
	  EndpointID is an 'electronic address' used within PEPPOL, which identifies, in simplified terms,
     a 'post box number' to which messages can be delivered.
	  For peppol_to_invoice EndpointID exists once for the 'buyer' and once for the 'seller.
	  The buyer’s EndpointID is 'my' address, which is where any response to this invoice should be sent.
	  The seller's EndpointID is 'their' address, which is where this invoice should be sent.
	  This EndpointID needs to be found somehow. It should possibly become part of res.company and
     res.partner and be assumed to be communicated between the parties beforehand.
	  There is an official online directory to them at https://directory.peppol.eu. Unkown if it has an API.
	  In the above directory the types of PEPPOL messages which are supported are also listed.

  2.4 Edit Interface.
	  Currently, a large button will appear whenever an l10n_se invoice is viewed,
     or an incoming invoice is created. This should be changed to the desired UI solution.
	  When the PEPPOL message is to be sent, in step 4, further interface changes will likely be needed here.

3.  Other PEPPOL messages.
	Currently, only 'Invoice' messages are handled. However, there are other types of messages
   that PEPPOL can also handle, like Order, Order-response, price list and others.
	Judging by the https://directory.peppol.eu. the message types 'Invoice' and 'CreditNote'
   are the most common and ‘CreditNote’ should then be implemented next.
	These should all be implemented by creating two new modules,
   one being peppol_to_####  which inherits from peppol_to_peppol
   and the other being peppol_from_#### which inherits from peppol_from_peppol.
	Note that some functions currently in peppol_to_invoice and peppol_from_invoice
   can be found to be useful and should then be moved to peppol_*_peppol so the new modules can use them.
	The interface in edi_peppol will need to be updated so that this new message type is handled.
	The validation will need a new validation function for this new message type.
	edi_peppol will also have to inherent from both peppol_to_#### and peppol_from_####.

4.  Create a system to send/receive a PEPPOL message through the PEPPOL network.
	This step involves connecting Odoo to the PEPPOL network so that messages are not just converted
   from Odoo to PEPPOL (or visa versa), but are also sent on the PEPPOL network.
	There will likely have to be another company, one of the 'PEPPPOL access points' involved in this step.
	This step is the least researched and most unclear step, so no further guidance can be given.
  """





class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder", "peppol.frominvoice"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."

    # Button click function comming from Odoo.
    # TODO: Adjust the view for this button so it appears more appropriately.
    def to_peppol_button(self):
        return self.to_peppol()

    # Button click function comming from Odoo.
    # TODO: Adjust the view for this button so it appears more appropriately.
    def from_peppol_button(self):
        return self.from_peppol()

    # Converts a account.move to a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())

        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml',
                   xml_declaration=True,
                   encoding='UTF-8',
                   pretty_print=True)

        # TODO: Should be validating here, and display error and remove the created XML file if the validation failed!
        #self.validate('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')
        #self.validation_thread()
        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        # TODO: Add a popup for if the export to PEPPOL was succesfull.

    # Converts a account.move from a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def from_peppol(self):
        tree = self.parse_xml('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        if tree is None:
            return None

        # TODO: Should be validating here, and display error and abort if the validation failed!

        temp = self.import_invoice(tree)

        return temp

    # This is a debugging functions, which is intended to compare
    #  a invoice that is made into a PEPPOL and then back again,
    #  in its before and after states
    def compare_account_moves(self, to_peppol_id, from_peppol_id):
      to_dict = self.extra_account_move_info(to_peppol_id)
      from_dict = self.extra_account_move_info(from_peppol_id)

      for n in to_dict:
        text = f"{n}" + ": " + f"{to_dict[n]}" + " =/= " + f"{from_dict[n]}"
        if to_dict[n] != from_dict[n]:
          _logger.error(text)

    # Helper Function for debugging pruposes
    def extra_account_move_info(self, move_id):
      dict = {}
      move = self.env['account.move'].browse(move_id)
      ingore_list = ['<lamda>', '_ids', '_origin', '_prefetch_ids', 'access_token', 'access_url',
                     'create_date', 'date', 'display_name', 'id', 'ids', 'name', 'write_date',
                     'highest_name', 'show_reset_to_draft', 'state']
      for a in dir(move):
        if not callable(getattr(move,a)):
          if not a.startswith('__'):
            if a not in ingore_list:
              dict.update({a: getattr(move, a)})
      return dict

    # TODO: This function was a attempt to get Validate to work. It did not work. Unclear why it dosen't.
    # Validates a inputed PEPPOL 'file'
    def validate(self, file):
      p = Process(target=self.validation_thread, args=())
      p.start()
      _logger.warning("CONTINIUING IN VALIDATE!")

    # TODO: This function was a attempt to get Validate to work. It did not work. Unclear why it dosen't.
    def validation_thread(self):
      _logger.warning("TRYING TO START SUBPROCESS")
      s = subprocess.check_output(["python3", "/usr/share/odoo-edi/edi_peppol_validate/models/validate_test.py"])
      #s = subprocess.check_output(["echo", "THIS IS A ECHO!"])
      _logger.warning(f"{s=}")
      _logger.warning("FINISHED SUBPROCESS")
      #print("PRINT WORKS")