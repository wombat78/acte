#!/usr/bin/python


from Transcriber import *


if __name__== '__main__':
    uttlist=UttList()
    uttlist.Load('tmp/test-video2/audio.wav','./tmp/test-video2/segments.txt')

    U=uttlist.GetSublist(1:10)
    U.Print()
    print '----'
    U=uttlist.GetSublist(8:12)
    U.Print()

#rethink uttlist datastructure
