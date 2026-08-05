# 第 4 课三级提示

## 提示 1

`contract.get(section)` 得到对象后，先用 `isinstance(value, list)` 检查形状。

## 提示 2

遍历 section 中的 case 字典，只保留 `case.get("expected_code") == expected_code`。

## 提示 3

结果是 `list[str]`。从每个匹配 case 读取 `name`，保持 JSON 文件中的原顺序，不要排序。
