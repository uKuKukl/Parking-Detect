import os

# 1. 把这里改成你存放图片的实际文件夹路径
folder_path = r"D:\Program Files\yolo_all\data\images\test"

# 统计一下删了多少
delete_count = 0

print("--- 开始扫描 ---")
for filename in os.listdir(folder_path):
    # 分离文件名和后缀 (例如 name="000001_2", ext=".jpg")
    name, ext = os.path.splitext(filename)
    
    # 核心逻辑：如果文件名里包含下划线 '_'
    if 'npy' in ext:
        file_path = os.path.join(folder_path, filename)
        print(f"找到衍生文件: {filename}")
        
        # ⚠️ 确认上面打印的列表没删错东西后，把下面这行代码开头的 '#' 删掉就能真正执行删除！
        os.remove(file_path)
        
        delete_count += 1
    if '_' in name:
        file_path = os.path.join(folder_path, filename)
        print(f"找到衍生文件: {filename}")
        
        # ⚠️ 确认上面打印的列表没删错东西后，把下面这行代码开头的 '#' 删掉就能真正执行删除！
        os.remove(file_path)

print(f"--- 扫描结束，共找到 {delete_count} 个带下划线的文件 ---")