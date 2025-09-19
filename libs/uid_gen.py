import random

alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

def generate_uid(length=5, admin=False):
    if admin == False:
        return ''.join(random.choice(alpha) for _ in range(length))
    else:
        code = ''
        for _ in range(3):
            code += random.choice('0123456789')
        return "admin_" + code