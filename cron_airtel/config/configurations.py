env = 'production'

if env == 'development':
    host = '127.0.0.1'
    port = 3308
    user = 'root'
    database = 'testbed'
    password = 'password'
elif env == 'production':
    host = '138.68.158.250'
    port = 3306
    user = 'jbiola'
    database = 'switch'
    password = 'gofreshbakeryproduction2020jb'
