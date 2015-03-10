#!/usr/bin/python

import sys,functools,os,time

class UttInfo:
    "Maintains information about an utterance"
    def __init__(self, wav_fp='', uttid='', start_time=0, end_time=0, transcription=''):
        
        self.wav_fp = wav_fp        # full path to wav file
        self.start_time = start_time       # start time for utterance
        self.end_time = end_time         # end time for utterance
        self.transcription = transcription     # speech transcription
        self.uttid=uttid

    def ParseSegmentation(self,line):
        "parses a segmentation file, and returns the utterance id"
        " returns None if fails"
        uttid,wavid,st,et = line.strip().split()
        self.uttid=uttid
        self.start_time = float(st)
        self.end_time = float(et)
        return uttid

    def ExtractToWav(self,outwavfp):
        cmd="sox %s %s trim %.3f =%.3f " % (self.wav_fp,outwavfp,self.start_time,self.end_time)
        os.system(cmd)

    def Print(self,fout=sys.stdout):
        "Prints out information about this utterance to screen"
        print >>fout, "%s -- [%s]: %s" % (self.wav_fp,self.uttid,self.transcription)
        print >>fout, "  from: %s (%.3f-%.3f)" % (self.wav_fp,self.start_time,self.end_time)

class UttList:
    "I represent a list of utterances"
    def __init__(self):
        self.utts = {}

    # iterator interface for an utterance list
    class Iterator():
        def __init__(self,uttlist):
            self.i=0
            self.uttlist=uttlist
            self.uttlist_keys = uttlist.utts.keys()
            self.uttlist_keys.sort()
        
        def next(self):
            if self.i>=len(self.uttlist_keys):
                raise StopIteration
            else:
                self.i+=1
                return self.uttlist.utts[self.uttlist_keys[self.i-1]]

    def __iter__(self):
        return UttList.Iterator(self)

    def __getitem__(self,k):
        uttkeys = self.utts.keys()
        uttkeys.sort()
        return map(lambda(x): self.utts[x],uttkeys[k])
    
    def Add(self,utt):
        # utt is UtteranceInfo
        self.utts[utt.uttid] = utt
    
    def Load(self,wav_fp,segments_fn,transcription_fn=''):
        "loads segment information into this utterance list"
        if segments_fn != '':
            fin=open(segments_fn,'rt')
            self.ReadSegments(fin,wav_fp)
            fin.close()
        if transcription_fn!= '':
            fin=open(transcription_fn,'rt')
            self.ReadTranscriptions(fin)
            fin.close()
    
    def ReadSegments(self,segments_fp,wav_fp=''):
        for line in segments_fp:
            utt=UttInfo(wav_fp)
            uttid=utt.ParseSegmentation(line)
            self.Add(utt)

    def ReadTranscriptions(self,transc_fp,wav_fp=''):
        for line in transc_fp:
            words=line.strip().split()
            uttid=words[0]
            transc=' '.join(words[1:])
            if uttid in utt:
                uttid[uttid].transcription=transc

    def GetSublist(self,indices):
        new_uttlist=UttList()
        for i in indices:
            new_uttlist.Add(self[i])
        return new_uttlist
    
    def Print(self):
        for uttid in self.utts:
            print "%s - " % uttid,
            self.utts[uttid].Print()

class Transcriber:
    "I represent a transcriber, I can asynchronously provide transcriptions"
    
    def __init__(self):  
        "create "
        self.notifier=None
        self.available=True
        pass

    # Interfaces
    def Available(self):
        "returns True if the transcriber is not occupied at the moment"
        return self.available

    def Poll(self):
        ""
        if self.available: return False
        if self.IsTranscriptionReady():
            print "transcription ready"
            self.Notify(self.GetTranscription())
            return True
        return False

    def Notify(self,uttlist):
        "notifies that the transcriptions are done"
        if self.available: return False
        print "sending notification"
        if self.notifier != None: 
            print "notifier present, sending"
            self.notifier(uttlist)
        self.available=True
        return True

    def RequestTranscription(self,uttlist,notifier=None):
        "request that the transcriber transcribe a list of utterances"
        " returns True if accepted, False if not"
        " when the transcription is completed, the notifier is called"
        if not self.available: return False
        self.notifier=notifier
        res =self.requestTranscription(uttlist)
        if res: self.available=False
        return res

    def GetTranscription(self):
        return self.getTranscription()

    def IsTranscriptionReady(self):
        return self.isTranscriptionReady()


from AbacusFTP import AbacusFTP
class AbacusTranscriber(Transcriber):
    "I interface with Abacus, treating it as if it were a real transcriber"

    def __init__(self,email=''):
        Transcriber.__init__(self)
        self.ftp=AbacusFTP()
        self.available=True
        self.currfn=''

    def isTranscriptionReady(self):
        return self.ftp.IsResultReady(self.currfn)

    def requestTranscription(self,uttlist):
        # create a zipped packet with this uttlist
        tmpdir='abacus/'
        zipfn='abacus.zip'
        # mkpath(tmpdir)
        for utt in uttlist:
            tmpfp=os.path.join(tmpdir,utt.uttid+'.wav')
            utt.ExtractToWav(tmpfp)
            print tmpfp
        fout=open(os.path.join(tmpdir,"transcript.txt"),'wt')
        for utt in uttlist:
            print >>fout,"%s %s" % (utt.uttid,utt.transcription)
        fout.close()

        # make a zip file
        cmd='zip -r %s %s' % (zipfn,tmpdir)
        os.system(cmd)

        # upload the data
        self.ftp.NewUpload(zipfn)
        self.currfn=zipfn
        print "request complete"
        return True
        
    def getTranscription(self):
        return self.ftp.GetResult(self.currfn)



    
class HumanTranscriber(Transcriber):
    
    def __init__(self,email=''):
        Transcriber.__init__(self)
        self.notification_type = 'email'
        self.email=email
        self.available=True

    def Available(self):
        if self.email == '': return False
        return self.available

    def requestTranscription(self,uttlist):
        # create a zipped packet with this uttlist
        tmpdir='abacus/'
        zipfn='abacus.zip'

        if os.path.exists(zipfn):
            os.unlink(zipfn)
        if os.path.exists(tmpdir):
            os.unlink(tmpdir)
        # mkpath(tmpdir)
        for utt in uttlist[0:10]:
            tmpfp=os.path.join(tmpdir,utt.uttid+'.wav')
            utt.ExtractToWav(tmpfp)
            print tmpfp
        fout=open(os.path.join(tmpdir,"transcript.txt"),'wt')
        for utt in uttlist:
            print >>fout,"%s %s" % (utt.uttid,utt.transcription)
        fout.close()

        # make a zip file
        cmd='zip -r %s %s' % (zipfn,tmpdir)
        os.system(cmd)
 
        # TODO - send out the email attachement to human
        

        #self.notifyHuman()

        #print "requesting" ,notifier
        uttlist.Print()
        pass
        
if __name__=='__main__':

    # main program
    fin=False
    def notification(uttlist):
        global fin
        print "NOTIFIED"
        fin=True

    uttlist=UttList()
    uttlist.Load('tmp/test-video2/audio.wav','./tmp/test-video2/segments.txt')

    mt = AbacusTranscriber()
    print "requesting for transcription:"
    mt.RequestTranscription(uttlist,notification)

    print "polling for result"
    while not fin:
        print "poll!"
        mt.Poll()
        time.sleep(5)
    print "finished"
    sys.exit()

