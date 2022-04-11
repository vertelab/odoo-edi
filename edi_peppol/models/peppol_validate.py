import sys
import os

#sys.path.append("/usr/lib")
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

    msgName = msg.rsplit('/', 1)[-1].split('.')[0]

#Creation of validation reports
    with saxonc.PySaxonProcessor(license=False) as proc:
        print(proc.version)

        xslt30_processor = proc.new_xslt30_processor()
        #schema_validator = proc.new_schema_validator()

        xslt30_processor.set_cwd(".")

        out = xslt30_processor.transform_to_string(source_file=msg,
                                                   stylesheet_file="../data/stylesheet-ubl.xslt")
        with open("../data/temp/report-ubl-" + msgName + ".xml", "w") as f:
            f.write(out)


        out = xslt30_processor.transform_to_string(source_file="../data/CEN-EN16931-UBL.sch",
                                                   stylesheet_file="../data/iso_schematron_skeleton_for_saxon.xsl")
        with open("../data/temp/stylesheet-TC434.xslt", "w") as f:
            f.write(out)

        xslt30_processor.transform_to_file(source_file=msg,
                                           stylesheet_file="../data/temp/stylesheet-TC434.xslt",
                                           output_file="../data/temp/report-TC434-" + msgName + ".xml")


        out = xslt30_processor.transform_to_string(source_file="../data/PEPPOL-EN16931-UBL.sch",
                                                   stylesheet_file="../data/iso_schematron_skeleton_for_saxon.xsl")
        with open("../data/temp/stylesheet-PEPPOL.xslt", "w") as f:
            f.write(out)

        xslt30_processor.transform_to_file(source_file=msg,
                                           stylesheet_file="../data/temp/stylesheet-PEPPOL.xslt",
                                           output_file="../data/temp/report-PEPPOL-" + msgName + ".xml")




#Checking of validation reports contents

    validationSuccessfull = True

    if not validate_report_print("../data/temp/report-TC434-" + msgName + ".xml", "TC434"):
        validationSuccessfull = False

    if not validate_report_print("../data/temp/report-PEPPOL-" + msgName + ".xml", "PEPPOL"):
        validationSuccessfull = False



    validate_cleanup()

    if not validationSuccessfull:
        print("VALIDATION FAILED FOR: " + msg)
    else:
        print("VALIDATION SUCCESSFUL FOR: " + msg)
    

    return validationSuccessfull




def validate_report_print(schema, name):
    validationSuccessfull = True

    val = validate_report(schema)
    if val[0] != '':
        validationSuccessfull = False
        print('\n' + "Validation failed for " + name + ":")
        for n in val:
            print(n)

    return validationSuccessfull



def validate_cleanup(full=False):
    if full:
        os.remove("../data/temp/*")
    else:
        os.remove("../data/temp/stylesheet-TC434.xslt")
        os.remove("../data/temp/stylesheet-PEPPOL.xslt")



def validate_report(report):
    with open(report) as f:
        lines = f.readlines()

    xmlString = '<?xml version="1.0" encoding="UTF-8"?>'

    lines[0] = lines[0].replace(xmlString,'')

    return lines