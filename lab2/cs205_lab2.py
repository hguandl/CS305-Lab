import math

def hello_world():
    print('Hello World')

def find_prime(start: int, end: int) -> list:
    list = []
    for i in range(start, end + 1):
        if i <= 1:
            continue
        prime = True
        for j in range(2, math.floor(math.sqrt(i)) + 1):
            if i % j == 0:
                prime = False
                break
        if prime:
            list.append(i)

    return list

class doggy:
    def __init__(self, name):
        self.name = name;
    def bark(self) -> str:
        return self.name + ' bark'
        
def printer_maker(key):
    def real_print(dict):
        return dict[key]
    return real_print

if __name__ == '__main__':
    hello_world()

    s = int(input("please input the start number of the range: "))
    e = int(input("please input the end number of the range: "))
    r = find_prime(s, e)
    print("the prime between [%s,%s] is: "%(s, e))
    print(r)

    adoggy = doggy("a doggy")
    print(adoggy.bark())

    key = input("please input the key: ")
    fun = printer_maker(key)
    adic = {"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4"}
    print(fun(adic))