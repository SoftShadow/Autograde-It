def fact(n):
    result = 1
    while n > 1:
        result *= n
        n -= 1
    return result

def fib(n):
    fibs = {1:1, 2:1}
    for i in xrange(3, n+1):
        fibs[i] = fibs[i-1] + fibs[i-2]
    return fibs[n]
