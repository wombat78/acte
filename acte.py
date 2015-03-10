#!/usr/bin/python

import time,thread,os,sys
from Transcriber import *

# configuration variables
INDIR  = "incoming/"
TMPDIR = "tmp/"
OUTDIR = "outgoing/"

# globals
verbose=True
debug=False

# helper functions
def strip_extension(fn):
    "strips off filename extensions."
    i=fn.rfind('.')
    if i!=-1: return fn[:i]
    return fn

def mkpath(fullpath):
    """mkpath(fullpath) - creates directories to make fullpath valid
Inputs: a fully qualified path to a file, or if ending with '/', a directory 
Returns: None
    """
    segs = fullpath.split('/')
    if len(segs)<=1: return
    del segs[-1];
    if len(segs)<=1: return

    # repeatedly build up the path
    if segs[0] == '': cpath=''
    elif segs[0][1] == ':':
        cpath = segs[0]
        del segs[0]
    else: cpath = os.getcwd();

    while len(segs)>0:
        cpath = cpath+'/'+segs[0]; del segs[0]
        # create if it is not there.
        try:
            x = os.stat(cpath)
        except:
            os.mkdir(cpath)

def exec_cmd(shell_cmd):
    "executes a shell command, returning the exit code"
    if verbose: "  exec: %s" % shell_cmd
    result=os.system(shell_cmd)
    return result

# data structure for managing requested transcriptions

class ChunkedUtteranceInfo():
    "information about a chunked utterance"
    def __init__(self,uttname,wavfp,st,et):
        self.uttname=uttname
        self.wavfp=wavfp
        self.st = float(st)
        self.et = float(et)

    def ExtractToWav(self,fp):
        "extracts this utterance to a .wav file"
        cmd='sox %s trim %.3f =%.3f' % (self.wavfp,self.st,self.et)
        exec_cmd(cmd)

class ChunkedSet:
    # a set of post-chunking utterances
    
    class Iterator:
        "Iterator for a chunked set"
        def __init__(self,cset):
            self.cset = cset
            self.cset_list = cset.keys()
            self.cset_list.sort()
            self.current = 0

        def next(self):
            if self.current>=len(self.cset_list):
                raise StopIteration
            else:
                self.current += 1
                return self.cset[self.cset_list[self.current]]


    def __init__(self,tagname=''):
        "constructs a set of utterances for a given tag"
        self.tagname=tagname
        self.set = {}

    def Load(self,wavfp,segmentfp):
        "loads chunked set from a segment file"
        fin=open(segmentfp,'rt')
        for line in fin:
            (uttname,tag,st,et)=line.strip().split()
            self.Add(uttname,wavfp,st,et)
        fin.close() 

    def Add(self,uttname,wavfp,start_time,end_time):
        self.set[uttname] = ChunkedUtteranceInfo(uttname,wavfp,start_time,end_time)

    def Remove(self,uttname):
        self.set.erase(uttname)

class TaskManager:
        
    def __init__(self):
        pass

# Main functions
def ConvertMp4To16kHzWav(infn,wavfn,tag):
    #  - TO FIX no ffmpeg installed
    #cmd='ffmpeg -i %s -vn -acodec pcm_s16le -ar 16000 -ac 1 %s' %\
    #    (infn,wavfn)
    #os.system(cmd)
    os.system("cp out.wav %s" % wavfn) # HACK
    return True

def SegmentAudio(wavfn,segmentsfn,tag):
    "create a scp file for compute-vad to use"
    scpfn=os.path.join(TMPDIR,tag,'wav.scp')
    fout=open(scpfn,'wt')
    print >>fout, "%s %s" % (tag,wavfn)
    fout.close()
    #
    cmd='/home/bplim/Work/acte/bin/compute-vad scp:%s | grep -v \'creating vad\' > %s' % (scpfn,segmentsfn)
    errcode=exec_cmd(cmd)
    return errcode==0

utt_queue=[]
def ProcessIncomingFile(fn):
    "process incoming video files by extracting the audio, then doing"
    "segmentation"
    # figure out path names
    tag=strip_extension(os.path.basename(fn))
    
    tmp_wavfn=os.path.join(TMPDIR,tag,"audio.wav")
    tmp_segmentation=os.path.join(TMPDIR,tag,"segments.txt")

    # create tmp directory
    mkpath(tmp_wavfn)

    # convert audio and segment
    ConvertMp4To16kHzWav(fn,tmp_wavfn,tag)
    SegmentAudio(tmp_wavfn,tmp_segmentation,tag)

    # queue utterances for processing
    new_utts=ChunkedSet()
    new_utts.Load(tmp_wavfn,tmp_segmentation)

    for utt in new_utts.set.keys():
        utt_queue.append(new_utts.set[utt])
    #cmd='bin/compute-vad %s' %\


def ScanIncomingDirectory():
    "monitors incoming directories for videos"
    if verbose: print "Scanning ..  %s" % INDIR
    for root,dirs,files in os.walk(INDIR):
        for fn in files:
            fp = os.path.join(root,fn)
            if fn[-4:]=='.mp4': 
                ProcessIncomingFile(fp)

def LoadConfiguration():
    pass 

def DistributeTasks():
    return True

def CheckForCompleteTranscription():
    "Checks that complete transcription including .srt file is ready"
    return False

##
#  Main program
##
ScanIncomingDirectory()
print utt_queue


#LoadConfiguration()
while True:
    ScanIncomingDirectory()
    DistributeTasks()
    CheckForCompleteTranscription()
    time.sleep(60)
