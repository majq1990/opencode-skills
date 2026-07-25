# WukongBlueprint 草案结构

`WukongBlueprint` 是原型图和悟空配置之间的中间层。它描述“要生成什么”，不是悟空原始 JSON。

## 最小结构

```json
{
  "version": "0.1",
  "input": {
    "mode": "prototype-image",
    "source": "path-or-description"
  },
  "screen": {
    "title": "城市运行态势大屏",
    "domain": "城市治理",
    "resolution": [1920, 1080],
    "layout": "center-map-side-panels"
  },
  "visualRegions": [],
  "widgets": [],
  "assets": [],
  "interactions": [],
  "dataIntents": [],
  "templatePlan": {
    "mode": "screen-template | component-rebuild | static-shell",
    "candidates": [],
    "fallbackReason": ""
  },
  "landing": {
    "targetAccount": "majianquan",
    "targetGroup": "Codex隔离测试",
    "mode": "package-patch",
    "requiresConfirmation": true
  },
  "quality": {
    "requireListAudit": true,
    "requirePreviewScreenshot": true,
    "requireInteractionSmoke": false
  }
}
```

## visualRegions

```json
{
  "id": "left_top_panel",
  "layer": "component",
  "role": "metric-group",
  "bbox": {"x": 40, "y": 160, "width": 430, "height": 240},
  "confidence": 0.82,
  "restoration": "wukong-component"
}
```

`restoration` 可选：

| 值 | 含义 |
| --- | --- |
| `wukong-component` | 还原为悟空组件 |
| `reuse-template` | 复用模板组件 |
| `slice-asset` | 切图为素材 |
| `placeholder` | 先占位，后续确认 |

## widgets

```json
{
  "id": "case_total",
  "role": "metric-card",
  "regionId": "left_top_panel",
  "componentHint": "BasicInfo",
  "title": "案件总数",
  "bbox": {"x": 60, "y": 190, "width": 180, "height": 90},
  "dataIntent": {
    "object": "案件",
    "metric": "总数",
    "resultShape": "metric-card"
  }
}
```

## interactions

```json
{
  "id": "region_filter_refresh",
  "source": "region_select",
  "event": "change",
  "targets": ["case_total", "case_trend", "case_rank"],
  "effect": "refresh-data"
}
```

## dataIntents

只描述业务目标，不写死接口：

```json
{
  "widgetId": "case_total",
  "businessObject": "案件",
  "need": "统计指定区域和时间范围内案件总数",
  "filters": ["region", "dateRange"],
  "expectedResult": [{"name": "案件总数", "value": 0, "unit": "件"}]
}
```

