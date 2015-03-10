#!/usr/bin/python
"""
 Wrapper for the abacus FTP upload service.`
Author: BP
  Date: Sun Mar  8 01:49:08 SGT 2015
"""

import os

from local import FTPSERVERIP
from local import FTPPORT
from local import USER
from local import PORT

from ftplib import FTP

def get_tag(fp):
    tag=os.path.basename(fp)
    i=tag.rfind('.')
    if i != -1:
        tag=tag[:i]
    return tag

def clean_result_line(line):
    words=line.strip().split()
    utt=words[0]
    transc=' '.join(words[1:])
    utt=os.path.basename(utt)
    return (utt,transc)

class AbacusFTP():
    "I wrap over an ftp service to interface to I2R's ASR offline testing"

    
    def addline(self,line):
        "helper function to append lines to the internal result object"
        if line.find('-----')!=-1:
            self.state+=1
            return
        if self.state==1:
            self.results.append(line)

    def __init__(self,username=USER,password=PORT):
        "initialize with the desired account info"
        self.username=username
        self.password=password

        self.curr_results=None
        self.results=[] # for retrieving results
        self.state=0

    # all of these functions take a full path as the input.

    def Upload(self,fp):
        "uploads a new zip packet"
        self.curr_results = None
        fn=os.path.basename(fp)
        ftp = FTP()
        ftp.connect(FTPSERVERIP,FTPPORT)
        ftp.login(self.username,self.password)
        ftp.cwd('upload')
        fobj=open(fn,'rb')
        ftp.storbinary('STOR %s' % fn,fobj)
        fobj.close()
        ftp.quit()

    def NewUpload(self,fp):
        "re-uploads a zip packet"
        print "Reuploading %s" % fp
        if self.IsResultReady(fp):
            print "deleting old result"
            self.ClearResult(fp)
        self.Upload(fp)

    def ClearResult(self,fp):
        "Clears an old result"
        self.curr_results=None
        tag=get_tag(fp)
        ftp = FTP()
        ftp.connect(FTPSERVERIP,FTPPORT)
        ftp.login(self.username,self.password)
        ftp.cwd('results/%s.result.txt' % tag)
        ftp.delete('result.txt')
        ftp.quit()

    def GetResult(self,fp):
        "Gets the decoding result, returning it as a list of tuples"
        " each tuple is an uttid followed by a string transcription."
        print "get %s" % fp
        if self.curr_results != None:
            print "returning cached results"
            return self.curr_results
        tag=get_tag(fp)
        ftp = FTP()
        ftp.connect(FTPSERVERIP,FTPPORT)
        ftp.login(self.username,self.password)
        ftp.cwd('results/%s.result.txt' % tag)
        self.results=[]
        self.state=0
        ftp.retrlines('RETR result.txt',self.addline)
    
        self.results=map(clean_result_line,self.results)
        self.curr_results=self.results
        print "retrieved"
        return self.results

    def IsResultReady(self,fp):
        "returns True if result is ready, false otherwise"
        try:
            self.p=self.GetResult(fp)
        except Exception as inst:
            print "except: ",inst
            return False
        print "ready!"
        return True
                



if 0: # example for uploading a test packet
    print "uploading"
    asr=ASROfflineService(USER,PASS)
    asr.Upload('human.zip')
    print "done"

if 0:
    asr=ASROfflineService(USER,PASS)
    result=asr.CheckResult('human.zip')
    for line in result:
        print line

if 0:
    asr=ASROfflineService(USER,PASS)
    if asr.IsResultReady('human2.zip'):
        result=asr.GetResult('human2.zip')
        for line in result:
            print line
    else:
        print "Result not ready"

if 0:
    asr=ASROfflineService(USER,PASS)
    asr.NewUpload('human.zip')



