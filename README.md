# **Purpose**

This project monitors updates to specific EZproxy stanza files published on OCUL’s website, based on the EZproxy configuration needs of Lakehead University Library.

OCUL maintains over 1,000 EZproxy stanzas, while Lakehead University Library only uses a limited subset.
Rather than scanning the entire OCUL stanza list, this tool focuses exclusively on checking updates for the stanzas that are actually in use, improving efficiency and reducing unnecessary load.


# **Project Files Overview**

## /data
### **mapping_source.csv**
Contains the original mapping data, including:
- EZproxy stanza filename (used locally)
- Corresponding stanza title as listed on the OCUL website

### **mapping.json**
A generated JSON file that defines the mapping relationship between local stanza filenames and OCUL stanza titles. This file is used by all update-checking scripts.

### **/stanzas** -ignored
Stores the EZproxy stanza files currently in use by Lakehead University Library.

### **/config** -ignored
Stores diff files generated from updates to `config.txt`, allowing version tracking and review of configuration changes.

### **/diff** -ignored
Stores diff files for stanza updates, showing differences between local and OCUL versions.

## /src
### **config.py**
Centralized configuration for:
- Project base directories
- Data and log paths
- OCUL URLs

### **logging_config.py**
Initializes Loguru logging configuration, including:
- Log file location
- Log rotation policy
- Log level

### **generate_mapping.py**
Generates mapping.json from mapping_source.csv, creating a structured mapping between local stanza filenames and OCUL stanza titles.

### **validate_mapping.py**
Validates whether each stanza title in mapping.json exists on the OCUL website.    
**_Note: This validation uses strict title matching._**    
Occasionally, OCUL may update or rename stanza titles (for example, University of Chicago Press Journals was later changed to University of Chicago Press), which may cause mismatches even though the stanza refers to the same resource.

### **update_stanza.py**
Checks whether any stanzas listed in mapping.json have been updated on the OCUL website after a specified date. By default, the comparison date is set to the current system date, but a custom date can be provided. **_This script is intended for manual or infrequent use (e.g. initial deployment or long gaps between checks)._**

### **most_recent_update_stanza.py**
Monitors only the “Recently updated database stanzas” section on OCUL’s website.
This approach:
- Avoids querying the full stanza list
- Reduces load on the OCUL site
- Minimizes the risk of page timeouts
- By default, the comparison date is set to the current system date
This script is recommended for regular (weekly) automated runs.

### **update_config_file.py**
Update the comment section in `config.txt` for reference.
E.g.:<br>
"# Knovel - last update 2021-05-21<br>
IncludeFile stanzas/knovel.txt"<br>
→<br>
"# Knovel - last update 2026-04-21<br>
IncludeFile stanzas/knovel.txt"

### **organize_config_file.py**  
Organizes the `IncludeFile` sections in `config.txt`. The following two sections are sorted independently in A–Z order based on filename:<br><br>

#------------ Start of IncludeFile - Custom Stanzas ------------#<br>
A to Z based on filename<br>
#------------ End of IncludeFile - Custom Stanzas ------------#<br><br>

#------------ Start of IncludeFile - OCLC ------------#<br>
A to Z based on filename<br>
#------------ End of IncludeFile - OCLC ------------#

### **diff_stanza.py**
Handles difference between local version and updated version. Save .diff file to /data/diff.   

### **send_email.py**
Handles email notifications.
- Email credentials are managed via environment variables
- Gmail App Password is required (available after enabling 2-step verification)

### **main.py**
The primary entry point for scheduled execution. Runs the **most recent update check** with retry logic, logging, and email notifications.

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
4. Initial Update Check:
    cd /path/to/ezproxy-stanza-sync    
    uv run -m src.update_stanza    
5. Schedule with Cron:     
    Edit cron jobs:   
        crontab -e   
    Example (run every Monday at 2am):   
        0 2 * * 1 cd /path/to/ezproxy-stanza-sync && uv run -m src.main >> logs/stanza.log 2>&1    


# **Scope and Limitations**
1. This tool only checks EZproxy stanzas that exist on the OCUL website.
2. Custom EZproxy stanzas created specifically by Lakehead University Library are not included, as there is no corresponding OCUL reference for comparison.
3. The tool does not automatically download or deploy updated stanzas. It only identifies updates and provides relevant links for review.
5. most_recent_update_stanza.py is recommended for regular monitoring. If there has been a long gap between checks or significant changes are suspected, run update_stanza.py manually before resuming scheduled checks.