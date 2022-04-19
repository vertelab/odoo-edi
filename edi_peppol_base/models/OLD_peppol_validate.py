"""
import sys
import os

sys.path.append("/home/bjornhayer/libsaxon-HEC-11.3/Saxon.C.API/python-saxon")
VALIDATE = True
try:
    import saxonc
except ImportError:
    VALIDATE = False


def validate_peppol (msg, type=None):
    if type is None:
        type = 'invoice'

    if type == 'invoice':
        validate_peppol_invoice(msg)

    return None


def validate_peppol_invoice (msg):
    if not VALIDATE:
        print("Validation was not performed as Saxon-c could not be importet. Is Saxon-C installed?")
        return False

    #msgName = msg.rsplit('/', 1)[-1].split('.')[0]
    msgName = os.path.basename(msg)

#Creation of validation reports
    with saxonc.PySaxonProcessor(license=False) as proc:
        print(proc.version)

        xslt30_processor = proc.new_xslt30_processor()
        #schema_validator = proc.new_schema_validator()

        xslt30_processor.set_cwd(".")

        out = xslt30_processor.transform_to_string(source_file=msg,
                                                   stylesheet_file="/usr/share/odoo-edi/edi_peppol_base/data/stylesheet-ubl.xslt")
        with open("/usr/share/odoo-edi/edi_peppol_base/data/temp/report-ubl-" + msgName + ".xml", "w") as f:
            f.write(out)


        out = xslt30_processor.transform_to_string(source_file="/usr/share/odoo-edi/edi_peppol_base/data/CEN-EN16931-UBL.sch",
                                                   stylesheet_file="/usr/share/odoo-edi/edi_peppol_base/data/iso_schematron_skeleton_for_saxon.xsl")
        with open("/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-TC434.xslt", "w") as f:
            f.write(out)

        xslt30_processor.transform_to_file(source_file=msg,
                                           stylesheet_file="/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-TC434.xslt",
                                           output_file="/usr/share/odoo-edi/edi_peppol_base/data/temp/report-TC434-" + msgName + ".xml")


        out = xslt30_processor.transform_to_string(source_file="/usr/share/odoo-edi/edi_peppol_base/data/PEPPOL-EN16931-UBL.sch",
                                                   stylesheet_file="/usr/share/odoo-edi/edi_peppol_base/data/iso_schematron_skeleton_for_saxon.xsl")
        with open("/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-PEPPOL.xslt", "w") as f:
            f.write(out)

        xslt30_processor.transform_to_file(source_file=msg,
                                           stylesheet_file="/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-PEPPOL.xslt",
                                           output_file="/usr/share/odoo-edi/edi_peppol_base/data/temp/report-PEPPOL-" + msgName + ".xml")

#Checking of validation reports contents

    validation_successfull = True

    if not validate_report_print("/usr/share/odoo-edi/edi_peppol_base/data/temp/report-TC434-" + msgName + ".xml", "TC434"):
        validation_successfull = False

    if not validate_report_print("/usr/share/odoo-edi/edi_peppol_base/data/temp/report-PEPPOL-" + msgName + ".xml", "PEPPOL"):
        validation_successfull = False



    validate_cleanup()

    if not validation_successfull:
        print("VALIDATION FAILED FOR: " + msg)
    else:
        print("VALIDATION SUCCESSFUL FOR: " + msg)
    

    return validation_successfull


def validate_report_print(schema, name):
    validation_successfull = True

    val = validate_report(schema)
    if val[0] != '':
        validation_successfull = False
        print('\n' + "Validation failed for " + name + ":")
        for n in val:
            print(n)

    return validation_successfull


def validate_cleanup(full=False):
    if full:
        os.remove("/usr/share/odoo-edi/edi_peppol_base/data/temp/*")
    else:
        os.remove("/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-TC434.xslt")
        os.remove("/usr/share/odoo-edi/edi_peppol_base/data/temp/stylesheet-PEPPOL.xslt")


def validate_report(report):
    with open(report) as f:
        lines = f.readlines()

    xml_string = '<?xml version="1.0" encoding="UTF-8"?>'

    lines[0] = lines[0].replace(xml_string,'')

    return lines
"""