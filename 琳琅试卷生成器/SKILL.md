# 灵珑认证阅卷安排表生成器

## 功能

根据用户提供的考核人员名单和配置信息，自动生成灵珑高级认证阅卷安排 Excel 文件，包含完整的公式、合并单元格和跨表引用。

## 触发条件

当用户需要：
- 生成灵珑认证阅卷安排表
- 创建认证考核评分表
- 准备灵珑实操考核文档

## 输入参数

用户需要提供以下信息（可通过对话逐步确认）：

### 必填
- **人员名单**：包含大区、区域、姓名（可从 Excel 文件读取或直接提供）
- **实操环境 URL**：如 `http://8.147.65.60:8080/linglong/index.html#/my-space/app`
- **用户中心 URL**：如 `http://8.147.65.60:8080/usercenter/index.html#/login`

### 可选（有默认值）
- **考核名称**：默认"灵珑高级认证"
- **期数**：默认自动递增
- **日期**：默认当天日期，格式 YYYYMMDD
- **账号后缀**：默认 `1`（即姓名+1 为账号）
- **密码**：默认 `eGova@2023Yhzx`
- **实操记录数据**：可从截图或数据库查询中提供
- **考官分配**：默认"待定"
- **输出路径**：默认 `D:/backup/user1/majq/Downloads/`
- **每组人数**：默认 16 人一组（影响评分表分组）

## 生成逻辑

### 文件结构（3 个 Sheet）

#### Sheet1 - 阅卷总表
| 列 | 内容 | 公式 |
|----|------|------|
| A | 大区 | - |
| B | 区域 | - |
| C | 人员 | - |
| D | 实操环境 | URL |
| E | 用户中心 | URL |
| F | 实操记录 | 数据填充 |
| G | 是否阅卷 | 手动填写 |
| H | 分数 | `=SUM(I:M)` |
| I | PC限停区域（30） | `=SUM('评分表'!得分列4:17)` |
| J | 社会主体（25） | `=SUM('评分表'!得分列18:27)` |
| K | 流程表单（20） | `=SUM('评分表'!得分列28:38)` |
| L | 移动端（15） | `=SUM('评分表'!得分列39:44)` |
| M | 视图（10） | `=SUM('评分表'!得分列45:51)` |
| N | 是否通过 | `=IF(H>=80,"是","否")` |
| O | 考官分配 | 合并单元格，按评分表分组 |

- Row 1: 合并 A1:N1
- O 列按评分表分组合并

#### 实操评分表1 / 实操评分表2
- 前 4 列 (A-D): 评分项结构（大项、子项、分值、描述），带合并单元格
- 每人占 3 列: 扣分 | 扣分说明 | 得分
- Row 1: 人员姓名（合并 3 列）
- Row 2: 扣分/扣分说明/得分 表头
- Row 3: 合计行，公式 `=SUM()`
- Row 4+: 得分公式 `=IF(扣分="",满分,满分-扣分)`

### 评分项大项行范围
| 大项 | 行范围 | 满分 |
|------|--------|------|
| 限停区域管理PC | 4-17 | 30 |
| 社会主体管理PC | 18-27 | 25 |
| 产品部署流程表单 | 28-38 | 20 |
| 案件列表移动端 | 39-44 | 15 |
| SQL视图 | 45-51 | 10 |

## 实现步骤

收到用户请求后，按以下步骤执行：

### Step 1: 确认参数
与用户确认人员名单来源、URL 地址、密码等配置。如果用户提供了 Excel 文件路径，读取对应 sheet 的人员数据。

### Step 2: 生成 Excel
运行以下 Python 脚本（根据参数动态调整）：

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl, json
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from copy import copy

# ===== 加载评分模板 =====
with open('D:/opencode/linlong_score_template.json', 'r', encoding='utf-8') as f:
    tpl_data = json.load(f)

score_rows_data = tpl_data['items']
merged_ranges = tpl_data['merges']
total_score_rows = tpl_data['total_rows']
score_values = [row[2] for row in score_rows_data]

SECTION_RANGES = [(4, 17), (18, 27), (28, 38), (39, 44), (45, 51)]

# ===== 参数（根据用户输入调整） =====
# people = [{'area': '...', 'region': '...', 'name': '...'}]
# PRACTICE_URL = '...'
# USER_CENTER_URL = '...'
# PASSWORD = '...'
# records = {'姓名1': 数量, ...}  # 实操记录
# output_path = '...'
# group_size = 16
# examiner_info = {'评分表1': '...', '评分表2': '...'}

# ===== 样式 =====
header_font = Font(bold=True, size=11)
header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
person_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
wrap_align = Alignment(vertical='center', wrap_text=True)

# ===== 分组 =====
group_size = 16  # 可调整
groups = []
for i in range(0, len(people), group_size):
    groups.append(people[i:i+group_size])

# ===== 创建工作簿 =====
wb = openpyxl.Workbook()

# ===== 评分表生成函数 =====
def create_score_sheet(ws, group):
    num_people = len(group)
    for r_idx, row_data in enumerate(score_rows_data):
        for c_idx in range(4):
            cell = ws.cell(row=r_idx + 1, column=c_idx + 1)
            cell.value = row_data[c_idx]
            cell.border = thin_border
            if r_idx < 3:
                cell.font = header_font
            if c_idx == 3:
                cell.alignment = wrap_align
            else:
                cell.alignment = center_align

    for min_r, min_c, max_r, max_c in merged_ranges:
        ws.merge_cells(start_row=min_r, start_column=min_c,
                       end_row=max_r, end_column=min(max_c, 4))

    for i, p in enumerate(group):
        base_col = 5 + i * 3
        dl = get_column_letter(base_col)
        sl = get_column_letter(base_col + 2)

        cell = ws.cell(row=1, column=base_col, value=p['name'])
        cell.font = Font(bold=True, size=11)
        cell.fill = person_fill
        cell.border = thin_border
        cell.alignment = center_align
        ws.merge_cells(start_row=1, start_column=base_col,
                       end_row=1, end_column=base_col + 2)
        for j in [1, 2]:
            ws.cell(row=1, column=base_col + j).border = thin_border

        for j, label in enumerate(['扣分', '扣分说明', '得分']):
            cell = ws.cell(row=2, column=base_col + j, value=label)
            cell.font = Font(bold=True, size=9)
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = center_align

        ws.cell(row=3, column=base_col).value = \
            '=SUM({0}4:{0}{1})'.format(dl, total_score_rows)
        ws.cell(row=3, column=base_col).border = thin_border
        ws.cell(row=3, column=base_col).alignment = center_align
        ws.cell(row=3, column=base_col).font = Font(bold=True, color='FF0000')
        ws.cell(row=3, column=base_col + 1).border = thin_border
        ws.cell(row=3, column=base_col + 2).value = \
            '=SUM({0}4:{0}{1})'.format(sl, total_score_rows)
        ws.cell(row=3, column=base_col + 2).border = thin_border
        ws.cell(row=3, column=base_col + 2).alignment = center_align
        ws.cell(row=3, column=base_col + 2).font = Font(bold=True, color='FF0000')

        for r_idx in range(3, total_score_rows):
            row_num = r_idx + 1
            full_score = score_values[r_idx]
            ws.cell(row=row_num, column=base_col).border = thin_border
            ws.cell(row=row_num, column=base_col).alignment = center_align
            ws.cell(row=row_num, column=base_col + 1).border = thin_border
            ws.cell(row=row_num, column=base_col + 1).alignment = wrap_align
            if full_score and str(full_score).strip():
                try:
                    fv = float(full_score)
                    if fv > 0:
                        fv_str = str(int(fv)) if fv == int(fv) else str(fv)
                        ws.cell(row=row_num, column=base_col + 2).value = \
                            '=IF({0}{1}="",{2},{2}-{0}{1})'.format(dl, row_num, fv_str)
                except (ValueError, TypeError):
                    pass
            ws.cell(row=row_num, column=base_col + 2).border = thin_border
            ws.cell(row=row_num, column=base_col + 2).alignment = center_align

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 6
    ws.column_dimensions['D'].width = 65
    for i in range(num_people):
        base_col = 5 + i * 3
        ws.column_dimensions[get_column_letter(base_col)].width = 7
        ws.column_dimensions[get_column_letter(base_col + 1)].width = 22
        ws.column_dimensions[get_column_letter(base_col + 2)].width = 7

# ===== 创建评分表 =====
sheet_names = []
for g_idx, group in enumerate(groups):
    sname = '实操评分表{}'.format(g_idx + 1)
    sheet_names.append(sname)
    ws = wb.create_sheet(sname)
    create_score_sheet(ws, group)

# ===== Sheet1 总表 =====
ws1 = wb.active
ws1.title = 'Sheet1'

headers = ['大区', '区域', '人员', '实操环境', '用户中心', '实操记录',
           '是否阅卷', '分数', 'PC限停区域（30）', '社会主体（25）',
           '流程表单（20）', '移动端（15）', '视图（10）', '是否通过']

ws1.merge_cells('A1:N1')
ws1.cell(row=1, column=1).border = thin_border

for col_idx, h in enumerate(headers, 1):
    cell = ws1.cell(row=2, column=col_idx)
    cell.value = h
    cell.font = header_font
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = center_align

for idx, p in enumerate(people):
    row_num = idx + 3
    account = p['name'] + '1'  # 账号后缀可配置
    rec = records.get(account, '')

    g_idx = idx // group_size
    person_idx = idx % group_size
    sheet_name = sheet_names[g_idx]
    score_col = 5 + person_idx * 3 + 2
    scl = get_column_letter(score_col)

    ws1.cell(row=row_num, column=1).value = p['area']
    ws1.cell(row=row_num, column=2).value = p['region']
    ws1.cell(row=row_num, column=3).value = p['name']
    ws1.cell(row=row_num, column=4).value = PRACTICE_URL
    ws1.cell(row=row_num, column=5).value = USER_CENTER_URL
    ws1.cell(row=row_num, column=6).value = rec
    ws1.cell(row=row_num, column=7).value = ''
    ws1.cell(row=row_num, column=8).value = '=SUM(I{0}:M{0})'.format(row_num)

    for sec_idx, (s_start, s_end) in enumerate(SECTION_RANGES):
        ws1.cell(row=row_num, column=9 + sec_idx).value = \
            "=SUM('{0}'!{1}{2}:{1}{3})".format(sheet_name, scl, s_start, s_end)

    ws1.cell(row=row_num, column=14).value = '=IF(H{0}>=80,"是","否")'.format(row_num)

    for col_idx in range(1, 15):
        cell = ws1.cell(row=row_num, column=col_idx)
        cell.border = thin_border
        cell.alignment = wrap_align if col_idx in [4, 5] else center_align

# O列考官信息（按组合并）
cumulative = 2
for g_idx, group in enumerate(groups):
    start_row = cumulative + 1
    end_row = cumulative + len(group)
    ws1.merge_cells(start_row=start_row, start_column=15,
                    end_row=end_row, end_column=15)
    info = examiner_info.get(sheet_names[g_idx],
        '{}\n\nPC限停区域：待定\n社会主体：待定\n流程表单：待定\n移动端、视图：待定'.format(
            sheet_names[g_idx]))
    ws1.cell(row=start_row, column=15).value = info
    ws1.cell(row=start_row, column=15).alignment = \
        Alignment(wrap_text=True, vertical='top')
    ws1.cell(row=start_row, column=15).border = thin_border
    cumulative = end_row

col_widths = [12, 12, 10, 55, 55, 10, 10, 8, 18, 16, 16, 12, 10, 10, 28]
for i, w in enumerate(col_widths, 1):
    ws1.column_dimensions[get_column_letter(i)].width = w

wb.move_sheet('Sheet1', offset=-len(groups))
wb.save(output_path)
```

### Step 3: 验证
生成后打印确认信息，包含人员数量、分组情况、公式验证等。

## 使用示例

### 示例 1: 从 Excel 读取人员
```
用户: 帮我生成灵珑阅卷安排表，人员从 D:\xxx\考核计划.xlsx 的"灵珑"sheet读取，
     实操环境是 http://xxx/linglong/index.html#/my-space/app，
     用户中心是 http://xxx/usercenter/index.html#/login
```

### 示例 2: 直接提供人员名单
```
用户: 生成灵珑阅卷表，人员如下：
     华北二区-北京区域-张三
     华南大区-广东区域-李四
     实操环境: http://...
```

### 示例 3: 附带实操记录
```
用户: 生成灵珑阅卷表，人员从xxx读取，实操记录如截图所示 [截图]
```

## 模板文件

评分项结构模板存储在：`D:/opencode/linlong_score_template.json`

该文件包含：
- `items`: 51 行评分项数据（大项、子项、分值、描述）
- `merges`: 21 个合并单元格范围
- `total_rows`: 总行数

如需更新评分项结构，修改此 JSON 文件即可。

## 注意事项

- 账号规则：姓名 + 后缀（默认 "1"），如"张三" -> "张三1"
- 人员超过 16 人时自动分成多个评分表
- 所有分数通过公式自动计算，阅卷时只需填写扣分和扣分说明
- Sheet1 的 I-M 列通过跨表公式自动从评分表汇总
