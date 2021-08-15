import os,tarfile

folder_name="2017-12-30->2018-01-05||afrinic.tal"

if __name__ == '__main__':
    dirlist=os.listdir(folder_name)
    for name in dirlist:
        if name=="result":
            continue
        print(name)
        t = tarfile.open(folder_name+'/'+name)
        
        t.extractall(folder_name+'/result')
    print("done!")