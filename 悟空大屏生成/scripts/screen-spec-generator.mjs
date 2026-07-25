/**
 * ScreenSpec 自动生成器
 *
 * 输入：用户自然语言需求（如"做个城市管理大屏"）
 * 输出：符合 screen-spec.schema.json 的 ScreenSpec JSON 对象
 *
 * 纯规则 + 关键词匹配，不依赖 LLM。
 */

// ============================================================
// 一、业务域关键词词典
// ============================================================

/**
 * 每个域包含：
 *  - keywords: 触发关键词
 *  - label: 显示名
 *  - objects: 该域典型的业务对象
 *  - preferredLayout: 默认骨架布局
 *  - componentHints: 按 slot 角色推荐的组件 code 列表
 */
const DOMAIN_REGISTRY = [
  {
    id: 'urban-management',
    label: '城市管理',
    keywords: ['城管', '城市管理', '市容', '市政', '城综', '综合管理', '数字城管', '智慧城管'],
    objects: ['案件', '部件', '事件', '网格', '巡查', '问题', '工单'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'SeniorRing10', 'Progress'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1', 'Top5'],
      table: ['Swiper11', 'BasicTable1'],
    },
  },
  {
    id: 'social-governance',
    label: '社会治理',
    keywords: ['社会治理', '网格化', '综治', '平安', '矛盾调解', '社区治理', '基层治理'],
    objects: ['网格', '事件', '人口', '房屋', '重点人员', '矛盾纠纷'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'CircleType', 'SeniorRing7'],
      chart: ['BasicBar29', 'BasicLine5', 'BasicRadar'],
      ranking: ['MultiDataList1', 'Top5'],
      table: ['Swiper11', 'Swiper18'],
    },
  },
  {
    id: 'sanitation',
    label: '环卫',
    keywords: ['环卫', '垃圾', '清扫', '保洁', '转运', '收运', '渣土', '固废', '消纳'],
    objects: ['车辆', '人员', '垃圾站', '转运站', '消纳场', '路段', '作业量'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'WaveBall', 'Percent2'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11', 'BasicTable1'],
    },
  },
  {
    id: 'party-building',
    label: '党建',
    keywords: ['党建', '党员', '党组织', '党务', '红色', '基层党建', '智慧党建'],
    objects: ['党员', '党组织', '活动', '学习', '志愿服务', '积分'],
    preferredLayout: 'indicator-dashboard',
    componentHints: {
      header: ['Header7'],
      'metric-group': ['BasicData1', 'SeniorRing10', 'Progress'],
      chart: ['BasicBar29', 'SeniorRing12', 'BasicLine5'],
      ranking: ['MultiDataList1', 'Top5'],
      table: ['Swiper11'],
    },
  },
  {
    id: 'hotline-12345',
    label: '12345热线',
    keywords: ['12345', '热线', '市民服务', '市长热线', '便民热线', '投诉', '诉求', '工单'],
    objects: ['来电', '工单', '诉求', '满意度', '办结率', '超时', '催办'],
    preferredLayout: 'indicator-dashboard',
    componentHints: {
      header: ['Header7'],
      'metric-group': ['BasicData1', 'DashboardInfo1', 'SeniorRing10'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1', 'Top5'],
      table: ['Swiper11', 'Swiper18'],
    },
  },
  {
    id: 'law-enforcement',
    label: '综合执法',
    keywords: ['执法', '综合执法', '行政执法', '城管执法', '查处', '案件'],
    objects: ['案件', '执法人员', '巡查', '处罚', '整改', '立案'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'CircleType', 'SeniorRing10'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11', 'Swiper18'],
    },
  },
  {
    id: 'emergency',
    label: '应急管理',
    keywords: ['应急', '安全生产', '防汛', '防灾', '救援', '预警', '灾害', '消防'],
    objects: ['预警', '事件', '物资', '队伍', '避难场所', '监测点'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'SeniorRing10', 'WaveBall'],
      chart: ['BasicBar29', 'BasicLine5'],
      ranking: ['Swiper5', 'Swiper16'],
      table: ['Swiper2', 'Swiper11'],
    },
  },
  {
    id: 'transportation',
    label: '交通运输',
    keywords: ['交通', '运输', '公交', '地铁', '出行', '路网', '拥堵', '停车'],
    objects: ['车辆', '线路', '站点', '客流', '拥堵指数', '停车场'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'DashboardInfo1', 'CircleType'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11'],
    },
  },
  {
    id: 'ecology',
    label: '生态环保',
    keywords: ['环保', '生态', '污染', '排放', '空气', '水质', 'PM2.5', '碳排放'],
    objects: ['监测站', '污染源', '空气质量', '水质', '企业', '排放量'],
    preferredLayout: 'indicator-dashboard',
    componentHints: {
      header: ['Header7'],
      'metric-group': ['BasicData1', 'DashboardInfo1', 'WaveBall'],
      chart: ['BasicBar29', 'BasicLine5', 'BasicRadar'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11'],
    },
  },
  {
    id: 'smart-community',
    label: '智慧社区',
    keywords: ['社区', '小区', '物业', '居民', '智慧社区', '老旧小区'],
    objects: ['小区', '住户', '设备', '报修', '活动', '出入记录'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'SeniorRing10', 'Progress'],
      chart: ['BasicBar29', 'SeniorRing12'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11'],
    },
  },
  {
    id: 'water-affairs',
    label: '水务',
    keywords: ['水务', '供水', '排水', '管网', '水厂', '污水', '雨水', '河湖'],
    objects: ['泵站', '管网', '水厂', '水质', '水位', '流量'],
    preferredLayout: 'center-map-side-panels',
    componentHints: {
      header: ['Header7'],
      map: ['Map2d'],
      'metric-group': ['BasicData1', 'WaveBall', 'DashboardInfo1'],
      chart: ['BasicBar29', 'BasicLine5'],
      ranking: ['Swiper5'],
      table: ['Swiper11'],
    },
  },
  {
    id: 'iot-device',
    label: '物联网/设备监控',
    keywords: ['物联网', 'IoT', '设备', '传感器', '监控', '告警', '在线率'],
    objects: ['设备', '告警', '传感器', '在线率', '故障'],
    preferredLayout: 'list-monitor',
    componentHints: {
      header: ['Header7'],
      'metric-group': ['BasicData1', 'SeniorRing10', 'CircleType'],
      chart: ['BasicBar29', 'BasicLine5'],
      ranking: ['Swiper2', 'Swiper5'],
      table: ['Swiper11', 'BasicTable1'],
    },
  },
  {
    id: 'video-surveillance',
    label: '视频监控',
    keywords: ['视频', '监控', '摄像头', '视频巡查', '天网', '雪亮'],
    objects: ['摄像头', '视频流', '告警', '抓拍'],
    preferredLayout: 'video-device',
    componentHints: {
      header: ['Header7'],
      video: ['EgovaPlayer', 'CommonPlayer'],
      'metric-group': ['BasicData1'],
      table: ['Swiper11'],
    },
  },
];

// ============================================================
// 二、骨架布局模板
// ============================================================

/**
 * 三类标准骨架 + 视频监控骨架。
 * 分辨率默认 1920x1080。
 * slots 定义位置区域，组件选型时按 slot 分配。
 * rect 为建议的 {x, y, w, h}，用于后续坐标分配。
 */
const LAYOUT_TEMPLATES = {
  // 1. 中心地图 + 左右栏（城管/治理/应急等最常见）
  'center-map-side-panels': {
    type: 'center-map-side-panels',
    resolution: { width: 1920, height: 1080 },
    slots: [
      { id: 'header', role: 'header', description: '页面标题栏', rect: { x: 0, y: 0, w: 1920, h: 80 } },
      { id: 'left-top', role: 'metric-group', description: '左侧顶部指标区', rect: { x: 20, y: 100, w: 440, h: 200 } },
      { id: 'left-mid', role: 'chart', description: '左侧中部图表', rect: { x: 20, y: 320, w: 440, h: 300 } },
      { id: 'left-bottom', role: 'ranking', description: '左侧底部排名/列表', rect: { x: 20, y: 640, w: 440, h: 340 } },
      { id: 'center-map', role: 'map', description: '中心地图', rect: { x: 480, y: 100, w: 960, h: 880 } },
      { id: 'right-top', role: 'metric-group', description: '右侧顶部指标区', rect: { x: 1460, y: 100, w: 440, h: 200 } },
      { id: 'right-mid', role: 'chart', description: '右侧中部图表', rect: { x: 1460, y: 320, w: 440, h: 300 } },
      { id: 'right-bottom', role: 'table', description: '右侧底部表格/列表', rect: { x: 1460, y: 640, w: 440, h: 340 } },
    ],
  },

  // 2. 指标驾驶舱（无地图，纯指标+图表矩阵）
  'indicator-dashboard': {
    type: 'indicator-dashboard',
    resolution: { width: 1920, height: 1080 },
    slots: [
      { id: 'header', role: 'header', description: '页面标题栏', rect: { x: 0, y: 0, w: 1920, h: 80 } },
      { id: 'metrics-row', role: 'metric-group', description: '顶部核心指标行', rect: { x: 20, y: 100, w: 1880, h: 160 } },
      { id: 'chart-left', role: 'chart', description: '左侧图表', rect: { x: 20, y: 280, w: 620, h: 360 } },
      { id: 'chart-center', role: 'chart', description: '中部图表', rect: { x: 660, y: 280, w: 600, h: 360 } },
      { id: 'chart-right', role: 'chart', description: '右侧图表', rect: { x: 1280, y: 280, w: 620, h: 360 } },
      { id: 'bottom-left', role: 'ranking', description: '底部左侧排名', rect: { x: 20, y: 660, w: 620, h: 320 } },
      { id: 'bottom-center', role: 'table', description: '底部中间列表', rect: { x: 660, y: 660, w: 600, h: 320 } },
      { id: 'bottom-right', role: 'chart', description: '底部右侧图表', rect: { x: 1280, y: 660, w: 620, h: 320 } },
    ],
  },

  // 3. 列表监控屏（IoT/告警/滚动列表为主）
  'list-monitor': {
    type: 'list-monitor',
    resolution: { width: 1920, height: 1080 },
    slots: [
      { id: 'header', role: 'header', description: '页面标题栏', rect: { x: 0, y: 0, w: 1920, h: 80 } },
      { id: 'summary-bar', role: 'metric-group', description: '顶部汇总指标', rect: { x: 20, y: 100, w: 1880, h: 140 } },
      { id: 'alert-list', role: 'table', description: '告警/事件滚动列表', rect: { x: 20, y: 260, w: 940, h: 400 } },
      { id: 'trend-chart', role: 'chart', description: '趋势图表', rect: { x: 980, y: 260, w: 920, h: 400 } },
      { id: 'detail-left', role: 'ranking', description: '底部左侧排名', rect: { x: 20, y: 680, w: 620, h: 300 } },
      { id: 'detail-center', role: 'chart', description: '底部中间图表', rect: { x: 660, y: 680, w: 600, h: 300 } },
      { id: 'detail-right', role: 'table', description: '底部右侧设备列表', rect: { x: 1280, y: 680, w: 620, h: 300 } },
    ],
  },

  // 4. 视频/设备监控（大面积视频窗口 + 侧栏信息）
  'video-device': {
    type: 'video-device',
    resolution: { width: 1920, height: 1080 },
    slots: [
      { id: 'header', role: 'header', description: '页面标题栏', rect: { x: 0, y: 0, w: 1920, h: 80 } },
      { id: 'video-main', role: 'video', description: '主视频窗口', rect: { x: 20, y: 100, w: 1280, h: 720 } },
      { id: 'video-list', role: 'table', description: '视频源列表', rect: { x: 20, y: 840, w: 1280, h: 160 } },
      { id: 'side-metrics', role: 'metric-group', description: '右侧指标', rect: { x: 1320, y: 100, w: 580, h: 200 } },
      { id: 'side-alerts', role: 'table', description: '右侧告警列表', rect: { x: 1320, y: 320, w: 580, h: 680 } },
    ],
  },
};


// ============================================================
// 三、componentType 与 slot role 的映射
// ============================================================

/** slot role → 对应的 componentType (schema enum) */
const ROLE_TO_COMPONENT_TYPE = {
  header: 'text',
  map: 'map-region',
  'metric-group': 'multi-metric-card',
  chart: 'bar-chart',     // 默认，会按具体组件 code 覆盖
  ranking: 'ranking',
  table: 'scroll-list',
  tree: 'tree',
  video: 'video',
  filter: 'filter',
  detail: 'custom',
  custom: 'custom',
};

/**
 * 根据组件 code 推断更精确的 componentType。
 * 简单前缀/包含匹配即可覆盖大部分组件。
 */
function inferComponentType(code) {
  if (!code) return 'custom';
  const c = code.toLowerCase();

  // 地图
  if (c.startsWith('map')) return 'map-region';

  // 指标/数据卡
  if (c.startsWith('basicdata') || c.startsWith('basedata')) return 'metric-card';
  if (c.startsWith('dashboardinfo')) return 'metric-card';
  if (c.startsWith('waveball') || c.startsWith('seniorball')) return 'metric-card';
  if (c.startsWith('percent') || c === 'progress' || c === 'circletype' || c === 'peopleinfo') return 'metric-card';
  if (c.startsWith('seniorring10') || c.startsWith('seniorring7')) return 'metric-card';

  // 饼图/环形图
  if (c.startsWith('seniorring') || c.startsWith('customring') || c.startsWith('multipie')) return 'pie-chart';

  // 折线图
  if (c.startsWith('basicline')) return 'line-chart';

  // 柱状图/条形图
  if (c.startsWith('basicbar') || c.startsWith('bar3d') || c.startsWith('barmountain')) return 'bar-chart';
  if (c.startsWith('swiperbar') || c.startsWith('newswiperbar')) return 'bar-chart';

  // 排名/列表
  if (c.startsWith('multidatalist') || c === 'top5') return 'ranking';

  // 表格/滚动列表
  if (c.startsWith('basictable') || c.startsWith('swiper')) return 'scroll-list';

  // 视频
  if (c.includes('player') || c.includes('video') || c.includes('meeting')) return 'video';

  // 雷达图
  if (c.startsWith('basicradar')) return 'custom';

  // 树
  if (c.startsWith('basictree')) return 'tree';

  // 标题/头部
  if (c.startsWith('header') || c.startsWith('title')) return 'text';

  // 词云
  if (c === 'hotwords' || c.startsWith('basicwordcloud')) return 'custom';

  return 'custom';
}


// ============================================================
// 四、数据意图推断
// ============================================================

/**
 * 根据 slot role、业务对象列表、组件类型 推断 dataIntent。
 */
function inferDataIntent(role, objects, componentType, slotDesc) {
  const mainObj = objects[0] || '数据';

  switch (role) {
    case 'header':
      return null; // 标题不需要数据绑定

    case 'map':
      return {
        object: mainObj,
        aggregation: 'points',
        notes: `在地图上展示${mainObj}的地理分布`,
      };

    case 'metric-group':
      return {
        object: mainObj,
        aggregation: 'count',
        notes: `展示${objects.slice(0, 3).join('/')}的核心统计指标`,
      };

    case 'chart': {
      // 根据 componentType 细分
      if (componentType === 'line-chart') {
        return {
          object: mainObj,
          aggregation: 'trend',
          notes: `按时间展示${mainObj}的变化趋势`,
        };
      }
      if (componentType === 'pie-chart') {
        return {
          object: mainObj,
          aggregation: 'group',
          notes: `按类别展示${mainObj}的占比分布`,
        };
      }
      // 默认柱状图
      return {
        object: mainObj,
        aggregation: 'group',
        notes: `按维度对比${mainObj}的数量或金额`,
      };
    }

    case 'ranking':
      return {
        object: mainObj,
        aggregation: 'rank',
        notes: `按指标排名展示 Top N ${mainObj}`,
      };

    case 'table':
      return {
        object: mainObj,
        aggregation: 'list',
        fields: ['名称', '时间', '状态', '负责人'],
        notes: `滚动展示最新的${mainObj}明细列表`,
      };

    case 'video':
      return {
        object: '视频流',
        aggregation: 'list',
        notes: '接入实时视频监控流',
      };

    default:
      return {
        object: mainObj,
        aggregation: 'custom',
        notes: slotDesc || `展示${mainObj}相关信息`,
      };
  }
}


// ============================================================
// 五、核心生成逻辑
// ============================================================

/**
 * 从用户需求中推断业务域。
 * 返回匹配度最高的域定义，找不到则返回通用默认域。
 */
function detectDomain(prompt) {
  const normalized = prompt.toLowerCase();
  let bestMatch = null;
  let bestScore = 0;

  for (const domain of DOMAIN_REGISTRY) {
    let score = 0;
    for (const kw of domain.keywords) {
      if (normalized.includes(kw.toLowerCase())) {
        // 更长的关键词给更高的分
        score += kw.length;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestMatch = domain;
    }
  }

  if (bestMatch) return bestMatch;

  // 通用回退域
  return {
    id: 'general',
    label: '综合管理',
    keywords: [],
    objects: ['数据', '指标', '事件'],
    preferredLayout: 'indicator-dashboard',
    componentHints: {
      header: ['Header7'],
      'metric-group': ['BasicData1', 'SeniorRing10'],
      chart: ['BasicBar29', 'BasicLine5', 'SeniorRing12'],
      ranking: ['MultiDataList1'],
      table: ['Swiper11'],
    },
  };
}

/**
 * 从用户需求中提取可能的区域信息（省/市/区/县）。
 * 排除动词+名词误匹配（如"做个城市"）。
 */
function extractRegion(prompt) {
  // 先排除明显不是地名的词（动词+城市/管理 等）
  const cleaned = prompt.replace(/(?:做|搭|建|生成|创建|设计|开发)(?:个|一个)?/g, '');
  // 匹配常见行政区划后缀：必须是真实地名（前面是汉字，后面是省/市/区/县等）
  const regionPattern = /([一-龥]{2,6}(?:省|自治区|自治州|市|区|县|新区|高新区|开发区))/g;
  const matches = cleaned.match(regionPattern);
  if (!matches) return undefined;

  // 过滤掉通用词（"城市""区域"等不是真实地名）
  const genericWords = ['城市', '城区', '市区', '区域', '县城', '社区', '小区', '新区域'];
  const filtered = matches.filter(m => !genericWords.includes(m));
  return filtered.length > 0 ? filtered[0] : undefined;
}

/**
 * 从用户需求中提取时间范围线索。
 */
function extractTimeRange(prompt) {
  if (/实时|实况|当前/.test(prompt)) return '实时';
  if (/今[日天]|当[日天]/.test(prompt)) return '今日';
  if (/本[周]|这[周]/.test(prompt)) return '本周';
  if (/本月|当月/.test(prompt)) return '本月';
  if (/本[年]|今年|年度/.test(prompt)) return '本年';
  if (/近\s*(\d+)\s*天/.test(prompt)) return prompt.match(/近\s*(\d+)\s*天/)[0];
  if (/近\s*(\d+)\s*月/.test(prompt)) return prompt.match(/近\s*(\d+)\s*月/)[0];
  return undefined;
}

/**
 * 从用户需求中提取额外的业务对象关键词。
 * 将用户明确提到但域默认列表中没有的对象加入。
 */
function extractExtraObjects(prompt, domainObjects) {
  const objectPatterns = [
    '案件', '工单', '人员', '车辆', '设备', '网格', '小区', '楼栋',
    '管网', '泵站', '摄像头', '告警', '预警', '投诉', '满意度',
    '巡查', '考核', '积分', '排名', '进度', '完成率', '处置率',
    '响应率', '办结率', '超时率', '覆盖率', '合格率',
  ];

  const extras = [];
  for (const pat of objectPatterns) {
    if (prompt.includes(pat) && !domainObjects.includes(pat)) {
      extras.push(pat);
    }
  }
  return extras;
}

/**
 * 推断用户想要的布局类型。
 * 优先看用户是否明确指定，否则用域默认。
 */
function detectLayout(prompt, domain) {
  const p = prompt.toLowerCase();

  // 用户明确指定
  if (/驾驶舱|仪表盘|dashboard|指标屏|指标大屏/.test(p)) return 'indicator-dashboard';
  if (/地图|gis|空间|分布/.test(p)) return 'center-map-side-panels';
  if (/列表|监控屏|告警屏|设备监控/.test(p)) return 'list-monitor';
  if (/视频|监控视频|摄像/.test(p)) return 'video-device';

  return domain.preferredLayout;
}

/**
 * 生成标题。
 * 如果用户需求里有明确标题就用，否则拼一个。
 */
function generateTitle(prompt, domain, region) {
  // 尝试从引号中提取标题
  const quoted = prompt.match(/[""「」『』]([^""「」『』]+)[""「」『』]/);
  if (quoted) return quoted[1];

  // 尝试提取"XX大屏/驾驶舱/监控屏"等完整名称
  // 先去掉前导的"做个/帮我搭"等动词
  const cleaned = prompt.replace(/^(?:帮我|请|给我|帮忙)?(?:做|搭|建|生成|创建|设计|开发|出)(?:个|一个|一份)?/g, '').trim();
  const screenTitle = cleaned.match(/([一-龥A-Za-z0-9]{2,20}(?:大屏|驾驶舱|监控屏|指挥屏|指标屏|数据屏))/);
  if (screenTitle) return screenTitle[1];

  // 自动拼接
  const prefix = region ? `${region}` : '';
  return `${prefix}${domain.label}数据大屏`;
}

/**
 * 为每个 slot 选择最合适的组件 code。
 * 返回 { slotId: code }
 */
function selectComponents(slots, hints, prompt) {
  const result = {};
  const p = prompt.toLowerCase();

  for (const slot of slots) {
    const role = slot.role;
    const candidates = hints[role];
    if (!candidates || candidates.length === 0) {
      // 没有候选，跳过（header 等辅助 slot 可能无组件）
      continue;
    }

    // 简单策略：对于 chart 角色的 slot，轮换选择不同类型的图表
    if (role === 'chart') {
      // 已选过的 chart code
      const usedCharts = Object.values(result).filter(c =>
        candidates.includes(c)
      );
      // 选一个没用过的
      const unused = candidates.filter(c => !usedCharts.includes(c));
      result[slot.id] = unused.length > 0 ? unused[0] : candidates[0];
    } else {
      // 其他角色取第一个推荐
      result[slot.id] = candidates[0];
    }
  }

  return result;
}

/**
 * 生成唯一组件 ID。
 * 格式：role-slotIndex（符合 schema pattern: ^[A-Za-z][A-Za-z0-9_\-]*$）
 */
function makeComponentId(role, slotId) {
  // 把中文/特殊字符替换掉，保留字母数字和连字符
  const safeSlot = slotId.replace(/[^A-Za-z0-9]/g, '-').replace(/-+/g, '-');
  return `comp-${safeSlot}`;
}


// ============================================================
// 六、主入口
// ============================================================

/**
 * 根据用户自然语言需求生成 ScreenSpec JSON 对象。
 *
 * @param {string} userPrompt - 用户需求描述，如"做个城市管理大屏"
 * @param {object} [options] - 可选配置
 * @param {string} [options.resolution] - 分辨率，如 "1920x1080"（默认）、"3840x2160"
 * @param {string} [options.forceLayout] - 强制使用的布局类型
 * @param {string[]} [options.extraObjects] - 额外指定的业务对象
 * @param {boolean} [options.withInteractions] - 是否生成交互定义（默认 true）
 * @param {boolean} [options.withFilters] - 是否生成筛选器（默认 true）
 * @returns {object} 符合 screen-spec.schema.json 的 ScreenSpec 对象
 */
export function generateScreenSpec(userPrompt, options = {}) {
  if (!userPrompt || typeof userPrompt !== 'string' || userPrompt.trim().length === 0) {
    throw new Error('userPrompt 不能为空');
  }

  const prompt = userPrompt.trim();

  // --- 1. 推断业务域 ---
  const domain = detectDomain(prompt);

  // --- 2. 确定布局类型 ---
  const layoutType = options.forceLayout || detectLayout(prompt, domain);
  const layoutTemplate = LAYOUT_TEMPLATES[layoutType];
  if (!layoutTemplate) {
    throw new Error(`未知的布局类型: ${layoutType}`);
  }

  // --- 3. 解析分辨率 ---
  let resolution = { ...layoutTemplate.resolution };
  if (options.resolution) {
    const parts = options.resolution.split('x');
    if (parts.length === 2) {
      resolution = { width: parseInt(parts[0], 10), height: parseInt(parts[1], 10) };
    }
  }

  // 如果分辨率和模板不同，按比例缩放 slot 坐标
  const scaleX = resolution.width / layoutTemplate.resolution.width;
  const scaleY = resolution.height / layoutTemplate.resolution.height;

  // --- 4. 提取场景信息 ---
  const region = extractRegion(prompt);
  const timeRange = extractTimeRange(prompt);
  const allObjects = [
    ...domain.objects,
    ...extractExtraObjects(prompt, domain.objects),
    ...(options.extraObjects || []),
  ];
  // 去重
  const uniqueObjects = [...new Set(allObjects)];

  // --- 5. 生成标题 ---
  const title = generateTitle(prompt, domain, region);

  // --- 6. 构建 slots（去掉 rect，rect 不在 schema 里） ---
  const slots = layoutTemplate.slots.map(s => ({
    id: s.id,
    role: s.role,
    description: s.description,
  }));

  // --- 7. 为每个 slot 选组件 ---
  const componentSelection = selectComponents(layoutTemplate.slots, domain.componentHints, prompt);

  // --- 8. 构建 components 数组 ---
  const components = [];
  for (const slot of layoutTemplate.slots) {
    const code = componentSelection[slot.id];
    if (!code) continue; // 该 slot 无组件可分配

    const compType = inferComponentType(code);
    const compId = makeComponentId(slot.role, slot.id);
    const dataIntent = inferDataIntent(slot.role, uniqueObjects, compType, slot.description);

    const component = {
      id: compId,
      slot: slot.id,
      intent: slot.description,
      componentType: compType,
      preferredComponentName: code,
    };

    if (dataIntent) {
      component.dataIntent = dataIntent;
    }

    // 地图和表格设置自动刷新
    if (slot.role === 'map' || slot.role === 'table') {
      component.refresh = { mode: 'interval', seconds: 60 };
    }

    // 视频实时
    if (slot.role === 'video') {
      component.refresh = { mode: 'interval', seconds: 5 };
    }

    components.push(component);
  }

  // --- 9. 构建筛选器 ---
  const filters = [];
  const withFilters = options.withFilters !== false;

  if (withFilters) {
    // 地图布局：添加区域筛选
    if (layoutType === 'center-map-side-panels') {
      filters.push({
        id: 'filter-region',
        type: 'region',
        scope: 'global',
        targetComponents: components.map(c => c.id),
      });
    }

    // 通用：添加时间范围筛选
    filters.push({
      id: 'filter-date-range',
      type: 'date-range',
      scope: 'global',
      defaultValue: timeRange || '本月',
      targetComponents: components.filter(c => c.dataIntent).map(c => c.id),
    });
  }

  // --- 10. 构建交互 ---
  const interactions = [];
  const withInteractions = options.withInteractions !== false;

  if (withInteractions) {
    // 找地图组件和排名/表格组件，建立联动
    const mapComp = components.find(c => c.componentType === 'map-region');
    const tableComps = components.filter(c =>
      c.componentType === 'scroll-list' || c.componentType === 'ranking'
    );

    if (mapComp && tableComps.length > 0) {
      interactions.push({
        source: mapComp.id,
        event: 'click',
        targets: tableComps.map(c => c.id),
        effect: 'refresh-data',
        payload: { paramKey: 'regionCode' },
      });
    }

    // 排名点击 → 弹窗明细
    const rankingComps = components.filter(c => c.componentType === 'ranking');
    for (const rc of rankingComps) {
      interactions.push({
        source: rc.id,
        event: 'click',
        targets: [rc.id],
        effect: 'open-detail',
        payload: { paramKey: 'id' },
      });
    }
  }

  // --- 11. 组装最终 ScreenSpec ---
  const spec = {
    version: '0.1',
    title,
    scene: {
      domain: domain.label,
      businessObjects: uniqueObjects,
    },
    layout: {
      type: layoutType,
      resolution,
      slots,
    },
    components,
    quality: {
      allowFallbackStaticData: true,
      requirePreviewPass: true,
      notes: [
        `业务域: ${domain.label}(${domain.id})`,
        `布局: ${layoutType}`,
        `组件数: ${components.length}`,
        `自动生成，需人工校准数据接口和样式`,
      ],
    },
  };

  // 可选字段仅在非空时添加
  if (region) spec.scene.region = region;
  if (timeRange) spec.scene.timeRange = timeRange;
  if (filters.length > 0) spec.filters = filters;
  if (interactions.length > 0) spec.interactions = interactions;

  return spec;
}


// ============================================================
// 七、工具函数（供外部调用）
// ============================================================

/** 列出所有已注册的业务域 */
export function listDomains() {
  return DOMAIN_REGISTRY.map(d => ({
    id: d.id,
    label: d.label,
    keywords: d.keywords,
    preferredLayout: d.preferredLayout,
  }));
}

/** 列出所有可用的布局类型 */
export function listLayouts() {
  return Object.entries(LAYOUT_TEMPLATES).map(([type, tpl]) => ({
    type,
    slotCount: tpl.slots.length,
    roles: tpl.slots.map(s => s.role),
  }));
}

/** 获取布局模板的 slot 详情（含建议坐标） */
export function getLayoutSlots(layoutType) {
  const tpl = LAYOUT_TEMPLATES[layoutType];
  if (!tpl) return null;
  return tpl.slots.map(s => ({ ...s }));
}


// ============================================================
// 八、CLI 入口（直接 node 运行时输出示例）
// ============================================================

const isMainModule = typeof process !== 'undefined'
  && process.argv[1]
  && (
    process.argv[1].endsWith('screen-spec-generator.mjs')
    || process.argv[1].replace(/\\/g, '/').endsWith('screen-spec-generator.mjs')
  );

if (isMainModule) {
  const prompt = process.argv[2] || '做个城市管理大屏';
  console.log(`\n输入: "${prompt}"\n`);
  const spec = generateScreenSpec(prompt);
  console.log(JSON.stringify(spec, null, 2));
}
