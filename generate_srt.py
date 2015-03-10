#!/usr/bin/python
"""
   Generates an SRT file given segmentation file and transcripts.
"""

LOC='tmp3/test-video/'

segmentation='tmp3/test-video/segments.txt'
transcripts='tmp3/test-video/transcript.txt'
outputs_srt='tmp3/test-video/audio.srt'

def LoadTranscripts(fn):
    "loads transcriptions into a map"
    transcriptions={}
    fin=open(fn,'rt')
    for line in fin:
        words=line.strip().split()
        uttid=words[0]
        transc=' '.join(words[1:])
        transcriptions[uttid]=transc
    fin.close()
    return transcriptions


def LoadSegments(segfn):
    fin=open(segfn,'rt')
    seg={}
    for line in fin:
        uttid,wavid,st,et=line.strip().split()
        seg[uttid]=(float(st),float(et))
    fin.close()
    return seg

def hmsd(seconds):
    h=int(seconds/3600.0)
    seconds=seconds-h*3600
    m=int(seconds/60.0)
    seconds=seconds-m*60
    s=int(seconds)
    d=int(1000.0*(seconds-s))
    return "%i:%02i:%02i,%03i" % (h,m,s,d)

def GenerateSRT(output,segmentation,transcripts):
    fout=open(outputs_srt,'wt')	
    seg=LoadSegments(segmentation)
    transc=LoadTranscripts(transcripts)
    
    def cmp_flt(a,b):
        return (int(1000*(seg[a][0]-seg[b][0])))
    utt_sequence=seg.keys()
    utt_sequence.sort(cmp=cmp_flt)

    frame_no = 1
    for utt in utt_sequence:
        print >>fout,"%i" % frame_no
        print >>fout,"%s --> %s" % (hmsd(seg[utt][0]),hmsd(seg[utt][1]))
        print >>fout,"%s" % transc[utt]
        print >>fout
        frame_no = frame_no+1

    fout.close()

if __name__=='__main__':
    GenerateSRT(outputs_srt,segmentation,transcripts)

