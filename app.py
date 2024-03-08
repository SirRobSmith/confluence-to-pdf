from atlassian import Confluence
import os
import json
import csv
import pprint
from pathlib import Path
from datetime import datetime


opUser = os.environ['OP_USER']
opPass = os.environ['OP_PASS']

now = datetime.now()
readableDate = now.strftime("%m/%d/%Y, %H:%M:%S")

# Edit these variables only
googleDriveBase = "/your/location"
confluenceServer = "http://1.1.1.1:8090"

sites = { "SiteKey1", "SiteKey2", "SiteKey3"}

confluence = Confluence(
    url=confluenceServer,
    username=opUser,
    password=opPass)

# Define a very simple logging function
def logProgress(logMessage):
    f = open(googleDriveBase+"pdf-export-log.log", "a")
    f.write(str(readableDate)+" | "+logMessage+"\r\n")
    f.close()

# Simple writing of completed sites
def writeSitesDone(site):
    sitesDone = open(googleDriveBase+"sites_done.csv", "a")
    sitesDone.write(site+",")
    sitesDone.close()

def isSiteDone(site):
    
    logProgress("- Checking to see if ("+site+") has been complete.")

    with open(googleDriveBase+"sites_done.csv", "r") as sites:
        csv_reader = csv.reader(sites)
        for row in (csv_reader):

            if(site == row[0]):
                logProgress("- ("+site+") has been completed.")
                return True
            else:
                logProgress("- ("+site+") has not been complete.")
                return False



# Create the PDF based on the data provided, file it in the appropriate folder
def createPDF(pageId, title, savePath):

    fullPath = savePath+title+".pdf"

    if(os.path.isfile(fullPath) == False):
        logProgress("Working on File ("+fullPath+")")
        try:
            pdfData = confluence.export_page(pageId)
        except:
            logProgress("- ERROR PDF not created for file ("+fullPath+")")
        else:
            Path(savePath).mkdir(parents=True, exist_ok=True)
            f = open(fullPath, "wb")
            f.write(pdfData)
            f.close()
            logProgress("- File created ("+fullPath+")")
    else:
        logProgress("- File found, skipping ("+fullPath+")")

# Download the attachment, file it in the appropriate folder
def downloadAttachment(pageId, savePath):

    try:
        getAttachments = confluence.download_attachments_from_page(pageId, path=savePath)
    except:
        logProgress("-- Downloading attachments for this page failed.")
    else:
        logProgress("-- Downloaded attachments for this page")


def cleanString(string):
    returnVar = ''.join(letter for letter in string if letter.isalnum())
    return returnVar

def getPages(pageId, savePath):

    # Get the page data
    pageData = confluence.get_page_by_id(pageId, expand='children.page', status=None, version=None)

    # Export the page
    createPDF(pageId, cleanString(pageData['title']), savePath)

    # Grab the attachments
    downloadAttachment(pageId, savePath)

    # Check for children
    for child in pageData['children']['page']['results']:

        getPages(child['id'], savePath+cleanString(child['title'])+"/")

logProgress("Tool Started")

# Work through each site
for site in sites:

    logProgress("- ("+site+") selected")


    # Before we start, have we processed this site already?
    if(isSiteDone(site) == False):

        # We need a bit of code to deal with the pagination from Confluence, these settings permit showing 2000 pages. Which exceeds the size of the largest site we have. 
        pageIds = list()
        for i in range(20):

            # Establish the first item we request in the list
            apistartPoint = i * 100

            # Grab the first/next 100 pages
            pages = confluence.get_all_pages_from_space(site, start=apistartPoint, limit=100, status=None, expand="ancestors", content_type='page')

            # Cycle through the pages, save the Ids to a dict()
            for page in pages:

                if(len(page['ancestors']) == 0):

                    pageIds.append(page['id'])

        for page in pageIds:

            logProgress("- Beginning work on ("+site+") with root page ("+page+")")
            getPages(page, googleDriveBase+site+"/")

logProgress("- Site ("+site+") complete")
writeSitesDone(site)
