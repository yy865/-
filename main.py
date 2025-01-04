import time
import pymysql
from config import db_config

# 连接到MySQL数据库
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# 创建用户表（如果不存在）
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    money DECIMAL(10, 2) NOT NULL DEFAULT 1000.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    account TEXT
)
''')

# 创建管理员表（如果不存在）
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
)
''')

# 提交更改
conn.commit()


# 取款业务模块
def get_money_info(login_user, money):
    """
    1.获取用户数据==》查看现有的金额
    2.判断账户里面有没有那么多钱
    3.修改余额/提示取款异常，存款不足
    4.保存数据==》修改余额，添加流水账单
    5.返回取款结果和取款说明明细
        return:1.取款结果，2.取款的说明信息
    """
    # 1.通过用户名获取用户数据
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (login_user,))
    user_data = cursor.fetchone()
    if user_data:
        # 2.查看余额
        user_money = user_data[3]
        # 3.判断余额是否足够
        money = float(money)
        if user_money >= money:
            # 4.修改余额的数据
            user_money -= money
            cursor.execute("UPDATE users SET money = %s WHERE user_name = %s", (user_money, login_user))
            # 5.添加流水账单信息
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            acc_info = f'{now_time} 用户{login_user},取款{money}元'
            cursor.execute("SELECT account FROM users WHERE user_name = %s", (login_user,))
            old_account = cursor.fetchone()[0]
            new_account = old_account + '\n' + acc_info if old_account else acc_info
            cursor.execute("UPDATE users SET account = %s WHERE user_name = %s", (new_account, login_user))
            # 6.提交更改并返回取款信息
            conn.commit()
            return True, acc_info
        elif user_money == 0:
            return False, '您的账户比您脸都干净还取啥呀？贷款呢？搁这儿？'
        return False, 'B子不够了，别想套我ATM的钱，重新说个数：'
    return False, '用户不存在，请先注册'


# 存钱业务模块
def save_money_info(login_user, money):
    """
    1.获取用户数据==》查看现有的金额
    2.修改余额
    3.保存数据==》修改余额，添加流水账单
    4.返回取款结果和取款说明明细
        return:1.取款结果，2.取款的说明信息
    """
    # 1.通过用户名获取用户数据
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (login_user,))
    user_data = cursor.fetchone()
    if user_data:
        # 2.查看余额
        user_data[3] += float(money)
        cursor.execute("UPDATE users SET money = %s WHERE user_name = %s", (user_data[3], login_user))
        # 3.添加流水账单信息
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        acc_info = f'{now_time} 用户{login_user},存款{money}元'
        cursor.execute("SELECT account FROM users WHERE user_name = %s", (login_user,))
        old_account = cursor.fetchone()[0]
        new_account = old_account + '\n' + acc_info if old_account else acc_info
        cursor.execute("UPDATE users SET account = %s WHERE user_name = %s", (new_account, login_user))
        # 4.提交更改并返回存款信息
        conn.commit()
        return True, acc_info
    return False, '用户不存在，请先注册'


# 转账业务模块
def transfer_money_info(login_user, to_user, money):
    """
    1.获取转出和转入用户数据
    2.判断转出账户余额是否足够
    3.进行转账处理，更新双方余额和流水账单
    4.返回转账结果和说明明细
        return:1.转账结果，2.转账的说明信息
    """
    # 1.获取转出和转入用户数据
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (login_user,))
    from_user_data = cursor.fetchone()
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (to_user,))
    to_user_data = cursor.fetchone()
    if from_user_data and to_user_data:
        # 2.判断转出账户余额是否足够
        from_user_money = from_user_data[3]
        money = float(money)
        if from_user_money >= money:
            # 3.进行转账处理，更新双方余额和流水账单
            from_user_money -= money
            to_user_money = to_user_data[3] + money
            cursor.execute("UPDATE users SET money = %s WHERE user_name = %s", (from_user_money, login_user))
            cursor.execute("UPDATE users SET money = %s WHERE user_name = %s", (to_user_money, to_user))
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            from_acc_info = f'{now_time} 用户{login_user},向用户{to_user}转账{money}元'
            to_acc_info = f'{now_time} 用户{to_user},收到用户{login_user}转账{money}元'
            cursor.execute("SELECT account FROM users WHERE user_name = %s", (login_user,))
            from_old_account = cursor.fetchone()[0]
            from_new_account = from_old_account + '\n' + from_acc_info if from_old_account else from_acc_info
            cursor.execute("UPDATE users SET account = %s WHERE user_name = %s", (from_new_account, login_user))
            cursor.execute("SELECT account FROM users WHERE user_name = %s", (to_user,))
            to_old_account = cursor.fetchone()[0]
            to_new_account = to_old_account + '\n' + to_acc_info if to_old_account else to_acc_info
            cursor.execute("UPDATE users SET account = %s WHERE user_name = %s", (to_new_account, to_user))
            # 4.提交更改并返回转账成功信息
            conn.commit()
            return True, from_acc_info
        return False, '余额不足，转账失败'
    return False, '转出或转入用户不存在，请检查用户名'


# 获取账单模块
def get_acc(login_user):
    cursor.execute("SELECT account FROM users WHERE user_name = %s", (login_user,))
    return cursor.fetchone()[0] if cursor.fetchone() else []


# 用户注册逻辑
def user_register_info(user_name, password):
    user_info = {
        "user_name": user_name,
        "password": password,
        "money": 1000,
        "currency": 'CNY',
        "account": []
    }
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (user_name,))
    if cursor.fetchone():
        return False, '注册失败，该用户已存在'
    cursor.execute("INSERT INTO users (user_name, password, money, currency, account) VALUES (%s, %s, %s, %s, %s)",
                   (user_name, password, user_info['money'], user_info['currency'], user_info['account']))
    conn.commit()
    return True, f'{user_name}注册成功'


# 用户登录逻辑
def user_login_info(user_name, password):
    cursor.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (user_name, password))
    if cursor.fetchone():
        return True, f'{user_name}登录成功'
    return False, '密码错误，请重新输入'


# 查看用户余额功能函数实现
def user_check_money_info(user_name):
    cursor.execute("SELECT money FROM users WHERE user_name = %s", (user_name,))
    return cursor.fetchone()[0] if cursor.fetchone() else 0


# 管理员注册逻辑
def admin_register_info(admin_name, password):
    cursor.execute("SELECT * FROM admins WHERE admin_name = %s", (admin_name,))
    if cursor.fetchone():
        return False, '管理员注册失败，该管理员已存在'
    cursor.execute("INSERT INTO admins (admin_name, password) VALUES (%s, %s)", (admin_name, password))
    conn.commit()
    return True, f'{admin_name}管理员注册成功'


# 管理员登录逻辑
def admin_login_info(admin_name, password):
    cursor.execute("SELECT * FROM admins WHERE admin_name = %s AND password = %s", (admin_name, password))
    if cursor.fetchone():
        return True, f'{admin_name}管理员登录成功'
    return False, '管理员密码错误，请重新输入'


# 语法糖
def is_user_login(func):
    def check(*args, **kwargs):
        # 先判断当前的用户登录状态
        if src.login_user:
            # func相当于check_money函数
            func(*args, **kwargs)
        else:
            print('请先登录用户账号')
            src.user_login()
    return check


def is_admin_login(func):
    def check(*args, **kwargs):
        # 先判断当前的管理员登录状态
        if src.admin_login_user:
            func(*args, **kwargs)
        else:
            print('请先登录管理员账号')
            src.admin_login()
    return check


from core import src

login_user = None
admin_login_user = None


def user_register():
    """用户注册模块
    a.输入用户名。密码。确认密码（两次输入密码不一致提示密码错误）
    b.输入合法.不合法就提示异常
    c.吧得到的用户数据保存写入到user_data中
    """
    while 1:
        user_name = input("请输入您的尊姓大名：")
        password = input("您给自己设置个密码吧，号别丢喽，歪歪这边建议您设置的别太简单了：")
        re_password = input("确定想好了吧，再输一遍吧以，防你忘了：")
        if password == re_password:
            flag, msg = user_register_info(user_name, password)
            if flag:
                print(msg)
            else:
                print(msg)
                break
        else:
            print("你这输的是同一个密码吗？好好想想，这边可没有改密码的服务")


def user_login():
    """用户登录模块
    1.写一个死循环，让程序可以重复执行
    2.让用户输入用户名和密码
    3.进行逻辑判断==》账号是否存在，密码是否一致==》返回一个结果
        a.登录是否成功
        b.登录信息
    """
    global login_user
    while 1:
        user_name = input('请输入您的尊姓大名：')
        password = input('给一下您的密码：')
        flag, msg = user_login_info(user_name, password)
        if flag:
            print(msg)
            login_user = user_name
            break
        else:
            print(msg)


def admin_register():
    """管理员注册模块
    a.输入管理员用户名。密码。确认密码（两次输入密码不一致提示密码错误）
    b.输入合法.不合法就提示异常
    c.吧得到的管理员数据保存写入到admin_data中
    """
    while 1:
        admin_name = input("请输入管理员用户名：")
        password = input("管理员设置个密码吧：")
        re_password = input("确定想好了吧，再输一遍吧以，防你忘了：")
        if password == re_password:
            flag, msg = admin_register_info(admin_name, password)
            if flag:
                print(msg)
            else:
                print(msg)
                break
        else:
            print("你这输的是同一个密码吗？好好想想，这边可没有改密码的服务")


def admin_login():
    """管理员登录模块
    1.写一个死循环，让程序可以重复执行
    2.让管理员输入用户名和密码
    3.进行逻辑判断==》账号是否存在，密码是否一致==》返回一个结果
        a.登录是否成功
        b.登录信息
    """
    global admin_login_user
    while 1:
        admin_name = input('请输入管理员用户名：')
        password = input('给一下管理员密码：')
        flag, msg = admin_login_info(admin_name, password)
        if flag:
            print(msg)
            admin_login_user = admin_name
            break
        else:
            print(msg)


# 语法糖装饰后的用户功能函数
@is_user_login
def user_check_money():
    """查看用户余额"""
    money = user_check_money_info(login_user)
    print(f'老逼登：{login_user},名下有{money}元')


@is_user_login
def user_recharge():
    """用户存钱模块"""
    while 1:
        money = input('想好你要存多少了吗？说个数儿：')
        if not money.isdigit():
            print('连个数儿都写不对？干啥吃的的？')
            continue
        else:
            print('行了，放俺这儿你放心。歪歪办事，效率贼高，用户都说好！')
            flag, msg = save_money_info(login_user, money)
            if flag:
                print(msg)
                break
            else:
                print(msg)
                break


@is_user_login
def user_get_money():
    """用户取钱模块
    1.让用户输入要取的金额
    2.进行取款的逻辑处理
    3.返回取款的结果
    """
    while 1:
        money = input('说吧，要多少？')
        if not money.isdigit():
            print('小B崽汁确定你输对了吗？再给你一次机会')
            continue
        else:
            flag, msg = get_money_info(login_user, money)
            if flag:
                print(msg)
                break
            else:
                print(msg)
                break


@is_user_login
def user_account():
    """查看用户账单模块"""
    acc_list = get_acc(login_user)
    print(acc_list)


@is_user_login
def user_transfer_money():
    """用户转账模块
    1.让用户输入对方用户名和转账金额
    2.进行转账的逻辑处理
    3.返回转账的结果
    """
    while 1:
        to_user = input('请输入对方用户名：')
        money = input('请输入转账金额：')
        if not money.isdigit():
            print('连个数儿都写不对？干啥吃的的？')
            continue
        else:
            flag, msg = transfer_money_info(login_user, to_user, money)
            if flag:
                print(msg)
                break
            else:
                print(msg)
                break


# 管理员功能函数（示例：查看所有用户信息，可根据需求扩展更多功能）
@is_admin_login
def admin_view_all_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"用户ID: {user[0]}, 用户名: {user[1]}, 余额: {user[3]}, 货币类型: {user[4]}")


fun_select = {
    # 元祖里面第一个值放描述信息，第二个值放实现的功能
    "0": ("退出", sys.exit),
    "1": ("用户注册", user_register),
    "2": ("用户登录", user_login),
    "3": ("查看用户余额", user_check_money),
    "4": ("用户存钱", user_recharge),
    "5": ("用户取钱", user_get_money),
    "6": ("查看用户账单", user_account),
    "7": ("用户转账", user_transfer_money),
    "8": ("管理员注册", admin_register),
    "9": ("管理员登录", admin_login),
    "10": ("管理员查看所有用户信息", admin_view_all_users)
}


def atm():
    while 1:
        print('欢迎来到歪歪银行🌹ᐕ)⁾⁾')
        for k in fun_select:
            print(k, fun_select[k][0])
        select = input("请选择你要进行的操作:")
        if select in fun_select:
            fun_select[select][1]()
        else:
            print("我是人工，不是傻子，希望你能认真输个正确的数，别欺负歪歪行不？")


if __name__ == '__main__':
    src.atm()