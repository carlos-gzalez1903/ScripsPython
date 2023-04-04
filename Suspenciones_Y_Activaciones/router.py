class Router:

    # user=""
    # password=""
    # ip=""

    def __init__(self, user, password, ip):
        self.user = user
        self.password = password
        self.ip=ip

    def __str__(self):
        # print("user =", self.user)
        # print("password =", self.password)
        # print("ip =", self.ip)
        return "{ user = "+ self.user+",\n password = "+ self.password+",\n ip = "+ self.ip+",\n}"

    def infoRouter(self):
        return self.user, self.password, self.ip