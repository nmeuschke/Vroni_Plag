# -*- coding: utf-8 -*-
#Don't think this file can be run here so download it along with the chromedriver ( and the pdf for testing)
#Make sure the following libraries are installed using pip
from bs4 import BeautifulSoup
import urllib2, requests
import time, sys
from selenium import webdriver
import os, sys
import argparse

chromedriver = "./chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver

URL = 'http://de.vroniplag.wikia.com/'
Soup = lambda x: BeautifulSoup(x, 'html.parser')

#get all texts with that are not black in font-colour 
def getplagtags(url):
    soup = Soup(gethtml(url))
    frgtab = soup.find('table', attrs={'class': 'ueberpruefte-fragmentseiten'})
    frgs = [e['href'] for e in frgtab.findAll('a') if e['href'] and 'Seite nicht vorhanden' not in e['title']]

    lst = []
    driver = webdriver.Chrome(chromedriver)
    for frg in frgs:
        driver.get(URL + frg[1:])
        for tag in driver.find_element_by_id('frag-0-0').find_elements_by_css_selector('[class^=fragmark]'):
            lst.append([tag.get_attribute('class'), tag.text])
    driver.quit()
    return lst

#create an xml text with starting positions of each plagiarism section and length
def crtxml(cd, lst):
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <document xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.uni-weimar.de/medien/webis/research/corpora/pan-pc-09/document.xsd" reference="suspicious-document00001.txt">
      <feature name="vroniplag" etext_number="''' + cd + '''" url="http://de.vroniplag.wikia.com/wiki/''' + cd + ''''"/>
      <feature name="language" value="de" />
    ''' + '\n'.join(['<feature name="artificial-plagiarism" this_offset="' + str(ls[1]) + '" this_length="' + str(ls[2]) + '" />' for ls in lst]) + '\n</document>'

#read each web page and return the html text
def gethtml(link):
    time.sleep(2)
    req = urllib2.Request(link, headers={'User-Agent': "Magic Browser"})
    con = urllib2.urlopen(req)
    html = con.read()
    return html

#convert the pdf to text
def getmetadata(filename):
    if not filename.endswith('.pdf'):
        sys.exit(filename + ' is not pdf')
    url = "http://pdfx.cs.man.ac.uk"
    try:
        fin = open(filename, 'rb')
        files = {'file': fin}
    except IOError:
        sys.exit("Error reading file!!")
    try:
        print ('Sending %s to %s' % (filename, url))
        r = requests.post(url, files=files, headers={'Content-Type': 'application/pdf'})
        print ('Got status code %d for %s' % (r.status_code, filename))
    except:
        sys.exit("Probable internet disruption. Try Again!!!")
    finally:
        fin.close()
    xml = r.content
    return xml

#convert html to text
def getcont(xml):
    soup = Soup(xml)
    paratags = soup.findAll("region", attrs={"class": "DoCO:TextChunk"})
    paras = '\n\n'.join([tag.text for tag in paratags])
    return paras

#put all functions in order
def txt2pdf(nm):
    cd = nm[:-4]
    content = getcont(getmetadata(nm)).encode('utf-8') #write 
    with open(cd + '.txt', 'wb') as outtxt: #writes pdf text to file
        outtxt.write(content)
    url = URL + cd
    print url
    plagsecs = getplagtags(url) #get all plagiarsed sections
    offslst = []
    for sec in plagsecs: #each section is searched in the text of the pdf
        ind = content.find(sec[1].encode('utf-8'))
        leng = len(sec[1])
        if ind != -1 and leng != 0:
            offslst.append([obf, ind, leng])
    with open(cd + '.xml', 'wb') as outxml: #write xml to text
        outxml.write(crtxml(cd, offslst))

#main function to read arguments from the command line
def Main():
    parser = argparse.ArgumentParser(description='Vroni Downloader')
    parser.add_argument('pdf', type=str, help='PDF to operate on')
    args = parser.parse_args()
    pdf = args.pdf
    if '.pdf' in pdf:
        txt2pdf(pdf)
    else:
        sys.exit("Unrecognised file format!!")


if __name__ == '__main__':
	Main()
