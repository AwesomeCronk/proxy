import re
import sys
def noIPv4(filepath):
    with open(filepath, 'r') as file:
        newStr = re.sub('[0-9][0-9][0-9][.][0-9][0-9][0-9][.][0-9][0-9][0-9][.][0-9][0-9]', '***.***.***.**', file.read())
    with open(filepath, 'w') as file:
        file.write(newStr)
    print('Done.')

if __name__ == '__main__':
    noIPv4(sys.argv[1])