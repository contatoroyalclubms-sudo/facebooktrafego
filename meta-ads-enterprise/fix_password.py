import bcrypt

password = 'admin123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print('New hash:', hashed.decode('utf-8'))
