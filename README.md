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

### **most_recent_update_stanza.py**
Monitors only the recently updated database stanzas from OCUL’s website to efficiently detect changes without querying the full stanza list, reducing load and avoiding page timeouts.
- Automatically sends email alerts when updates are found
- Email configuration is managed through environment variables
- Gmail app password is required (available after enabling 2-step verification)


# **How it works**
1. Install uv (Python environment manager),and restart terminal after installation.
2. Setup Python Environment
    - Clone the repository:
        git clone https://github.com/lu-library/ezproxy-stanza-sync
        cd /path/to/repo
    - Sync environment and dependencies:
        uv sync
    This will:
        - Install Python 3.10 (if not present)
        - Create a virtual environment
        - Install required packages
3. Email Notification Setup, email credentials are stored using environment variables:
    Add to ~/.bashrc or ~/.profile:
        export EMAIL_SENDER="your_email@gmail.com"
        export EMAIL_RECEIVER="receiver_email@gmail.com"
        export EMAIL_PASSWORD="your_app_password"
    Reload:
        source ~/.bashrc
    _Gmail app password can be generated after enabling 2-step verification._
4. Schedule with Cron:
    Edit cron jobs:
        crontab -e
    Example (run every Monday at 2am):
        0 2 * * 1 cd /path/to/repo && uv run most_recent_update_stanza.py >> stanza.log 2>&1


# **Scope and Limitations**
- This tool only checks stanzas that exist on the OCUL website.
- Custom EZproxy stanzas created specifically by Lakehead University Library are not included, since there is no corresponding reference on OCUL’s website for comparison.
- The script does not attempt to automatically download or deploy updated stanzas; it only identifies updated resources and outputs their associated links for further action.
- most_recent_update_stanza.py is recommended for regular check-ups since update_stanza.py will check from all stanza page, which loads way more slower. However, if there's a change or a big gap between check-ups, please run update_stanza.py first.
