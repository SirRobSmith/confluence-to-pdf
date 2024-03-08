"""
Export a Confluence site to PDF
"""
import os
import csv
from pathlib import Path
from datetime import datetime
from atlassian import Confluence

op_user = os.environ['OP_USER']
op_pass = os.environ['OP_PASS']

now = datetime.now()
readableDate = now.strftime("%m/%d/%Y, %H:%M:%S")

# Edit these variables only
GOOGLE_DRIVE_BASE = "/your/location/"
CONFLUENCE_SERVER = "http://1.1.1.1:8090"

sites = { "SiteKey1", "SiteKey2", "SiteKey3"}

confluence = Confluence(
    url = CONFLUENCE_SERVER,
    username=op_user,
    password=op_pass)

def log_progress(log_message):
    """
    Log a message to a file
    :param log_message: the message to log
    """
    with open(f'{GOOGLE_DRIVE_BASE}pdf-export-log.log', "a", encoding="utf-8") as f:
        f.write(str(readableDate)+" | "+log_message+"\r\n")
        f.close()

def write_sites_done(site_name):
    """
    Log the given site as done
    :param site: name of the site which is done
    """
    with open(f'{GOOGLE_DRIVE_BASE}sites_done.csv', "a", encoding="utf-8") as sites_done:
        sites_done.write(f'{site_name},')
        sites_done.close()

def is_site_done(site_name):
    """
    Check if a site has been processed already
    :param site_name: site to check
    :return: True if the site has previously been completed, otherwise False
    """
    log_progress(f'- Checking to see if ({site_name}) has been completed.')

    with open(f'{GOOGLE_DRIVE_BASE}sites_done.csv', "r", encoding="utf-8") as sites_done:
        csv_reader = csv.reader(sites_done)
        for row in (csv_reader):
            if site_name == row[0]:
                log_progress(f'- ({site_name}) has been completed.')
                return True
            log_progress(f'- ({site_name}) has not been completed.')
            return False

# Create the PDF based on the data provided, file it in the appropriate folder
def create_pdf(page_id, title, save_path):
    """
    Create a PDF from the page and save it
    :param page_id: page for which to create the PDF
    :param save_path: path to save PDF
    """
    full_path = save_path + title + ".pdf"

    if os.path.isfile(full_path) is False:
        log_progress(f'Working on File ({full_path})')
        try:
            pdf_data = confluence.get_page_as_pdf(page_id)
        except Exception:
            log_progress(f'- ERROR PDF not created for file ({full_path})')
        else:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(pdf_data)
                f.close()
            log_progress(f'- File created ({full_path})')
    else:
        log_progress(f'- File found, skipping ({full_path})')

def download_attachment(page_id, save_path):
    """
    Download an attachment from the page and save it
    :param page_id: page from which to download attachments
    :param save_path: path to save attachments
    """
    try:
        attachments = confluence.download_attachments_from_page(page_id, path=save_path)
    except Exception:
        log_progress("-- Downloading attachments for this page failed.")
    else:
        log_progress("-- Downloaded attachments for this page")


def clean_string(string):
    """
    Clean non alphnumeric characters from a string
    :param string: string to be cleaned
    :return: cleaned string
    """
    return ''.join(letter for letter in string if letter.isalnum())

def export_pages(page_id, save_path):
    """
    Export the page and all children to PDF, saving in the given directory
    :param page_id: id of the page to export
    :param save_path: path to save the PDFs and attachments to
    """
    # Get the page data
    page_data = confluence.get_page_by_id(page_id, expand='children.page',
                                          status=None, version=None)

    # Export the page
    create_pdf(page_id, clean_string(page_data['title']), save_path)

    # Grab the attachments
    download_attachment(page_id, save_path)

    # Check for children
    for child in page_data['children']['page']['results']:
        export_pages(child['id'], save_path + clean_string(child['title']) + "/")

if __name__ == "__main__":
    log_progress("Tool Started")

    # Work through each site
    for site in sites:
        log_progress(f'- ({site}) selected')
        # Before we start, have we processed this site already?
        if is_site_done(site) is False:
            # We need a bit of code to deal with the pagination from Confluence,
            # These settings permit showing 2000 pages which exceeds the size
            # of the largest site we have.
            page_ids = []
            for i in range(20):
                # Establish the first item we request in the list
                apistartPoint = i * 100

                # Grab the first/next 100 pages
                pages = confluence.get_all_pages_from_space(site, start=apistartPoint,
                  limit=100, status=None,
                  expand="ancestors", content_type='page')

                # Cycle through the pages, save the ids to a sequence
                for page in pages:
                    if len(page['ancestors']) == 0:
                        page_ids.append(page['id'])

            # Now get the pages from Confluence and save them to the folder.
            for page in page_ids:
                log_progress(f'- Beginning work on ({site}) with root page ({page})')
                export_pages(page, f'{GOOGLE_DRIVE_BASE}{site}/')

    log_progress(f'- Site ({site}) complete')
    write_sites_done(site)
