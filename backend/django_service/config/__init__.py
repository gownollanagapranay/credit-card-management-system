import pymysql

# Inject PyMySQL as default MySQLdb driver for Django
pymysql.install_as_MySQLdb()