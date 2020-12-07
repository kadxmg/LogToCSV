# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 按两次 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import os
import sys
import time
import re
from datetime import datetime

debug_verbose = 0
debug = 1


class Log_Parser_Template:
    def __init__(self,
                 file_name_regular,
                 file_name_sort_lambda,
                 file_name_output,
                 keyword_line_regular,
                 keyword_field_regulart,
                 keyword_time_regulart,
                 keyword_head_regulart,
                 keyword_field_split):
        self.file_name_regular = file_name_regular
        self.file_name_sort_lambda = file_name_sort_lambda
        self.file_name_output = file_name_output
        self.keyword_line_regular = keyword_line_regular
        self.keyword_field_regulart = keyword_field_regulart
        self.keyword_time_regulart = keyword_time_regulart
        self.keyword_head_regulart = keyword_head_regulart
        self.keyword_field_split = keyword_field_split


Log_Parser_UNISOC = Log_Parser_Template(
    # 0-kernel.log
    file_name_regular='^\d-kernel\.log$',
    file_name_sort_lambda=(lambda x: int(x[0:1])),
    file_name_output='unisoc_battery.csv',
    # 5A245 <6> [27634.217721][12-02 20:18:22.217] charger-manager charger-manager: battery voltage = 3411000, OCV = 3536769, current = -1113000, capacity = 10, charger status = 2, force set full = 0, charging current = 0, charging limit current = 0, battery temperature = 513,board temperature = 583, track state = 1, charger type = 2, thm_adjust_cur = -22, charger input voltage = 0
    keyword_line_regular='.* charger-manager charger-manager:(.*)$',
    keyword_head_regulart='.* charger-manager charger-manager: battery voltage = (.*)$',
    keyword_field_regulart='(.+?) = (.+?),',
    keyword_field_split=',',
    keyword_time_regulart='^.*?\[.*\]\[(.*)\] ',
)

Log_Parsers = [Log_Parser_UNISOC]


class CsvItem:
    head_keyword_keypairs = {}

    def __init__(self):
        self.time = ''
        self.timestamp = 0.0
        self.keyword_keypairs = {}
        self.raw = ''
        self.file = ''
        self.line_number = -1
        self.head = False

    def dump(self):
        if len(self.time) > 0:
            print("time :", self.time)
        if self.timestamp > 0:
            print("timestamp :", self.timestamp)
        if len(self.keyword_keypairs) > 0:
            print("keypairs :", self.keyword_keypairs)
        if len(self.raw) > 0:
            print("raw :", self.raw)
        if len(self.file) > 0:
            print("file :", self.file)
        if self.line_number != -1:
            print("line_number :", self.line_number)

    @staticmethod
    def get_csv_head():
        return ",".join(["time",
                         "timestamp",
                         ",".join(list(CsvItem.head_keyword_keypairs.keys())),
                         "file",
                         "line_number", ])
    def add_keyword_keypairs(self,key,value):
        CsvItem.head_keyword_keypairs[key] = ''
        self.keyword_keypairs[key] = value

    def get_csv_head_vales(self):
        values = ""
        for key in CsvItem.head_keyword_keypairs.keys():
            if key in self.keyword_keypairs:
                values = values + "," + self.keyword_keypairs[key]
            else:
                values = values + ","
        return values[1:] # remove the firs ,

    def get_csv_line(self):
        return ",".join([self.time,
                         str(self.timestamp),
                         self.get_csv_head_vales(),
                         self.file,
                         str(self.line_number), ])


def process_log_line(line, keyword_time_regulart, keyword_line_regular, keyword_field_regulart,keyword_field_split, keyword_head_regulart):
    line = line.replace('\n', '').replace('\r', '')  # remove /r/n first
    line_match_obj = re.match(keyword_line_regular, line)
    keyword_head_match_obj = re.match(keyword_head_regulart, line)

    if line_match_obj is not None:
        # we found something match
        item = CsvItem()
        if debug:
            print("keyword line :", line)
        if keyword_head_match_obj is not None:
            item.head = True  # this is a head item
        item.raw = line
        # 10-19 18:54:29.010
        time_matchObj = re.match(keyword_time_regulart, line)
        item.time = time_matchObj.group(1)
        if debug_verbose:
            print("time str:", item.time)
        dt = datetime.strptime(item.time, '%m-%d %H:%M:%S.%f')
        dt = dt.replace(year=datetime.now().year)
        if debug_verbose:
            print("time stamp:", dt, dt.timestamp())
        item.timestamp = dt.timestamp()

        csv_content = line_match_obj.group(1) + keyword_field_split
        items_match_obj = re.findall(keyword_field_regulart, csv_content)
        for item_matchObj in items_match_obj:
            print("items_match_obj:", item_matchObj)
            key = item_matchObj[0].strip()
            value = item_matchObj[1].strip()
            print("items_match_obj:", key, ":", value)
            # item.keyword_keypairs[key] = value
            # some more thing is do in function
            item.add_keyword_keypairs(key, value)
        return item
    else:
        return None


def find_last_csv_items_by_name(name, csv_items):
    for item in csv_items[::-1]:
        if item.name == name:
            return item
    return None


def find_first_csv_items_by_name(name, csv_items, after_item):
    after_index = 0
    if after_item is None:
        after_index = 0
    else:
        after_index = csv_items.index(after_item)
    for item in csv_items[after_index:]:
        if item.name == name:
            return item
    return None


def process_log_file(log_file_path, csv_items, praser):
    try:
        log_file = open(log_file_path, 'r', encoding='utf-8', errors='ignore')
        lines = log_file.readlines()  # 读取全部内容 ，并以列表方式返回
        log_file.close()
    except IOError as reason:
        print('读取文件失败！' + log_file_path + ":" + str(reason))
        return None
    line_number = 0
    item_number = 0
    last_head_item = None
    for line in lines:
        line_number += 1
        item = process_log_line(line,
                                praser.keyword_time_regulart,
                                praser.keyword_line_regular,
                                praser.keyword_field_regulart,
                                praser.keyword_field_split,
                                praser.keyword_head_regulart,)
        if item is not None:
            if item.head:
                item.file = log_file_path
                item.line_number = line_number
                if debug:
                    item.dump()
                csv_items.append(item)
                last_head_item = item
                print("item:", item_number)
                item_number = item_number + 1
            else:
                if last_head_item is not None:
                    last_head_item.keyword_keypairs.update(item.keyword_keypairs)
                    print("merge to last item:", item.keyword_keypairs)
                else:
                    print("unable merge ，drop one item:", item.keyword_keypairs)


def save_csv(csv_log_path, csv_items):
    print('csv_items:', len(csv_items))
    try:
        csv_log = open(csv_log_path, 'w', encoding='utf-8', errors='ignore')
        if len(csv_items) > 0:
            csv_log.write(csv_items[0].get_csv_head() + "\n")
        for item in csv_items:
            if debug_verbose:
                item.dump()
            csv_log.write(item.get_csv_line() + "\n")
        csv_log.close()
        print('保存完成！' + csv_log_path)
    except IOError as reason:
        print('保存文件失败！' + csv_log_path + ":" + str(reason))


class SatisticsAvg:
    def __init__(self):
        self.count = 0
        self.avg = 0

    def add(self, new_value):
        self.avg = round((self.avg * self.count + new_value) / (self.count + 1), 3)
        self.count += 1


def filter_file_names(file_name, file_name_regular):
    if re.match(file_name_regular, file_name) == None:
        return False
    else:
        return True


def process_log_dir(praser, dir_name):
    log_files = []
    csv_items = []

    try:
        work_dir_files = os.listdir(dir_name)
    except IOError as reason:
        print('工作文件夹打开失败！' + str(reason))
        return
    while work_dir_files:
        file_name = work_dir_files.pop()
        if filter_file_names(file_name, praser.file_name_regular):
            log_files.append(file_name)

    log_files.sort(key=praser.file_name_sort_lambda)
    for file_name in log_files:
        path = dir_name + "\\" + file_name
        if debug:
            print('处理 Log 文件 ', path)
        process_log_file(path, csv_items, praser)

    output_path = work_dir + "\\" + praser.file_name_output
    save_csv(output_path, csv_items)
    os.system('start ' + output_path)


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    work_dir = os.getcwd()
    if len(sys.argv) < 1:
        print('格式:', sys.argv[0], ' <work_dir>')
        os.system('pause')
        sys.exit(2)
    if len(sys.argv) >= 2:
        work_dir = sys.argv[1]
    print('工作的文件夹：', work_dir)
    start = time.time()

    for praser in Log_Parsers:
        process_log_dir(praser, work_dir)

    end = time.time()
    print("耗时（秒）：", int(end - start))
    os.system('pause')

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
