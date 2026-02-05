# **Purpose**

This project is developed to monitor updates for specific EZproxy stanza files published on OCUL’s website, based on Lakehead University Library’s EZproxy configuration needs.

OCUL maintains over 300 EZproxy stanzas, while Lakehead University Library only uses a subset of them. This tool focuses exclusively on checking updates for the stanzas that are actually in use, rather than scanning the entire OCUL list.


# **Project Files Overview**

### **mapping_source.csv**
Contains the original mapping data, including:
- EZproxy stanza filename (used locally)
- Corresponding stanza title as listed on the OCUL website

### **generate_mapping.py**
Generates mapping.json from mapping_source.csv, creating a structured mapping between local stanza filenames and OCUL stanza titles.

### **validate_mapping.py**
Validates whether each stanza title in mapping.json exists on the OCUL website.

**_Note: This validation uses strict title matching._**
Occasionally, OCUL may update or rename stanza titles (for example, University of Chicago Press Journals was later changed to University of Chicago Press), which may cause mismatches even though the stanza refers to the same resource.

### **update_stanza.py**
Checks whether any stanzas listed in mapping.json have been updated on the OCUL website after a specified date.
- By default, the comparison date is set to the current system date
- A custom date can be provided for testing or historical checks

# **Scope and Limitations**
- This tool only checks stanzas that exist on the OCUL website.
- Custom EZproxy stanzas created specifically by Lakehead University Library are not included, since there is no corresponding reference on OCUL’s website for comparison.
- The script does not attempt to automatically download or deploy updated stanzas; it only identifies updated resources and outputs their associated links for further action.
