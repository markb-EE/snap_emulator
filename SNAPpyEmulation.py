HOOK_1S = '1s'
HOOK_100MS = '100ms'

def setHook(a):
    def outer(a):
        def inner():
            pass
        return inner
    return outer

# TODO: implement timer hooks using the apy scheduler

