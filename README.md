# odoo-edi
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)


EDI-modules |Description
--- | --- 
 edi_route                 | Main module for communication services and routing. Adds generic routes, envelopes and messages for EDI usage
 edi_route_ftp| Sftp and FTP communication server. Requires python libraries paramiko and pycrypto
 edi_route_mail | Mail communation server, ties an email address to a route
 edi_route_[purchase,sale,sale_stock,stock]| Catches and ties signals to routing
 edi_gs1| Implements GS1 (Global Standard 1) and EDIFACT. ESAP20-routing and mapping to Odoo-classes. Messages: ORDERS, CONTRL, ORDRSP, DESADV, INVOIC
 edi_gs1_[ica,axfood,coop,bergendahls]| Implements special handling of these parties
 edi_peppol| Implements PEPPOL, Pan-European Public Procurement On-Line
 
 Other modules |Description
 --- | ---
 account_invoice_credit_reason|Adds a credit reason selection to invoice. The reason codes conform to the ESAP20 EDI specification.
 sale_purchase|Implements a link between the sales and purchase management applications
 portal_edi|This module adds edi rights for suppliers for portal use
 
