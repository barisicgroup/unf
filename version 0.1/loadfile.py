import json

f = open('C:/Development/unf/version 0.1/loop.json',) 
   
data = json.load(f) 

print(data['singleStrands']['1']['1'])


# Closing file 
f.close() 