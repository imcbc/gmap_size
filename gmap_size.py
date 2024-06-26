"""
File:   gmap_size.py
Author: CBC
Date:   2024.04.27

This tool would be work with GNU map file(Generated by GCC with -Wl,-Map option),
and parser the given section names and counting the size in:
  - total text, data, bss
  - each object file's total text, data, bss
  - each object file's symbol type and size

Normally the usage would be 

python gmap_size.py -i {.map file} -t .text,.vectors -d .rodata,.data -b .bss,.stack,.heap --detail

For the case STM32:

python gmap_size.py -i {.map file} -t .isr_vector,.text,.init -d .rodata,.data,.ARM,.ARM.exidx,.init_array,.fini_array -b .bss,._user_heap_stack --detail
"""

import sys
import re
import logging
import argparse


def print_db(db):
    for l in db:
        out_str = "{:<60}{:<16}{:<16}{}".format(l[0], hex(int(str(l[1]))), hex(int(str(l[2]))), l[3][-100:])
        logging.info(out_str)


parser = argparse.ArgumentParser()
parser.add_argument('-i',     type=str,                                 help = 'Input map file')
parser.add_argument('-v',     action='store_true',   default = False,   help = 'Verbose mode')
parser.add_argument('-t',     dest='text', type=str, default = '',      help = 'Text sections list, seperate with comma')
parser.add_argument('--text', dest='text', type=str, default = '',      help = 'Same as -t')
parser.add_argument('-d',     dest='data', type=str, default = '',      help = 'Data sections list, seperate with comma')
parser.add_argument('--data', dest='data', type=str, default = '',      help = 'Same as -d')
parser.add_argument('-b',     dest='bss',  type=str, default = '',      help = 'Bss sections list, seperate with comma')
parser.add_argument('--bss',  dest='bss',  type=str, default = '',      help = 'Same as -b')
parser.add_argument('--ignore', type=str,            default = '',      help = 'Ignore sections list, sperate with comma')
parser.add_argument('--detail', action='store_true', default = False,   help = 'Report symbol usage in detail')

args = parser.parse_args()

if args.v == True:
    verbose_level = logging.DEBUG
else:
    verbose_level = logging.ERROR


param_map    = args.i
param_text   = args.text #'.text;.vectors;.rst_hdl;.rodata'
param_data   = args.data #'.data;.tcmd_list'
param_bss    = args.bss  #'.bss;.stack;.reclaim;.heap'
param_ignore = args.ignore #'.ARM.attributes'

ignore_gap_size = 256

list_text   = param_text.strip(',').split(',')
list_data   = param_data.strip(',').split(',')
list_bss    = param_bss.strip(',').split(',')
list_ignore = param_ignore.strip(',').split(',')


if '.fini' not in param_text:
    list_text += ['fini']

if 'COMMON' not in param_bss:
    list_bss += ['COMMON']

if '.ARM.attributes' not in param_ignore:
    list_ignore += ['.ARM.attributes']

logging.basicConfig(level=verbose_level, stream=sys.stdout, format='%(message)s')

start_mark = 'Linker script and memory map'
end_mark = 'OUTPUT('

fd = open(param_map, 'r')
fd_in = fd.readlines()
fd.close()

lk_map = []

a,b=0,0
for l in fd_in:
    l = l.strip()
    if l == start_mark:
        a = 1
        continue
    if a == 1:
        if end_mark in l:
            break
        if l != '' and len(l) > 2:
            if 'load address' in l:
                continue
            lk_map += [l]
        
    
pattern1     = r"^0x([0-9A-Fa-f]+)\s+0x([0-9A-Fa-f]+)\s+([\w.\-/\\():]+)"    
pattern2     = r"([\w.]+)\s+0x([0-9A-Fa-f]+)\s+0x([0-9A-Fa-f]+)\s+([\w.\-/\\():]+)"    
pattern3     = r"(\*fill\*)\s+0x([0-9A-Fa-f]+)\s+0x([0-9A-Fa-f]+)"
pattern_name = r'\(([^)\s]*\.o)\)'

cnt = 0
sec_db = []
last_valid_name = ''
#print("----- Level1 DB Parsing-----")
for l in lk_map:
    result  = re.findall(pattern1, l)
    result2 = re.findall(pattern2, l)
    result3 = re.findall(pattern3, l)
    if len(result) > 0:
        if result[0][1] != '0':
            #print('1 '+ str(result))
            try:
                addr = int(result[0][0], 16)
                size = int(result[0][1], 16)
            except:
                print("Error can not convert string to hex", result)
                sys.exit(-1)
            
            result_name = re.findall(pattern_name, result[0][2])
            if len(result_name) > 0:
                objname = result_name[0]
            else:
                objname = result[0][2]
            sec_db += [[lk_map[cnt - 1], addr, size, objname]]
            last_valid_name = result[0][2]
    if len(result2) > 0:
        if result2[0][2] != '0':
            #print('2 '+ str(result2))
            try:
                addr = int(result2[0][1], 16)
                size = int(result2[0][2], 16)
            except:
                print("Error can not convert string to hex", result)
                sys.exit(-1)
            
            result_name = re.findall(pattern_name, result2[0][3])
            if len(result_name) > 0:
                objname = result_name[0]
            else:
                objname = result2[0][3]
            
            sec_db += [[result2[0][0], addr, size, objname]]
            last_valid_name = result2[0][3]
    if len(result3) > 0:
        if result3[0][2] != '0':
            #print('3 '+ str(result3))
            try:
                addr = int(result3[0][1], 16)
                size = int(result3[0][2], 16)
            except:
                print("Error can not convert string to hex", result)
                sys.exit(-1)
            
            result_name = re.findall(pattern_name, last_valid_name)
            if len(result_name) > 0:
                objname = result_name[0]
            else:
                objname = last_valid_name
            
            sec_db += [['*fill*', addr, size, objname]]
    cnt += 1

sec_db.sort(key = lambda x:x[1])

logging.info("\r\n\r\n----- Level1 DB -----")
print_db(sec_db)

#check gap
idx = 0
sec_db2 = []
total_gap = 0
overlap_size = 0
for l in sec_db:
    if idx == 0:
        idx += 1
        lsect, laddr, lsize, lfname = l
        continue

    sect,addr,size,fname = l

    if addr == (laddr + lsize):
        pass
    elif addr > (laddr + lsize):
        gap = addr - (laddr + lsize)
        if gap >= ignore_gap_size:
            pass
        else:
            lsize += gap
            total_gap += gap
    elif addr < (laddr + lsize):
        if addr == laddr:
            if (addr + size) > (laddr + lsize):
                lsize = size
        else:
            if (addr + size) > (laddr + lsize):
                ovlp = (laddr + lsize) - addr
                overlap_size += ovlp
                lsize += ((addr + size) - (laddr + lsize))
        continue
    sec_db2 += [[lsect, laddr, lsize, lfname]]
    lsect, laddr, lsize, lfname = sect, addr, size, fname

sec_db2 += [[lsect, laddr, lsize, lfname]]

logging.debug("\r\n\r\n----- Level2 DB -----")
print_db(sec_db2)


idx = 0
for l in sec_db2:
    if idx == 0:
        idx += 1
        lsect, laddr, lsize, lfname = l
        continue
    sect,addr,size,fname = l    
    if addr == (laddr + lsize):
        pass
    elif addr > (laddr + lsize):
        gap = addr - (laddr + lsize)
        if gap >= ignore_gap_size:
            pass
        else:
            print("!!!Gap")
            print(hex(addr),">",hex(laddr+lsize))
            print("Last line:", sec_db2[idx-1])
            print("Current Line:",l)
    elif addr < (laddr + lsize):
        print("!!!!Overlap")
    lsect, laddr, lsize, lfname = l
    idx += 1

logging.debug(">>Merged Gap Size = " + str(total_gap))
logging.debug(">>Overlap Size = " +  str(overlap_size))


#processing all symbols to count size
total_text,  total_data, total_bss = 0, 0, 0
last_type = 0
last_obj = '._i_g_n_o_r_e_.'
obj_text_db = {}
obj_data_db = {}
obj_bss_db = {}
sec_db3 = []
for i in range(len(sec_db2)):
    l = sec_db2[i]
    sect, addr, size, obj = l
    #print('Processing ', l)
    ignore_flag = 0
    for s in list_ignore:
        if s == '':
            continue
        if sect in s or s in sect:
            ignore_flag = 1
            last_type = 0
            last_obj = '._i_g_n_o_r_e_.'
            #print('Ignore')
            break
    if ignore_flag == 1:
        continue
    
    if sect == '*fill*':
        if last_type == 0:
            #ignroe type
            continue
        elif last_type == 1:
            #print('fill add to text')
            if last_obj in obj_text_db.keys():
                obj_text_db[last_obj] += size
            else:
                obj_text_db[last_obj] = size
            sec_db3 += [['text', sect, addr, size, obj]]
            total_text += size
        elif last_type == 2:
            #print('fill add to data')
            if last_obj in obj_data_db.keys():
                obj_data_db[last_obj] += size
            else:
                obj_data_db[last_obj] = size
            sec_db3 += [['data', sect, addr, size, obj]]
            total_data += size
        elif last_type == 3:
            #print('fill add to bss')
            if last_obj in obj_bss_db.keys():
                obj_bss_db[last_obj] += size
            else:
                obj_bss_db[last_obj] = size
            sec_db3 += [['bss', sect, addr, size, obj]]
            total_bss += size
        continue

    match_flag = 0
    
    for s in list_text:
        if s == '':
            continue
        if sect in s or s in sect:
            match_flag = 1
            total_text += size
            if obj in obj_text_db.keys():
                obj_text_db[obj] += size
            else:
                obj_text_db[obj] = size
            last_type = 1
            last_obj = obj
            sec_db3 += [['text', sect, addr, size, obj]]
            #print('fill add to text')
            break
    if match_flag == 1:
        continue

    for s in list_data:
        if s == '':
            continue
        if sect in s or s in sect:
            match_flag = 1
            total_data += size
            if obj in obj_data_db.keys():
                obj_data_db[obj] += size
            else:
                obj_data_db[obj] = size
            last_type = 2
            last_obj = obj
            sec_db3 += [['data', sect, addr, size, obj]]
            #print('fill add to data')
            break
    if match_flag == 1:
        continue

    for s in list_bss:
        if s == '':
            continue
        if sect in s or s in sect:
            match_flag = 1
            total_bss += size
            if obj in obj_bss_db.keys():
                obj_bss_db[obj] += size
            else:
                obj_bss_db[obj] = size
            last_type = 3
            last_obj = obj
            sec_db3 += [['Bss', sect, addr, size, obj]]
            #print('fill add to bss')
            break
    if match_flag == 1:
        continue

print("\r\n\r\n\r\n========== Section Size ==========")
out_str = 'Total {:<4} = {:<7} (Dec)  {:<8} (Hex)'
print(out_str.format('Text', total_text, hex(total_text)))
print(out_str.format('Data', total_data, hex(total_data)))
print(out_str.format('Bss',  total_bss,  hex(total_bss)))

t1, t2, t3 = list(obj_text_db.keys()),list(obj_data_db.keys()),list(obj_bss_db.keys()) 

t = t1 + t2 + t3
obj_all = list(set(t))

#print(obj_all)
print('\r\n\r\n\r\nText      Data      Bss       Object')
print('======================================')
for f in obj_all:
    if f in obj_text_db.keys():
        text = obj_text_db[f]
    else:
        text = 0

    if f in obj_data_db.keys():
        data = obj_data_db[f]
    else:
        data = 0

    if f in obj_bss_db.keys():
        bss = obj_bss_db[f]
    else:
        bss = 0

    out_str = "{:<10}{:<10}{:<10}{}".format(text, data, bss, f[-100:])
    print(out_str)
print('--------------------------------------')
out_str = "{:<10}{:<10}{:<10}{}{:.1f} KB".format(total_text, total_data, total_bss, 'Total = ', (total_text + total_data + total_bss)/1024)
print(out_str)

if args.detail == True:
    print("\r\n\r\n\r\n========== Symbol Size Report ==========")
    #Report eabh object
    for f in obj_all:
        print(f,":")
        for l in sec_db3:
            stype, sect, addr, size, obj = l
            if obj == f:
                out_str = "  {:<8}{:<10}{:<50}".format(stype, size, sect)
                print(out_str)
        print('\r\n')