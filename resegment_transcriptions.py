#!/bin/python

import argparse,sys,os,math

def load_segments(seg_fn,transc_fn):
    "reads in segments and transcriptions"
    segs={}; trans={}
    uttid_list=[]
    # read in the segments
    fin=open(seg_fn,'rt');
    for l in fin:
        uttid,wavid,st,et=l.strip().split()
        segs[uttid] = (float(st),float(et))
        uttid_list.append(uttid)
    fin.close()
    # read in corresponding transcriptions
    fin=open(transc_fn,'rt');
    for l in fin:
        parts=l.split() 
        uttid=parts[0]
        transcripts=' '.join(parts[1:])
        trans[uttid]=transcripts.strip()
    fin.close()
    # sanity check, make sure that segments and transcripts match
    if (trans.keys() != segs.keys()):
        print "Warning: mismatched segments and transcripts"
        os.exit(-1)
    # return a paired list
    segl=[]
    transl=[]
    for uttid in uttid_list:
        segl.append(segs[uttid])
        transl.append(trans[uttid])
    return wavid,segl,transl

def write_segments(fnroot,wavid,segments,trans):
    "writes segments and transcriptions to fnroot.segments and fnroot.txt"
    out_segments="%s.segments" % fnroot 
    out_trans="%s.text" % fnroot 
    fout=open(out_segments,'wt')
    fout2=open(out_trans,'wt')
    for i in range(len(segments)):
        uttid="%s.%03i" % (wavid,(i+1))
        st,et=segments[i]
        print >>fout,"%s %s %.3f %.3f" % (uttid,wavid,st,et)
        print >>fout2,"%s %s" % (uttid,trans[i])
    fout.close()

p=argparse.ArgumentParser("cleans up and resegments transcriptions so that they look 'sane'");
p.add_argument("src_segment");
p.add_argument("src_text");
p.add_argument("tgt");
args=p.parse_args(sys.argv[1:]);

def find_candidate(line,alpha=1.0):
    "returns an index between 0 and len(line) that is a good candidate for split"
    best_k=0
    best_score=-1
    for k in range(len(line)):
        score=0
        if line[k]!=' ': continue
        if k>0 and line[k-1] == '.': score=score+1 # prefer chopping at fstop
        if k>0 and line[k-1] == ',': score=score+0.5 # prefer chopping at comma
        score=score+alpha*(1.0-((math.fabs(len(line)/2-k))/len(line)/2))
        if score>best_score:
            best_score = score
            best_k = k
    return best_k


def resegment(segment,transcript,max_char=62):
    "resegment the segments and transcripts if they are too long"
    i=0;
    while i<len(segment):
        if len(transcript[i])>max_char:
            # find a good point to segment
            k=find_candidate(transcript[i])
            ctrans=transcript[i]
            cst,cet = segment[i]
            # compute time point interval
            ct=float(k)/len(ctrans)*cst+(1.0-float(k)/len(ctrans))*cet;
            
            ntrans1=ctrans[0:k] 
            ntrans2=ctrans[k+1:] 
            st1=cst
            et1=ct-0.001
            st2=ct+0.001
            et2=cet

            # insert a new fella
            ntrans=transcript[0:i]
            ntrans.append(ntrans1)
            ntrans.append(ntrans2)
            ntrans.extend(transcript[i+1:])
            transcript=ntrans

            nseg=segment[0:i]
            nseg.append((st1,et1))
            nseg.append((st2,et2))
            nseg.extend(segment[i+1:])
            segment=nseg
            print "breaking utt %i" % i 
        else:
            i=i+1

    return segment,transcript

        
# read in the segments
wavid,segments,transcripts=load_segments(args.src_segment,args.src_text)
segments,transcripts=resegment(segments,transcripts)

# write out processed segments
write_segments(args.tgt,wavid,segments,transcripts)

