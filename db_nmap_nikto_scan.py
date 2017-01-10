#!/usr/bin/python
import time
import subprocess as sub
from os import listdir

    #*******************************#
    #** # = Optional code         **#
    #** ## = Comments             **#
    #** Created By: CBC Aug 2016  **#
    #*******************************#

## A function that runs the ps -e command and searches for a given process
def process_check(search):
    done = False
    while done != True:
        try:
            ps = sub.check_output('ps -e |grep '+search, shell=True)
        except:
            done = True

start =time.asctime( time.localtime(time.time()) )
iprng = raw_input('What is the IP or range of IPs? ')
# iprng = '192.168.1.0/24'# Test IP range
socket = {}
address_lst = []

## Pulls the assessing machine's IP for exclusion from the sweep scan.
## This only works for Kali. A Debian system formats the output differently.
eth0 = sub.check_output('ifconfig eth0', shell=True)
eth0 = eth0.split('\n')
eth0 = eth0[1].split(' ')
myip = eth0[9]

## Finding active IPs and writting them to file
#sweep = sub.Popen('nmap -sn -n -vv '+iprng+' --exclude '+myip+' -oG /home/????/scans/nmap/pingsweep.gnmap', shell=True)# Ping sweep for active IPs
sweep = sub.Popen('nmap -sT -n -vv '+iprng+' --exclude '+myip+' -oG /home/?????/scans/nmap/pingsweep.gnmap', shell=True)# TCP sweep for active IPs

## Waits for all nmap scans to complete
process_check('nmap')

## Opens the pingsweep file for reading.
with open('/home/?????/scans/nmap/pingsweep.gnmap', 'r') as file1:
    pingsweep = file1.read()
    pingsweep = pingsweep.split('\n')

    ## Removes the first and last two entries from the list
    pingsweep.pop(0)
    pingsweep.pop(0)
    pingsweep.pop(-1)
    pingsweep.pop(-1)

    ## Creates the iplist.txt file if it doesn't exist and opens it for for writing.
    with open('/home/?????/scans/nmap/iplist.txt', 'w+') as file2a:

        ## Pulls the active IPs and writes them to file.
        for line in pingsweep:
            lst = line.split(' ')
            if lst[3] == 'Up':
                file2a.write(lst[1]+'\n')

## Opens the iplist.txt for reading.
with open('/home/?????/scans/nmap/iplist.txt', 'r') as file2b:
    ip_lst = file2b.read()
    ip_lst = ip_lst.split('\n')

    ## Launches a TCP and UDP NMAP scan for each IP in the iplist.txt file and backgrounds the process.
    for ip in ip_lst:
        if ip != '':
            sub.Popen('nmap -Pn -sT -sV -O -n -vv '+ip+' -p0-65535 -oX /home/?????/scans/nmap/tcp/'+ip+'_tcp.xml &', shell=True)
            sub.Popen('nmap -Pn -sU -sV -n -vv '+ip+' -oX /home/?????/scans/nmap/udp/'+ip+'_udp.xml &', shell=True)

## Waits for all nmap scans to complete
process_check('nmap')

## Launches Metasploit and loads the resource file
  ## The resource file creates a workspace, switches to that workspace, imports the NMAP scans, 
  ## filters the services for HTTP related services and outputs it to a file and exits Metasploit.
sub.Popen('msfconsole -r /home/?????/scripts/import_nmap.rc', shell=True)

## Waits for metasploit to complete the import process
process_check('ruby')

## Parses exported HTTP .csv file
with open('/home/?????/scripts/python/http_services.csv', 'r') as socket_file:
    socket_lst = str.split(socket_file.read())
    for line in socket_lst[1:]:
        address, port = line.split(',')
        address=address.strip('"')
        if address not in address_lst:
            address_lst.append(address)
            socket[address]=[port]
        else:
            socket[address].append(port)

## Launches nikto
for i in address_lst:
    ## Delet existing files
    try: sub.Popen('rm /home/?????/scans/nikto/'+i+'.nik -f', shell=True)
    except: print '******\n* OOPS, SOMETHING WHENT WRONG!\n*****'; next
    port_lst = socket[i]
    ports = ''
    for x in port_lst:
        ports += x+','
    ## Nikto does not like quotes
    ports = ports.replace('"','')
    sub.Popen('nikto -host '+i+' -port '+ports+' -output /home/?????/scans/nikto/'+i+'.nik -Format XML', shell=True)
    #sub.Popen('nikto -host '+i+' -port '+ports+' -output /home/?????/scans/nikto/'+i+'.xml', shell=True)

## Waits for all nikto scans to complete
process_check('nikto')

## Nikto has a formatting issue with XML. For some reason it does not add the correct number of closing tags.
# Indexes all .nik and .xml files within the current directory
for filename in listdir('/home/?????/scans/nikto/'):
    if filename.endswith('.nik') or filename.endswith('.xml'):
        with open('/home/?????/scans/nikto/'+filename, 'a+') as nikto_file:
            nikto_lst = str.split(nikto_file.read())
            print 'Opening %s for reading.' % filename
            open_tag = 0
            close_tag = 0

            ## Searches for and counts the number of open & close tags
            for line in nikto_lst:
                if line == '<niktoscan':
                    open_tag += 1
                elif line == '</niktoscan>':
                    close_tag += 1
            ## Diffs the open and close tags adds the missing close tags
            if open_tag > close_tag:
                add_close_tag = open_tag - close_tag
                nikto_file.write('\n</niktoscan>'*add_close_tag)
            else: next

## Launches Metasploit and loads the resource file
  ##  The resource file switches to the designated workspace, imports all files in the nikto directory and exits Metasploit.

## If import error occures: "Could not automatically determine file type" then most likly Nikto
## did not find anything for this IP
sub.Popen('msfconsole -r /home/?????/scripts/import_nikto.rc', shell=True)

## Waits for metasploit to complete the import process
process_check('ruby')

## Prevents any code from executing for the next 5 seconds
time.sleep(5)

## Prints the start and end time of the scan
print '\n\nScript started at '+start
print 'Script finished at '+time.asctime( time.localtime(time.time()) )
