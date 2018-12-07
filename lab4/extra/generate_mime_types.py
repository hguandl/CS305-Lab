types = {}

with open('mime.types', 'r') as f:
    for line in f.readlines():
        str1 = line.split(' ')
        while '' in str1:
            str1.remove('')
        str1 = [i.replace(';\n', '') for i in str1]
        if '\n' in str1[-1]:
            continue
        for i in str1[1:]:
            types[i] = str1[0]

print(types)

f.close()