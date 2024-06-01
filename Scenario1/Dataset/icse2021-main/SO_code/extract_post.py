import os 
import time 
import traceback
from bs4 import BeautifulSoup

INPUT_DIR = 'Posts'
OUTPUT_FILE = 'mobile_dl_url.txt'

PROCESS_NUM = 10
EXTRACT_TAGS = ['tensorflow-lite', 'coreml']

def worker(input_file):
    f_res = open(OUTPUT_FILE, 'a')
    
    with open(input_file, 'r') as f:
        for line in f:
            try:
                line = line.strip()
                content = json.loads(line)
                
                # exclude posts without accept answers
                if 'AcceptedAnswerId' not in content:
                    continue
                
                # filter by tag
                tags = content['Tags'].split('><')
                contain_tag = False
                for tag in tags:
                    tag = tag.strip().replace('<', '').replace('>', '')
                    if tag in EXTRACT_TAGS:
                        contain_tag = True
                        break
                
                # exclude posts without code
                body = '<html>{}</html>'.format(content['Body'].strip())
                soup = BeautifulSoup(body, 'html.parser')
                has_code = False
                for c in soup.find_all('code'):
                    has_code = True
                    break
                    
                if contain_tag and has_code:
                    f_res.write('https://stackoverflow.com/questions/{}\t{}\n'.format(content['Id'], content['Tags']))
            except:
                traceback.print_exc()

def main():
    print('Start to extract posts...')

    start = time.time()
    pool = multiprocessing.Pool(processes = PROCESS_NUM)
    files = os.listdir(INPUT_DIR)
    for file in files:
        pool.apply_async(worker, ('{}/{}'.format(INPUT_DIR, file), ))
    pool.close()
    pool.join()
    
    print('Done in {} seconds.'.format(time.time() - start))
    

if __name__ == '__main__':
    main()