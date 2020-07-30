import re
from datetime import datetime, timezone


# dt=datetime.now()
# print ("dt=", dt)



# text1 = '/donoff/h3/out/time_up'
# text1 = '/donoff/dmzk18/out/time_up'
# text1 = '/donoff/dmzk18/out/time_p'

text2='N:hotter=0'

text2='r1:off,lschm,off'
 
parser = re.match(r'^(.+):([^,]+),(.+)$',text2) #все кроме :

#parser = re.match('N:(.*)=(.+)',text2)


print(parser.group(1)+"..."+parser.group(2)+"..."+ parser.group(3)) if parser else print ('na') # 'abcdf'

# onoff=parser.group(2)

# res= re.match(r'^[oO][Nn]$', onoff)

# if res :
#     print ('on found')
# else:
#     print('on not found')


# res= re.match(r'^[oO][Ff][Ff]$', onoff)


# if res :
#     print ('off found')
# else:
#     print('off not found')