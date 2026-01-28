import pandas as pd
import random
from datetime import datetime


def generate_large_dataset(num=1000):
    """生成大量随机员工数据"""

    # 扩展的姓氏和名字列表
    all_surnames = ['王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴', '徐', '孙', '马', '朱', '胡', '林',
                    '郭', '何', '高', '罗', '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹', '彭', '曾']

    all_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛',
                 '明', '超', '秀兰', '霞', '平', '刚', '桂英', '华', '云', '梅', '鹏', '红', '金', '文', '建国']

    print(f"正在生成 {num} 个随机员工数据...")

    data = []
    used_ids = set()

    for i in range(num):
        # 生成名字（两字或三字）
        surname = random.choice(all_surnames)
        if random.random() < 0.7:
            name = surname + random.choice(all_names)
        else:
            name = surname + random.choice(all_names) + random.choice(all_names)

        # 生成唯一工号
        while True:
            # 随机选择工号格式
            if random.random() < 0.5:
                emp_id = f"EMP{random.randint(10000, 99999)}"
            else:
                emp_id = f"{random.choice(['G', 'A', 'B', 'C'])}{random.randint(10000, 99999)}"

            if emp_id not in used_ids:
                used_ids.add(emp_id)
                break

        data.append([i + 1, name, emp_id])

    return data


# 生成80个员工数据
employees = generate_large_dataset(80)

# 创建DataFrame
df = pd.DataFrame(employees, columns=['序号', '姓名', '工号'])

# 保存到Excel
timestamp = datetime.now().strftime("%Y%m%d")
filename = f"员工名单_{len(employees)}人_{timestamp}.xlsx"
df.to_excel(filename, index=False)

print(f"\n✅ 完成！已生成 {len(employees)} 条记录")
print(f"📁 保存为: {filename}")
print("\n前10条数据预览:")
print(df.head(10).to_string(index=False))