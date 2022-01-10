import sqlite3

class ValueExistError(Exception):
    pass

class DaoFactory:

    def __init__(self):
        self.con = sqlite3.connect('./role-manage.db')
        self.cur = self.con.cursor()
        self.cur.execute('''SELECT count(*) from sqlite_master
                                WHERE type='table' AND name='role' ''')
        rows = self.cur.fetchall()
        if not rows[0][0]:
            self.__init_tables__()


    def __init_tables__(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS role
                (guildID str, roleID str, name str)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS emoji
                (guildID str, name str)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS guild
                (guildID str, ownerID str, messID str, chanID str)''')
        self.con.commit()

    def get_role_table(self, guildID:str):
        self.cur.execute("SELECT * FROM role WHERE guildID=?", (guildID,))
        res = self.cur.fetchall()
        return res

    def set_role_table(self, guildID:str, roleID:str, name:str):
        self.cur.execute("INSERT INTO role VALUES(?, ?, ?)", \
					(guildID, roleID, name))
        self.con.commit()
        return

    def get_emoji_table(self, guildID:str):
        self.cur.execute("SELECT * FROM emoji WHERE guildID=?", (guildID,))
        res = self.cur.fetchall()
        return res

    def set_emoji_table(self, guildID:str, name:str):
        self.cur.execute("INSERT INTO emoji VALUES(?, ?)", (guildID, name))
        self.con.commit()
        return

    def remove_all_elem(self, guildID:str):
        self.cur.execute("DELETE FROM role WHERE guildID=?", (guildID,))
        self.con.commit()
        self.cur.execute("DELETE FROM emoji WHERE guildID=?", (guildID,))
        self.con.commit()
        self.cur.execute("DELETE FROM guild WHERE guildID=?", (guildID,))
        self.con.commit()
        return

    def check_guild_table(self, guildID:str):
        self.cur.execute("SELECT * FROM guild WHERE guildID=?", (guildID,))
        res = self.cur.fetchone()
        if res:
            raise ValueExistError
        return True

    def get_id_channel(self, guildID:str):
        self.cur.execute("SELECT chanID FROM guild WHERE guildID=?", (guildID,))
        res = self.cur.fetchall()
        return res[0]

    def get_id_mess(self, guildID:str):
        self.cur.execute("SELECT messID FROM guild WHERE guildID=?", (guildID,))
        res = self.cur.fetchall()
        return res[0]

    def set_guild_table(self, guildID:str, ownerID:str, messID:str, chanID:str):
        self.cur.execute("SELECT * FROM guild WHERE guildID=? AND ownerID=?", (guildID, ownerID))
        res = self.cur.fetchone()
        if res is None:
            self.cur.execute("INSERT INTO guild VALUES(?, ?, ?, ?)", \
					(guildID, ownerID, messID, chanID))
        else:
            raise ValueExistError
        self.con.commit()
        return True
