import os
from mrtparse import Reader,MRT_T
from dump_form import BgpDump
import time
import copy

folder_name="2017-12-30->2018-01-05||afrinic.tal"
dirlist=os.listdir(folder_name)
i = 0
start_index=0
for name in dirlist:
    if name=="result":
        continue
    if i<start_index:
        i += 1
        continue
    path_to_file = str(folder_name) + "/" + str(name)
    path_to_write= str(folder_name) + "/" + str("result/") + str(name) + str(".txt")
    r = Reader(path_to_file)   
    count = 0
    print("starting %d"%(i))
    start_time=time.time()
    b = BgpDump(path_to_write)
    for m in r:
        print(m)
        if m.err:
            continue
        if m.data['type'][0] == MRT_T['TABLE_DUMP']:
            b.td(m.data, count)
        elif m.data['type'][0] == MRT_T['TABLE_DUMP_V2']:
            b.td_v2(m.data)
        elif m.data['type'][0] == MRT_T['BGP4MP']:
            b.bgp4mp(m.data, count)
        b.clear()
        count += 1
    b.close()
    end_time=time.time()
    print(end_time-start_time)
    print("finish %d / %d"%(i,len(dirlist)))
    i += 1

print("done!")

